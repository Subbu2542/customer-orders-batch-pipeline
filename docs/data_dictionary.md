# Data Dictionary

## 1. Customers

**Grain:** One accepted row per customer ID.

| Column | Type | Required | Rule |
|---|---|---|---|
| customer_id | String | Yes | Must be nonblank and unique |
| customer_name | String | Yes | Must not be empty |
| email | String | No | If provided, must match the configured email pattern |

## 2. Orders

**Grain:** One accepted row per order ID.

| Column | Type | Required | Rule |
|---|---|---|---|
| order_id | String | Yes | Must be nonblank and unique |
| customer_id | String | Yes | Must reference an accepted customer |
| order_date | Date | Yes | Must be parseable and is published as YYYY-MM-DD |
| amount | Decimal | Yes | Must be finite and greater than zero |
| status | String | Yes | Allowed values: pending, completed, cancelled |

## 3. Rejected records

Rejected records preserve the original input values and include:

- source_file
- source_row
- rejection_reason

A record may have more than one rejection reason when multiple checks fail.

## 4. Duplicate policy

- Repeated identical rows: retain the first occurrence and reject later copies.
- Conflicting rows with the same nonblank business key: reject all conflicting rows.
- Missing keys: reject through required-field validation.
- Case-normalize order status to lowercase before publishing.

## 5. Assumptions

The status list and positive-amount rule are project assumptions.
The source problem statement does not prescribe exact CSV column names
or an exhaustive list of business rules. These assumptions must remain
explicit and may be adjusted if the official specification requires it.
