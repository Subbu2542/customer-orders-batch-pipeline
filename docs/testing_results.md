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

One observed three-iteration benchmark reported:
- Median runtime: 73.7273 seconds
- Median throughput: 1,627.62 rows/second
- All three iterations reconciled successfully

These are machine-specific observations, not guaranteed performance.
The run also printed two warm-up iterations, so the benchmark should be
rerun after verifying the final benchmark script and report methodology.

The benchmark excludes DuckDB publication and output CSV writing.

## Commands to reproduce

Run tests:

    python -m pytest -v

Generate large data:

    python -m src.generate_data --customers 20000 --orders 100000 --seed 42 --invalid-rate 0.01

Run benchmark:

    python -m src.benchmark --repeats 3

Run the sample pipeline:

    python -m src.validate
