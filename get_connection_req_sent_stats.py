import csv
import os
import glob
from collections import defaultdict

LOG_DIR = os.path.join(os.path.dirname(__file__), "linkedin/log")
STATS_DIR = os.path.join(os.path.dirname(__file__), "statistics")
STATS_FILE = os.path.join(STATS_DIR, "statistics.csv")


def parse_logs():
    """Parse all CSV files in log/ and return per-company, per-date send counts."""
    # { company: { date_str: count } }
    stats = defaultdict(lambda: defaultdict(int))

    log_files = glob.glob(os.path.join(LOG_DIR, "*.csv"))
    if not log_files:
        print("[!] No log files found in log/ directory.")
        return stats

    for filepath in log_files:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                status = row.get("status", "").strip().lower()
                if status != "sent":
                    continue
                company = row.get("company", "Unknown").strip()
                timestamp = row.get("timestamp", "").strip()
                # Extract date part (YYYY-MM-DD) from timestamp
                date_str = timestamp[:10] if len(timestamp) >= 10 else "unknown"
                stats[company][date_str] += 1

    return stats


def write_statistics(stats):
    """Write aggregated statistics to statistics/statistics.csv."""
    os.makedirs(STATS_DIR, exist_ok=True)

    with open(STATS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["company", "total_sent", "date_breakdown"])

        for company in sorted(stats.keys()):
            date_counts = stats[company]
            total = sum(date_counts.values())
            breakdown = " | ".join(
                f"{date}={count}" for date, count in sorted(date_counts.items())
            )
            writer.writerow([company, total, breakdown])

    print(f"[✓] Statistics written to {STATS_FILE}")


def main():
    stats = parse_logs()
    if not stats:
        print("[!] No successful connection requests found in logs.")
        return
    write_statistics(stats)

    # Print summary to console
    print(f"\n{'Company':<30} {'Total':<8} {'Date Breakdown'}")
    print("-" * 80)
    for company in sorted(stats.keys()):
        date_counts = stats[company]
        total = sum(date_counts.values())
        breakdown = " | ".join(
            f"{d}={c}" for d, c in sorted(date_counts.items())
        )
        print(f"{company:<30} {total:<8} {breakdown}")


if __name__ == "__main__":
    main()
