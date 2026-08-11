import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from routers.promotions import router as promotions_router
from wyrmwood_coffee.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


app = FastAPI(lifespan=lifespan)
app.include_router(promotions_router)


def dev():
    subprocess.run(["fastapi", "dev", str(Path(__file__))])


@app.get("/")
def root():
    return {"message": "Welcome to Wyrmwood Coffee!"}
