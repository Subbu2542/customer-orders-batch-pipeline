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
    """Measure CSV loading and validation without publishing data."""

    total_start = perf_counter()

    # Measure source ingestion.
    load_start = perf_counter()

    customers_df = load_csv(customers_path, CUSTOMER_COLUMNS)
    orders_df = load_csv(orders_path, ORDER_COLUMNS)

    load_seconds = perf_counter() - load_start

    # Measure customer validation.
    customer_start = perf_counter()

    valid_customers, rejected_customers = validate_customers(
        customers_df
    )

    customer_seconds = perf_counter() - customer_start

    # Measure order validation.
    customer_ids = {
        row["customer_id"] for row in valid_customers
    }

    order_start = perf_counter()

    valid_orders, rejected_orders = validate_orders(
        orders_df,
        customer_ids,
    )

    order_seconds = perf_counter() - order_start

    total_seconds = perf_counter() - total_start

    customer_input = len(customers_df)
    order_input = len(orders_df)
    total_input = customer_input + order_input

    customer_reconciled = (
        customer_input
        == len(valid_customers) + len(rejected_customers)
    )

    order_reconciled = (
        order_input == len(valid_orders) + len(rejected_orders)
    )

    return {
        "customers": {
            "input": customer_input,
            "accepted": len(valid_customers),
            "rejected": len(rejected_customers),
            "reconciled": customer_reconciled,
            "validation_seconds": round(customer_seconds, 4),
        },
        "orders": {
            "input": order_input,
            "accepted": len(valid_orders),
            "rejected": len(rejected_orders),
            "reconciled": order_reconciled,
            "validation_seconds": round(order_seconds, 4),
        },
        "load_seconds": round(load_seconds, 4),
        "total_input_rows": total_input,
        "total_seconds": round(total_seconds, 4),
        "rows_per_second": round(
            total_input / total_seconds, 2
        ) if total_seconds > 0 else None,
        "overall_reconciled": (
            customer_reconciled and order_reconciled
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark CSV ingestion and validation."
    )

    parser.add_argument(
        "--customers",
        type=Path,
        default=DEFAULT_DATA_DIR / "customers.csv",
    )
    parser.add_argument(
        "--orders",
        type=Path,
        default=DEFAULT_DATA_DIR / "orders.csv",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Number of benchmark iterations (default: 1).",
    )

    args = parser.parse_args()

    if args.repeats < 1:
        parser.error("--repeats must be at least 1")

    for path in [args.customers, args.orders]:
        if not path.is_file():
            parser.error(f"Input file does not exist: {path}")

        print("Warm-up iteration (excluded from results)...")
        warmup = run_benchmark(args.customers, args.orders)

        print(
        f"Warm-up complete: {warmup['total_seconds']:.4f}s"
)
    results = []

    for iteration in range(1, args.repeats + 1):
        print(f"Benchmark iteration {iteration}/{args.repeats}...")

        result = run_benchmark(args.customers, args.orders)
        results.append(result)

        print(
            f"  Rows: {result['total_input_rows']:,} | "
            f"Runtime: {result['total_seconds']:.4f}s | "
            f"Throughput: {result['rows_per_second']:,.2f} rows/s"
        )

    runtimes = [item["total_seconds"] for item in results]
    throughputs = [item["rows_per_second"] for item in results]

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "customers_file": str(args.customers.resolve()),
        "orders_file": str(args.orders.resolve()),
        "repeats": args.repeats,
        "methodology": (
            "One warm-up iteration is excluded. Timings include CSV loading "
            "and row-level validation, but exclude DuckDB publishing and "
            "output CSV writing."
        ),
        "median_runtime_seconds": round(
            statistics.median(runtimes), 4
        ),
        "median_rows_per_second": round(
            statistics.median(throughputs), 2
        ),
        "iterations": results,
        "all_runs_reconciled": all(
            item["overall_reconciled"] for item in results
        ),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    report_path = REPORT_DIR / f"benchmark_{timestamp}.json"
    latest_path = REPORT_DIR / "benchmark_latest.json"

    report_path.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    latest_path.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    print("\nBENCHMARK SUMMARY")
    print(f"Median runtime: {report['median_runtime_seconds']} seconds")
    print(f"Median throughput: {report['median_rows_per_second']} rows/second")
    print(f"All runs reconciled: {report['all_runs_reconciled']}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
