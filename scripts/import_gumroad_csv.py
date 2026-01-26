import csv
import os
import sys

from models import SessionLocal, Subscriber, init_db


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_gumroad_csv.py path/to/gumroad.csv")
        return 1

    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return 1

    init_db()
    session = SessionLocal()
    added = 0
    updated = 0

    try:
        with open(csv_path, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                email = _extract_email(row)
                if not email:
                    continue
                email = email.strip().lower()
                subscriber = session.query(Subscriber).filter_by(email=email).first()
                if subscriber:
                    subscriber.status = "paid"
                    subscriber.is_active = True
                    updated += 1
                else:
                    subscriber = Subscriber(
                        email=email,
                        status="paid",
                        unsubscribe_token=os.urandom(12).hex(),
                        is_active=True,
                    )
                    session.add(subscriber)
                    added += 1
        session.commit()
    finally:
        session.close()

    print(f"Added: {added}")
    print(f"Updated: {updated}")
    return 0


def _extract_email(row: dict) -> str | None:
    for key in row.keys():
        if key.lower() in {"email", "buyer email", "buyer_email"}:
            return row.get(key)
    return None


if __name__ == "__main__":
    raise SystemExit(main())
