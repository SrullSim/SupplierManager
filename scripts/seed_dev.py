"""
Seed the staging/dev database with a factory_admin, sample products, and a demo branch.
Run from the repo root: python scripts/seed_dev.py
"""

import asyncio
import os
import sys

sys.path.insert(0, "backend")

os.environ.setdefault("BOOTSTRAP_ADMIN_CODE", "admin")
os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "admin1234")
os.environ.setdefault("SECRET_KEY", "dev-secret-key-not-for-production")

from auth.models import RefreshToken, User  # noqa: E402
from branches.models import Branch  # noqa: E402
from catalog.models import Product  # noqa: E402
from core.database import connect_db  # noqa: E402
from core.security import hash_password  # noqa: E402

# bootstrap_admin.py lives in this same directory (on sys.path[0]).
from bootstrap_admin import create_initial_admin  # noqa: E402

SAMPLE_PRODUCTS = [
    ("חלה", "loaf"),       # challah
    ("בורקס", "tray"),      # borekas
    ("לחמניות", "bag"),     # rolls
    ("עוגת שמרים", "unit"),  # yeast cake
]

DEMO_BRANCH_CODE = "jeru01"
DEMO_BRANCH_PASSWORD = "branch1234"


async def seed() -> None:
    # Initialize Beanie with ALL document models the seed touches.
    await connect_db([User, RefreshToken, Product, Branch])
    await create_initial_admin()  # idempotent

    # Products — only seed if none exist yet.
    if await Product.find_all().count() == 0:
        product_ids = []
        for name, unit in SAMPLE_PRODUCTS:
            product = Product(name=name, unit=unit)
            await product.insert()
            product_ids.append(str(product.id))
        print(f"Seeded {len(product_ids)} products.")
    else:
        product_ids = [str(p.id) for p in await Product.find_all().to_list()]
        print("Products already present; skipping.")

    # Demo branch + its login user.
    if not await Branch.find_one(Branch.branch_code == DEMO_BRANCH_CODE):
        branch = Branch(
            branch_code=DEMO_BRANCH_CODE,
            name="Jerusalem Center",
            assigned_product_ids=product_ids[:2],  # assign challah + borekas
        )
        await branch.insert()
        await User(
            role="branch_user",
            branch_code=DEMO_BRANCH_CODE,
            hashed_password=hash_password(DEMO_BRANCH_PASSWORD),
            branch_id=str(branch.id),
        ).insert()
        print(f"Seeded demo branch {DEMO_BRANCH_CODE!r} (password: {DEMO_BRANCH_PASSWORD}).")
    else:
        print("Demo branch already present; skipping.")

    print("\nDev seed complete.")
    print("  Factory admin  -> branch_code=admin    password=admin1234")
    print(f"  Demo branch    -> branch_code={DEMO_BRANCH_CODE}   password={DEMO_BRANCH_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
