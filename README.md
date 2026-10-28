# Customer Orders Data Engineering Pipeline

Individual candidate project for the YottaFlex AI Data Engineering recruitment challenge.

## 1. Overview

This project implements a local batch data pipeline for customer and
order CSV files. It validates schemas, checks data quality and
referential integrity, separates accepted and rejected records,
publishes a curated snapshot to DuckDB, and produces reconciliation
reports.

The implementation uses Python, Pandas, DuckDB, Pytest, and Git.

## 2. Architecture

1. Ingest customer and order CSV files.
2. Validate required columns and input structure.
3. Detect missing fields, duplicates, malformed dates, invalid amounts,
   unsupported statuses, and unknown customer references.
4. Transform valid records to the target representation.
5. Write curated and rejected CSV outputs with rejection reasons.
6. Publish the latest data snapshot to DuckDB in a transaction.
7. Record successful run metrics.
8. Write structured logs and a JSON reconciliation report.

## 3. Technology Stack

- Python: pipeline implementation
- Pandas: CSV ingestion and data validation
- DuckDB: local analytical database
- Pytest: automated tests
- Git and GitHub: version control and submission

## 4. Project Structure

    data/
      input/                 Small reproducible example datasets
      generated/             Generated benchmark datasets
    src/
      validate.py            Validation and CSV output
      publish.py              Transactional DuckDB publishing
      observability.py       Logging and reconciliation reporting
      generate_data.py       Reproducible synthetic data generator
      benchmark.py           Ingestion and validation benchmark
    tests/
      test_validate.py       Validation tests
      test_publish.py        Publication and rollback tests
    docs/
      data_dictionary.md
      design_decisions.md
      testing_results.md
    prompts/
      chatgpt.md              Project prompt record
    outputs/
      curated/                Accepted CSV records
      rejects/                Rejected CSV records with reasons
      reports/                Run and benchmark reports
      yottaflex.duckdb        Local database created when running
    logs/
      pipeline.log            Local execution log

## 5. Requirements

Use Python 3.13 or 3.14 and a supported Windows PowerShell terminal.

Create and activate a virtual environment:

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1

Install the dependencies:

    python -m pip install -r requirements.txt

## 6. Run the Sample Pipeline

Run from the project root:

    python -m src.validate

The sample inputs are:

    data/input/customers.csv
    data/input/orders.csv

The command validates the data and writes accepted and rejected
CSV files. It also publishes the latest database snapshot and
writes a run-history entry and reconciliation reports.

Inspect the latest report:

    Get-Content outputs/reports/latest_run.json

## 7. Run Automated Tests

    python -m pytest -v

The test suite covers sample validation, duplicate IDs, empty inputs,
schema errors, email validation, out-of-order records, repeated
publication, and rollback following a simulated database failure.

## 8. Generate Larger Datasets

Generate 20,000 customers and 100,000 orders:

    python -m src.generate_data --customers 20000 --orders 100000 --seed 42 --invalid-rate 0.01

The generator writes its files to data/generated/. It records the
configuration in generation_metadata.json and uses a fixed seed for
reproducibility.

## 9. Benchmark

    python -m src.benchmark --repeats 3

The benchmark measures CSV loading and row-level validation.
It excludes DuckDB publication and output CSV writing.

Results are written to outputs/reports/benchmark_latest.json and
a timestamped benchmark report.

Performance depends on hardware, system load, caching, and dataset
characteristics. Measurements should be reported as observations
from the machine used for testing, not as universal guarantees.

## 10. Data Quality and Duplicate Policies

- Required identifiers must be present.
- Nonblank customer and order keys must be unique in curated data.
- Exact duplicate records retain their first occurrence; subsequent
  copies are rejected.
- Conflicting records with the same key are rejected rather than
  selecting an arbitrary winner.
- Customer references must resolve to accepted customers.
- Dates must be valid.
- Amounts must be finite and greater than zero.
- Status is normalized to lowercase and must be pending, completed,
  or cancelled.
- Rejected rows retain their source details and rejection reasons.

These business rules are documented project assumptions, not
a claim that the original challenge prescribed every rule.

## 11. Database and Recovery

DuckDB stores customers, orders, rejected_customers, rejected_orders,
and pipeline_runs.

Publishing replaces the four data tables inside a database transaction.
Successful executions are recorded separately in pipeline_runs.
Automated tests verify repeated publication and rollback after a
simulated publication error.

The database transaction does not include the separate filesystem CSV
writes. A production implementation would need coordinated recovery
to prevent file outputs and database contents diverging on failure.

## 12. Limitations and Future Improvements

- The initial implementation uses row-oriented validation, which can
  be slow at larger scale.
- The benchmark excludes database publication and file output time.
- Run history currently records successful database publications;
  comprehensive failed-run auditing remains future work.
- The pipeline is a local batch process, not a distributed service.
- Production deployment would require stronger recovery orchestration,
  alerting, schema-evolution policies, access control, and monitoring.

## 13. Design and Testing Documentation

See:

- docs/data_dictionary.md
- docs/design_decisions.md
- docs/testing_results.md
- prompts/chatgpt.md

The AI prompt record should contain the project-related prompts
submitted to AI tools, including those from other tools if used.
Assistant responses are omitted because they are not required by
the project FAQ. Prompt omissions must be resolved before submission.

## 14. AI Usage Disclosure

AI tools supported planning, implementation assistance, debugging,
and documentation. The submitted implementation must be reviewed,
tested, and understood by the candidate.

The prompt-history file records the prompts available in the
documented conversation. Any missing prompts or prompts submitted
to other AI tools must be added before submission.
