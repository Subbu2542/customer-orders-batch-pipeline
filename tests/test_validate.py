import pandas as pd
import pytest

from src.validate import (
    CUSTOMER_COLUMNS,
    ORDER_COLUMNS,
    INPUT_DIR,
    load_csv,
    validate_customers,
    validate_orders,
)


def make_frame(records, columns):
    """Create a test dataframe with source row numbers."""
    df = pd.DataFrame(records, columns=columns)
    df["_source_row"] = range(2, len(df) + 2)
    return df


def test_sample_customers_have_expected_counts():
    df = load_csv(INPUT_DIR / "customers.csv", CUSTOMER_COLUMNS)

    accepted, rejected = validate_customers(df)

    assert len(df) == 5
    assert len(accepted) == 3
    assert len(rejected) == 2

    reasons = {row["rejection_reason"] for row in rejected}
    assert "duplicate_exact_customer_id" in reasons
    assert "missing_customer_id" in reasons


def test_sample_orders_have_expected_counts_and_reasons():
    customers_df = load_csv(
        INPUT_DIR / "customers.csv",
        CUSTOMER_COLUMNS,
    )
    orders_df = load_csv(INPUT_DIR / "orders.csv", ORDER_COLUMNS)

    accepted_customers, _ = validate_customers(customers_df)
    customer_ids = {
        row["customer_id"] for row in accepted_customers
    }

    accepted, rejected = validate_orders(orders_df, customer_ids)

    assert len(orders_df) == 10
    assert len(accepted) == 3
    assert len(rejected) == 7

    reasons = {
        reason
        for row in rejected
        for reason in row["rejection_reason"].split(";")
    }

    expected_reasons = {
        "unknown_customer_id",
        "non_positive_amount",
        "duplicate_exact_order_id",
        "missing_order_id",
        "invalid_order_date",
        "invalid_amount",
        "invalid_status",
    }

    assert expected_reasons.issubset(reasons)


def test_conflicting_duplicate_order_ids_are_rejected():
    records = [
        {
            "order_id": "O2001",
            "customer_id": "C001",
            "order_date": "2026-10-27",
            "amount": "100",
            "status": "completed",
        },
        {
            "order_id": "O2001",
            "customer_id": "C001",
            "order_date": "2026-10-27",
            "amount": "200",
            "status": "completed",
        },
    ]

    df = make_frame(records, ORDER_COLUMNS)

    accepted, rejected = validate_orders(df, {"C001"})

    assert len(accepted) == 0
    assert len(rejected) == 2
    assert all(
        row["rejection_reason"] == "conflicting_duplicate_order_id"
        for row in rejected
    )


def test_empty_datasets_are_handled():
    customers_df = pd.DataFrame(
        columns=CUSTOMER_COLUMNS + ["_source_row"]
    )
    orders_df = pd.DataFrame(
        columns=ORDER_COLUMNS + ["_source_row"]
    )

    accepted_customers, rejected_customers = validate_customers(
        customers_df
    )
    accepted_orders, rejected_orders = validate_orders(
        orders_df,
        set(),
    )

    assert accepted_customers == []
    assert rejected_customers == []
    assert accepted_orders == []
    assert rejected_orders == []


def test_uppercase_status_is_normalized():
    records = [
        {
            "order_id": "O3001",
            "customer_id": "C001",
            "order_date": "2026-10-27",
            "amount": "250.00",
            "status": "COMPLETED",
        }
    ]

    df = make_frame(records, ORDER_COLUMNS)

    accepted, rejected = validate_orders(df, {"C001"})

    assert len(accepted) == 1
    assert len(rejected) == 0
    assert accepted[0]["status"] == "completed"


def test_missing_required_column_raises_schema_error(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "customer_id,customer_name\nC001,Ravi\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Schema error"):
        load_csv(csv_path, CUSTOMER_COLUMNS)
def test_invalid_customer_email_is_rejected():
    records = [
        {
            "customer_id": "C900",
            "customer_name": "Test Customer",
            "email": "not-an-email",
        }
    ]

    df = make_frame(records, CUSTOMER_COLUMNS)

    accepted, rejected = validate_customers(df)

    assert accepted == []
    assert len(rejected) == 1
    assert rejected[0]["rejection_reason"] == "invalid_email"


def test_out_of_order_orders_are_accepted():
    records = [
        {
            "order_id": "O9002",
            "customer_id": "C001",
            "order_date": "2026-10-28",
            "amount": "200.00",
            "status": "completed",
        },
        {
            "order_id": "O9001",
            "customer_id": "C001",
            "order_date": "2026-10-25",
            "amount": "100.00",
            "status": "pending",
        },
    ]

    df = make_frame(records, ORDER_COLUMNS)

    accepted, rejected = validate_orders(df, {"C001"})

    assert len(accepted) == 2
    assert rejected == []
    assert [row["order_id"] for row in accepted] == [
        "O9002",
        "O9001",
    ]


def test_conflicting_duplicate_customer_ids_reject_all():
    records = [
        {
            "customer_id": "C901",
            "customer_name": "Customer One",
            "email": "one@example.com",
        },
        {
            "customer_id": "C901",
            "customer_name": "Customer Two",
            "email": "two@example.com",
        },
    ]

    df = make_frame(records, CUSTOMER_COLUMNS)

    accepted, rejected = validate_customers(df)

    assert accepted == []
    assert len(rejected) == 2

    assert all(
        row["rejection_reason"] == "conflicting_duplicate_customer_id"
        for row in rejected
    )