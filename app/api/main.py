from fastapi import FastAPI
from .routers import runs, scenarios, units

app = FastAPI(title="BDSTEAM API", version="0.1.0")
app.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(units.router, prefix="/units", tags=["units"])


@app.get("/health")
def health():
    return {"status": "ok"}
