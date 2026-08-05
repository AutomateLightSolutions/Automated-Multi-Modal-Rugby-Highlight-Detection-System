"""
Command-line interface for local testing without running the full
Docker stack. Useful for testing individual pipeline stages.
"""

import argparse
import sys


def cmd_health(args):
    """Check DB and Redis connectivity."""
    print("Checking system health...\n")

    try:
        from config import settings
        import sqlalchemy
        engine = sqlalchemy.create_engine(settings.SYNC_DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        print("[OK] PostgreSQL: connected")
    except Exception as e:
        print(f"[FAIL] PostgreSQL: {e}")

    try:
        import redis
        from config import settings
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        print("[OK] Redis: connected")
    except Exception as e:
        print(f"[FAIL] Redis: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Rugby Highlight Generator CLI"
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("health", help="Check DB and Redis connectivity")

    args = parser.parse_args()

    if args.command == "health":
        cmd_health(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
