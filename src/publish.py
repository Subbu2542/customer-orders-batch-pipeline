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
    """Create the database tables if they do not already exist."""

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
            elapsed_seconds DOUBLE
        )
    """)


def insert_frame(con, name, frame, sql):
    """Register a DataFrame and insert its rows.

    If insertion fails, leave cleanup to the transaction
    rollback and connection close.
    """

    con.register(name, frame)

    try:
        con.execute(sql)
    except Exception:
        # The transaction may be aborted.
        # Do not run more SQL cleanup commands here.
        raise
    else:
        con.unregister(name)


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
    """Publish a complete snapshot and run metrics transactionally."""

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
            INSERT INTO customers
            SELECT customer_id, customer_name, email
            FROM incoming_customers
            """,
        )

        insert_frame(
            con,
            "incoming_orders",
            orders_df,
            """
            INSERT INTO orders
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
            INSERT INTO rejected_customers
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
            INSERT INTO rejected_orders
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

        con.execute(
            """
            INSERT INTO pipeline_runs VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
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
            ],
        )

        # Commit the complete data snapshot and its run record.
        con.execute("COMMIT")

        print("\nDATABASE PUBLISHING")
        print(f"Database: {DB_PATH}")
        print(f"Run ID: {run_id}")
        print(f"Status: {status}")
        print(f"Processing seconds: {elapsed_seconds}")

        return {
            "run_id": run_id,
            "status": status,
            "elapsed_seconds": elapsed_seconds,
        }

    except Exception:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass

        raise

    finally:
        con.close()
