"""
convert_genre_to_flat.py - Konversi slug_by_genre.json (nested) ke anime_flat.json.

Jalankan:
    python tools/convert_genre_to_flat.py                          # default
    python tools/convert_genre_to_flat.py --input data/slug.json   # custom
    python tools/convert_genre_to_flat.py --output data/anime.json # custom out
    python tools/convert_genre_to_flat.py --dedupe                 # hapus duplikat
"""
import sys
import json
import argparse
from pathlib import Path

# ═══════════════════════════════════════════════════════════
#  PATH FIX
# ═══════════════════════════════════════════════════════════
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ═══════════════════════════════════════════════════════════
#  DEFAULT
# ═══════════════════════════════════════════════════════════
DEFAULT_INPUT = _ROOT / "data" / "base" / "dump" / "slug_by_genre.json"
DEFAULT_OUTPUT = _ROOT / "data" / "base" / "cache" / "anime_flat.json"


# ═══════════════════════════════════════════════════════════
#  COLORS
# ═══════════════════════════════════════════════════════════
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"


def cprint(text, color=""):
    print(f"{color}{text}{C.RESET}")


# ═══════════════════════════════════════════════════════════
#  CONVERT
# ═══════════════════════════════════════════════════════════
def convert(input_path, output_path, dedupe=True, use_slug=False):
    """
    Konversi nested JSON ke flat.

    Input format (nested):
        {
          "action": {
            "count": 45,
            "animes": [
              {"slug": "psyren-sub-indo", "title": "Psyren", ...}
            ]
          }
        }

    Output format (flat):
        {
          "ANIME_1": "Psyren",
          "ANIME_2": "Tempal: Item no Chikara",
          ...
        }
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    # Cek input
    if not input_path.exists():
        cprint(f"❌ Input tidak ada: {input_path}", C.RED)
        return False

    # Baca JSON
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception as e:
        cprint(f"❌ Gagal baca JSON: {e}", C.RED)
        return False

    # ═══ Detect format ═══
    items = []

    if not isinstance(data, dict):
        cprint("❌ Format tidak dikenali (harus dict)", C.RED)
        return False

    # Cek: nested atau flat?
    nested = False
    for k, v in data.items():
        if isinstance(v, dict) and "animes" in v:
            nested = True
            break

    # ═══ Nested format ═══
    if nested:
        cprint("📦 Format: Nested (per genre)", C.CYAN)
        print()
        seen = set()
        idx = 1

        for genre_key, genre_data in data.items():
            animes = genre_data.get("animes", [])
            print(f"  📁 {genre_key:<20} {len(animes)} anime")

            for anime in animes:
                if isinstance(anime, dict):
                    title = anime.get("title") or anime.get("slug") or ""
                    slug = anime.get("slug", "")
                elif isinstance(anime, str):
                    title = anime
                    slug = anime
                else:
                    continue

                if not title:
                    continue

                # Dedupe
                key = slug or title
                if dedupe and key in seen:
                    continue
                seen.add(key)

                # Value: pakai slug atau title?
                value = slug if use_slug else title

                items.append({
                    "value": value,
                    "title": title,
                    "slug": slug,
                    "genre": genre_key,
                })
                idx += 1

    # ═══ Flat format (sudah flat) ═══
    else:
        cprint("📦 Format: Flat (sudah)", C.CYAN)
        for k, v in data.items():
            if isinstance(v, str):
                items.append({"value": v, "title": v, "slug": v, "genre": ""})

    # ═══ Build output ═══
    output = {}
    for i, item in enumerate(items, 1):
        output[f"ANIME_{i}"] = item["value"]

    # Simpan
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Ringkasan
    print()
    cprint("=" * 60, C.GREEN)
    cprint("  ✅ SELESAI", C.BOLD + C.GREEN)
    cprint("=" * 60, C.GREEN)
    print()
    print(f"  📥 Input   : {input_path}")
    print(f"  📤 Output  : {output_path}")
    print(f"  📊 Total   : {len(items)} anime")
    if dedupe:
        print(f"  🧹 Dedupe  : ON")
    print(f"  💾 Size    : {output_path.stat().st_size:,} bytes")
    print()

    # Preview
    print(f"  Preview 10:")
    for i, (k, v) in enumerate(list(output.items())[:10], 1):
        print(f"    {k:<12} = {v}")

    return True


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(
        description="Konversi nested JSON ke flat (ANIME_N)",
    )
    ap.add_argument("--input", "-i", type=str, default=str(DEFAULT_INPUT),
                    help=f"Input JSON (default: {DEFAULT_INPUT})")
    ap.add_argument("--output", "-o", type=str, default=str(DEFAULT_OUTPUT),
                    help=f"Output JSON (default: {DEFAULT_OUTPUT})")
    ap.add_argument("--dedupe", action="store_true", default=True,
                    help="Hapus duplikat (default: ON)")
    ap.add_argument("--no-dedupe", action="store_true",
                    help="Jangan hapus duplikat")
    ap.add_argument("--use-slug", action="store_true",
                    help="Pakai slug (bukan title)")

    args = ap.parse_args()

    dedupe = not args.no_dedupe

    print()
    cprint("=" * 60, C.CYAN)
    cprint("  CONVERT GENRE TO FLAT", C.BOLD + C.CYAN)
    cprint("=" * 60, C.CYAN)
    print()

    success = convert(
        args.input,
        args.output,
        dedupe=dedupe,
        use_slug=args.use_slug,
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Interrupted\n")
        sys.exit(130)