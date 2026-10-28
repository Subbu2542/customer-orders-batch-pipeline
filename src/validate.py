from pathlib import Path
from decimal import Decimal, InvalidOperation
import re
import sys

import pandas as pd

from datetime import datetime, timezone
from time import perf_counter

from src.publish import publish_to_duckdb
import logging

from src.observability import (
    configure_logging,
    write_reconciliation_report,
)
# Project paths
ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "data" / "input"
CURATED_DIR = ROOT / "outputs" / "curated"
REJECTS_DIR = ROOT / "outputs" / "rejects"

CUSTOMER_COLUMNS = ["customer_id", "customer_name", "email"]

ORDER_COLUMNS = [
    "order_id",
    "customer_id",
    "order_date",
    "amount",
    "status",
]

ALLOWED_STATUSES = {"pending", "completed", "cancelled"}

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def load_csv(path, expected_columns):
    """Load a CSV and check its schema."""

    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    df = pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    missing = sorted(set(expected_columns) - set(df.columns))
    unexpected = sorted(set(df.columns) - set(expected_columns))

    if missing or unexpected:
        raise ValueError(
            f"Schema error in {path.name}. "
            f"Missing columns: {missing}. "
            f"Unexpected columns: {unexpected}."
        )

    # Standardize whitespace without changing the source file.
    df = df[expected_columns].copy()

    for column in expected_columns:
        df[column] = df[column].str.strip()

    # CSV line 1 contains the header, so the first data row is line 2.
    df["_source_row"] = range(2, len(df) + 2)

    return df


def find_duplicate_keys(df, key_column, data_columns):
    """
    Detect duplicate keys efficiently.

    Policy:
    - Ignore blank keys; required-field validation handles them.
    - Keep the first exact duplicate and reject subsequent copies.
    - Reject all rows when the same key has conflicting data.
    """

    # Identify only rows whose nonblank key appears more than once.
    nonblank_mask = df[key_column].ne("")

    duplicate_mask = (
        nonblank_mask
        & df[key_column].duplicated(keep=False)
    )

    duplicate_rows = df.loc[duplicate_mask]

    # Most records are expected to have unique keys.
    if duplicate_rows.empty:
        return {}

    # Count distinct versions of each duplicated key.
    # One distinct version means exact copies.
    # Multiple distinct versions mean conflicting records.
    distinct_rows = duplicate_rows.drop_duplicates(
        subset=[key_column, *data_columns]
    )

    distinct_counts = distinct_rows.groupby(
        key_column,
        sort=False,
    ).size()

    conflicting_keys = set(
        distinct_counts[distinct_counts > 1].index
    )

    duplicate_reasons = {}

    # Group only actual duplicates instead of every input row.
    for key, group in duplicate_rows.groupby(
        key_column,
        sort=False,
    ):
        indexes = list(group.index)

        if key in conflicting_keys:
            for index in indexes:
                duplicate_reasons[index] = (
                    f"conflicting_duplicate_{key_column}"
                )
        else:
            for index in indexes[1:]:
                duplicate_reasons[index] = (
                    f"duplicate_exact_{key_column}"
                )

    return duplicate_reasons


def make_rejection(df, index, source_file, reason):
    """Preserve the input values and explain why a row was rejected."""

    row = df.loc[index]

    rejected = {
        column: row[column]
        for column in df.columns
        if column != "_source_row"
    }

    rejected["source_file"] = source_file
    rejected["source_row"] = int(row["_source_row"])
    rejected["rejection_reason"] = reason

    return rejected


def validate_customers(df):
    """Validate customer records and return accepted and rejected rows."""

    duplicate_reasons = find_duplicate_keys(
        df,
        "customer_id",
        CUSTOMER_COLUMNS,
    )

    valid_rows = []
    rejected_rows = []

    for index, row in df.iterrows():
        reasons = []

        if index in duplicate_reasons:
            reasons.append(duplicate_reasons[index])
        else:
            if not row["customer_id"]:
                reasons.append("missing_customer_id")

            if not row["customer_name"]:
                reasons.append("missing_customer_name")

            email = row["email"]

            if email and not EMAIL_PATTERN.match(email):
                reasons.append("invalid_email")

        if reasons:
            rejected_rows.append(
                make_rejection(
                    df,
                    index,
                    "customers.csv",
                    ";".join(reasons),
                )
            )
        else:
            valid_rows.append({
                column: row[column]
                for column in CUSTOMER_COLUMNS
            })

    return valid_rows, rejected_rows


def validate_orders(df, accepted_customer_ids):
    """Validate order records and check customer references."""

    duplicate_reasons = find_duplicate_keys(
        df,
        "order_id",
        ORDER_COLUMNS,
    )

    valid_rows = []
    rejected_rows = []

    for index, row in df.iterrows():
        reasons = []

        if index in duplicate_reasons:
            reasons.append(duplicate_reasons[index])
        else:
            # Check required fields.
            if not row["order_id"]:
                reasons.append("missing_order_id")

            if not row["customer_id"]:
                reasons.append("missing_customer_id")

            # Check customer referential integrity.
            if (
                row["customer_id"]
                and row["customer_id"] not in accepted_customer_ids
            ):
                reasons.append("unknown_customer_id")

            # Validate the date.
            order_date = None

            if not row["order_date"]:
                reasons.append("missing_order_date")
            else:
                parsed_date = pd.to_datetime(
                    row["order_date"],
                    errors="coerce",
                )

                if pd.isna(parsed_date):
                    reasons.append("invalid_order_date")
                else:
                    order_date = parsed_date.strftime("%Y-%m-%d")

            # Validate the amount using Decimal.
            amount = None

            if not row["amount"]:
                reasons.append("missing_amount")
            else:
                try:
                    amount = Decimal(row["amount"])

                    if not amount.is_finite():
                        reasons.append("invalid_amount")
                    elif amount <= 0:
                        reasons.append("non_positive_amount")

                except InvalidOperation:
                    reasons.append("invalid_amount")

            # Normalize status to lowercase.
            status = row["status"].lower()

            if not status:
                reasons.append("missing_status")
            elif status not in ALLOWED_STATUSES:
                reasons.append("invalid_status")

        if reasons:
            rejected_rows.append(
                make_rejection(
                    df,
                    index,
                    "orders.csv",
                    ";".join(reasons),
                )
            )
        else:
            valid_rows.append({
                "order_id": row["order_id"],
                "customer_id": row["customer_id"],
                "order_date": order_date,
                "amount": format(amount, "f"),
                "status": status,
            })

    return valid_rows, rejected_rows


def save_csv(rows, columns, path):
    """Write output consistently, including an empty output with headers."""

    path.parent.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(rows, columns=columns).to_csv(
        path,
        index=False,
        encoding="utf-8",
    )


def run_pipeline():
    """Run customer validation followed by order validation."""

    logger = configure_logging()

    started_at = datetime.now(timezone.utc)
    started_clock = perf_counter()

    logger.info("Starting CSV validation pipeline")
    print("Starting CSV validation pipeline...")

    customers_df = load_csv(
        INPUT_DIR / "customers.csv",
        CUSTOMER_COLUMNS,
    )

    orders_df = load_csv(
        INPUT_DIR / "orders.csv",
        ORDER_COLUMNS,
    )

    valid_customers, rejected_customers = validate_customers(
        customers_df
    )

    accepted_customer_ids = {
        row["customer_id"] for row in valid_customers
    }

    valid_orders, rejected_orders = validate_orders(
        orders_df,
        accepted_customer_ids,
    )

    save_csv(
        valid_customers,
        CUSTOMER_COLUMNS,
        CURATED_DIR / "customers.csv",
    )

    save_csv(
        valid_orders,
        ORDER_COLUMNS,
        CURATED_DIR / "orders.csv",
    )

    rejection_columns = [
        "customer_id",
        "customer_name",
        "email",
        "source_file",
        "source_row",
        "rejection_reason",
    ]

    save_csv(
        rejected_customers,
        rejection_columns,
        REJECTS_DIR / "customers_rejected.csv",
    )

    order_rejection_columns = ORDER_COLUMNS + [
        "source_file",
        "source_row",
        "rejection_reason",
    ]

    save_csv(
        rejected_orders,
        order_rejection_columns,
        REJECTS_DIR / "orders_rejected.csv",
    )
    run_info=publish_to_duckdb(
        valid_customers=valid_customers,
        valid_orders=valid_orders,
        rejected_customers=rejected_customers,
        rejected_orders=rejected_orders,
        customer_input_count=len(customers_df),
        order_input_count=len(orders_df),
        started_at=started_at,
        started_clock=started_clock,
    )

    report_path = write_reconciliation_report(
        run_info,
        {
            "customers": {
                "input": len(customers_df),
                "accepted": len(valid_customers),
                "rejected": len(rejected_customers),
            },
            "orders": {
                "input": len(orders_df),
                "accepted": len(valid_orders),
                "rejected": len(rejected_orders),
            },
        },
    )

    logger.info("Reconciliation report written to %s", report_path)
    logger.info("Pipeline completed successfully")
    print("\nCUSTOMER RESULTS")
    print(f"Input rows:       {len(customers_df)}")
    print(f"Accepted rows:    {len(valid_customers)}")
    print(f"Rejected rows:    {len(rejected_customers)}")

    print("\nORDER RESULTS")
    print(f"Input rows:       {len(orders_df)}")
    print(f"Accepted rows:    {len(valid_orders)}")
    print(f"Rejected rows:    {len(rejected_orders)}")

    print("\nOUTPUT FILES")
    print(f"Curated data: {CURATED_DIR}")
    print(f"Rejected data: {REJECTS_DIR}")

    print("\nPipeline finished with row-level validation.")


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as exc:
        print(f"PIPELINE ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
