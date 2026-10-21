# Architecture Decision Records (ADR) & Major Coding Decisions

> **Project:** TrailVerse / Virsa  
> **Status:** Active & Maintained  
> **Rule for Contributors & AI Agents:** Whenever introducing an architectural pattern, choosing a major library, changing database structure, or modifying authentication/authorization semantics, you **must** log the decision in this document following the template below.

---

## 📑 Table of Contents

- [Maintenance Policy & Decision Template](#maintenance-policy--decision-template)
- [Summary of Decisions](#summary-of-decisions)
- [ADR-001: Workspace & Monorepo Structure](#adr-001-workspace--monorepo-structure)
- [ADR-002: Backend Framework Selection (FastAPI + Uvicorn)](#adr-002-backend-framework-selection-fastapi--uvicorn)
- [ADR-003: API Routing Hierarchy and Versioning Strategy](#adr-003-api-routing-hierarchy-and-versioning-strategy)
- [ADR-004: Data Validation, Serialization, and DTOs (Pydantic v2)](#adr-004-data-validation-serialization-and-dtos-pydantic-v2)
- [ADR-005: Database ORM and Connection Strategy (SQLAlchemy 2.0)](#adr-005-database-orm-and-connection-strategy-sqlalchemy-20)
- [ADR-006: Database Schema Migrations (Alembic)](#adr-006-database-schema-migrations-alembic)
- [ADR-007: Authentication & Token Architecture (JWT with Dual Login Endpoints)](#adr-007-authentication--token-architecture-jwt-with-dual-login-endpoints)
- [ADR-008: Password Security & Cryptography (Bcrypt via Passlib)](#adr-008-password-security--cryptography-bcrypt-via-passlib)
- [ADR-009: Layered Dependency Injection & Role-Based Access Control (RBAC)](#adr-009-layered-dependency-injection--role-based-access-control-rbac)
- [ADR-010: E-Commerce Relational Domain Modeling & Integrity Constraints](#adr-010-e-commerce-relational-domain-modeling--integrity-constraints)
- [ADR-011: Inventory Reservation & Checkout Concurrency Control](#adr-011-inventory-reservation--checkout-concurrency-control)
- [ADR-012: Configuration Management & 12-Factor Environment Settings](#adr-012-configuration-management--12-factor-environment-settings)
- [ADR-013: Streamlined Minimal Backend Architecture](#adr-013-streamlined-minimal-backend-architecture)
- [ADR-014: Modern Authentication Cryptography (pwdlib[argon2] & PyJWT)](#adr-014-modern-authentication-cryptography-pwdlibargon2--pyjwt)
- [ADR-015: User-Focused Backend Scope and Database Baseline](#adr-015-user-focused-backend-scope-and-database-baseline)
- [ADR-016: User Registration and Credential Persistence](#adr-016-user-registration-and-credential-persistence)
- [ADR-017: JSON Login and JWT Identity](#adr-017-json-login-and-jwt-identity)

---

## Maintenance Policy & Decision Template

### Policy
1. **Immutable History:** Once a decision is accepted and implemented, do not delete it. If the decision changes in the future, mark its status as `Superseded by ADR-XXX` and create a new record.
2. **Mandatory Documentation:** Every major new service, library, data layer modification, security change, or integration must be recorded here before or immediately after implementation.

### Decision Template
```markdown
### ADR-XXX: [Short Descriptive Title]

- **Date:** YYYY-MM-DD
- **Status:** [Proposed | Accepted | Implemented | Deprecated | Superseded by ADR-YYY]
- **Components:** [e.g., Backend, Auth, Database, API, Frontend]

#### Context
What problem was being addressed? What constraints or considerations were present?

#### Decision
What choice was made? What technologies, patterns, or architecture were adopted?

#### Consequences & Rationale
- **Benefits:** Why this is good.
- **Trade-offs / Risks:** What we sacrifice or must monitor.
- **Alternatives Considered:** What options were rejected and why.
```

---

## Summary of Decisions

| ID | Title | Status | Primary Component |
| :--- | :--- | :--- | :--- |
| **ADR-001** | Workspace & Monorepo Structure | `Implemented` | Project Architecture |
| **ADR-002** | Backend Framework Selection (FastAPI + Uvicorn) | `Implemented` | Backend Framework |
| **ADR-003** | API Routing Hierarchy & Versioning (`/api/v1`) | `Implemented` | API Design |
| **ADR-004** | Data Validation, Serialization, and DTOs (Pydantic v2) | `Implemented` | Data Validation |
| **ADR-005** | Database ORM & Session Lifecycle (SQLAlchemy 2.0) | `Implemented` | Persistence Layer |
| **ADR-006** | Database Schema Migrations (Alembic) | `Implemented` | Database Tooling |
| **ADR-007** | JWT Authentication with Dual Login Endpoints | `Implemented` | Authentication & Security |
| **ADR-008** | Password Hashing (Bcrypt via Passlib) | `Implemented` | Security / Crypto |
| **ADR-009** | Layered Dependency Injection & RBAC | `Implemented` | Authorization & Architecture |
| **ADR-010** | Relational Domain Modeling & Referential Integrity | `Implemented` | Data Modeling |
| **ADR-011** | Inventory Reservation & Checkout Concurrency (`with_for_update`) | `Implemented` | Business Logic / Transactions |
| **ADR-012** | 12-Factor Environment Settings (`pydantic-settings`) | `Implemented` | Configuration & DevOps |
| **ADR-013** | Streamlined Minimal Backend Architecture | `Implemented` | Project Architecture |
| **ADR-014** | Modern Authentication Cryptography (`pwdlib[argon2]` & `PyJWT`) | `Implemented` | Security / Crypto & Auth |
| **ADR-015** | User-Focused Backend Scope & Database Baseline | `Implemented` | Backend Core & Database |
| **ADR-016** | User Registration & Credential Persistence | `Implemented` | Authentication & User Management |
| **ADR-017** | JSON Login & JWT Identity | `Implemented` | Authentication & API |

---

## ADR-001: Workspace & Monorepo Structure

- **Status:** `Implemented`
- **Components:** Project Architecture

### Context
TrailVerse is an evolving platform featuring a backend core (`virsa-backend`) that serves e-commerce, cultural heritage, or marketplace capabilities, with anticipated additions for web/mobile frontends. We needed a clean directory structure that keeps the codebase unified without creating tight coupling between the backend and future client apps.

### Decision
Adopt a modular monorepo directory layout at workspace root:
- `virsa-backend/`: Self-contained Python application containing its own virtual environment configurations, dependency manifests (`requirements.txt`), migrations (`alembic/`), and application logic (`app/`).
- Root level contains shared repository governance (`README.md`, `DECISIONS.md`, `.gitignore`, and agent customization rules).
- Client applications (e.g. web frontend, admin dashboard) will reside in sibling directories alongside `virsa-backend/`.

### Consequences & Rationale
- **Benefits:** Simplifies version control, coordinates documentation, and enables cross-project workflows while keeping backend deployment isolated.
- **Trade-offs:** Requires running backend commands from `virsa-backend` or referencing subpaths.

---

## ADR-002: Backend Framework Selection (FastAPI + Uvicorn)

- **Status:** `Implemented`
- **Components:** Backend Framework

### Context
The backend requires high-throughput asynchronous execution, native OpenAPI/Swagger documentation, strict type validation, and rapid API endpoint development.

### Decision
Selected **FastAPI** (`fastapi>=0.110.0`) running on the **Uvicorn** ASGI server (`uvicorn[standard]>=0.28.0`).

### Consequences & Rationale
- **Benefits:**
  - Standardized OpenAPI 3.0 schemas automatically exposed at `/api/v1/docs` (Swagger UI) and `/api/v1/redoc` (ReDoc).
  - Modern Python type hints throughout request handlers and database transactions.
  - Native asynchronous support and dependency injection system.
- **Trade-offs:** Requires standard ASGI deployment setup rather than traditional WSGI (like Gunicorn + WSGI).

---

## ADR-003: API Routing Hierarchy and Versioning Strategy

- **Status:** `Implemented`
- **Components:** API Design & Routing

### Context
Client applications require stable endpoints that can evolve without breaking backwards compatibility. The API also needs health monitoring for container orchestrators and load balancers.

### Decision
1. **Global Version Prefix:** All API endpoints are namespaced under `/api/v1` (`settings.API_V1_STR`), aggregated through a central `api_router` in `app/api/routes/__init__.py`.
2. **Modular Sub-Routers:** Dedicated route files by domain:
   - `/auth`: Registration, OAuth2 login, JSON login, current profile (`/me`).
   - `/users`: User administration and profile updates.
   - `/products`: Product listing, filtering, search, and category management.
   - `/cart`: Dynamic cart availability check and price calculation.
   - `/orders`: Order placement, user order history, and detailed order retrieval.
3. **Health Check Endpoints:**
   - `GET /`: Root informational status including project name, status string, and interactive docs URL.
   - `GET /health`: Lightweight heartbeat endpoint (`{"status": "healthy"}`) for probes and load balancers.

### Consequences & Rationale
- **Benefits:** Clear route ownership, predictable URL taxonomy, zero conflicts across domains, and readiness for future `/api/v2` versioning if breaking changes are introduced.

---

## ADR-004: Data Validation, Serialization, and DTOs (Pydantic v2)

- **Status:** `Implemented`
- **Components:** Data Validation & DTO Layer

### Context
APIs must strictly validate incoming request payloads to prevent malformed data or security vulnerabilities (e.g., mass-assignment or injection), while preventing leakage of sensitive internal columns (e.g., `hashed_password`).

### Decision
Utilize **Pydantic v2** (`pydantic>=2.6.0`) with a layered Data Transfer Object (DTO) schema pattern in `app/schemas/`:
1. **Base Schema (`*Base`):** Defines shared fields and field constraints (e.g., `UserBase`, `ProductBase`, `CategoryBase`).
2. **Create Schema (`*Create`):** Adds fields required only at creation time (e.g., plain-text `password` in `UserCreate`).
3. **Update Schema (`*Update`):** All fields optional to support partial updates (`PATCH`/`PUT`).
4. **Response Schema (`*Response`):** Explicitly specifies which fields are serialized to clients. Configured with `model_config = ConfigDict(from_attributes=True)` to map directly from SQLAlchemy ORM entities. Sensitive fields like `hashed_password` are strictly omitted.

### Consequences & Rationale
- **Benefits:** Compile-time and runtime type safety, automatic 422 Unprocessable Entity responses for invalid inputs, and protection against accidental disclosure of credentials.

---

## ADR-005: Database ORM and Connection Strategy (SQLAlchemy 2.0)

- **Status:** `Implemented`
- **Components:** Persistence Layer

### Context
We need a robust ORM that allows local rapid prototyping (zero-configuration SQLite) while providing seamless portability to production-grade relational databases like PostgreSQL.

### Decision
1. **SQLAlchemy 2.0:** Standardized on `sqlalchemy>=2.0.28` using `declarative_base()` (`app.db.base.Base`).
2. **Session Lifecycle via Dependency Injection:** A FastAPI generator dependency `get_db()` in `app/dependencies.py` instantiates `SessionLocal()`, yields the active session to the route handler, and reliably calls `db.close()` in a `finally` block.
3. **Connection Pooling & Multi-Dialect Setup:**
   - `pool_pre_ping=True` ensures stale or dropped connections are reconnected before query execution.
   - Conditional `{"check_same_thread": False}` enabled automatically when running against SQLite.
   - Production can switch directly to PostgreSQL simply by configuring `DATABASE_URL=postgresql://user:pass@host/db` without altering Python code.

### Consequences & Rationale
- **Benefits:** Prevents connection leaks, provides complete database decoupling, and isolates transaction boundaries cleanly per HTTP request.

---

## ADR-006: Database Schema Migrations (Alembic)

- **Status:** `Implemented`
- **Components:** Database Tooling

### Context
Manual schema updates lead to drift across environments and loss of historical structural tracking. We need repeatable, code-controlled migrations.

### Decision
Adopt **Alembic** (`alembic>=1.13.1`):
1. Configuration in `virsa-backend/alembic.ini` and environment script `virsa-backend/alembic/env.py`.
2. Dynamic connection URL resolution: `alembic/env.py` reads `settings.DATABASE_URL` directly from application settings.
3. Centralized Model Aggregation: `app/db/base.py` imports all ORM models (`User`, `Category`, `Product`, `Order`, `OrderItem`, `Review`) and binds their metadata to `target_metadata = Base.metadata`. This guarantees `alembic revision --autogenerate` detects every table and relation.

### Consequences & Rationale
- **Benefits:** Zero manual SQL file tracking needed; all schema changes are versioned alongside source code and can be verified across staging and production.

---

## ADR-007: Authentication & Token Architecture (JWT with Dual Login Endpoints)

- **Status:** `Implemented`
- **Components:** Authentication & Security

### Context
Client applications (React/Next.js/mobile) typically interact via standard JSON REST bodies (`{"email": "...", "password": "..."}`). However, OpenAPI/Swagger UI relies on the OAuth2 specification (`OAuth2PasswordRequestForm` with `application/x-www-form-urlencoded` fields `username` and `password`) to drive the interactive "Authorize" lock button.

### Decision
Implement stateless **JWT (JSON Web Tokens)** using `python-jose` with dual authentication endpoints in `app/api/routes/auth.py`:
1. `POST /api/v1/auth/login`: Accepts `OAuth2PasswordRequestForm` to provide full compatibility with Swagger UI.
2. `POST /api/v1/auth/login/json`: Accepts `LoginRequest` (JSON body) for seamless SPA, mobile, and third-party API clients.
3. Tokens are signed using HMAC-SHA256 (`HS256`) containing the subject `sub` (user's email) and expiration timestamp `exp`.
4. Lifetime configured via `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60 minutes).

### Consequences & Rationale
- **Benefits:** Best of both worlds: full Swagger UI interactivity during development/testing, and native JSON payloads for frontend clients without requiring form-data encoders.

---

## ADR-008: Password Security & Cryptography (Bcrypt via Passlib)

- **Status:** `Implemented`
- **Components:** Security / Cryptography

### Context
Passwords must never be stored in plaintext. They require slow, salted, computationally intensive hashing algorithms resistant to GPU acceleration and precomputed rainbow table attacks.

### Decision
Standardize on **Bcrypt** via `passlib[bcrypt]` and `bcrypt>=4.0.1`:
- Encapsulated in `app/core/security.py` via `CryptContext(schemes=["bcrypt"], deprecated="auto")`.
- `verify_password(plain_password, hashed_password) -> bool`
- `get_password_hash(password) -> str`
- Hashes are verified and generated exclusively in the service layer (`app/services/auth_service.py`).

### Consequences & Rationale
- **Benefits:** Industry-standard password hashing with automatic salt generation and work-factor calibration.

---

## ADR-009: Layered Dependency Injection & Role-Based Access Control (RBAC)

- **Status:** `Implemented`
- **Components:** Authorization & Middleware

### Context
Different endpoints require varying security guarantees: public access, authenticated user access, active user status, or administrator (superuser) access. Duplicating authorization logic in route bodies creates bugs and security regressions.

### Decision
Implement a layered dependency chain in `app/dependencies.py`:
```
                  ┌──────────────────────┐
                  │       get_db         │
                  └──────────┬───────────┘
                             │
                  ┌──────────▼───────────┐
                  │   get_current_user   │  (validates JWT bearer token)
                  └──────────┬───────────┘
                             │
               ┌─────────────▼──────────────┐
               │  get_current_active_user   │  (ensures user.is_active == True)
               └─────────────┬──────────────┘
                             │
             ┌───────────────▼───────────────┐
             │ get_current_active_superuser  │  (ensures user.is_superuser == True)
             └───────────────────────────────┘
```
- Non-authenticated requests receive `401 Unauthorized` with `WWW-Authenticate: Bearer`.
- Inactive accounts receive `400 Bad Request`.
- Regular users attempting admin actions (e.g. creating products or reading user directories) receive `403 Forbidden`.

### Consequences & Rationale
- **Benefits:** Extremely clean route signatures (e.g., `current_user: User = Depends(get_current_active_superuser)`), zero code repetition, and deterministic enforcement of least-privilege principles.

---

## ADR-010: E-Commerce Relational Domain Modeling & Integrity Constraints

- **Status:** `Implemented`
- **Components:** Domain Models / Database

### Context
The e-commerce data model consists of `User`, `Category`, `Product`, `Order`, `OrderItem`, and `Review`. Relationships require careful foreign key cascade actions to prevent dangling records and protect historical financial transactions.

### Decision
1. **Foreign Key Deletion Rules:**
   - `Order.user_id`: `CASCADE` with User.
   - `OrderItem.order_id`: `CASCADE` with Order.
   - `OrderItem.product_id`: `RESTRICT`. Deleting a product must not erase or corrupt historical order records or receipts.
   - `Product.category_id`: `SET NULL`. Deleting a category keeps associated products active without a assigned category.
   - `Review.user_id` & `Review.product_id`: `CASCADE`.
2. **Historical Pricing Preservation:** `OrderItem` captures a standalone `price: Float` column at the moment of order placement, decoupling historical records from subsequent product price changes.
3. **Database-Level Data Integrity Constraints:**
   - Unique constraints on `User.email`, `Category.name`, and `Category.slug`.
   - `CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range")` enforced directly in the database for `Review`.

### Consequences & Rationale
- **Benefits:** Eliminates orphaned items, preserves financial audit history, and enforces valid ratings at both database and schema layers.

---

## ADR-011: Inventory Reservation & Checkout Concurrency Control

- **Status:** `Implemented`
- **Components:** Orders & Inventory / Concurrency

### Context
In concurrent e-commerce systems, multiple customers may simultaneously order the last remaining units of stock. Without synchronization, race conditions allow overselling below zero.

### Decision
1. **Pessimistic Locking on Checkout:** In `POST /api/v1/orders` (`app/api/routes/orders.py`), product stock verification uses `db.query(Product)...with_for_update()`.
2. **Atomic Inventory Decrement:** In the same database transaction, available stock is decremented (`product.stock -= item.quantity`), line items are generated, the order is created, and the transaction is committed atomically. If any item is out of stock, the transaction aborts with `400 Bad Request`.
3. **Read-Only Cart Estimation:** `POST /api/v1/cart/calculate` performs live product and stock validation without acquiring row locks, ensuring high read throughput prior to the actual checkout step.

### Consequences & Rationale
- **Benefits:** Prevents race conditions and inventory deficits during sales spikes while keeping browsing and cart viewing performant.

---

## ADR-012: Configuration Management & 12-Factor Environment Settings

- **Status:** `Implemented`
- **Components:** Configuration & Environment

### Context
Configuration values (JWT secrets, token expiry, database connection strings, CORS origins) vary across local development, testing, staging, and production. Hardcoding configurations or secrets in repository code violates Twelve-Factor App principles and introduces security risks.

### Decision
Adopt **`pydantic-settings`** with `BaseSettings` in `app/core/config.py`:
- Configuration attributes define sane development defaults with environment variable overrides loaded from `.env`.
- CORS configuration accepts a typed `list[str]` of allowed client origins.
- Sensitive values like `SECRET_KEY` are isolated, with `.env` ignored by git and template values documented in `.env.example`.

### Consequences & Rationale
- **Benefits:** Zero-code deployments across environments, strict validation of configuration types at boot, and complete isolation of credentials.

---

## ADR-013: Streamlined Minimal Backend Architecture

- **Date:** 2026-10-21
- **Status:** `Implemented` (Supersedes ADR-003, ADR-006, ADR-007, ADR-008, ADR-009, ADR-010, ADR-011 for minimal baseline)
- **Components:** Backend Core, Database, Project Architecture

### Context
To facilitate rapid incremental prototyping and minimize operational complexity at the early development stage, the backend structure needed to be streamlined down to its essential core: direct database connectivity and a centralized application entrypoint.

### Decision
Consolidate `virsa-backend/` to a lightweight, minimalist baseline layout:
```
virsa-backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── db/
│       ├── __init__.py
│       └── session.py
├── .env
└── .gitignore
```
1. **Application Entrypoint (`app/main.py`):** Instantiates FastAPI, loads environment settings via `dotenv`, sets up root info and `/health` probes with live database ping verification.
2. **Database Engine & Session (`app/db/session.py`):** Configures SQLAlchemy declarative base, thread-safe connection pool, `SessionLocal`, and FastAPI dependency `get_db`.
3. **Environment Configuration (`.env`):** Defines minimal variables (`PROJECT_NAME`, `DATABASE_URL`).
4. **Git Ignore (`.gitignore`):** Ignores virtual environments, secrets, databases, and Python caches.

### Consequences & Rationale
- **Benefits:** Low barrier to entry, minimal boilerplate, and immediate readiness for targeted feature additions.
- **Trade-offs:** Advanced features like migrations (Alembic), JWT authentication routes, and multi-resource schemas will be reintroduced incrementally as each domain area is developed.

---

## ADR-014: Modern Authentication Cryptography (pwdlib[argon2] & PyJWT)

- **Date:** 2026-10-21
- **Status:** `Implemented` (Supersedes ADR-007 and ADR-008 crypto tooling)
- **Components:** Security / Crypto & Authentication

### Context
`passlib` has ceased active maintenance and triggers deprecation warnings on modern Python/cryptography releases. Similarly, `python-jose` lacks active maintenance for newer cryptographic primitives. Modern FastAPI production best practices recommend switching to `pwdlib` with Argon2id support for password hashing and `PyJWT` for robust token signing and validation.

### Decision
Adopt modern, actively maintained cryptographic tooling:
1. **Password Hashing:** `pwdlib[argon2]>=0.2.0` utilizing Argon2id as the default password hasher (the winner of the Password Hashing Competition, memory-hard and GPU-resistant).
2. **Token Signing & Verification:** `pyjwt[crypto]>=2.8.0` for HMAC-SHA256 and asymmetric JWT operations.
3. **Email Validation:** `email-validator>=2.1.0` for strict RFC 5322 email syntax and DNS checks in Pydantic schemas.

### Consequences & Rationale
- **Benefits:** Eliminates legacy deprecation warnings, provides superior protection against hardware brute-force attacks via Argon2id, and aligns with standard modern FastAPI security architecture.
- **Trade-offs:** Slightly higher CPU/memory consumption per hash verification during login, which is tunable via Argon2 time and memory cost parameters.

---

## ADR-015: User-Focused Backend Scope and Database Baseline

- **Date:** 2026-10-21
- **Status:** `Implemented` (Refines ADR-013 for the current development baseline)
- **Components:** Backend Core, Database, Project Architecture

### Context
The initial backend scaffold included routes, models, schemas, services, and migration metadata for products, categories, carts, orders, and reviews. The next development increment is focused on the user and authentication domain, so retaining unused commerce surfaces would increase maintenance cost and create misleading API and schema contracts.

### Decision
Reduce the active backend surface to the user and authentication domains:
1. Remove the unused cart, order, product, category, review, and user-administration route/model/schema/service surfaces from the runtime application.
2. Keep the FastAPI entrypoint, SQLAlchemy session/base, authentication modules, user model, and Alembic configuration needed for incremental development.
3. Establish the `users` table through an Alembic migration and keep database connectivity and health checks operational while additional domains are reintroduced deliberately.
4. Use SQLAlchemy metadata creation at application startup for the current lightweight development baseline, while retaining Alembic migration files for tracked schema history.

### Consequences & Rationale
- **Benefits:** Smaller runtime surface, clearer ownership of the current milestone, faster iteration, and fewer inactive endpoints or models to maintain.
- **Trade-offs / Risks:** Commerce functionality is not available until it is reintroduced as a separately designed domain; startup table creation must be replaced or restricted before production deployment.
- **Alternatives Considered:** Keeping all initial commerce modules was rejected because unused routes and models would make the current API contract broader than the implemented product scope.

---

## ADR-016: User Registration and Credential Persistence

- **Date:** 2026-10-21
- **Status:** `Implemented`
- **Components:** Authentication, User Management, Database

### Context
The user-focused backend needs a safe account-creation flow that validates client input, prevents duplicate accounts, and never stores a plaintext password. User responses must also avoid exposing the stored password hash.

### Decision
Implement `POST /api/v1/auth/register` using dedicated Pydantic schemas and the existing SQLAlchemy session:
1. Validate name, email, and password length with `UserRegister`; use `EmailStr` for email validation.
2. Normalize email addresses by trimming whitespace and converting them to lowercase before persistence and lookup.
3. Reject an existing email with `409 Conflict`.
4. Hash the password with the Argon2id-backed `pwdlib` helper before writing the `users` table.
5. Assign newly registered accounts the `customer` role and active status by default.
6. Return a `UserResponse` containing public user fields only; never serialize `hashed_password`.

### Consequences & Rationale
- **Benefits:** Consistent account identity, safe credential storage, explicit validation, and a stable public response contract.
- **Trade-offs / Risks:** Email normalization means email comparisons are case-insensitive by policy; password-hash cost must be monitored as deployment capacity changes.
- **Alternatives Considered:** Storing plaintext or returning the complete ORM entity was rejected because either choice would expose credentials.

---

## ADR-017: JSON Login and JWT Identity

- **Date:** 2026-10-21
- **Status:** `Implemented` (Supersedes ADR-007's dual-login endpoint design for the current baseline)
- **Components:** Authentication, API, Authorization

### Context
The current client contract is JSON-based and the backend needs a single straightforward login path for obtaining an access token and calling protected endpoints. The token must identify the authenticated database user and support expiry validation.

### Decision
Implement `POST /api/v1/auth/login` with a JSON `UserLogin` payload and `TokenResponse` response:
1. Normalize the submitted email in the same way as registration and look up the user by email.
2. Return `401 Unauthorized` with a bearer challenge for unknown users or invalid passwords, without revealing which credential failed.
3. Return `403 Forbidden` for inactive accounts.
4. Create a JWT using the configured algorithm and secret, with the user's numeric ID in the `sub` claim plus `iat` and `exp` claims.
5. Validate bearer tokens through FastAPI's `OAuth2PasswordBearer` dependency, reject malformed/non-numeric subjects and invalid or expired JWTs, and load the active user from the database.
6. Expose `GET /api/v1/auth/me` for retrieving the authenticated user's public profile.

### Consequences & Rationale
- **Benefits:** Simple SPA/mobile-friendly API contract, consistent error semantics, stateless token verification, and database-backed active-user checks.
- **Trade-offs / Risks:** Access tokens remain valid until expiry unless token revocation is added; the JWT secret must be supplied through the environment and protected operationally.
- **Alternatives Considered:** Maintaining separate form and JSON login endpoints was deferred for the current minimal API because the implemented clients use JSON and the additional compatibility surface was not required.

---

*This document must be updated whenever any major architectural decision or new technical component is introduced to TrailVerse.*
