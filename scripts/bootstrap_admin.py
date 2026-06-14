"""
One-off script to create the initial factory_admin.

Usage (prod):
    BOOTSTRAP_ADMIN_CODE=admin BOOTSTRAP_ADMIN_PASSWORD=secret python scripts/bootstrap_admin.py

Safe to run multiple times — does nothing if a factory_admin already exists.
"""

import asyncio
import sys

sys.path.insert(0, "backend")

from auth.models import RefreshToken, User
from core.config import settings
from core.database import connect_db
from core.security import hash_password


async def create_initial_admin() -> None:
    """Create the first factory_admin. Assumes the DB/Beanie is already initialized."""
    code = settings.bootstrap_admin_code
    password = settings.bootstrap_admin_password

    if not code or not password:
        print("ERROR: BOOTSTRAP_ADMIN_CODE and BOOTSTRAP_ADMIN_PASSWORD must be set.")
        sys.exit(1)

    existing = await User.find_one(User.role == "factory_admin")
    if existing:
        print(f"factory_admin already exists (branch_code={existing.branch_code}). Nothing to do.")
        return

    admin = User(role="factory_admin", branch_code=code, hashed_password=hash_password(password))
    await admin.insert()
    print(f"factory_admin created with branch_code={code!r}.")


async def main() -> None:
    await connect_db([User, RefreshToken])
    await create_initial_admin()


if __name__ == "__main__":
    asyncio.run(main())
