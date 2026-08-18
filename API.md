# API Documentation

## Endpoints

### Summary

| Method | Path | Requires Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/` | No | [Welcome Message](#get-) |
| `POST` | `/baked-goods` | No | [Create Baked Good](#post-baked-goods) |
| `GET` | `/customers` | No | [List Customers](#get-customers) |
| `POST` | `/customers` | No | [Create Customer](#post-customers) |
| `GET` | `/employees/{id}` | No | [Get Employee](#get-employeesid) |
| `POST` | `/employees` | No | [Create Employee](#post-employees) |
| `POST` | `/vendors` | No | [Create Vendor](#post-vendors) |
| `GET` | `/promotions` | No | [List Promotions](#get-promotions) |
| `POST` | `/promotions` | No | [Create Promotion](#post-promotions) |
| `POST` | `/ingredients` | No | [Create Ingredient](#post-ingredients) |

### `GET` /

**Welcome Message**

Returns a simple welcome message. Used as a basic liveness check for the service.

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `200` | The welcome message | `application/json` `{ "message": string }` |

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

### `GET` /promotions

**List Promotions**

Return all Promotions currently stored in the system.

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `200` | The list of Promotions | `application/json` array of [`PromotionRead`](#promotionread) |

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

### `POST` /ingredients

**Create Ingredient**

Creates a new ingredient and links it to an existing vendor.

**Request body** (required)

`application/json` — [`IngredientCreate`](#ingredientcreate)

**Responses**

| Status | Description | Body |
| --- | --- | --- |
| `201` | The newly created ingredient | `application/json` [`IngredientRead`](#ingredientread) |
| `404` | The Vendor was not found. | `application/json` `{ "detail": string }` |
| `409` | An Ingredient with that name and vendor ID already exists. | `application/json` `{ "detail": string }` |
| `422` | The provided IngredientCreate is malformed or invalid. | `application/json` [`HTTPValidationError`](#httpvalidationerror) |

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
| `purchasing_cost` | float | yes | The cost to purchase the ingredient; must be `> 0` |
| `unit_amount` | float | yes | The amount per unit of measure; must be `> 0` |
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
| `purchasing_cost` | float | yes | The cost to purchase the ingredient |
| `unit_amount` | float | yes | The amount per unit of measure |
| `unit_of_measure` | string | yes | The unit used to measure this ingredient. Must be one of: g, kg, oz, lb, fl oz, mL, L, gal, pumps, scoops, shots, dashes |
| `vendor_id` | int | yes | The ID of the vendor supplying this ingredient |
| `allergens` | array[string] | yes | A list of allergens present in the ingredient |

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
