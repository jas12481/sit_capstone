"""
migrate_workflows_to_storage.py — One-time migration: dify-data/*.yml → Supabase Storage.

Seeds the "dify-workflows" bucket with the current on-disk workflow exports so
Storage starts out identical to dify-data/ before it becomes the sole source
of truth for "current" workflow state (scan/status/snapshot/upload all move
to reading Storage instead of local disk after this). dify-data/ itself is
kept afterward as a frozen historical artifact, not deleted.

Safe to re-run — uploads use upsert, so re-running just overwrites with
whatever's currently on disk rather than erroring on existing files.

Usage:
    python migrate_workflows_to_storage.py
"""

import glob
import os

from dotenv import load_dotenv
from supabase import create_client

BUCKET = "dify-workflows"

load_dotenv()


def main() -> None:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY not set in .env")
        return

    sb = create_client(url, key)

    files = sorted(glob.glob("dify-data/*.yml"))
    if not files:
        print("No .yml files found under dify-data/.")
        return

    print(f"Migrating {len(files)} file(s) to Storage bucket '{BUCKET}'...\n")

    success, failed = 0, []

    for i, path in enumerate(files, 1):
        name = os.path.basename(path)
        print(f"[{i:02d}/{len(files)}] {name}...", end=" ", flush=True)
        try:
            with open(path, "rb") as f:
                raw = f.read()

            sb.storage.from_(BUCKET).upload(
                path=name,
                file=raw,
                file_options={"content-type": "application/x-yaml", "upsert": "true"},
            )
            print(f"OK ({len(raw):,}b)")
            success += 1
        except Exception as e:  # noqa: BLE001
            print(f"FAILED — {e}")
            failed.append(name)

    print(f"\n{success}/{len(files)} uploaded successfully.")
    if failed:
        print(f"Failed: {', '.join(failed)}")

    # Verify: list what's actually in the bucket now
    print("\nVerifying bucket contents...")
    listed = sb.storage.from_(BUCKET).list()
    listed_names = sorted(item["name"] for item in listed)
    print(f"Bucket now contains {len(listed_names)} file(s).")

    local_names = sorted(os.path.basename(p) for p in files)
    missing = set(local_names) - set(listed_names)
    if missing:
        print(f"WARNING — present locally but not confirmed in bucket: {sorted(missing)}")
    else:
        print("Confirmed: every local file is present in the bucket.")


if __name__ == "__main__":
    main()
