import logging
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from wyrmwood_coffee.database import Base, get_engine
from wyrmwood_coffee.logging import setup_logging
from wyrmwood_coffee.middleware import RequestLoggingMiddleware
from wyrmwood_coffee.routers import (
    auth,
    baked_goods,
    customers,
    employees,
    ingredients,
    vendors,
)
from wyrmwood_coffee.routers.promotions import router as promotions_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug("Dropping all tables in database")
    Base.metadata.drop_all(bind=get_engine())
    logger.debug("Creating database tables")
    Base.metadata.create_all(bind=get_engine())
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)
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
