"""
control/seed.py — Import JSON hasil scrape ke database.

Jalankan:
    python -m control.seed data/output/yowaki-max-sub-indo.json
    python -m control.seed data/output/      # semua JSON di folder
"""
import sys
import json
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from db import get_session, init_db
from db.repository import save_scrape_result


def seed_from_file(json_path: Path):
    """Import 1 file JSON."""
    print(f"  📄 {json_path.name}...")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"     ❌ Gagal baca: {e}")
        return False

    # Kalau format dari scraper.py
    if "metadata" in data and "episode_details" in data:
        counters = save_scrape_result(data)
        print(f"     ✅ Anime: {counters['anime']}, "
              f"Episode: {counters['episodes']}, "
              f"Download: {counters['downloads']}")
        return True

    # Kalau format array [episodes]
    if isinstance(data, list):
        fake_result = {
            "source": "otakudesu",
            "slug": json_path.stem,
            "url": "",
            "metadata": {"title": json_path.stem, "genres": []},
            "episode_details": data,
        }
        counters = save_scrape_result(fake_result)
        print(f"     ✅ Episode: {counters['episodes']}, "
              f"Download: {counters['downloads']}")
        return True

    print(f"     ⚠️  Format tidak dikenal")
    return False


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage:")
        print("  python -m control.seed <file.json>")
        print("  python -m control.seed <folder/>")
        return

    target = Path(args[0])

    print("=" * 62)
    print("  🌱 SEED DATABASE")
    print("=" * 62)

    # Init dulu
    init_db()

    if target.is_file() and target.suffix == ".json":
        seed_from_file(target)
    elif target.is_dir():
        files = list(target.glob("*.json"))
        print(f"  📁 Found {len(files)} JSON files\n")
        ok = 0
        for f in files:
            if seed_from_file(f):
                ok += 1
        print(f"\n  ✅ Seeded {ok}/{len(files)} files")
    else:
        print(f"  ❌ Target tidak valid: {target}")


if __name__ == "__main__":
    main()