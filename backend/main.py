from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from auth.models import RefreshToken, User
from auth.router import router as auth_router
from branches.branch_router import router as branch_router
from branches.models import Branch
from branches.router import router as branches_router
from catalog.models import Product
from catalog.router import router as catalog_router
from core.config import settings
from core.database import close_db, connect_db
from deliveries.models import Delivery, DeliverySchedule
from deliveries.router import router as deliveries_router

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

ALL_DOCUMENT_MODELS = [User, RefreshToken, Product, Branch, Delivery, DeliverySchedule]


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    await connect_db(ALL_DOCUMENT_MODELS)
    yield
    await close_db()


app = FastAPI(
    title="Bakery Orders API",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "staging" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(branches_router)
app.include_router(branch_router)
app.include_router(deliveries_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "env": settings.app_env}
