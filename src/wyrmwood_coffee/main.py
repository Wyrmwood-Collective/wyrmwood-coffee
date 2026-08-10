from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from wyrmwood_coffee.database import Base, engine, get_db
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
from wyrmwood_coffee.models.ingredient import (
    Ingredient,
    IngredientCreate,
    IngredientRead,
    IngredientUpdate,
)

app = FastAPI(
    title="Wyrmwood Coffee API",
    version="1.0.0",
    description="Backend API for managing ingredients.",
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


@app.post(
    "/ingredients",
    response_model=IngredientRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Ingredients"],
)
def create_ingredient(payload: IngredientCreate, db: Session = Depends(get_db)):
    db_item = Ingredient(**payload.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.get("/ingredients", response_model=list[IngredientRead], tags=["Ingredients"])
def get_ingredients(db: Session = Depends(get_db)):
    return db.query(Ingredient).filter(Ingredient.active == True).all()


@app.get(
    "/ingredients/{ingredient_id}", response_model=IngredientRead, tags=["Ingredients"]
)
def get_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    item = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return item


@app.put(
    "/ingredients/{ingredient_id}", response_model=IngredientRead, tags=["Ingredients"]
)
def update_ingredient(
    ingredient_id: int, payload: IngredientUpdate, db: Session = Depends(get_db)
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
    "/ingredients/{ingredient_id}", status_code=status.HTTP_200_OK, tags=["Ingredients"]
)
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    item = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    item.active = False
    db.commit()
    return {"message": "Ingredient deactivated"}
