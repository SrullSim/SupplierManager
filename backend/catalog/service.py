from fastapi import HTTPException, status

from catalog import repository
from catalog.models import Product
from catalog.schemas import ProductCreate, ProductUpdate


def _to_out(product: Product) -> dict:
    return {"id": str(product.id), "name": product.name, "unit": product.unit, "active": product.active}


async def create_product(data: ProductCreate) -> dict:
    product = await repository.create(data.name, data.unit)
    return _to_out(product)


async def list_products() -> list[dict]:
    products = await repository.list_all()
    return [_to_out(p) for p in products]


async def update_product(product_id: str, data: ProductUpdate) -> dict:
    product = await repository.get(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    update_fields = data.model_dump(exclude_unset=True)
    for key, value in update_fields.items():
        setattr(product, key, value)
    await product.save()
    return _to_out(product)
