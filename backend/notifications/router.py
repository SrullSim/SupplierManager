from fastapi import APIRouter, Depends

from core.dependencies import require_branch_user
from notifications import service
from notifications.schemas import PushTokenOut, PushTokenRegister

router = APIRouter(prefix="/branch", tags=["notifications"])


@router.post("/push-token", response_model=PushTokenOut, status_code=201)
async def register_push_token(
    body: PushTokenRegister, user: dict = Depends(require_branch_user)
) -> dict:
    doc = await service.register_token(user["branch_id"], body.token, body.device_label)
    return {"id": str(doc.id), "device_label": doc.device_label}
