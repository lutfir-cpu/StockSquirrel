from fastapi import FastAPI

app = FastAPI(title="StockSquirrel Backend")


@app.get("/")
def root():
    return {"message": "StockSquirrel backend running"}