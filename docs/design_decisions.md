# Design Decisions and Trade-offs

## Technology choices

- Python: readable, modular batch-processing implementation.
- Pandas: CSV ingestion, data validation, and transformations.
- DuckDB: local SQL database for curated data, rejected records,
  and pipeline run history.
- Pytest: repeatable tests for validation, publication, and rollback.
- Git: version history and public repository submission.

## Processing design

1. Load both CSV files and verify their schemas.
2. Validate customer records.
3. Build the accepted customer ID set.
4. Validate orders, including customer references.
5. Save curated and rejected CSV outputs.
6. Publish the latest snapshot to DuckDB transactionally.
7. Record successful run metrics.
8. Produce a reconciliation report and structured logs.

## Duplicate handling

Exact duplicate rows keep the first occurrence. Conflicting
records with the same nonblank business key are rejected.
This avoids arbitrarily selecting a winner between conflicting
records.

## Publication and reruns

The four database data tables are replaced inside a transaction.
Successful executions are recorded in pipeline_runs with their row
counts and elapsed time.

If database publication fails, the publication transaction is rolled
back. The pipeline then attempts to record the failed run, including
its failure reason, using a separate connection. If the database itself
is unavailable, recording the failure may also be impossible.

Automated tests verify repeated publication, rollback, preservation of
the previous successful snapshot, and failed-run auditing.

The filesystem CSV outputs and database publication are not one atomic
transaction. A failure between these operations can leave the outputs
out of sync. Coordinated recovery remains an improvement for production use.

## Storage trade-offs

DuckDB avoids the need to configure an external database server.
CSV outputs are easy to inspect and share. The database is local,
so this implementation is not yet a distributed production service.

## Known limitations

- Validation is row-oriented and can be slow for large datasets.
- The benchmark currently measures CSV loading and validation,
  not end-to-end database publication.
- Run history records successful database publications only.
- File outputs and database publication are not one atomic transaction.
  A failure between writing CSV files and committing the database
  can leave files and database contents out of sync.
- A full production implementation would need stronger recovery
  orchestration, schema evolution policies, alerting, access control,
  and deployment monitoring.
