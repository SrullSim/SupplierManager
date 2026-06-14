from beanie import PydanticObjectId

from branches.models import Branch


async def create(branch_code: str, name: str) -> Branch:
    branch = Branch(branch_code=branch_code, name=name)
    await branch.insert()
    return branch


async def get(branch_id: str) -> Branch | None:
    if not PydanticObjectId.is_valid(branch_id):
        return None
    return await Branch.get(PydanticObjectId(branch_id))


async def get_by_code(branch_code: str) -> Branch | None:
    return await Branch.find_one(Branch.branch_code == branch_code)


async def list_all() -> list[Branch]:
    return await Branch.find_all().to_list()
