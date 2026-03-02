from fastapi import FastAPI

app = FastAPI(title="Jam Bot Admin")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
