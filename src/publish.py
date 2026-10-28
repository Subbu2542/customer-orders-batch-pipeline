from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import duckdb
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "outputs" / "yottaflex.duckdb"

CUSTOMER_COLUMNS = [
    "customer_id",
    "customer_name",
    "email",
]

ORDER_COLUMNS = [
    "order_id",
    "customer_id",
    "order_date",
    "amount",
    "status",
]

CUSTOMER_REJECT_COLUMNS = CUSTOMER_COLUMNS + [
    "source_file",
    "source_row",
    "rejection_reason",
]

ORDER_REJECT_COLUMNS = ORDER_COLUMNS + [
    "source_file",
    "source_row",
    "rejection_reason",
]


def create_tables(con):
    """Create database tables and migrate older run-history schemas."""

    con.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id VARCHAR PRIMARY KEY,
            customer_name VARCHAR NOT NULL,
            email VARCHAR
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id VARCHAR PRIMARY KEY,
            customer_id VARCHAR NOT NULL,
            order_date DATE NOT NULL,
            amount DECIMAL(18, 2) NOT NULL,
            status VARCHAR NOT NULL
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS rejected_customers (
            customer_id VARCHAR,
            customer_name VARCHAR,
            email VARCHAR,
            source_file VARCHAR,
            source_row INTEGER,
            rejection_reason VARCHAR
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS rejected_orders (
            order_id VARCHAR,
            customer_id VARCHAR,
            order_date VARCHAR,
            amount VARCHAR,
            status VARCHAR,
            source_file VARCHAR,
            source_row INTEGER,
            rejection_reason VARCHAR
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id VARCHAR PRIMARY KEY,
            started_at TIMESTAMPTZ,
            finished_at TIMESTAMPTZ,
            status VARCHAR,
            customers_input BIGINT,
            customers_accepted BIGINT,
            customers_rejected BIGINT,
            orders_input BIGINT,
            orders_accepted BIGINT,
            orders_rejected BIGINT,
            elapsed_seconds DOUBLE,
            failure_reason VARCHAR
        )
    """)

    # Add failure_reason to databases created by older versions.
    columns = {
        row[1]
        for row in con.execute(
            "PRAGMA table_info('pipeline_runs')"
        ).fetchall()
    }

    if "failure_reason" not in columns:
        con.execute("""
            ALTER TABLE pipeline_runs
            ADD COLUMN failure_reason VARCHAR
        """)


def insert_frame(con, name, frame, sql):
    """
    Register a DataFrame and execute its insert statement.

    If execution fails, let the caller roll back and close the
    connection. Avoid issuing cleanup SQL during an aborted transaction.
    """

    con.register(name, frame)

    try:
        con.execute(sql)
    except Exception:
        raise
    else:
        con.unregister(name)


def record_failed_run(
    run_id,
    started_at,
    started_clock,
    failure_reason,
    customer_input_count=0,
    customer_accepted_count=0,
    customer_rejected_count=0,
    order_input_count=0,
    order_accepted_count=0,
    order_rejected_count=0,
):
    """Persist a failed run using a separate database connection."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(DB_PATH))

    try:
        create_tables(con)

        finished_at = datetime.now(timezone.utc)
        elapsed_seconds = round(
            perf_counter() - started_clock,
            4,
        )

        con.execute(
            """
            INSERT INTO pipeline_runs (
                run_id,
                started_at,
                finished_at,
                status,
                customers_input,
                customers_accepted,
                customers_rejected,
                orders_input,
                orders_accepted,
                orders_rejected,
                elapsed_seconds,
                failure_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                run_id,
                started_at,
                finished_at,
                "failed",
                customer_input_count,
                customer_accepted_count,
                customer_rejected_count,
                order_input_count,
                order_accepted_count,
                order_rejected_count,
                elapsed_seconds,
                failure_reason[:4000],
            ],
        )

    finally:
        con.close()


def publish_to_duckdb(
    valid_customers,
    valid_orders,
    rejected_customers,
    rejected_orders,
    customer_input_count,
    order_input_count,
    started_at,
    started_clock,
):
    """Publish a complete snapshot transactionally and record run status."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    run_id = str(uuid4())

    customers_df = pd.DataFrame(
        valid_customers,
        columns=CUSTOMER_COLUMNS,
    )

    orders_df = pd.DataFrame(
        valid_orders,
        columns=ORDER_COLUMNS,
    )

    rejected_customers_df = pd.DataFrame(
        rejected_customers,
        columns=CUSTOMER_REJECT_COLUMNS,
    )

    rejected_orders_df = pd.DataFrame(
        rejected_orders,
        columns=ORDER_REJECT_COLUMNS,
    )

    con = duckdb.connect(str(DB_PATH))

    try:
        create_tables(con)
        con.execute("BEGIN TRANSACTION")

        # Replace the previous data snapshot.
        con.execute("DELETE FROM customers")
        con.execute("DELETE FROM orders")
        con.execute("DELETE FROM rejected_customers")
        con.execute("DELETE FROM rejected_orders")

        insert_frame(
            con,
            "incoming_customers",
            customers_df,
            """
            INSERT INTO customers (
                customer_id,
                customer_name,
                email
            )
            SELECT
                customer_id,
                customer_name,
                email
            FROM incoming_customers
            """,
        )

        insert_frame(
            con,
            "incoming_orders",
            orders_df,
            """
            INSERT INTO orders (
                order_id,
                customer_id,
                order_date,
                amount,
                status
            )
            SELECT
                order_id,
                customer_id,
                CAST(order_date AS DATE),
                CAST(amount AS DECIMAL(18, 2)),
                status
            FROM incoming_orders
            """,
        )

        insert_frame(
            con,
            "incoming_rejected_customers",
            rejected_customers_df,
            """
            INSERT INTO rejected_customers (
                customer_id,
                customer_name,
                email,
                source_file,
                source_row,
                rejection_reason
            )
            SELECT
                customer_id,
                customer_name,
                email,
                source_file,
                CAST(source_row AS INTEGER),
                rejection_reason
            FROM incoming_rejected_customers
            """,
        )

        insert_frame(
            con,
            "incoming_rejected_orders",
            rejected_orders_df,
            """
            INSERT INTO rejected_orders (
                order_id,
                customer_id,
                order_date,
                amount,
                status,
                source_file,
                source_row,
                rejection_reason
            )
            SELECT
                order_id,
                customer_id,
                order_date,
                amount,
                status,
                source_file,
                CAST(source_row AS INTEGER),
                rejection_reason
            FROM incoming_rejected_orders
            """,
        )

        finished_at = datetime.now(timezone.utc)

        elapsed_seconds = round(
            perf_counter() - started_clock,
            4,
        )

        status = (
            "success_with_rejects"
            if rejected_customers or rejected_orders
            else "success"
        )

        # Supply one value for every SQL placeholder.
        con.execute(
            """
            INSERT INTO pipeline_runs (
                run_id,
                started_at,
                finished_at,
                status,
                customers_input,
                customers_accepted,
                customers_rejected,
                orders_input,
                orders_accepted,
                orders_rejected,
                elapsed_seconds,
                failure_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                run_id,
                started_at,
                finished_at,
                status,
                customer_input_count,
                len(valid_customers),
                len(rejected_customers),
                order_input_count,
                len(valid_orders),
                len(rejected_orders),
                elapsed_seconds,
                None,
            ],
        )

        con.execute("COMMIT")

        run_info = {
            "run_id": run_id,
            "status": status,
            "elapsed_seconds": elapsed_seconds,
        }

    except Exception as exc:
        # Roll back the data replacement before recording the failure.
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass

        # Close the failed transaction's connection before opening
        # a separate connection for the failure audit.
        try:
            con.close()
        finally:
            con = None

        failure_reason = (
            f"{type(exc).__name__}: {exc}"
        )

        try:
            record_failed_run(
                run_id=run_id,
                started_at=started_at,
                started_clock=started_clock,
                failure_reason=failure_reason,
                customer_input_count=customer_input_count,
                customer_accepted_count=len(valid_customers),
                customer_rejected_count=len(rejected_customers),
                order_input_count=order_input_count,
                order_accepted_count=len(valid_orders),
                order_rejected_count=len(rejected_orders),
            )
        except Exception as audit_exc:
            # Preserve the original publication exception even if
            # the separate failure audit cannot be written.
            print(
                "WARNING: Could not record failed pipeline run: "
                f"{audit_exc}"
            )

        raise

    finally:
        if con is not None:
            con.close()

    print("\nDATABASE PUBLISHING")
    print(f"Database: {DB_PATH}")
    print(f"Run ID: {run_info['run_id']}")
    print(f"Status: {run_info['status']}")
    print(
        f"Processing seconds: "
        f"{run_info['elapsed_seconds']}"
    )

    return run_info