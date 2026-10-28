# Testing Results

## Automated test suite

The project currently has 11 automated tests.

### Validation tests

- Expected customer acceptance and rejection counts.
- Expected order acceptance and rejection counts.
- Conflicting duplicate order IDs.
- Empty dataframes.
- Status normalization.
- Missing CSV columns.
- Invalid customer email.
- Out-of-order orders.
- Conflicting duplicate customer IDs.

### Database publication tests

- Repeated publication does not duplicate rows in snapshot tables.
- Failed publication rolls back and preserves the previously committed
  customer and order records.

## Latest observed result

Date: 2026-10-28

Command:

    python -m pytest -v

Observed result:

    11 passed

## Sample data reconciliation

Customers:
- Input rows: 5
- Accepted rows: 3
- Rejected rows: 2

Orders:
- Input rows: 10
- Accepted rows: 3
- Rejected rows: 7

## Large-data benchmark

Dataset:
- Customers: 20,000 rows
- Orders: 100,000 rows
- Total: 120,000 rows

Latest measured benchmark:
- One warm-up iteration: 61.3608 seconds, excluded from results
- Measured runtimes: 61.6726, 62.1801, and 60.3316 seconds
- Median runtime: 61.6726 seconds
- Median throughput: 1,945.76 rows/second
- All three measured runs reconciled successfully

Customer results:
- Input: 20,000
- Accepted: 19,807
- Rejected: 193

Order results:
- Input: 100,000
- Accepted: 97,987
- Rejected: 2,013

Methodology:
- One warm-up iteration is excluded.
- Timings include CSV loading and row-level validation.
- DuckDB publishing and output CSV writing are excluded.
- Runtime depends on hardware, system load, caching, and dataset
  characteristics. These values are machine-specific observations,
  not universal performance guarantees.

## Commands to reproduce

Run tests:

    python -m pytest -v

Generate large data:

    python -m src.generate_data --customers 20000 --orders 100000 --seed 42 --invalid-rate 0.01

Run benchmark:

    python -m src.benchmark --repeats 3

Run the sample pipeline:

    python -m src.validate
