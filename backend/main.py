from fastapi import FastAPI

from api.routes import router

app = FastAPI(
    title="StockSquirrel Backend",
    version="0.1.0",
)

app.include_router(router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "StockSquirrel backend running"}