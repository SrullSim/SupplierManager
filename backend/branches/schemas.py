from pydantic import BaseModel, Field


class BranchCreate(BaseModel):
    branch_code: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=128)
    # Optional explicit password; if omitted the factory gets a generated one back.
    password: str | None = Field(default=None, min_length=8, max_length=256)


class BranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    active: bool | None = None


class AssignProductsRequest(BaseModel):
    product_ids: list[str]


class BranchOut(BaseModel):
    id: str
    branch_code: str
    name: str
    assigned_product_ids: list[str]
    active: bool


class BranchCreatedOut(BranchOut):
    # Returned ONCE at creation so the factory can hand the password to the branch.
    generated_password: str | None = None
