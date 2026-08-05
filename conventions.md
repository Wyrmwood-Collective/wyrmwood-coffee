# Conventions

## Database

Table Naming: Plural, snake case (`customers`, `baked_goods`)

## Branching

Sprint branches: `sprint/1`, `sprint/2`, etc.
Feature branches: `feature/wc-11` (use the Jira issue key, lowercased)

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

Begin with uppercase letter, use imperative form ("Fix bug in list products handler")
