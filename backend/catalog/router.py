from fastapi import APIRouter, Depends

from catalog import service
from catalog.schemas import ProductCreate, ProductOut, ProductUpdate
from core.dependencies import require_factory_admin

router = APIRouter(prefix="/factory/products", tags=["catalog"])


@router.get("", response_model=list[ProductOut])
async def list_products(_admin: dict = Depends(require_factory_admin)) -> list[dict]:
    return await service.list_products()


@router.post("", response_model=ProductOut, status_code=201)
async def create_product(body: ProductCreate, _admin: dict = Depends(require_factory_admin)) -> dict:
    return await service.create_product(body)


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(product_id: str, body: ProductUpdate, _admin: dict = Depends(require_factory_admin)) -> dict:
    return await service.update_product(product_id, body)
