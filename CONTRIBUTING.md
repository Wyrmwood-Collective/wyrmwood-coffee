# Contribution Guidelines

## Database

**Table Naming:** Plural, snake case (`customers`, `baked_goods`)

## Branching

**Sprint Branch Naming:** `sprint/1`, `sprint/2`, etc.

**Feature Branch Naming:** `feature/wc-11` (use the Jira issue key, lowercased)

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

## Commit Messages

Commits should start with the Jira key the commit is meant for, followed by a description of the commit.
For example, `WC-1 Add IngredientCreate Pydantic model`, or `WC-4 Add tests for update_ingredient handler`.
The description should begin with an uppercase letter. Do not end with a period.
