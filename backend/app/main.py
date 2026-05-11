from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.decisions import router as decisions_router
from app.api.feedback import router as feedback_router
from app.api.portfolio import router as portfolio_router
from app.api.settings import router as settings_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Mifos X Portfolio Health Agent MVP",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portfolio_router)
app.include_router(decisions_router)
app.include_router(feedback_router)
app.include_router(settings_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": app.version or "0.1.0",
    }
