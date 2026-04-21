import structlog
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from typing import Any

# ── LOGGING CONFIGURATION ──────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20), # INFO
    context_class=dict,
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger()

# ── CONFIGURATION ─────────────────────────────────────────────
class Settings(BaseSettings):
    PROJECT_NAME: str = "VeriFundu API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    POSTGRES_HOST: str = "localhost"
    POSTGRES_USER: str = "verifundu"
    POSTGRES_PASSWORD: str = "dev_password"
    POSTGRES_DB: str = "verifundu"
    
    REDIS_HOST: str = "localhost"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# ── APP INITIALIZATION ────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to dashboard domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def logging_middleware(request: Request, call_next: Any) -> Any:
    log = logger.new(method=request.method, path=request.url.path)
    try:
        response = await call_next(request)
        log.info("request_finished", status_code=response.status_code)
        return response
    except Exception as e:
        log.error("request_failed", error=str(e))
        raise e

# ── ROUTES ───────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}

@app.get(settings.API_V1_STR + "/health")
async def api_health_check():
    return {"status": "online", "environment": settings.ENVIRONMENT}

# ── MAIN ENTRY POINT ──────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
