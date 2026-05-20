import asyncio
from contextlib import suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import auth, dashboard, interests, internal, refresh, scraps
from app.services.worker_status_service import mark_stale_workers_offline


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="ContextNews AI")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.frontend_origin,
            settings.deployed_frontend_origin,
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def startup() -> None:
        init_db()
        app.state.worker_monitor_task = asyncio.create_task(_worker_monitor_loop())

    @app.on_event("shutdown")
    async def shutdown() -> None:
        task = getattr(app.state, "worker_monitor_task", None)
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    @app.get("/health")
    def health():
        return {"ok": True}

    app.include_router(auth.router)
    app.include_router(interests.router)
    app.include_router(refresh.router)
    app.include_router(dashboard.router)
    app.include_router(scraps.router)
    app.include_router(internal.router)
    return app


app = create_app()


async def _worker_monitor_loop() -> None:
    settings = get_settings()
    while True:
        mark_stale_workers_offline()
        await asyncio.sleep(settings.ai_worker_health_check_interval_seconds)
