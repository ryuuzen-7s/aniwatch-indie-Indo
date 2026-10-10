"""
Worker — baca daftar slug dari agent/.env, lalu scrape satu per satu.

Output:
  data/dump/<slug>.json per anime

Usage:
  python -m agent.worker
  python main.py worker
"""
import json
import time
from pathlib import Path

from config import config
from logger import get_logger
from agent.otakudesu import OtakudesuScraper

log = get_logger("Worker")


class Worker:
    """Loop scraping berdasarkan daftar slug di agent/.env."""

    def __init__(self):
        self.scraper = OtakudesuScraper()

    # ------------------------------------------------------------------
    def run(self, slugs: list[str] | None = None) -> dict:
        """
        Jalankan scraping untuk semua slug.
        Return ringkasan: {total, ok, gagal, hasil}
        """
        slugs = slugs or config.get_slugs()

        if not slugs:
            log.warning(
                "Tidak ada slug di agent/.env. "
                "Tambahkan SLUG_1=... lalu jalankan lagi."
            )
            return {"total": 0, "ok": 0, "gagal": 0, "hasil": []}

        config.ensure_dirs()
        log.info(f"Worker mulai: {len(slugs)} slug")

        hasil = []
        ok = 0
        gagal = 0

        for i, slug in enumerate(slugs, 1):
            log.info(f"[{i}/{len(slugs)}] Proses: {slug}")
            try:
                data = self.scraper.get_anime(slug)

                if "error" in data:
                    gagal += 1
                    log.error(f"[{i}/{len(slugs)}] GAGAL {slug}: {data['error']}")
                    if config.WORKER_STOP_ON_ERROR:
                        log.error("WORKER_STOP_ON_ERROR=true, berhenti.")
                        break
                    continue

                ok += 1
                hasil.append({
                    "slug": data.get("slug", slug),
                    "title": data.get("title", ""),
                    "episodes": len(data.get("episodes", [])),
                })

                if config.WORKER_SAVE_EACH:
                    self._save(data)

                # Jeda sopan antar anime
                if i < len(slugs):
                    time.sleep(config.WORKER_DELAY)

            except Exception as e:
                gagal += 1
                log.exception(f"[{i}/{len(slugs)}] ERROR {slug}: {e}")
                if config.WORKER_STOP_ON_ERROR:
                    break

        ringkasan = {
            "total": len(slugs),
            "ok": ok,
            "gagal": gagal,
            "hasil": hasil,
        }
        self._print_summary(ringkasan)
        return ringkasan

    # ------------------------------------------------------------------
    def _save(self, data: dict) -> Path:
        """Simpan hasil satu anime ke data/dump/<slug>.json."""
        slug = data.get("slug", "unknown")
        out_file = config.DUMP_DIR / f"{slug}.json"
        out_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        try:
            rel = out_file.relative_to(config.ROOT_DIR)
        except ValueError:
            rel = out_file
        log.info(f"  tersimpan: {rel}")
        return out_file

    # ------------------------------------------------------------------
    @staticmethod
    def _print_summary(r: dict) -> None:
        print()
        print("=" * 40)
        print("worker selesai")
        print("=" * 40)
        print(f"  total  : {r['total']}")
        print(f"  ok     : {r['ok']}")
        print(f"  gagal  : {r['gagal']}")
        print("-" * 40)
        for h in r["hasil"]:
            print(f"  [{h['episodes']:>3} ep] {h['title'][:50]}")
        print("=" * 40)
        print()


# ======================================================================
# Manual run
# ======================================================================
def main():
    Worker().run()


if __name__ == "__main__":
    main()