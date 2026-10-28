import json
import logging
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
REPORT_DIR = ROOT / "outputs" / "reports"


def configure_logging():
    """Configure console and persistent file logging."""

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                LOG_DIR / "pipeline.log",
                encoding="utf-8",
            ),
        ],
        force=True,
    )

    return logging.getLogger("yottaflex.pipeline")


def write_reconciliation_report(run_info, counts):
    """Write per-run and latest-run JSON reconciliation reports."""

    customers = counts["customers"]
    orders = counts["orders"]

    customer_reconciled = (
        customers["input"]
        == customers["accepted"] + customers["rejected"]
    )

    order_reconciled = (
        orders["input"]
        == orders["accepted"] + orders["rejected"]
    )

    report = {
        "report_generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "run_id": run_info["run_id"],
        "pipeline_status": run_info["status"],
        "elapsed_seconds": run_info["elapsed_seconds"],
        "entities": {
            "customers": {
                **customers,
                "reconciled": customer_reconciled,
            },
            "orders": {
                **orders,
                "reconciled": order_reconciled,
            },
        },
        "total_input_rows": (
            customers["input"] + orders["input"]
        ),
        "total_accepted_rows": (
            customers["accepted"] + orders["accepted"]
        ),
        "total_rejected_rows": (
            customers["rejected"] + orders["rejected"]
        ),
        "overall_reconciled": (
            customer_reconciled and order_reconciled
        ),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    paths = [
        REPORT_DIR / f"run_{run_info['run_id']}.json",
        REPORT_DIR / "latest_run.json",
    ]

    for path in paths:
        temporary_path = path.with_suffix(path.suffix + ".tmp")

        try:
            temporary_path.write_text(
                json.dumps(report, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary_path.replace(path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    return paths[0]
