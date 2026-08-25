# Contribution Guidelines

## Imports

Use absolute imports (`from wyrmwood_coffee.models.customer import Customer`, not `from .customer import Customer`).

## Module Names

Use singular names for modules in `models` (`ingredient.py`).
Use plural names for modules in `routers` (`ingredients.py`).
Use plural names for modules in `test` (`test_ingredients.py`).

Non-resource routers (cross-cutting concerns such as authentication) are an exception: use a descriptive module name instead of a pluralized resource name (`auth.py`, `test_auth.py`).

## Database

**Table Naming:** Plural, snake case (`customers`, `baked_goods`)

## Branching

**Sprint Branch Naming:** `sprint/1`, `sprint/2`, etc.

**Feature Branch Naming:** `feature/wc-11` (use the Jira issue key, lowercased)

## SQLAlchemy/Pydantic Model Names

SQLAlchemy models should be named after the singular form of the resource (`Customer`).

Each resource should have Pydantic schemas named `{Resource}Create` and `{Resource}Read`, mirroring the name of the associated ORM model (`Vendor` -> `VendorCreate`, `VendorRead`).

If a resource's `Create` schema is embedded as a field on another resource's `Create` schema, and it omits a field that would otherwise be implied by that nesting (such as a foreign key to the parent), suffix it `{Resource}CreateNested` instead of `{Resource}Create` (for example, `VendorContactCreateNested` is embedded in `VendorCreate.contacts`, omitting `vendor_id`).

## FastAPI Handlers

Given a resource like `products`, the `products.py` file should contain, in order:

```python
def list_products()  # GET /products
def get_product()    # GET /products/{id}
def create_product() # POST /products
def update_product() # PUT /products/{id}
def patch_product()  # PATCH /products/{id}
def delete_product() # DELETE /products/{id}
```

## Endpoint Documentation

In the docstring for the handler, **do not** include `Args`, `Returns`, or `Raises` blocks. Rely on type annotations in the parameter list and the `responses` / `response_model` parameters in the route decorator. **Do** include the summary line and optionally include a detailed description.

The docstring for the handler should describe the endpoint's primary contract. In other words, it should describe what happens on a successful request. Deviations from the success path (uniqueness constraint violations, invalid input, etc.) should be documented only in the `responses` parameter.

For example, given a `POST /vendors` endpoint where vendor names must be unique:

```python
@app.post(
    "/vendors",
    status_code=status.HTTP_201_CREATED,
    response_model=VendorRead,
    response_description="The newly created Vendor",
    responses={
        409: {"description": "A vendor with that name already exists."},
        422: {"description": "The provided VendorCreate is malformed or invalid."},
    },
)
def create_vendor(session: DbSession, payload: VendorCreate):
    """
    Create a new vendor, along with its initial set of contacts.

    Returns the created vendor, including generated IDs for the vendor
    and each vendor contact.
    """
```

`Returns the created vendor...` describes the endpoint's contract, so it stays in the docstring. The uniqueness rule describes a way the request gets rejected instead, so it lives only in the `409` description.

## Endpoint Response Values

Explicitly construct the return value as an instance of the intended response model. In other words, instead of returning the SQLAlchemy model and relying on FastAPI to convert:

```python
product = Product(...)
session.add(product)
session.commit()
return product
```

Construct the response model explicitly:

```python
product = Product(...)
session.add(product)
session.commit()
return ProductRead.model_validate(product)
```

and ensure the return type of the handler matches:

```python
def create_product(...) -> ProductRead:
```

## Endpoint Naming

- Use the plural form of the resource for CRUD resource endpoints.
- Endpoints for resources that are more than one word ("baked goods") should be located at `/baked-goods`, not `/baked_goods`.
- Action-style or non-resource endpoints (for example authentication) may use a descriptive path instead of a pluralized resource name (`/auth/login`).

## Parameter Naming

Handlers that accept a JSON request body (`create_vendor`) should accept that body as a parameter named `payload`.

Handlers that accept non-JSON request bodies (for example OAuth2 form data via `OAuth2PasswordRequestForm`) should use a name that reflects the body type (`form_data`), not `payload`.

The database session object should be called `session`.

## Decorator Argument Order

`status_code`, `response_model`, `response_description`, `responses`, `dependencies`, `tags`, then any others. For example:

```python
@app.post(
    "/vendors/{id}",
    status_code=status.HTTP_200_OK,
    response_model=VendorRead,
    response_description="The updated vendor",
    responses={404: {"description": "A vendor with that ID does not exist."}},
    dependencies=[Depends(require_auth)],
    tags=["vendors"],
)
```

## Commits and Pull Requests

All commits should begin with an uppercase letter and should not end with a period. Prefer commit messages that begin with present-tense imperative verbs ("Add Customer models", "Update README").

Commits within a feature branch (`feature/*`) need not be atomic (that is, a snapshot is not required to be in a working state or pass all tests), though it is still highly encouraged.

Commit chains made up mostly of fixups, work-in-progress snapshots, or "address feedback"/"typo" commits should be squashed into a smaller set of meaningful commits before merging into the sprint branch. Or in other words, each commit should represent a coherent, meaningful change, even if that change is nonatomic.

Pull request titles must start with the Jira key of the card the branch is for, followed by the title of the Jira card (for example, "WC-1 Create Ingredient").

## Tests

### Type Annotations

Type annotations are not necessary in the test modules.

### Fixture Scope

Fixtures should be scoped as narrowly as possible. For example, if the `test_product` module depends on a fixture called `sample_product`, and no tests outside that module depend on `sample_product`, the fixture should be defined in the `test_product` module. If a fixture is shared by multiple modules, place the fixture in a `conftest.py` file at the lowest directory level common to those modules.

### Fixture Argument Order

`db_session`, `client`, then any others

### Naming Conventions

A handler that tests a successful response should have the format `test_HANDLER_with_STATE_should_return_RESULT`, where `HANDLER` is the name of the handler, `STATE` describes the valid state (if needed), and `RESULT` is the expected response.
For example, `test_create_product_should_return_product`, or `test_create_product_with_zero_cost_should_return_product_with_default_cost`.

A handler that tests an invalid/error response should have the format `test_HANDLER_with_STATE_should_return_CODE`, where `HANDLER` is the name of the handler, `STATE` describes the invalid state, and `CODE` is the expected error code.
For example, `test_create_product_with_missing_name_should_return_422`.

A handler that tests a side effect (e.g. database state) should have the format `test_HANDLER_with_STATE_should_EFFECT`, where `HANDLER` is the name of the handler, `STATE` describes the state (if needed), and `EFFECT` is the side effect being verified.
For example, `test_create_vendor_should_persist_to_db`.

### Test Order

Tests should be ordered by which handler they test (see FastAPI Handlers above).
Tests for the same handler should be ordered so that tests for successful responses come first, then tests for invalid/error responses, and finally tests for side effects.

## Standard Response Messages

- `201`: The `REQUEST_MODEL` was created successfully.
- `204` (deletion): The `REQUEST_MODEL` was deleted successfully.
- `404`: The `REQUEST_MODEL` was not found.
- `409`: A `REQUEST_MODEL` with that `ATTRIBUTE` already exists.
- `409`: A `REQUEST_MODEL` with that `ATTRIBUTE_1` and `ATTRIBUTE_2` already exists.
- `422`: The provided `REQUEST_MODEL` is malformed or invalid.
- `422`: The provided path parameter is malformed or invalid.

## Postman

CRUD resource endpoints should be organized into folders named after the plural form of their primary resource ("Customers", "Baked Goods"), and be arranged in the same order as the route handlers.
Non-resource endpoint groups (for example authentication) may use a descriptive folder name instead ("Auth").
The endpoints should follow the same naming convention as the handlers, except with proper spacing and capitalization ("Create Customer", "List Vendors", "Login").

If an endpoint accepts a request body (e.g., `create_vendor`), a default/example request body should be provided. The example must be well-formed and satisfy the request schema, but it is not required to succeed against a fresh database (it may assume the existence of resources it depends on). For example, `create_ingredient`'s example body may reference a `vendor_id` that doesn't exist yet, as long as the body itself is otherwise valid.

## API Documentation

API documentation in `API.md` should follow the existing formatting.
All schemas should be ordered alphabetically.
All rows in the Summary section should include a link to the detailed endpoint description, and all schema references should be linked to the appropriate schema description.
