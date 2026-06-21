# Supplier Manager

Multi-branch inventory and ordering system for a supplier (e.g. a bakery factory) and its retail branches.

**Factory** manages a product catalog, creates branches with credentials, and views all orders per delivery.  
**Branches** select products and quantities for upcoming deliveries, subject to a 12-hour lock rule.

## Architecture

```
Flutter app (Android/iOS/Web/Desktop)
        |
     HTTP / JWT
        |
  FastAPI  (Python 3.12+, Modular Monolith)
        |
    MongoDB (Beanie ODM)
```

**Backend modules:** `core/` | `auth/` | `branches/` | `catalog/` | `orders/` | `deliveries/` | `notifications/`

## Tech Stack

| Layer    | Stack                                                     |
|----------|-----------------------------------------------------------|
| Frontend | Flutter (Dart 3+), Riverpod, go_router, dio, intl (RTL)  |
| Backend  | FastAPI, Pydantic v2, Uvicorn, Beanie (Motor)             |
| Database | MongoDB 7                                                 |
| Auth     | JWT (access + refresh), Argon2 password hashing           |
| Infra    | Docker Compose (dev), staging / prod env configs          |

## Quick Start (Development)

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- (Later) Flutter SDK 3+

### 1. Start MongoDB

```bash
docker compose up -d mongo
```

### 2. Install backend dependencies

```bash
cd backend
pip install -e ".[dev]"
```

### 3. Bootstrap the first factory admin

```bash
SECRET_KEY=dev-secret-change-me \
BOOTSTRAP_ADMIN_CODE=admin \
BOOTSTRAP_ADMIN_PASSWORD=admin1234 \
  python ../scripts/bootstrap_admin.py
```

Or seed the full dev dataset (admin + sample products + demo branch):

```bash
SECRET_KEY=dev-secret-change-me python ../scripts/seed_dev.py
```

### 4. Run the API server

```bash
SECRET_KEY=dev-secret-change-me uvicorn main:app --reload
```

Open **http://localhost:8000/docs** to explore the interactive API docs.

### 5. Run tests

```bash
cd backend
pytest tests/ -v
```

## Environment Variables

| Variable                    | Required | Default              | Description                               |
|-----------------------------|----------|----------------------|-------------------------------------------|
| `SECRET_KEY`                | Yes      | -                    | JWT signing key (use a long random string)|
| `ALGORITHM`                 | No       | `HS256`              | JWT algorithm                             |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No    | `30`                 | Access token TTL                          |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No      | `7`                  | Refresh token TTL                         |
| `MONGO_URI`                 | No       | `mongodb://localhost:27017` | MongoDB connection string          |
| `MONGO_DB_NAME`             | No       | `bakery_orders`      | Database name                             |
| `FACTORY_TIMEZONE`          | No       | `Asia/Jerusalem`     | IANA timezone for cutoff calculations     |
| `APP_ENV`                   | No       | `staging`            | `staging` or `prod`                       |
| `BOOTSTRAP_ADMIN_CODE`      | No       | -                    | One-off: initial admin login code         |
| `BOOTSTRAP_ADMIN_PASSWORD`  | No       | -                    | One-off: initial admin password           |
| `FIREBASE_CREDENTIALS_JSON` | No       | -                    | Path to Firebase service-account JSON     |

**Never commit `.env.staging` or `.env.prod`.** Only `.env.example` is tracked.

## Key Business Rules

- **12-hour lock:** A branch can edit its order only until `delivery_datetime - 12 hours`. After the cutoff, the order is read-only for the branch. The factory always has full visibility.
- **Empty order at lock:** If no order exists when the cutoff passes, it finalizes as empty and the factory is notified.
- **Least privilege:** A branch can only see its own assigned products and its own orders. It cannot see other branches or the full catalog.
- **Timezone-aware:** All datetimes are stored in UTC. Cutoff calculations use the factory's configured timezone (`Asia/Jerusalem` by default), including correct handling across DST transitions.

## Security

- JWT authentication with access + refresh token rotation
- Refresh tokens stored as SHA-256 hashes; logout revokes them
- Passwords hashed with Argon2
- Rate-limited login endpoint
- Role-based access: `factory_admin` and `branch_user`
- Strict Pydantic v2 input validation on all endpoints
- No secrets in code or git

## Folder Structure

```
supplier-manager/
|-- backend/
|   |-- .env.example
|   |-- Dockerfile
|   |-- pyproject.toml
|   |-- main.py                     # FastAPI app entrypoint
|   |-- core/                       # Config, DB, security, dependencies
|   |-- auth/                       # Login, refresh, logout, JWT, tokens
|   |-- branches/                   # Branch CRUD, product assignment
|   |-- catalog/                    # Product catalog management
|   |-- deliveries/                 # (Milestone 3) Schedules & deliveries
|   |-- orders/                     # (Milestone 4) Order logic & 12h lock
|   |-- notifications/              # (Milestone 8) Push notifications
|   +-- tests/
|
|-- frontend/                       # (Milestones 5-7) Flutter app
|
|-- scripts/
|   |-- bootstrap_admin.py          # One-off admin creation (safe for prod)
|   |-- seed_dev.py                 # Dev data seeder
|   +-- check.sh                    # Format + lint + type-check + test
|
|-- docker-compose.yml
|-- Makefile
+-- README.md
```

## Quality & Tooling

```bash
make format    # isort + black
make lint      # pylint
make type-check # mypy
make test      # pytest
make check     # all of the above
```

## Milestones

- [x] **M1** Backend foundation (core, auth, JWT, rate limiting, tests)
- [x] **M2** Branches & catalog (products, branch CRUD, assignment, least-privilege)
- [x] **M3** Deliveries & schedule (recurring weekly, one-off, factory config)
- [x] **M4** Orders & 12h lock (create/edit/confirm, lock enforcement, factory summary)
- [x] **M5** Flutter auth + app shell (login, routing, RTL/Hebrew)
- [x] **M6** Flutter branch UI (product list, order builder, lock indicator + countdown)
- [x] **M7** Flutter factory UI (dashboard, branches, catalog, deliveries, order summary)
- [x] **M8** Notifications & lock finalization (push tokens, pre-lock reminders, auto-confirm + empty-order finalize at cutoff)
- [x] **M9** Polish & tooling (pre-commit, full run guide, frontend in check script)

**All milestones complete.** Full run guide: [RUN.md](RUN.md) · file map: [FILE_GUIDE.md](FILE_GUIDE.md)

## License

Private project. All rights reserved.
