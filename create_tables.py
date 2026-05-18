"""
One-shot script to create all database tables.
Run once after PostgreSQL is up: python create_tables.py
"""
from db import sync_engine, Base

print("Creating tables...")
Base.metadata.create_all(sync_engine)
print("Done. Tables created:")
for table in Base.metadata.sorted_tables:
    print(f"  - {table.name}")
