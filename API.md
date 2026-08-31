# API Documentation

## Endpoints

### Summary

| Method | Path | Requires Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/` | No | [Welcome Message](#get-) |
| `POST` | `/auth/login` | No | [Login](#post-authlogin) |
| `POST` | `/baked-goods` | No | [Create Baked Good](#post-baked-goods) |
| `GET` | `/customers` | No | [List Customers](#get-customers) |
| `GET` | `/customers/{id}` | No | [Get Customer](#get-customersid) |
| `POST` | `/customers` | No | [Create Customer](#post-customers) |
| `POST` | `/drinks` | No | [Create Drink](#post-drinks) |
| `GET` | `/employees` | No | [List Employees](#get-employees) |
| `GET` | `/employees/{id}` | No | [Get Employee](#get-employeesid) |
| `POST` | `/employees` | No | [Create Employee](#post-employees) |
| `GET` | `/ingredients` | No | [List Ingredients](#get-ingredients) |
| `GET` | `/ingredients/{id}` | No | [Get Ingredient](#get-ingredientsid) |
| `POST` | `/ingredients` | No | [Create Ingredient](#post-ingredients) |
| `PUT` | `/ingredients/{id}` | No | [Update Ingredient](#put-ingredientsid) |
| `DELETE` | `/ingredients/{id}` | Employee | [Delete Ingredient](#delete-ingredientsid) |
| `GET` | `/promotions` | No | [List Promotions](#get-promotions) |
| `GET` | `/promotions/{id}` | No | [Get Promotion](#get-promotionsid) |
| `POST` | `/promotions` | No | [Create Promotion](#post-promotions) |
| `DELETE` | `/promotions/{id}` | No | [Delete Promotion](#delete-promotionsid) |
| `GET` | `/vendors` | No | [List Vendors](#get-vendors) |
| `POST` | `/vendors` | No | [Create Vendor](#post-vendors) |

### `GET` /

**Welcome Message**

Returns a simple welcome message. Used as a basic liveness check for the service.

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `200` | The welcome message | `application/json` `{ "message": string }` |

[Back to Summary](#summary)

---

### `POST` /auth/login

**Login**

Authenticate an employee and return a JWT access token.

Accepts standard OAuth2 form data (username, password).

**Request body** (required)

`application/x-www-form-urlencoded` — [`Login`](#login)

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `200` | The generated JWT access token | `application/json` [`Token`](#token) |
| `401` | Incorrect username or password. | `application/json` `{ "detail": string }` |
| `422` | The provided Login is malformed or invalid. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

[Back to Summary](#summary)

---

### `POST` /baked-goods

**Create Baked Good**

Create a new baked good.

**Request body** (required)

`application/json` — [`BakedGoodCreate`](#bakedgoodcreate)

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `201` | The newly created baked good | `application/json` [`BakedGoodRead`](#bakedgoodread) |
| `422` | The provided BakedGoodCreate is malformed or invalid. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

[Back to Summary](#summary)

---

### `GET` /customers

**List Customers**

Returns a list of all customer records in the system.

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `200` | The list of all customers in the system, or an empty list if none exist. | `application/json` `array of` [`CustomerRead`](#customerread) |

[Back to Summary](#summary)

---

### `GET` /customers/{id}

**Get Customer**

Retrieve a single customer by ID.

**Path parameters**

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | int | yes | The unique identifier of the customer; must be a positive integer at most 2,147,483,647 |

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `200` | The requested customer | `application/json` [`CustomerRead`](#customerread) |
| `404` | The customer was not found. | `application/json` `{ "detail": string }` |
| `422` | The provided path parameter is malformed or invalid. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

[Back to Summary](#summary)

---

### `POST` /customers

**Create Customer**

Create a new customer record.

Both email and phone must be unique.

**Request body** (required)

`application/json` — [`CustomerCreate`](#customercreate)

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `201` | The newly created customer. | `application/json` [`CustomerRead`](#customerread) |
| `409` | A customer with the given email or phone already exists. | `application/json` `{ "detail": string }` |
| `422` | Missing or invalid values. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

[Back to Summary](#summary)

---

### `POST` /drinks

**Create Drink**

Create a new drink recipe.

**Request body** (required)

`application/json` — [`DrinkCreate`](#drinkcreate)

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `201` | The newly created drink | `application/json` [`DrinkRead`](#drinkread) |
| `404` | The ingredient was not found. | `application/json` `{ "detail": string }` |
| `409` | A drink with that name already exists. | `application/json` `{ "detail": string }` |
| `422` | The provided DrinkCreate is malformed or invalid. This includes: invalid 'type', invalid 'unit', duplicate 'ingredient_id' values, or 'production_cost' not less than 'sale_price'. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

[Back to Summary](#summary)

---

### `GET` /employees

**List Employees**

Retrieve a list of all employees.

Returns each employee without the password field.

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `200` | The list of all employees, or an empty list if none exist. | `application/json` `array of` [`EmployeeRead`](#employeeread) |

[Back to Summary](#summary)

---

### `GET` /employees/{id}

**Get Employee**

Retrieve a single employee by ID.

Returns the employee without the password field.

**Path parameters**

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | int | yes | The unique identifier of the employee; must be a positive integer at most 2,147,483,647 |

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `200` | The requested employee | `application/json` [`EmployeeRead`](#employeeread) |
| `404` | The employee was not found. | `application/json` `{ "detail": string }` |
| `422` | The provided path parameter is malformed or invalid. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

[Back to Summary](#summary)

---

### `POST` /employees

**Create Employee**

Create a new employee and persist it to the database.

Returns the created employee without the password field.

**Request body** (required)

`application/json` — [`EmployeeCreate`](#employeecreate)

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `201` | The newly created employee | `application/json` [`EmployeeRead`](#employeeread) |
| `409` | An employee with that username already exists. | `application/json` `{ "detail": string }` |
| `422` | The provided EmployeeCreate is malformed or invalid. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

[Back to Summary](#summary)

---

### `GET` /ingredients

**List Ingredients**

Returns a list of all ingredient records in the system.

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `200` | The list of all ingredients in the system, or an empty list if none exist. | `application/json` `array of` [`IngredientRead`](#ingredientread) |

[Back to Summary](#summary)

---

### `GET` /ingredients/{id}

**Get Ingredient**

Retrieve a single ingredient by ID.

**Path parameters**

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | int | yes | The unique identifier of the ingredient |

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `200` | The requested ingredient | `application/json` [`IngredientRead`](#ingredientread) |
| `404` | The ingredient was not found. | `application/json` `{ "detail": string }` |
| `422` | The provided path parameter is malformed or invalid. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

[Back to Summary](#summary)

---

### `POST` /ingredients

**Create Ingredient**

Creates a new ingredient and links it to an existing vendor.

**Request body** (required)

`application/json` — [`IngredientCreate`](#ingredientcreate)

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `201` | The newly created Ingredient | `application/json` [`IngredientRead`](#ingredientread) |
| `404` | The vendor was not found. | `application/json` `{ "detail": string }` |
| `409` | An ingredient with that name and vendor ID already exists. | `application/json` `{ "detail": string }` |
| `422` | The provided IngredientCreate is malformed or invalid. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

[Back to Summary](#summary)

---

### `PUT` /ingredients/{id}

**Update Ingredient**

Update an existing ingredient.

**Path parameters**

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | int | yes | The ID of the ingredient to update |

**Request body** (required)

`application/json` — [`IngredientUpdate`](#ingredientupdate)

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `200` | The updated ingredient | `application/json` [`IngredientRead`](#ingredientread) |
| `404` | The ingredient was not found. | `application/json` `{ "detail": string }` |
| `404` | The vendor was not found. | `application/json` `{ "detail": string }` |
| `409` | An ingredient with that name and vendor ID already exists. | `application/json` `{ "detail": string }` |
| `422` | The provided path parameter is malformed or invalid. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |
| `422` | The provided IngredientUpdate is malformed or invalid. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

[Back to Summary](#summary)

---

### `DELETE` /ingredients/{id}

**Delete Ingredient**

Soft-deletes an existing ingredient.

**Path parameters**

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | int | yes | The ID of the ingredient to delete |

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `204` | The ingredient was successfully deleted. | No content |
| `404` | The ingredient was not found. | `application/json` `{ "detail": string }` |
| `422` | The provided path parameter is malformed or invalid. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

[Back to Summary](#summary)

---

### `GET` /promotions

**List Promotions**

Return all Promotions currently stored in the system.

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `200` | The list of Promotions | `application/json` array of [`PromotionRead`](#promotionread) |

[Back to Summary](#summary)

---

### `GET` /promotions/{id}

**Get Promotion**

Retrieve a single promotion by ID.

**Path parameters**

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | int | yes | The unique identifier of the promotion |

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `200` | The requested promotion | `application/json` [`PromotionRead`](#promotionread) |
| `404` | The promotion was not found. | `application/json` `{ "detail": string }` |
| `422` | The provided path parameter is malformed or invalid. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

[Back to Summary](#summary)

---

### `POST` /promotions

**Create Promotion**

Create a new promotion with an active status, promo code, discount percentage,
start date, and end date.

Returns the created promotion, including its generated ID.

**Request body** (required)

`application/json` — [`PromotionCreate`](#promotioncreate)

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `201` | The newly created promotion | `application/json` [`PromotionRead`](#promotionread) |
| `409` | A Promotion with that promo code already exists. | `application/json` `{ "detail": string }` |
| `422` | The provided PromotionCreate is malformed or invalid. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

[Back to Summary](#summary)

---

### `DELETE` /promotions/{id}

**Delete Promotion**

Soft deletes a promotion by ID.

The promotion remains stored in the database for historical records, but it is no longer visible through normal promotion endpoints and cannot be used in active operations.

**Path parameters**

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | int | yes | The unique identifier of the promotion; must be a positive integer |

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `204` | The Promotion was deleted successfully. | No content |
| `404` | The promotion was not found. | `application/json` `{ "detail": string }` |
| `422` | The provided path parameter is malformed or invalid. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

[Back to Summary](#summary)

---

### `GET` /vendors

**List Vendors**

Retrieve a list of all vendors.

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `200` | A list of all vendors | `application/json` `array of` [`VendorRead`](#vendorread) |

[Back to Summary](#summary)

---

### `POST` /vendors

**Create Vendor**

Create a new vendor, along with its initial set of contacts.

Returns the created vendor, including generated IDs for the vendor
and each vendor contact.

**Request body** (required)

`application/json` — [`VendorCreate`](#vendorcreate)

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `201` | The newly created vendor | `application/json` [`VendorRead`](#vendorread) |
| `422` | Validation Error | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

[Back to Summary](#summary)

---

## Schemas

### BakedGoodCreate

Input schema for creating a new baked good. Does not include `id`, since this will be assigned on creation.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `active` | bool | no | Whether or not the baked good is active; defaults to `true` |
| `name` | string | yes | The name of the baked good, min length `1` |
| `description` | string | yes | A description of the baked good, min length `1` |
| `purchase_cost` | decimal | yes | The purchase cost, in dollars per baked good; must be `>= 0`, at most 10 digits and 2 decimal places |
| `retail_price` | decimal | yes | The retail price, in dollars per baked good; must be `>= 0`, at most 10 digits and 2 decimal places |
| `allergens` | array[string] | yes | A list of any allergens present in the baked good |

### BakedGoodRead

The baked good representation returned to an API client.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | int | yes | The unique identifier for this baked good |
| `active` | bool | no | Whether or not the baked good is active; defaults to `true` |
| `name` | string | yes | The name of the baked good |
| `description` | string | yes | A description of the baked good |
| `purchase_cost` | decimal | yes | The purchase cost, in dollars per baked good |
| `retail_price` | decimal | yes | The retail price, in dollars per baked good |
| `allergens` | array[string] | yes | A list of any allergens present in the baked good |

### CustomerBase

Base schema of a customer in the system. At least `email` or `phone` must be provided.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `active` | bool | no | Whether the customer is currently active; defaults to `true` |
| `first_name` | string | yes | The customer's first name, min length of `1` |
| `last_name` | string | yes | The customer's last name, min length of `1` |
| `email` | string | yes, if `phone=None` | The customer's email; syntax must be a proper email address, and defaults to `None` |
| `phone` | string | yes, if `email=None` | The customer's phone number; must match pattern `\d{3}-\d{3}-\d{4}`, and defaults to `None` |
| `loyalty_points` | int | no | The customer's loyalty points, defaults to `0` |

### CustomerCreate

Input schema for creating a new customer. At least `email` or `phone` must be provided. Does not include `id`, since this will be assigned on creation.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `active` | bool | no | Whether the customer is currently active; defaults to `true` |
| `first_name` | string | yes | The customer's first name, min length of `1` |
| `last_name` | string | yes | The customer's last name, min length of `1` |
| `email` | string | yes, if `phone=None` | The customer's email; syntax must be a proper email address, and defaults to `None` |
| `phone` | string | yes, if `email=None` | The customer's phone number; must match pattern `\d{3}-\d{3}-\d{4}`, and defaults to `None` |
| `loyalty_points` | int | no | The customer's loyalty points, defaults to `0` |
| `loyalty_expires_at` | datetime | no | The expiration date of the customer's loyalty points; set to one year after customer record creation |

### CustomerRead

Represents a customer in the system.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `active` | bool | no | Whether the customer is currently active; defaults to `true` |
| `first_name` | string | yes | The customer's first name, min length of `1` |
| `last_name` | string | yes | The customer's last name, min length of `1` |
| `email` | string | yes, if `phone=None` | The customer's email; syntax must be a proper email address, and defaults to `None` |
| `phone` | string | yes, if `email=None` | The customer's phone number; must match pattern `\d{3}-\d{3}-\d{4}`, and defaults to `None` |
| `loyalty_points` | int | no | The customer's loyalty points, defaults to `0` |
| `id` | int | yes | The unique identifier of the customer |
| `loyalty_expires_at` | datetime | no | The expiration date of the customer's loyalty points; set to one year after customer record creation |

### DrinkBase

Base schema of a drink recipe in the system.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `active` | bool | no | Whether the drink recipe is currently active; defaults to `true` |
| `name` | string | yes | The drink's name, min length of `1` |
| `description` | string | yes | The drink's description, min length of `1` |
| `type` | string | yes | The type of drink. Must be one of: coffee, tea, soda, refresher, or other. |
| `markup_percentage` | decimal | yes | The markup percentage of the drink `+ 1`, which means it must be greater than or equal to 1 |

### DrinkCreate

Input schema for creating a new drink recipe. Does not include `id` since this will be assigned on creation.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `active` | bool | no | Whether the drink recipe is currently active; defaults to `true` |
| `name` | string | yes | The drink's name, min length of `1` |
| `description` | string | yes | The drink's description, min length of `1` |
| `type` | string | yes | The type of drink. Must be one of: coffee, tea, soda, refresher, or other. |
| `markup_percentage` | decimal | yes | The markup percentage of the drink `+ 1`, which means it must be greater than or equal to 1 |
| `ingredients` | array[[`DrinkIngredientCreateNested`](#drinkingredientcreatenested)] | yes | The ingredients required for the drink recipe |

### DrinkIngredientBase

Base schema of an ingredient for a unique drink in the system. The ingredient must exist in the system and their `id` specified.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `ingredient_id` | int | yes | The unique identifier of the ingredient |
| `amount` | decimal | yes | The ingredient amount required for the drink recipe |
| `unit` | string | yes | The unit of measurement of the ingredient for the drink recipe |

### DrinkIngredientCreateNested

Input schema for attaching an existing ingredient to a new drink recipe. `unit` must be one of: g, kg, oz, lb, fl oz, mL, L, gal, pumps, scoops, shots, dashes.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `ingredient_id` | int | yes | The unique identifier of the ingredient |
| `amount` | decimal | yes | The ingredient amount required for the drink recipe |
| `unit` | string | yes | The unit of measurement of the ingredient for the drink recipe |

### DrinkIngredientRead

Represents an ingredient for a unique drink recipe in the system.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `ingredient_id` | int | yes | The unique identifier of the ingredient |
| `amount` | decimal | yes | The ingredient amount required for the drink recipe |
| `unit` | string | yes | The unit of measurement of the ingredient for the drink recipe |

### DrinkRead

Represents a new drink recipe in the system. `production_cost` and `sale_price` are computed fields handled by `services/drinks`.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `active` | bool | no | Whether the drink recipe is currently active; defaults to `true` |
| `name` | string | yes | The drink's name, min length of `1` |
| `description` | string | yes | The drink's description, min length of `1` |
| `type` | string | yes | The type of drink. Must be one of: coffee, tea, soda, refresher, or other. |
| `markup_percentage` | decimal | yes | The markup percentage of the drink `+ 1`, which means it must be greater than or equal to 1 |
| `id` | int | yes | The unique identifier of the drink recipe |
| `ingredients` | array[[`DrinkIngredientRead`](#drinkingredientread)] | yes | The ingredients specified in the drink recipe |
| `production_cost` | decimal | yes | The purchasing cost sum of all ingredients in the drink recipe |
| `sale_price` | decimal | yes | The sale price of the drink computed as the `markup_percentage * production_cost` |

### EmployeeCreate

Input schema for creating a new employee. Does not include `id`, since this will be assigned on creation. The password is hashed before it is stored.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `active` | bool | no | Whether the employee is currently active; defaults to `true` |
| `first_name` | string | yes | The employee's first name, min length `1` |
| `last_name` | string | yes | The employee's last name, min length `1` |
| `role` | string | yes | The employee's role; one of `employee`, `manager`, `admin` |
| `hourly_rate` | decimal | yes | The employee's hourly rate in dollars, must be greater than `0`, at most 10 digits and 2 decimal places |
| `hire_date` | date | yes | The date the employee was hired |
| `term_date` | date \| null | no | The date the employee was terminated, if applicable; defaults to `null`; must be later than `hire_date` |
| `username` | string | yes | The employee's username for system access, min length `1`, must be unique |
| `password` | string | yes | The employee's password; min length `8`, must include a capital letter, a number, and a special character from !@#$%^&*()_+-=[]{};':"\\|,.<>/?`~ |

### EmployeeRead

Represents an employee returned from the system. Does not include `password`.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | int | yes | The unique identifier of the employee |
| `active` | bool | yes | Whether the employee is currently active |
| `first_name` | string | yes | The employee's first name |
| `last_name` | string | yes | The employee's last name |
| `role` | string | yes | The employee's role; one of `employee`, `manager`, `admin` |
| `hourly_rate` | decimal | yes | The employee's hourly rate in dollars, at most 10 digits and 2 decimal places |
| `hire_date` | date | yes | The date the employee was hired |
| `term_date` | date \| null | no | The date the employee was terminated, if applicable; must be later than `hire_date` |
| `username` | string | yes | The employee's username for system access |

### HTTPValidationError

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `detail` | array[[`ValidationError`](#validationerror)] | no |  |

### IngredientCreate

Input schema for creating a new ingredient. Does not include `id`, since this will be assigned on creation.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `active` | bool | no | Whether or not the ingredient is active; defaults to `true` |
| `name` | string | yes | The name of the ingredient, min length `1` |
| `purchasing_cost` | decimal | yes | The cost to purchase this ingredient |
| `unit_amount` | decimal | yes | The amount per unit of measure; must be `> 0` |
| `unit_of_measure` | string | yes | The unit used to measure this ingredient. Must be one of: g, kg, oz, lb, fl oz, mL, L, gal, pumps, scoops, shots, dashes |
| `vendor_id` | int | yes | The ID of the vendor supplying this ingredient |
| `allergens` | array[string] | no | A list of allergens present in the ingredient |

### IngredientRead

The ingredient representation returned to an API client.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | int | yes | The unique identifier for this ingredient |
| `active` | bool | yes | Whether or not the ingredient is active |
| `name` | string | yes | The name of the ingredient |
| `purchasing_cost` | decimal | yes | The cost to purchase this ingredient |
| `unit_amount` | decimal | yes | The amount per unit of measure |
| `unit_of_measure` | string | yes | The unit used to measure this ingredient. Must be one of: g, kg, oz, lb, fl oz, mL, L, gal, pumps, scoops, shots, dashes |
| `vendor_id` | int | yes | The ID of the vendor supplying this ingredient |
| `allergens` | array[string] | yes | A list of allergens present in the ingredient |

### IngredientUpdate

Input schema for updating an existing ingredient.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `active` | bool | no | Whether or not the ingredient is active |
| `name` | string | yes | The name of the ingredient, min length `1` |
| `purchasing_cost` | decimal | yes | The cost to purchase this ingredient |
| `unit_amount` | decimal | yes | The amount per unit of measure; must be `> 0` |
| `unit_of_measure` | string | yes | The unit used to measure this ingredient. Must be one of: g, kg, oz, lb, fl oz, mL, L, gal, pumps, scoops, shots, dashes |
| `vendor_id` | int | yes | The ID of the vendor supplying this ingredient |
| `allergens` | array[string] | no | A list of allergens present in the ingredient |

### Login

Input schema for authenticating an employee. Submitted as OAuth2 form data.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `username` | string | yes | The employee's username for system access |
| `password` | string | yes | The employee's password for system access |

### PromotionCreate

Input schema for creating a new promotion. Does not include `id`, since this
will be assigned on creation.

| Field                 | Type    | Required | Notes                                                                      |
| --------------------- | ------- | -------- | -------------------------------------------------------------------------- |
| `active`              | bool    | yes      | Whether or not the promotion is active                                     |
| `promo_code`          | string  | yes      | Must contain uppercase letters only; spaces and underscores are permitted  |
| `discount_percentage` | decimal | yes      | Must be numeric and between `0` and `100`                                  |
| `start_date`           | date    | yes      | Promotion start date; must use one of the supported date formats           |
| `end_date`             | date    | yes      | Promotion end date; cannot occur before `start_date`                       |

### PromotionRead

Represents a promotion returned by the API.

| Field                 | Type    | Required | Notes                                      |
| --------------------- | ------- | -------- | ------------------------------------------ |
| `id`                  | int     | yes      | The promotion's unique identifier          |
| `active`              | bool    | yes      | Whether or not the promotion is active     |
| `promo_code`          | string  | yes      | The promotion code                         |
| `discount_percentage` | decimal | yes      | The percentage discount                    |
| `start_date`           | date    | yes      | The promotion start date                   |
| `end_date`             | date    | yes      | The promotion end date                     |

### Token

Token schema returned from the system.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `access_token` | string | yes | The JWT access token for the authenticated employee |
| `token_type` | string | yes | The type of the access token |

### ValidationError

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `loc` | array[string \| int] | yes |  |
| `msg` | string | yes |  |
| `type` | string | yes |  |
| `input` | any | no |  |
| `ctx` | object | no |  |

### VendorContactCreateNested

Input schema for a contact nested inside a [`VendorCreate`](#vendorcreate) payload. Does not include `id` or `vendor_id`, since these are assigned on creation.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | yes | The vendor contact's name, min length `1` |
| `role` | string | yes | The vendor contact's role, min length `1` |
| `email` | string | yes | The vendor contact's email, must match pattern `.+@.+` |
| `phone` | string | yes | The vendor contact's phone, must match pattern `\d{3}-\d{3}-\d{4}` |

### VendorContactRead

Represents a contact belonging to a vendor.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | int | yes | The vendor contact's unique identifier |
| `name` | string | yes | The vendor contact's name |
| `role` | string | yes | The vendor contact's role |
| `email` | string | yes | The vendor contact's email |
| `phone` | string | yes | The vendor contact's phone |
| `vendor_id` | int | yes | The ID of this contact's vendor |

### VendorCreate

Input schema for creating a new vendor. Does not include `id`, since this will be assigned on creation.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `active` | bool | no | Whether or not the vendor is active, defaults to `true` |
| `name` | string | yes | The name of the vendor, min length `1` |
| `contacts` | array[[`VendorContactCreateNested`](#vendorcontactcreatenested)] | no | The vendor's contacts, min length `1`; a vendor must be created with at least one contact |

### VendorRead

Represents a vendor and its associated contacts.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | int | yes | The vendor's unique identifier |
| `active` | bool | yes | Whether or not the vendor is active |
| `name` | string | yes | The name of the vendor |
| `contacts` | array[[`VendorContactRead`](#vendorcontactread)] | yes | The list of this vendor's contacts |
