from datetime import datetime, timezone
from time import perf_counter

import duckdb
import pytest

from src import publish as publisher


def sample_data():
    customers = [
        {
            "customer_id": "C001",
            "customer_name": "Ravi",
            "email": "ravi@example.com",
        }
    ]

    orders = [
        {
            "order_id": "O001",
            "customer_id": "C001",
            "order_date": "2026-10-27",
            "amount": "100.00",
            "status": "completed",
        }
    ]

    rejected_customers = [
        {
            "customer_id": "",
            "customer_name": "Bad Customer",
            "email": "",
            "source_file": "customers.csv",
            "source_row": 3,
            "rejection_reason": "missing_customer_id",
        }
    ]

    rejected_orders = [
        {
            "order_id": "O002",
            "customer_id": "C999",
            "order_date": "2026-10-27",
            "amount": "50.00",
            "status": "completed",
            "source_file": "orders.csv",
            "source_row": 4,
            "rejection_reason": "unknown_customer_id",
        }
    ]

    return (
        customers,
        orders,
        rejected_customers,
        rejected_orders,
    )


def run_publication(data):
    customers, orders, rejected_customers, rejected_orders = data

    return publisher.publish_to_duckdb(
        valid_customers=customers,
        valid_orders=orders,
        rejected_customers=rejected_customers,
        rejected_orders=rejected_orders,
        customer_input_count=2,
        order_input_count=2,
        started_at=datetime.now(timezone.utc),
        started_clock=perf_counter(),
    )


def test_repeated_publication_does_not_duplicate_curated_data(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        publisher,
        "DB_PATH",
        tmp_path / "idempotency.duckdb",
    )

    data = sample_data()

    run_publication(data)
    run_publication(data)

    con = duckdb.connect(str(publisher.DB_PATH), read_only=True)

    try:
        assert con.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0] == 1

        assert con.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0] == 1

        assert con.execute(
            "SELECT COUNT(*) FROM rejected_customers"
        ).fetchone()[0] == 1

        assert con.execute(
            "SELECT COUNT(*) FROM rejected_orders"
        ).fetchone()[0] == 1

        assert con.execute(
            "SELECT COUNT(*) FROM pipeline_runs"
        ).fetchone()[0] == 2

    finally:
        con.close()


def test_failed_publication_preserves_previous_snapshot(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        publisher,
        "DB_PATH",
        tmp_path / "recovery.duckdb",
    )

    original_data = sample_data()
    run_publication(original_data)

    # Create a new batch that fails when DuckDB converts the date.
    replacement_customers = [
        {
            "customer_id": "C002",
            "customer_name": "Priya",
            "email": "priya@example.com",
        }
    ]

    invalid_orders = [
        {
            "order_id": "O999",
            "customer_id": "C002",
            "order_date": "not-a-date",
            "amount": "75.00",
            "status": "completed",
        }
    ]

    with pytest.raises(duckdb.ConversionException):
        publisher.publish_to_duckdb(
            valid_customers=replacement_customers,
            valid_orders=invalid_orders,
            rejected_customers=[],
            rejected_orders=[],
            customer_input_count=1,
            order_input_count=1,
            started_at=datetime.now(timezone.utc),
            started_clock=perf_counter(),
        )

    con = duckdb.connect(str(publisher.DB_PATH), read_only=True)

    try:
        # The previous data must survive the failed transaction.
        assert con.execute(
            "SELECT customer_id FROM customers"
        ).fetchall() == [("C001",)]

        assert con.execute(
            "SELECT order_id FROM orders"
        ).fetchall() == [("O001",)]

        # Only the original successful run should be recorded.
        assert con.execute(
            "SELECT COUNT(*) FROM pipeline_runs"
        ).fetchone()[0] == 1

    finally:
        con.close()
