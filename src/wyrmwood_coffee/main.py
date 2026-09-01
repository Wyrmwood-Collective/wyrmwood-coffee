import logging
import subprocess
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from wyrmwood_coffee.logging import setup_logging
from wyrmwood_coffee.middleware import RequestLoggingMiddleware
from wyrmwood_coffee.routers import (
    auth,
    baked_goods,
    customers,
    drinks,
    employees,
    ingredients,
    vendors,
)
from wyrmwood_coffee.routers.promotions import router as promotions_router

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(RequestLoggingMiddleware)
app.include_router(auth.router)
app.include_router(baked_goods.router, prefix="/baked-goods", tags=["Baked Goods"])
app.include_router(customers.router, prefix="/customers", tags=["Customers"])
app.include_router(drinks.router, prefix="/drinks", tags=["Drinks"])
app.include_router(employees.router)
app.include_router(ingredients.router)
app.include_router(promotions_router)
app.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])


def dev():
    subprocess.run(["fastapi", "dev", str(Path(__file__))])


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # log-level rationale (per WC-49 requirements):
    # error, because an unhandled exception indicates a failure path
    # we have not accounted for
    logger.error("Unhandled exception", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/")
def root():
    return {"message": "Welcome to Wyrmwood Coffee!"}
