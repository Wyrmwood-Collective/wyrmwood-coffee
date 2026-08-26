import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from wyrmwood_coffee.database import Base, engine
from wyrmwood_coffee.routers import (
    auth,
    baked_goods,
    customers,
    employees,
    ingredients,
    vendors,
)
from wyrmwood_coffee.routers.promotions import router as promotions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(baked_goods.router, prefix="/baked-goods", tags=["Baked Goods"])
app.include_router(customers.router, prefix="/customers", tags=["Customers"])
app.include_router(employees.router)
app.include_router(ingredients.router)
app.include_router(promotions_router)
app.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])


def dev():
    subprocess.run(["fastapi", "dev", str(Path(__file__))])


@app.get("/")
def root():
    return {"message": "Welcome to Wyrmwood Coffee!"}
