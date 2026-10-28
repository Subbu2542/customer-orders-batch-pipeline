import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from src.validate import (
    CUSTOMER_COLUMNS,
    ORDER_COLUMNS,
    load_csv,
    validate_customers,
    validate_orders,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data" / "generated"
REPORT_DIR = ROOT / "outputs" / "reports"


def run_benchmark(customers_path, orders_path):
    """
    Measure CSV loading and row-level validation.

    This benchmark does not publish data to DuckDB and does not
    write curated or rejected CSV outputs.
    """

    total_start = perf_counter()

    # Step 1: Measure CSV ingestion.
    load_start = perf_counter()

    customers_df = load_csv(
        customers_path,
        CUSTOMER_COLUMNS,
    )

    orders_df = load_csv(
        orders_path,
        ORDER_COLUMNS,
    )

    load_seconds = perf_counter() - load_start

    # Step 2: Validate customers.
    customer_start = perf_counter()

    valid_customers, rejected_customers = validate_customers(
        customers_df
    )

    customer_seconds = perf_counter() - customer_start

    # Step 3: Build the set of accepted customer IDs.
    customer_ids = {
        row["customer_id"]
        for row in valid_customers
    }

    # Step 4: Validate orders and customer references.
    order_start = perf_counter()

    valid_orders, rejected_orders = validate_orders(
        orders_df,
        customer_ids,
    )

    order_seconds = perf_counter() - order_start

    # Step 5: Calculate overall runtime and record counts.
    total_seconds = perf_counter() - total_start

    customer_input = len(customers_df)
    order_input = len(orders_df)

    total_input = customer_input + order_input

    customer_accepted = len(valid_customers)
    customer_rejected = len(rejected_customers)

    order_accepted = len(valid_orders)
    order_rejected = len(rejected_orders)

    # Step 6: Reconcile the input and output counts.
    customer_reconciled = (
        customer_input
        == customer_accepted + customer_rejected
    )

    order_reconciled = (
        order_input
        == order_accepted + order_rejected
    )

    overall_reconciled = (
        customer_reconciled and order_reconciled
    )

    # Step 7: Calculate throughput.
    rows_per_second = (
        total_input / total_seconds
        if total_seconds > 0
        else None
    )

    # Step 8: Return structured results.
    return {
        "customers": {
            "input": customer_input,
            "accepted": customer_accepted,
            "rejected": customer_rejected,
            "reconciled": customer_reconciled,
            "validation_seconds": round(
                customer_seconds, 4
            ),
        },
        "orders": {
            "input": order_input,
            "accepted": order_accepted,
            "rejected": order_rejected,
            "reconciled": order_reconciled,
            "validation_seconds": round(
                order_seconds, 4
            ),
        },
        "load_seconds": round(load_seconds, 4),
        "total_input_rows": total_input,
        "total_seconds": round(total_seconds, 4),
        "rows_per_second": round(
            rows_per_second, 2
        ) if rows_per_second is not None else None,
        "overall_reconciled": overall_reconciled,
    }


def main():
    """Parse arguments, run benchmarks, and save the report."""

    parser = argparse.ArgumentParser(
        description=(
            "Benchmark CSV ingestion and data validation."
        )
    )

    parser.add_argument(
        "--customers",
        type=Path,
        default=DEFAULT_DATA_DIR / "customers.csv",
        help="Path to the customer CSV file.",
    )

    parser.add_argument(
        "--orders",
        type=Path,
        default=DEFAULT_DATA_DIR / "orders.csv",
        help="Path to the order CSV file.",
    )

    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Number of measured iterations (default: 1).",
    )

    args = parser.parse_args()

    # Validate the repeat count.
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")

    # Validate both input files before starting the benchmark.
    for path in [args.customers, args.orders]:
        if not path.is_file():
            parser.error(
                f"Input file does not exist: {path}"
            )

    # Run exactly one warm-up, outside the file-validation loop.
    print("Warm-up iteration (excluded from results)...")

    warmup = run_benchmark(
        args.customers,
        args.orders,
    )

    print(
        f"Warm-up complete: "
        f"{warmup['total_seconds']:.4f}s"
    )

    # Only measured runs are added to this list.
    results = []

    for iteration in range(1, args.repeats + 1):
        print(
            f"Benchmark iteration "
            f"{iteration}/{args.repeats}..."
        )

        result = run_benchmark(
            args.customers,
            args.orders,
        )

        results.append(result)

        print(
            f"  Rows: {result['total_input_rows']:,} | "
            f"Runtime: {result['total_seconds']:.4f}s | "
            f"Throughput: "
            f"{result['rows_per_second']:,.2f} rows/s"
        )

    # Calculate medians using measured runs only.
    runtimes = [
        item["total_seconds"]
        for item in results
    ]

    throughputs = [
        item["rows_per_second"]
        for item in results
        if item["rows_per_second"] is not None
    ]

    median_runtime = statistics.median(runtimes)

    median_throughput = (
        statistics.median(throughputs)
        if throughputs
        else None
    )

    all_runs_reconciled = all(
        item["overall_reconciled"]
        for item in results
    )

    # Build the benchmark report.
    report = {
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "customers_file": str(
            args.customers.resolve()
        ),
        "orders_file": str(
            args.orders.resolve()
        ),
        "repeats": args.repeats,
        "warmup_iterations": 1,
        "methodology": (
            "Exactly one warm-up iteration is excluded. "
            "Measured timings include CSV loading and "
            "row-level validation, but exclude DuckDB "
            "publishing and output CSV writing."
        ),
        "median_runtime_seconds": round(
            median_runtime, 4
        ),
        "median_rows_per_second": (
            round(median_throughput, 2)
            if median_throughput is not None
            else None
        ),
        "iterations": results,
        "all_runs_reconciled": all_runs_reconciled,
    }

    # Create report directory if necessary.
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    report_path = REPORT_DIR / (
        f"benchmark_{timestamp}.json"
    )

    latest_path = REPORT_DIR / "benchmark_latest.json"

    report_text = json.dumps(
        report,
        indent=2,
    ) + "\n"

    # Save the timestamped and latest reports.
    report_path.write_text(
        report_text,
        encoding="utf-8",
    )

    latest_path.write_text(
        report_text,
        encoding="utf-8",
    )

    # Print final summary.
    print("\nBENCHMARK SUMMARY")

    print(
        f"Median runtime: "
        f"{report['median_runtime_seconds']} seconds"
    )

    if report["median_rows_per_second"] is not None:
        print(
            f"Median throughput: "
            f"{report['median_rows_per_second']} rows/second"
        )

    print(
        f"All runs reconciled: "
        f"{report['all_runs_reconciled']}"
    )

    print(f"Report: {report_path}")

    # Exit unsuccessfully if the counts do not reconcile.
    if not all_runs_reconciled:
        raise SystemExit(
            "ERROR: At least one benchmark iteration "
            "failed reconciliation."
        )


if __name__ == "__main__":
    main()