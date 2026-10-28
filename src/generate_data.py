import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "data" / "generated"

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

VALID_STATUSES = ["pending", "completed", "cancelled"]


def generate_customers(path, count, rng, invalid_rate):
    """Generate deterministic customer data with deliberate defects."""

    path.parent.mkdir(parents=True, exist_ok=True)
    invalid_count = 0

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CUSTOMER_COLUMNS)
        writer.writeheader()

        for i in range(1, count + 1):
            row = {
                "customer_id": f"C{i:07d}",
                "customer_name": f"Customer {i:07d}",
                "email": f"customer{i:07d}@example.com",
            }

            # Keep the first row valid so duplicate tests have a known target.
            if i > 1 and rng.random() < invalid_rate:
                issue = rng.choice(
                    ["missing_id", "duplicate_id", "invalid_email"]
                )

                if issue == "missing_id":
                    row["customer_id"] = ""
                elif issue == "duplicate_id":
                    row["customer_id"] = "C0000001"
                else:
                    row["email"] = "not-an-email"

                invalid_count += 1

            writer.writerow(row)

    return invalid_count


def generate_orders(path, count, customer_count, rng, invalid_rate):
    """Generate reproducible orders and selected invalid cases."""

    path.parent.mkdir(parents=True, exist_ok=True)
    invalid_count = 0
    start_date = date(2026, 10, 1)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=ORDER_COLUMNS)
        writer.writeheader()

        for i in range(1, count + 1):
            customer_number = rng.randint(1, customer_count)

            row = {
                "order_id": f"O{i:07d}",
                "customer_id": f"C{customer_number:07d}",
                "order_date": (
                    start_date + timedelta(days=rng.randint(0, 27))
                ).isoformat(),
                "amount": f"{rng.uniform(10, 5000):.2f}",
                "status": rng.choice(VALID_STATUSES),
            }

            # Keep the first row valid as a known duplicate target.
            if i > 1 and rng.random() < invalid_rate:
                issue = rng.choice([
                    "unknown_customer",
                    "negative_amount",
                    "invalid_date",
                    "invalid_amount",
                    "invalid_status",
                    "missing_order_id",
                    "duplicate_order_id",
                ])

                if issue == "unknown_customer":
                    row["customer_id"] = "C999999999"
                elif issue == "negative_amount":
                    row["amount"] = "-25.00"
                elif issue == "invalid_date":
                    row["order_date"] = "not-a-date"
                elif issue == "invalid_amount":
                    row["amount"] = "abc"
                elif issue == "invalid_status":
                    row["status"] = "unknown"
                elif issue == "missing_order_id":
                    row["order_id"] = ""
                elif issue == "duplicate_order_id":
                    row["order_id"] = "O0000001"

                invalid_count += 1

            writer.writerow(row)

    return invalid_count


def main():
    parser = argparse.ArgumentParser(
        description="Generate reproducible YottaFlex pipeline CSV inputs."
    )

    parser.add_argument("--customers", type=int, default=20000)
    parser.add_argument("--orders", type=int, default=100000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--invalid-rate", type=float, default=0.01)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)

    args = parser.parse_args()

    if args.customers < 1:
        parser.error("--customers must be at least 1")

    if args.orders < 1:
        parser.error("--orders must be at least 1")

    if not 0 <= args.invalid_rate < 1:
        parser.error("--invalid-rate must be at least 0 and less than 1")

    rng = random.Random(args.seed)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    customers_path = output_dir / "customers.csv"
    orders_path = output_dir / "orders.csv"

    customer_invalid = generate_customers(
        customers_path,
        args.customers,
        rng,
        args.invalid_rate,
    )

    order_invalid = generate_orders(
        orders_path,
        args.orders,
        args.customers,
        rng,
        args.invalid_rate,
    )

    metadata = {
        "seed": args.seed,
        "requested_customers": args.customers,
        "requested_orders": args.orders,
        "invalid_rate": args.invalid_rate,
        "customer_rows_with_injected_defects": customer_invalid,
        "order_rows_with_injected_defects": order_invalid,
        "total_source_rows": args.customers + args.orders,
        "customers_file": str(customers_path),
        "orders_file": str(orders_path),
    }

    metadata_path = output_dir / "generation_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )

    print("DATA GENERATION COMPLETE")
    print(f"Customers: {args.customers:,}")
    print(f"Orders: {args.orders:,}")
    print(f"Total data rows: {args.customers + args.orders:,}")
    print(f"Seed: {args.seed}")
    print(f"Invalid-data rate: {args.invalid_rate:.2%}")
    print(f"Output directory: {output_dir}")
    print(f"Metadata: {metadata_path}")


if __name__ == "__main__":
    main()
