from beanie import PydanticObjectId

from catalog.models import Product


async def create(name: str, unit: str) -> Product:
    product = Product(name=name, unit=unit)
    await product.insert()
    return product


async def get(product_id: str) -> Product | None:
    if not PydanticObjectId.is_valid(product_id):
        return None
    return await Product.get(PydanticObjectId(product_id))


async def list_all(include_inactive: bool = True) -> list[Product]:
    if include_inactive:
        return await Product.find_all().to_list()
    return await Product.find(Product.active == True).to_list()  # noqa: E712


async def list_by_ids(product_ids: list[str]) -> list[Product]:
    valid_ids = [PydanticObjectId(pid) for pid in product_ids if PydanticObjectId.is_valid(pid)]
    if not valid_ids:
        return []
    return await Product.find({"_id": {"$in": valid_ids}}).to_list()
