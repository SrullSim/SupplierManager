from fastapi import APIRouter, Request

from auth import service
from auth.schemas import LoginRequest, LogoutRequest, RefreshRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, body: LoginRequest) -> TokenResponse:
    access, refresh = await service.login(body.branch_code, body.password)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest) -> TokenResponse:
    access, refresh = await service.refresh(body.refresh_token)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/logout", status_code=204)
async def logout(body: LogoutRequest) -> None:
    await service.logout(body.refresh_token)
