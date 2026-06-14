import secrets

from fastapi import HTTPException, status

from auth.models import User
from branches import repository
from branches.models import Branch
from branches.schemas import BranchCreate, BranchUpdate
from catalog import repository as catalog_repository
from core.security import hash_password


def _to_out(branch: Branch) -> dict:
    return {
        "id": str(branch.id),
        "branch_code": branch.branch_code,
        "name": branch.name,
        "assigned_product_ids": branch.assigned_product_ids,
        "active": branch.active,
    }


async def create_branch(data: BranchCreate) -> dict:
    # branch_code must be unique across login identities (users) and branches.
    if await repository.get_by_code(data.branch_code) or await User.find_one(User.branch_code == data.branch_code):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="branch_code already in use")

    password = data.password or secrets.token_urlsafe(12)

    branch = await repository.create(data.branch_code, data.name)

    user = User(
        role="branch_user",
        branch_code=data.branch_code,
        hashed_password=hash_password(password),
        branch_id=str(branch.id),
    )
    await user.insert()

    out = _to_out(branch)
    # Return the password ONLY at creation, only when we generated it.
    out["generated_password"] = password if data.password is None else None
    return out


async def list_branches() -> list[dict]:
    branches = await repository.list_all()
    return [_to_out(b) for b in branches]


async def update_branch(branch_id: str, data: BranchUpdate) -> dict:
    branch = await repository.get(branch_id)
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    update_fields = data.model_dump(exclude_unset=True)
    for key, value in update_fields.items():
        setattr(branch, key, value)
    await branch.save()
    return _to_out(branch)


async def assign_products(branch_id: str, product_ids: list[str]) -> dict:
    branch = await repository.get(branch_id)
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    # Validate every product id exists; reject the whole request otherwise.
    unique_ids = list(dict.fromkeys(product_ids))  # de-dupe, preserve order
    found = await catalog_repository.list_by_ids(unique_ids)
    if len(found) != len(unique_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more product IDs are invalid")

    branch.assigned_product_ids = unique_ids
    await branch.save()
    return _to_out(branch)
