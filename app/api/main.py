from fastapi import FastAPI

from .engine.registry import register_defaults
from .routers import runs, scenarios, units

app = FastAPI(title="BDSTEAM API", version="0.1.0")
register_defaults()

app.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(units.router, prefix="/units", tags=["units"])


@app.get("/health")
def health():
    return {"status": "ok"}
