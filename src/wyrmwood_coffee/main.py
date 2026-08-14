import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from wyrmwood_coffee.database import Base, engine
from wyrmwood_coffee.routers import customers, employees, vendors


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(employees.router)

app.include_router(customers.router, prefix="/customers", tags=["Customers"])
app.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])


def dev():
    subprocess.run(["fastapi", "dev", str(Path(__file__))])


@app.get("/")
def root():
    return {"message": "Welcome to Wyrmwood Coffee!"}
