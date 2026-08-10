from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from wyrmwood_coffee.database import Base, engine
from wyrmwood_coffee.dependencies import DbSession
from wyrmwood_coffee.models.ingredient import (
    Ingredient,
    IngredientCreate,
    IngredientRead,
    IngredientUpdate,
)
from wyrmwood_coffee.models.vendor import (
    Vendor,
)
from wyrmwood_coffee.routers import customers, employees, vendors


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(employees.router)

app.include_router(customers.router, prefix="/customers", tags=["Customers"])
app.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])


@app.get("/", tags=["Health"])
def root():
    return {"message": "Welcome to Wyrmwood Coffee!"}


# ---------------------------------------------------------
# INGREDIENT ENDPOINTS (Updated)
# ---------------------------------------------------------


@app.post(
    "/ingredients",
    response_model=IngredientRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Ingredients"],
)
def create_ingredient(payload: IngredientCreate, db: DbSession):
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
def get_ingredients(db: DbSession):
    return db.query(Ingredient).filter(Ingredient.active).all()


@app.get(
    "/ingredients/{ingredient_id}",
    response_model=IngredientRead,
    tags=["Ingredients"],
)
def get_ingredient(ingredient_id: int, db: DbSession):
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
    db: DbSession,
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
def delete_ingredient(ingredient_id: int, db: DbSession):
    item = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    item.active = False
    db.commit()
    return {"message": "Ingredient deactivated"}
