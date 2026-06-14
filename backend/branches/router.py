from fastapi import APIRouter, Depends

from branches import service
from branches.schemas import (
    AssignProductsRequest,
    BranchCreate,
    BranchCreatedOut,
    BranchOut,
    BranchUpdate,
)
from core.dependencies import require_factory_admin

router = APIRouter(prefix="/factory/branches", tags=["branches"])


@router.get("", response_model=list[BranchOut])
async def list_branches(_admin: dict = Depends(require_factory_admin)) -> list[dict]:
    return await service.list_branches()


@router.post("", response_model=BranchCreatedOut, status_code=201)
async def create_branch(body: BranchCreate, _admin: dict = Depends(require_factory_admin)) -> dict:
    return await service.create_branch(body)


@router.patch("/{branch_id}", response_model=BranchOut)
async def update_branch(branch_id: str, body: BranchUpdate, _admin: dict = Depends(require_factory_admin)) -> dict:
    return await service.update_branch(branch_id, body)


@router.put("/{branch_id}/products", response_model=BranchOut)
async def assign_products(
    branch_id: str, body: AssignProductsRequest, _admin: dict = Depends(require_factory_admin)
) -> dict:
    return await service.assign_products(branch_id, body.product_ids)
