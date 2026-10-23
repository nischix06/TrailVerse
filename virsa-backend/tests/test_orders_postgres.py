import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from unittest.mock import patch
from urllib.parse import urlsplit

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.api.routes.orders import (
    _decrement_stock as real_decrement_stock,
    checkout,
    cancel_order,
)
from app.models.artwork import Artwork
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem
from app.models.user import User
from app.schemas.order import CheckoutRequest


POSTGRES_URL = os.getenv("POSTGRES_TEST_DATABASE_URL")
MIGRATION_TIMEOUT_SECONDS = 30
CONNECT_TIMEOUT_SECONDS = 5
DEDICATED_DATABASE_NAME = "trailverse_test"
DEDICATED_DATABASE_USER = "trailverse_test"
ALLOWED_TEST_HOSTS = {"localhost", "127.0.0.1", "::1"}

pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason=(
        "Set POSTGRES_TEST_DATABASE_URL to an isolated PostgreSQL "
        "database to run concurrency integration tests."
    ),
)

@pytest.fixture(scope="session")
def postgres_engine():
    assert POSTGRES_URL is not None

    if os.getenv("ALLOW_DESTRUCTIVE_POSTGRES_TESTS") != "1":
        pytest.fail(
            "Destructive PostgreSQL tests require explicit opt-in: "
            "set ALLOW_DESTRUCTIVE_POSTGRES_TESTS=1 only for a disposable "
            "local test database or the isolated CI PostgreSQL service."
        )

    parsed_url = urlsplit(POSTGRES_URL)

    if parsed_url.scheme not in {"postgresql", "postgresql+psycopg"}:
        pytest.fail(
            "POSTGRES_TEST_DATABASE_URL must use a PostgreSQL SQLAlchemy URL."
        )

    database_name = parsed_url.path.lstrip("/").split("?", 1)[0]

    if database_name != DEDICATED_DATABASE_NAME:
        pytest.fail(
            "POSTGRES_TEST_DATABASE_URL must target the dedicated "
            f"'{DEDICATED_DATABASE_NAME}' database."
        )

    if parsed_url.hostname not in ALLOWED_TEST_HOSTS:
        pytest.fail(
            "Destructive PostgreSQL tests may connect only to a local "
            "PostgreSQL host: localhost, 127.0.0.1, or ::1."
        )

    if parsed_url.username != DEDICATED_DATABASE_USER:
        pytest.fail(
            "POSTGRES_TEST_DATABASE_URL must use the dedicated "
            f"'{DEDICATED_DATABASE_USER}' database user."
        )

    engine = create_engine(
        POSTGRES_URL,
        connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
        pool_size=8,
        max_overflow=4,
    )

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        engine.dispose()
        pytest.fail(
            "Could not connect to the dedicated PostgreSQL test database "
            f"within {CONNECT_TIMEOUT_SECONDS} seconds: "
            f"{type(exc).__name__}: {exc}"
        )

    migration_environment = os.environ.copy()
    migration_environment["DATABASE_URL"] = POSTGRES_URL
    migration_directory = os.path.dirname(os.path.dirname(__file__))

    def run_migration(*arguments):
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "alembic", *arguments],
                cwd=migration_directory,
                env=migration_environment,
                capture_output=True,
                text=True,
                timeout=MIGRATION_TIMEOUT_SECONDS,
                check=True,
            )
        except subprocess.TimeoutExpired:
            pytest.fail(
                f"Alembic {' '.join(arguments)} exceeded the "
                f"{MIGRATION_TIMEOUT_SECONDS}-second timeout. "
                "The PostgreSQL connection or migration may be stuck."
            )
        except subprocess.CalledProcessError as exc:
            output = "\n".join(
                part for part in (exc.stdout, exc.stderr) if part
            )
            pytest.fail(
                f"Alembic {' '.join(arguments)} failed with exit code "
                f"{exc.returncode}:\n{output}"
            )

        return completed

    run_migration("downgrade", "base")
    run_migration("upgrade", "head")

    yield engine

    try:
        run_migration("downgrade", "base")
    finally:
        engine.dispose()

@pytest.fixture
def postgres_session_factory(postgres_engine):
    factory = sessionmaker(
        bind=postgres_engine,
        autoflush=False,
        expire_on_commit=False,
    )
    with factory() as cleanup:
        cleanup.execute(
            text(
                "TRUNCATE TABLE order_items, orders, cart_items, carts, "
                "artworks, seller_applications, users "
                "RESTART IDENTITY CASCADE"
            )
        )
        cleanup.commit()
    return factory


def _seed_customer(factory, email):
    with factory() as db:
        user = User(
            name=email.split("@")[0],
            email=email,
            hashed_password="test-only",
            role="customer",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id

def _seed_artwork_and_cart(factory, customer_ids, stock, quantities):
    with factory() as db:
        seller = User(
            name="Seller",
            email="seller@example.com",
            hashed_password="test-only",
            role="seller",
            is_active=True,
        )
        db.add(seller)
        db.flush()
        artwork = Artwork(
            seller_id=seller.id,
            title="Concurrent artwork",
            description="PostgreSQL concurrency fixture.",
            price=Decimal("10.00"),
            stock_quantity=stock,
            category="Textiles",
            state="Punjab",
            image_url="https://example.com/artwork.jpg",
            status="published",
        )
        db.add(artwork)
        db.flush()
        for customer_id, quantity in zip(customer_ids, quantities):
            cart = Cart(user_id=customer_id)
            db.add(cart)
            db.flush()
            db.add(
                CartItem(
                    cart_id=cart.id,
                    artwork_id=artwork.id,
                    quantity=quantity,
                )
            )
        db.commit()
        return artwork.id


def _run_checkout(factory, customer_id):
    with factory() as db:
        customer = db.get(User, customer_id)
        try:
            order = checkout(
                current_user=customer,
                db=db,
                _payload=CheckoutRequest(),
            )
            return ("success", order.id)
        except Exception as exc:
            return ("error", type(exc).__name__, str(exc))


@pytest.mark.parametrize("attempt", range(3))
def test_postgres_two_customers_compete_for_one_unit(
    postgres_session_factory,
    attempt,
):
    first = _seed_customer(
        postgres_session_factory,
        f"first-{attempt}@example.com",
    )
    second = _seed_customer(
        postgres_session_factory,
        f"second-{attempt}@example.com",
    )
    artwork_id = _seed_artwork_and_cart(
        postgres_session_factory,
        [first, second],
        stock=1,
        quantities=[1, 1],
    )
    barrier = Barrier(2)

    def synchronized_decrement(db, artwork_id, quantity):
        barrier.wait(timeout=15)
        return real_decrement_stock(db, artwork_id, quantity)

    with patch(
        "app.api.routes.orders._decrement_stock",
        side_effect=synchronized_decrement,
    ):
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(
                executor.map(
                    lambda customer_id: _run_checkout(
                        postgres_session_factory,
                        customer_id,
                    ),
                    [first, second],
                )
            )

    with postgres_session_factory() as db:
        artwork = db.get(Artwork, artwork_id)
        assert artwork.stock_quantity == 0
        assert db.query(Order).count() == 1
        assert db.query(OrderItem).count() == 1
        assert sum(result[0] == "success" for result in results) == 1


def test_postgres_concurrent_quantities_cannot_exceed_stock(
    postgres_session_factory,
):
    customers = [
        _seed_customer(postgres_session_factory, f"quantity-{i}@example.com")
        for i in range(3)
    ]
    artwork_id = _seed_artwork_and_cart(
        postgres_session_factory,
        customers,
        stock=5,
        quantities=[3, 3, 2],
    )
    barrier = Barrier(3)

    def synchronized_decrement(db, artwork_id, quantity):
        barrier.wait(timeout=15)
        return real_decrement_stock(db, artwork_id, quantity)

    with patch(
        "app.api.routes.orders._decrement_stock",
        side_effect=synchronized_decrement,
    ):
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(
                executor.map(
                    lambda customer_id: _run_checkout(
                        postgres_session_factory,
                        customer_id,
                    ),
                    customers,
                )
            )

    with postgres_session_factory() as db:
        artwork = db.get(Artwork, artwork_id)
        sold = sum(
            item.quantity
            for item in db.query(OrderItem)
            .join(Order)
            .filter(Order.status == "pending")
            .all()
        )
        assert artwork.stock_quantity >= 0
        assert sold <= 5
        assert sum(result[0] == "success" for result in results) >= 1


def test_postgres_multi_item_failure_rolls_back_everything(
    postgres_session_factory,
):
    customer = _seed_customer(
        postgres_session_factory,
        "multi-item@example.com",
    )
    with postgres_session_factory() as db:
        seller = User(
            name="Multi Seller",
            email="multi-seller@example.com",
            hashed_password="test-only",
            role="seller",
            is_active=True,
        )
        db.add(seller)
        db.flush()
        artworks = [
            Artwork(
                seller_id=seller.id,
                title=f"Artwork {index}",
                description="Rollback fixture.",
                price=Decimal("10.00"),
                stock_quantity=2,
                category="Textiles",
                state="Punjab",
                image_url="https://example.com/artwork.jpg",
                status="published",
            )
            for index in range(2)
        ]
        db.add_all(artworks)
        db.flush()
        cart = Cart(user_id=customer)
        db.add(cart)
        db.flush()
        db.add_all(
            [
                CartItem(
                    cart_id=cart.id,
                    artwork_id=artwork.id,
                    quantity=1,
                )
                for artwork in artworks
            ]
        )
        db.commit()
        artwork_ids = [artwork.id for artwork in artworks]

    calls = 0

    def decrement_then_fail(db, artwork_id, quantity):
        nonlocal calls
        calls += 1
        if calls == 1:
            return real_decrement_stock(db, artwork_id, quantity)
        return False

    with patch(
        "app.api.routes.orders._decrement_stock",
        side_effect=decrement_then_fail,
    ):
        result = _run_checkout(postgres_session_factory, customer)

    assert result[0] == "error"
    with postgres_session_factory() as db:
        assert db.query(Order).count() == 0
        assert db.query(OrderItem).count() == 0
        assert db.query(CartItem).count() == 2
        assert [
            db.get(Artwork, artwork_id).stock_quantity
            for artwork_id in artwork_ids
        ] == [2, 2]


def test_postgres_concurrent_cancellation_restores_once(
    postgres_session_factory,
):
    customer = _seed_customer(
        postgres_session_factory,
        "cancel-race@example.com",
    )
    artwork_id = _seed_artwork_and_cart(
        postgres_session_factory,
        [customer],
        stock=5,
        quantities=[2],
    )
    result = _run_checkout(postgres_session_factory, customer)
    assert result[0] == "success"
    order_id = result[1]
    barrier = Barrier(2)

    def run_cancel():
        barrier.wait(timeout=15)
        with postgres_session_factory() as db:
            user = db.get(User, customer)
            try:
                order = cancel_order(order_id, user, db)
                return ("success", order.status)
            except Exception as exc:
                return ("error", type(exc).__name__, str(exc))

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: run_cancel(), range(2)))

    with postgres_session_factory() as db:
        artwork = db.get(Artwork, artwork_id)
        order = db.get(Order, order_id)
        assert artwork.stock_quantity == 5
        assert order.status == "cancelled"
        assert sum(result[0] == "success" for result in results) == 1
