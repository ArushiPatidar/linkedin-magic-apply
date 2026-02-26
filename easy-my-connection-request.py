import argparse
from main import main as linkedin_main

def main():
    parser = argparse.ArgumentParser(description="Automate connection requests.")
    parser.add_argument(
        "--applicationPortal",
        type=str,
        choices=["linkedin", "instahyre"],
        default="linkedin",
        help="Portal to use: linkedin or instahyre (default: linkedin)"
    )
    args = parser.parse_args()

    if args.applicationPortal == "instahyre":
        from instahyre.instahyre_apply import apply_to_jobs
        apply_to_jobs()
    else:
        linkedin_main()

if __name__ == "__main__":
    main()