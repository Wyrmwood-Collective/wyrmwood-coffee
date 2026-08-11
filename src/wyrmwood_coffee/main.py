import subprocess
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, status
from sqlalchemy.orm import Session

from wyrmwood_coffee.database import Base, engine, get_db
from wyrmwood_coffee.models.vendor import (
    Vendor,
    VendorContact,
    VendorCreate,
    VendorRead,
)
from wyrmwood_coffee.routers import employees


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(employees.router)

DbSession = Annotated[Session, Depends(get_db)]


def dev():
    subprocess.run(["fastapi", "dev", str(Path(__file__))])


@app.get("/")
def root():
    return {"message": "Welcome to Wyrmwood Coffee!"}


@app.post(
    "/vendors",
    status_code=status.HTTP_201_CREATED,
    response_model=VendorRead,
    response_description="The newly created Vendor",
    responses={
        422: {"description": "The provided VendorCreate is malformed or invalid."}
    },
)
def create_vendor(session: DbSession, payload: VendorCreate):
    """
    Create a new vendor, along with its initial set of contacts.

    Returns the created vendor, including generated IDs for the vendor
    and each vendor contact.
    """
    new_vendor = Vendor(
        name=payload.name,
        active=payload.active,
        contacts=[
            VendorContact(**contact.model_dump(mode="json"))
            for contact in payload.contacts
        ],
    )
    session.add(new_vendor)
    session.commit()
    return new_vendor
