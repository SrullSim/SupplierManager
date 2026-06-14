from fastapi import APIRouter, Depends

from core.dependencies import require_factory_admin
from deliveries import service
from deliveries.schemas import (
    DeliveryCreate,
    DeliveryOut,
    DeliveryUpdate,
    ScheduleOut,
    ScheduleUpdate,
)

router = APIRouter(prefix="/factory", tags=["deliveries"])


# ── Schedule ───────────────────────────────────────────────────────────────────

@router.get("/schedule", response_model=ScheduleOut)
async def get_schedule(_admin: dict = Depends(require_factory_admin)) -> dict:
    return await service.get_schedule()


@router.put("/schedule", response_model=ScheduleOut)
async def update_schedule(body: ScheduleUpdate, _admin: dict = Depends(require_factory_admin)) -> dict:
    return await service.update_schedule(body)


# ── Deliveries ─────────────────────────────────────────────────────────────────

@router.get("/deliveries", response_model=list[DeliveryOut])
async def list_deliveries(_admin: dict = Depends(require_factory_admin)) -> list[dict]:
    return await service.list_upcoming()


@router.post("/deliveries", response_model=DeliveryOut, status_code=201)
async def create_delivery(body: DeliveryCreate, _admin: dict = Depends(require_factory_admin)) -> dict:
    return await service.create_one_off(body)


@router.patch("/deliveries/{delivery_id}", response_model=DeliveryOut)
async def update_delivery(
    delivery_id: str, body: DeliveryUpdate, _admin: dict = Depends(require_factory_admin)
) -> dict:
    return await service.update_delivery(delivery_id, body)


@router.get("/deliveries/{delivery_id}", response_model=DeliveryOut)
async def get_delivery(delivery_id: str, _admin: dict = Depends(require_factory_admin)) -> dict:
    return await service.get_delivery(delivery_id)


# ── Generation trigger ─────────────────────────────────────────────────────────

@router.post("/deliveries/generate", status_code=200)
async def generate_deliveries(_admin: dict = Depends(require_factory_admin)) -> dict:
    count = await service.generate_upcoming_deliveries()
    return {"generated": count}
