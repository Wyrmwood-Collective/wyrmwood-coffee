# API Documentation

## Endpoints

### Summary

| Method | Path | Requires Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/` | No | [Welcome Message](#get-) |
| `POST` | `/customers` | No | [Create Customer](#post-customers) |
| `POST` | `/employees` | No | [Create Employee](#post-employees) |
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

## Schemas

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

### ValidationError

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `loc` | array[string \| int] | yes |  |
| `msg` | string | yes |  |
| `type` | string | yes |  |
| `input` | any | no |  |
| `ctx` | object | no |  |
