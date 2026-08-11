# API Documentation

## Endpoints

### Summary

| Method | Path | Requires Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/` | No | [Welcome Message](#get-) |
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
