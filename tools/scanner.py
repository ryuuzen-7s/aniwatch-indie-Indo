"""
scanner.py - Scan bug di semua file project (v2).

Jalankan:
    python tools/scanner.py              # scan default (semua .py)
    python tools/scanner.py --full       # scan + web + config
    python tools/scanner.py --path api   # scan folder tertentu
    python tools/scanner.py --ext .py,.js # custom extension
"""
import sys
import re
import ast
import json
import argparse
import py_compile
from datetime import datetime
from pathlib import Path
from collections import defaultdict


# ═══════════════════════════════════════════════════════════
#  PATH FIX
# ═══════════════════════════════════════════════════════════
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


ROOT = _ROOT
REPORT_FILE = ROOT / "data" / "base" / "scanner_report.json"


# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
SKIP_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "env",
    "node_modules", ".pytest_cache", ".ruff_cache",
    ".vscode", ".idea", "data", "backup", "logs",
    "output", "aniwatch_output", "debug_output",
    "env_backup", "scrape_output", "resolver_output",
    "api", "core", "db", "cache", "security",
    "control", "agent", "web", "docs", "test", "tools",
    "deploy", "scripts", "fixed", "bin",
}

SCAN_EXT_DEFAULT = [".py"]
SCAN_EXT_FULL = [".py", ".js", ".css", ".html", ".json", ".md", ".txt"]

MIN_FILE_SIZE = 30


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
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


def cprint(text, color=""):
    print(f"{color}{text}{C.RESET}")


# ═══════════════════════════════════════════════════════════
#  STRIP KOMENTAR & STRING
# ═══════════════════════════════════════════════════════════
def strip_comments(content, ext=".py"):
    """
    Hapus komentar dari file.

    Untuk .py: pakai ast (akurat).
    Untuk lain: pakai regex.
    """
    if ext == ".py":
        return strip_comments_python(content)
    elif ext in (".js", ".css"):
        # Hapus /* */ dan //
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        content = re.sub(r"//[^\n]*", "", content)
        return content
    elif ext in (".html",):
        # Hapus <!-- -->
        return re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    elif ext == ".json":
        # JSON tidak punya komentar
        return content
    else:
        return content


def strip_comments_python(content):
    """
    Hapus komentar Python.
    Docstring multi-line dihapus, tapi string biasa dipertahankan.
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        # Kalau syntax error, pakai regex fallback
        return _strip_comments_regex(content)

    lines = content.split("\n")
    to_remove = set()

    # Tandai baris yang di-remove (docstring)
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                # Ini docstring
                for i in range(node.lineno - 1, node.end_lineno):
                    if i < len(lines):
                        to_remove.add(i)

    # Untuk komentar, hapus inline comment
    result = []
    for i, line in enumerate(lines):
        if i in to_remove:
            result.append("")
            continue
        # Hapus komentar inline (# ...) tapi jaga string
        # Cari '#' yang tidak di dalam string
        cleaned = _remove_inline_comment(line)
        result.append(cleaned)

    return "\n".join(result)


def _strip_comments_regex(content):
    """Fallback: hapus komentar dengan regex."""
    # Hapus inline comments
    lines = []
    for line in content.split("\n"):
        lines.append(_remove_inline_comment(line))
    return "\n".join(lines)


def _remove_inline_comment(line):
    """Hapus komentar inline, jaga string."""
    in_string = False
    quote_char = None
    i = 0
    while i < len(line):
        c = line[i]

        if not in_string:
            if c in ('"', "'"):
                in_string = True
                quote_char = c
            elif c == "#":
                return line[:i].rstrip()
        else:
            if c == "\\":
                i += 2
                continue
            elif c == quote_char:
                in_string = False
                quote_char = None

        i += 1

    return line


# ═══════════════════════════════════════════════════════════
#  SCAN 1 — SYNTAX ERROR
# ═══════════════════════════════════════════════════════════
def scan_python_syntax(path):
    try:
        py_compile.compile(str(path), doraise=True)
        return None
    except py_compile.PyCompileError as e:
        msg = str(e)
        m = re.search(r"line (\d+)", msg)
        line = m.group(1) if m else "?"
        clean = re.sub(r"\s+", " ", msg)[:200]
        return f"SyntaxError line {line}: {clean}"
    except Exception as e:
        return f"{type(e).__name__}: {str(e)[:200]}"


# ═══════════════════════════════════════════════════════════
#  SCAN 2 — FILE KOSONG / KECIL
# ═══════════════════════════════════════════════════════════
def scan_empty(path):
    size = path.stat().st_size

    if size == 0:
        return "File kosong (0 byte)"

    if path.suffix == ".py" and size < MIN_FILE_SIZE:
        # Skip __init__.py (boleh kosong / cuma docstring)
        if path.name == "__init__.py":
            return None
        return f"File terlalu kecil ({size} byte)"

    # Cek file yang cuma komentar
    if path.suffix == ".py":
        content = path.read_text(encoding="utf-8", errors="ignore")

        # Skip __init__.py
        if path.name == "__init__.py":
            return None

        # Strip komentar
        stripped = strip_comments_python(content).strip()

        if not stripped:
            return f"File hanya komentar/docstring ({size} byte)"

    return None


# ═══════════════════════════════════════════════════════════
#  SCAN 3 — MISSING IMPORTS
# ═══════════════════════════════════════════════════════════
def scan_missing_imports(path):
    """Cek import hilang di file Python."""
    if path.suffix != ".py":
        return None

    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return None

    # Strip komentar dulu
    stripped = strip_comments_python(content)

    issues = []

    # Mapping: modul → import yang dibutuhkan
    checks = [
        ("logging.getLogger", "import logging"),
        ("logging.", "import logging"),
        ("json.loads", "import json"),
        ("json.dumps", "import json"),
        ("secrets.", "import secrets"),
        ("hashlib.", "import hashlib"),
        ("threading.", "import threading"),
        ("re.match", "import re"),
        ("re.search", "import re"),
        ("re.sub", "import re"),
        ("re.findall", "import re"),
        ("time.sleep", "import time"),
        ("time.time", "import time"),
        ("os.system", "import os"),
        ("os.path", "import os"),
        ("os.environ", "import os"),
        ("os.name", "import os"),
    ]

    for usage, import_stmt in checks:
        if usage in stripped:
            # Cek apakah import ada
            if import_stmt not in stripped:
                # Khusus logging
                if import_stmt == "import logging":
                    if "logging.getLogger" in stripped or "logging.info" in stripped:
                        issues.append(f"{usage} dipakai tapi tidak ada '{import_stmt}'")
                    continue
                issues.append(f"{usage} dipakai tapi tidak ada '{import_stmt}'")

    # Cek Depends (FastAPI)
    if "Depends(" in stripped:
        # Cari import from fastapi
        m = re.search(r"from fastapi import ([^\n]+)", stripped)
        has_depends = False
        if m and "Depends" in m.group(1):
            has_depends = True
        elif "import Depends" in stripped:
            has_depends = True

        if not has_depends:
            issues.append("Depends dipakai tapi tidak import dari fastapi")

    # Cek Path
    if "Path(" in stripped:
        has_path = (
            "from pathlib import Path" in stripped
            or "import pathlib" in stripped
            or "Path," in stripped
            or "Path)" in stripped
        )
        if not has_path:
            issues.append("Path dipakai tapi tidak import")

    # Cek datetime
    if "datetime.now" in stripped or "datetime.strptime" in stripped:
        has_dt = "from datetime import" in stripped or "import datetime" in stripped
        if not has_dt:
            issues.append("datetime dipakai tapi tidak import")

    # Dedupe issues
    seen = set()
    unique = []
    for issue in issues:
        if issue not in seen:
            seen.add(issue)
            unique.append(issue)

    return unique if unique else None


# ═══════════════════════════════════════════════════════════
#  SCAN 4 — TODO/FIXME (HANYA KOMENTAR)
# ═══════════════════════════════════════════════════════════
def scan_todo_fixme(path):
    """
    Cek TODO/FIXME yang BENAR-BENAR masalah.
    Hanya deteksi di KOMENTAR, bukan di string / docstring.
    """
    # Skip file scanner sendiri
    if path.name == "scanner.py":
        return None

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    issues = []

    if path.suffix == ".py":
        # Extract komentar saja (bukan string, bukan docstring)
        comments = _extract_comments_python(content)

        for pattern in ["TODO", "FIXME", "XXX", "HACK"]:
            # Cari pattern sebagai kata utuh
            regex = re.compile(rf"\b{pattern}\b", re.IGNORECASE)
            for comment in comments:
                if regex.search(comment):
                    # Ambil konteks
                    text = comment.strip()[:100]
                    issues.append(f"{pattern}: {text}")
                    break  # 1 issue per pattern per file

    elif path.suffix in (".js", ".css"):
        # Strip string (kasar)
        comments = re.findall(r"//[^\n]*|/\*.*?\*/", content, re.DOTALL)
        for pattern in ["TODO", "FIXME"]:
            for comment in comments:
                if pattern in comment.upper():
                    issues.append(f"{pattern}: {comment.strip()[:100]}")
                    break

    elif path.suffix == ".html":
        comments = re.findall(r"<!--.*?-->", content, re.DOTALL)
        for pattern in ["TODO", "FIXME"]:
            for comment in comments:
                if pattern in comment.upper():
                    issues.append(f"{pattern}: {comment.strip()[:100]}")
                    break

    return issues if issues else None


def _extract_comments_python(content):
    """
    Extract komentar Python (bukan docstring, bukan string).
    Return: list of comment strings.
    """
    comments = []

    # Strategy: parse dulu (kalau valid), extract docstring ranges
    docstring_ranges = []

    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str):
                    docstring_ranges.append((node.lineno, node.end_lineno))
    except SyntaxError:
        pass

    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        # Skip kalau di dalam docstring
        in_docstring = any(start <= i <= end for start, end in docstring_ranges)
        if in_docstring:
            continue

        # Cari '#' di luar string
        comment = _find_comment(line)
        if comment:
            comments.append(comment)

    return comments


def _find_comment(line):
    """Cari komentar (# ...) di line, return string comment atau None."""
    in_string = False
    quote_char = None
    i = 0

    while i < len(line):
        c = line[i]

        if not in_string:
            if c in ('"', "'"):
                in_string = True
                quote_char = c
            elif c == "#":
                return line[i:]
        else:
            if c == "\\":
                i += 2
                continue
            elif c == quote_char:
                in_string = False
                quote_char = None

        i += 1

    return None


# ═══════════════════════════════════════════════════════════
#  SCAN 5 — ENCODING
# ═══════════════════════════════════════════════════════════
def scan_encoding(path):
    if path.suffix not in (".py", ".js", ".css", ".html", ".json", ".md", ".txt"):
        return None

    try:
        path.read_text(encoding="utf-8")
        return None
    except UnicodeDecodeError:
        return "Encoding bukan UTF-8 (mungkin binary)"

    return None


# ═══════════════════════════════════════════════════════════
#  SCAN 6 — JSON VALIDITY
# ═══════════════════════════════════════════════════════════
def scan_json(path):
    if path.suffix != ".json":
        return None

    try:
        content = path.read_text(encoding="utf-8")
        json.loads(content)
        return None
    except json.JSONDecodeError as e:
        return f"JSON invalid: {e.msg} (line {e.lineno})"
    except Exception as e:
        return f"{type(e).__name__}: {str(e)[:100]}"


# ═══════════════════════════════════════════════════════════
#  SCANNER CLASS
# ═══════════════════════════════════════════════════════════
class Scanner:
    def __init__(self, root=ROOT, extensions=None, skip_dirs=None):
        self.root = Path(root)
        self.extensions = extensions or SCAN_EXT_DEFAULT
        self.skip_dirs = skip_dirs or SKIP_DIRS
        self.results = []

    def should_skip(self, path):
        for part in path.parts:
            if part in self.skip_dirs:
                return True
        return False

    def find_files(self):
        files = []
        for ext in self.extensions:
            for f in self.root.rglob(f"*{ext}"):
                try:
                    rel = f.relative_to(self.root)
                except ValueError:
                    continue
                if self.should_skip(rel):
                    continue
                if f.is_file():
                    files.append(f)
        return sorted(set(files))

    def scan_file(self, path):
        issues = []

        # 1. Empty / small
        issue = scan_empty(path)
        if issue:
            issues.append({"type": "empty", "msg": issue, "severity": "error"})

        # 2. Encoding
        issue = scan_encoding(path)
        if issue:
            issues.append({"type": "encoding", "msg": issue, "severity": "error"})

        # 3. Syntax
        if path.suffix == ".py":
            issue = scan_python_syntax(path)
            if issue:
                issues.append({"type": "syntax", "msg": issue, "severity": "error"})

        # 4. Missing imports
        issues_import = scan_missing_imports(path)
        if issues_import:
            for msg in issues_import:
                issues.append({"type": "import", "msg": msg, "severity": "error"})

        # 5. TODO/FIXME (hanya di komentar)
        issues_todo = scan_todo_fixme(path)
        if issues_todo:
            for msg in issues_todo:
                issues.append({"type": "todo", "msg": msg, "severity": "info"})

        # 6. JSON
        if path.suffix == ".json":
            issue = scan_json(path)
            if issue:
                issues.append({"type": "json", "msg": issue, "severity": "error"})

        return issues

    def run(self, show_progress=True):
        files = self.find_files()

        if show_progress:
            print()
            cprint("=" * 66, C.CYAN)
            cprint(f"  SCANNING {len(files)} FILES", C.BOLD + C.CYAN)
            cprint("=" * 66, C.CYAN)
            print()

        self.results = []

        for i, f in enumerate(files, 1):
            issues = self.scan_file(f)

            if show_progress:
                icon = f"{C.GREEN}✅{C.RESET}" if not issues else f"{C.RED}❌{C.RESET}"
                rel = f.relative_to(self.root)
                print(f"  {icon} [{i:>3}/{len(files)}] {rel}")

            if issues:
                self.results.append({
                    "file": str(f.relative_to(self.root)),
                    "full_path": str(f),
                    "issues": issues,
                    "size": f.stat().st_size,
                })

        return self.results

    def stats(self):
        total_files = len(self.find_files())
        bug_files = len(self.results)
        clean_files = total_files - bug_files

        by_severity = {"error": 0, "warning": 0, "info": 0}
        by_type = defaultdict(int)

        for r in self.results:
            for issue in r["issues"]:
                by_severity[issue.get("severity", "info")] += 1
                by_type[issue["type"]] += 1

        folders = set()
        for f in self.find_files():
            folders.add(f.parent.relative_to(self.root))

        return {
            "total_files": total_files,
            "total_folders": len(folders),
            "bug_files": bug_files,
            "clean_files": clean_files,
            "total_issues": sum(by_severity.values()),
            "by_severity": by_severity,
            "by_type": dict(by_type),
        }


# ═══════════════════════════════════════════════════════════
#  DISPLAY
# ═══════════════════════════════════════════════════════════
def print_header(stats):
    print()
    cprint("=" * 66, C.CYAN)
    cprint("  ANIWATCH SCANNER v2", C.BOLD + C.CYAN)
    cprint("=" * 66, C.CYAN)
    print()
    print(f"  📁 Root         : {ROOT}")
    print(f"  📊 Jumlah File  : {stats['total_files']}")
    print(f"  📁 Jumlah Folder: {stats['total_folders']}")
    print(f"  🕐 Scan time    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    cprint("=" * 66, C.CYAN)
    cprint(f"  SCANNING...", C.BOLD + C.YELLOW)
    cprint("=" * 66, C.CYAN)
    print()


def print_summary(stats, results):
    print()
    cprint("=" * 66, C.GREEN)
    cprint("  RINGKASAN", C.BOLD + C.GREEN)
    cprint("=" * 66, C.GREEN)
    print()
    print(f"  📊 Total File       : {stats['total_files']}")
    print(f"  📁 Total Folder     : {stats['total_folders']}")
    print(f"  🐛 File Bug         : {C.RED}{stats['bug_files']}{C.RESET}")
    print(f"  ✅ File Bersih      : {C.GREEN}{stats['clean_files']}{C.RESET}")
    print(f"  ⚠️  Total Issues     : {stats['total_issues']}")
    print()

    if stats["by_severity"]:
        print("  Severity:")
        sev = stats["by_severity"]
        if sev.get("error"):
            print(f"    {C.RED}❌ Error   : {sev['error']}{C.RESET}")
        if sev.get("warning"):
            print(f"    {C.YELLOW}⚠️  Warning : {sev['warning']}{C.RESET}")
        if sev.get("info"):
            print(f"    {C.CYAN}ℹ️  Info    : {sev['info']}{C.RESET}")
        print()

    if stats["by_type"]:
        print("  Tipe Issue:")
        for t, count in sorted(stats["by_type"].items(), key=lambda x: -x[1]):
            print(f"    {t:<15} : {count}")
        print()


def print_bug_details(results):
    if not results:
        cprint("  ✅ Tidak ada bug ditemukan!", C.GREEN)
        return

    cprint("=" * 66, C.RED)
    cprint(f"  DETAIL BUG ({len(results)} files)", C.BOLD + C.RED)
    cprint("=" * 66, C.RED)
    print()

    for r in results:
        cprint(f"  📄 {r['file']}", C.BOLD + C.YELLOW)
        print(f"     Size: {r['size']:,} bytes")

        for issue in r["issues"]:
            severity = issue.get("severity", "info")
            msg = issue["msg"]
            t = issue["type"]

            icon = {
                "error": f"{C.RED}❌",
                "warning": f"{C.YELLOW}⚠️ ",
                "info": f"{C.CYAN}ℹ️ ",
            }.get(severity, "•")

            print(f"       {icon} [{t}] {msg}{C.RESET}")

        print()


def print_bug_directories(results):
    if not results:
        return

    folders = defaultdict(int)
    for r in results:
        folder = str(Path(r["file"]).parent)
        folders[folder] += 1

    cprint("=" * 66, C.MAGENTA)
    cprint("  📁 DIREKTORI BUG", C.BOLD + C.MAGENTA)
    cprint("=" * 66, C.MAGENTA)
    print()

    for folder, count in sorted(folders.items(), key=lambda x: -x[1]):
        if folder == ".":
            folder = "(root)"
        bar = "█" * min(count, 30)
        cprint(f"  {folder:<40} {count:>3} file  {bar}", C.MAGENTA)
    print()


def save_report(stats, results):
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "scanned_at": datetime.now().isoformat(),
        "root": str(ROOT),
        "stats": stats,
        "bug_files": results,
    }

    REPORT_FILE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return REPORT_FILE


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(
        description="Scan bug di semua file project (v2)",
    )
    ap.add_argument("--full", action="store_true",
                    help="Scan semua extension")
    ap.add_argument("--path", "-p", type=str, default=None,
                    help="Scan folder tertentu")
    ap.add_argument("--ext", type=str, default=None,
                    help="Custom extension")
    ap.add_argument("--no-progress", action="store_true",
                    help="Sembunyikan progress")
    ap.add_argument("--json", action="store_true",
                    help="Output JSON")
    ap.add_argument("--only-errors", action="store_true",
                    help="Tampilkan hanya error")

    args = ap.parse_args()

    root = Path(args.path) if args.path else ROOT

    if args.ext:
        extensions = [e.strip() for e in args.ext.split(",")]
    elif args.full:
        extensions = SCAN_EXT_FULL
    else:
        extensions = SCAN_EXT_DEFAULT

    scanner = Scanner(root=root, extensions=extensions)

    if not args.json:
        files = scanner.find_files()
        stats_pre = {
            "total_files": len(files),
            "total_folders": len(set(f.relative_to(root).parent for f in files)),
        }
        print_header(stats_pre)

    results = scanner.run(show_progress=not args.json and not args.no_progress)
    stats = scanner.stats()

    # Filter hanya error
    if args.only_errors:
        for r in results:
            r["issues"] = [i for i in r["issues"] if i.get("severity") == "error"]
        results = [r for r in results if r["issues"]]

    if args.json:
        report = {
            "scanned_at": datetime.now().isoformat(),
            "root": str(root),
            "stats": stats,
            "bug_files": results,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    print_summary(stats, results)
    print_bug_details(results)
    print_bug_directories(results)

    report_path = save_report(stats, results)
    print()
    cprint("=" * 66, C.CYAN)
    cprint(f"  💾 Report: {report_path}", C.BOLD + C.CYAN)
    cprint("=" * 66, C.CYAN)
    print()

    if stats["by_severity"].get("error", 0) > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  ⏸️  Interrupted\n")
        sys.exit(130)