from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from wyrmwood_coffee.database import Base, engine, get_db
from wyrmwood_coffee.models.ingredient import (
    Ingredient,
    IngredientCreate,
    IngredientRead,
    IngredientUpdate,
)
from wyrmwood_coffee.models.vendor import (
    Vendor,
    VendorContact,
    VendorCreate,
    VendorRead,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


app = FastAPI(lifespan=lifespan)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables on shutdown (your original behavior)
    Base.metadata.drop_all(bind=engine)


app = FastAPI(
    title="Wyrmwood Coffee API",
    version="1.0.0",
    description="Backend API for managing ingredients.",
    lifespan=lifespan,
)

DbSession = Annotated[Session, Depends(get_db)]


@app.get("/", tags=["Health"])
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


# ---------------------------------------------------------
# INGREDIENT ENDPOINTS (Updated)
# ---------------------------------------------------------


@app.post(
    "/ingredients",
    response_model=IngredientRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Ingredients"],
)
def create_ingredient(payload: IngredientCreate, db: Session = Depends(get_db)):
    # Ensure vendor exists
    vendor = db.get(Vendor, payload.vendor_id)
    if vendor is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Vendor does not exist",
        )

    ingredient = Ingredient(
        name=payload.name,
        purchasing_cost=payload.purchasing_cost,
        unit_amount=payload.unit_amount,
        unit_of_measure=payload.unit_of_measure,
        allergens=payload.allergens,
        vendor_id=payload.vendor_id,
        active=payload.active,
    )

    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)

    return IngredientRead.model_validate(ingredient)


@app.get(
    "/ingredients",
    response_model=list[IngredientRead],
    tags=["Ingredients"],
)
def get_ingredients(db: Session = Depends(get_db)):
    return db.query(Ingredient).filter(Ingredient.active == True).all()


@app.get(
    "/ingredients/{ingredient_id}",
    response_model=IngredientRead,
    tags=["Ingredients"],
)
def get_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    item = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return item


@app.put(
    "/ingredients/{ingredient_id}",
    response_model=IngredientRead,
    tags=["Ingredients"],
)
def update_ingredient(
    ingredient_id: int,
    payload: IngredientUpdate,
    db: Session = Depends(get_db),
):
    item = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


@app.delete(
    "/ingredients/{ingredient_id}",
    status_code=status.HTTP_200_OK,
    tags=["Ingredients"],
)
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    item = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    item.active = False
    db.commit()
    return {"message": "Ingredient deactivated"}
