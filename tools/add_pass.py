"""
add_pass.py - Manajemen API key + user + default config.

Jalankan:
    python add_pass.py                     # menu interaktif
    python add_pass.py --list              # list semua API key
    python add_pass.py --add               # tambah API key
    python add_pass.py --edit <id>         # edit API key
    python add_pass.py --delete <id>       # hapus API key
    python add_pass.py --revoke <id>       # revoke
    python add_pass.py --activate <id>     # aktifkan
    python add_pass.py --default           # set default config
    python add_pass.py --reset             # hapus SEMUA API key
    python add_pass.py --users             # list semua user
    python add_pass.py --del-user <id>     # hapus user
"""
import sys
import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

from sqlalchemy import select, func, delete
from pathlib import Path
import sys
# ═══════════════════════════════════════════════════════════
#  PATH FIX — supaya bisa import dari root project
# ═══════════════════════════════════════════════════════════
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
# ═══════════════════════════════════════════════════════════

from db import get_session
from db.models import ApiKey, User


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


def section(title):
    print()
    cprint("=" * 72, C.CYAN)
    cprint("  " + title, C.BOLD + C.CYAN)
    cprint("=" * 72, C.CYAN)


# ═══════════════════════════════════════════════════════════
#  KONFIRMASI (Enter = Ya)
# ═══════════════════════════════════════════════════════════
def ask_yes_no(question, default_yes=True):
    """
    Tanya Y/N. Enter = default (ya).
    Return True kalau ya.
    """
    suffix = "[Y/n]" if default_yes else "[y/N]"
    answer = input(f"  {question} {suffix} (enter): ").strip().lower()
    if not answer:
        return default_yes
    return answer in ("y", "ya", "yes", "1", "true")


def ask_confirm_delete(what):
    """
    Konfirmasi hapus dengan pola: 'hapus $konten ? Y/N (enter)'
    Enter = default (ya kalau default_yes=True).
    """
    cprint(f"\n  ⚠️  Hapus {what} ? Y/N (enter = ya)", C.YELLOW)
    answer = input("  > ").strip().lower()
    if not answer or answer in ("y", "ya", "yes"):
        return True
    return False


def ask_text(prompt, default=""):
    """Input teks dengan default."""
    if default:
        val = input(f"  {prompt} [{default}]: ").strip()
        return val if val else default
    return input(f"  {prompt}: ").strip()


# ═══════════════════════════════════════════════════════════
#  DEFAULT CONFIG (disimpan di file)
# ═══════════════════════════════════════════════════════════
DEFAULT_CONFIG_FILE = Path(__file__).parent / "data" / "default_config.json"

DEFAULT_CONFIG = {
    "user": {
        "rate_limit": 100,
        "expires_days": 30,
    },
    "admin": {
        "rate_limit": 1200,
        "expires_days": 90,
    },
}


def load_default_config():
    """Load default config dari file."""
    if DEFAULT_CONFIG_FILE.exists():
        try:
            data = json.loads(DEFAULT_CONFIG_FILE.read_text(encoding="utf-8"))
            # Merge dengan default
            result = {
                "user": {**DEFAULT_CONFIG["user"], **data.get("user", {})},
                "admin": {**DEFAULT_CONFIG["admin"], **data.get("admin", {})},
            }
            return result
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_default_config(cfg):
    """Simpan default config ke file."""
    DEFAULT_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_CONFIG_FILE.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════
def fmt_dt(dt):
    if not dt:
        return "-"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M")


def time_until(dt):
    if not dt:
        return "∞ (no expiry)"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if dt < now:
        return "EXPIRED"
    delta = dt - now
    days = delta.days
    hours = delta.seconds // 3600
    if days > 0:
        return f"{days}d {hours}h"
    minutes = delta.seconds // 60
    return f"{hours}h {minutes}m"


def parse_expires(s):
    """Parse input expires."""
    s = str(s).strip().lower()
    if not s or s in ("0", "none", "never"):
        return None

    if "-" in s:
        try:
            dt = datetime.strptime(s, "%Y-%m-%d")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    try:
        days = int(s)
        if days <= 0:
            return None
        return datetime.now(timezone.utc) + timedelta(days=days)
    except ValueError:
        pass

    return None


# ═══════════════════════════════════════════════════════════
#  LIST KEY
# ═══════════════════════════════════════════════════════════
def list_keys():
    section("📋 DAFTAR API KEY")

    with get_session() as s:
        keys = list(s.execute(select(ApiKey).order_by(ApiKey.id)).scalars())

        if not keys:
            cprint("  (belum ada API key)", C.YELLOW)
            return []

        print(f"  {'ID':<4} {'PREFIX':<16} {'NAME':<18} {'ROLE':<7} "
              f"{'LIMIT':<7} {'USED':<6} {'STATUS':<10} {'EXPIRES':<17} {'TIME'}")
        cprint("  " + "-" * 110, C.DIM)

        for k in keys:
            if not k.is_active:
                status = f"{C.RED}REVOKED{C.RESET}"
            elif k.expires_at:
                exp = k.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp < datetime.now(timezone.utc):
                    status = f"{C.RED}EXPIRED{C.RESET}"
                else:
                    status = f"{C.GREEN}ACTIVE{C.RESET}"
            else:
                status = f"{C.GREEN}ACTIVE{C.RESET}"

            tu = time_until(k.expires_at)
            if tu == "EXPIRED":
                tu = f"{C.RED}{tu}{C.RESET}"
            elif tu.startswith("∞"):
                tu = f"{C.DIM}{tu}{C.RESET}"

            print(f"  {k.id:<4} {k.key_prefix:<16} {(k.name or '-')[:16]:<18} "
                  f"{k.role:<7} {k.rate_limit:<7} {k.request_count or 0:<6} "
                  f"{status:<20} {fmt_dt(k.expires_at):<17} {tu}")

        return keys


# ═══════════════════════════════════════════════════════════
#  LIST USER
# ═══════════════════════════════════════════════════════════
def list_users():
    section("👤 DAFTAR USER")

    with get_session() as s:
        users = list(s.execute(select(User).order_by(User.id)).scalars())

        if not users:
            cprint("  (belum ada user)", C.YELLOW)
            return []

        print(f"  {'ID':<4} {'USERNAME':<20} {'EMAIL':<28} {'ROLE':<7} "
              f"{'ACTIVE':<8} {'CREATED':<17} {'LAST LOGIN'}")
        cprint("  " + "-" * 110, C.DIM)

        for u in users:
            active = f"{C.GREEN}YES{C.RESET}" if u.is_active else f"{C.RED}NO{C.RESET}"

            # Count keys
            key_count = s.scalar(
                select(func.count()).select_from(ApiKey).where(ApiKey.user_id == u.id)
            ) or 0

            print(f"  {u.id:<4} {u.username[:18]:<20} {(u.email or '-')[:26]:<28} "
                  f"{u.role:<7} {active:<16} {fmt_dt(u.created_at):<17} {fmt_dt(u.last_login)}")
            if key_count:
                print(f"       {C.DIM}└─ {key_count} API key{C.RESET}")

        return users


# ═══════════════════════════════════════════════════════════
#  ADD KEY
# ═══════════════════════════════════════════════════════════
def add_key_interactive():
    section("➕ TAMBAH API KEY BARU")

    cfg = load_default_config()

    name = ask_text("Nama key", "default")

    # Role
    print("  Role:")
    print("    [1] user  (default)")
    print("    [2] admin")
    role_choice = input("  Pilih (1/2) [1]: ").strip() or "1"
    role = "admin" if role_choice == "2" else "user"

    # Ambil default dari config
    default_limit = cfg[role]["rate_limit"]
    default_days = cfg[role]["expires_days"]

    # Rate limit
    limit_str = ask_text("Rate limit (req/menit)", str(default_limit))
    try:
        rate_limit = int(limit_str)
    except ValueError:
        rate_limit = default_limit

    # Expires
    print("  Expired:")
    print("    Kosong / 0 / none = tanpa expired")
    print("    Angka (mis. 30)   = X hari dari sekarang")
    print("    Tanggal (YYYY-MM-DD) = tanggal spesifik")
    default_exp_str = str(default_days) if default_days else "none"
    exp_str = ask_text("Expires", default_exp_str)
    if exp_str == "none":
        expires_at = None
    else:
        expires_at = parse_expires(exp_str)

    # User (opsional)
    user_id = None
    with get_session() as s:
        users = list(s.execute(select(User)).scalars())
        if users:
            print()
            print("  Bind ke user? (opsional)")
            for u in users[:10]:
                print(f"    [{u.id}] {u.username} ({u.role})")
            uid = ask_text("User ID (kosong = tidak bind)", "")
            if uid:
                try:
                    user_id = int(uid)
                except ValueError:
                    user_id = None

    # Konfirmasi
    print()
    cprint("  Konfirmasi:", C.BOLD)
    print(f"    Name       : {name}")
    print(f"    Role       : {role}")
    print(f"    Rate limit : {rate_limit} req/menit")
    print(f"    Expires at : {fmt_dt(expires_at)}  ({time_until(expires_at)})")
    print(f"    User ID    : {user_id or '(tidak bind)'}")
    print()

    if not ask_yes_no("Lanjut buat?", default_yes=True):
        cprint("  ❌ Dibatalkan", C.YELLOW)
        return None

    # Generate
    from security.api_key import generate_api_key

    with get_session() as s:
        result = generate_api_key(
            s,
            name=name,
            user_id=user_id,
            role=role,
            rate_limit=rate_limit,
            expires_days=None,
        )

        if expires_at:
            key = s.get(ApiKey, result["info"]["id"])
            key.expires_at = expires_at
            s.flush()

        s.commit()

    print()
    cprint("  ✅ API KEY BERHASIL DIBUAT", C.GREEN)
    cprint("  " + "-" * 60, C.DIM)
    cprint(f"  KEY: {result['key']}", C.BOLD + C.GREEN)
    cprint("  " + "-" * 60, C.DIM)
    cprint("  ⚠️  SIMPAN KEY DI ATAS — HANYA MUNCUL SEKALI!", C.YELLOW)
    print()
    print(f"  ID         : {result['info']['id']}")
    print(f"  Prefix     : {result['info']['key_prefix']}")
    print(f"  Name       : {result['info']['name']}")
    print(f"  Role       : {result['info']['role']}")
    print(f"  Rate limit : {result['info']['rate_limit']} req/menit")
    print(f"  Expires    : {fmt_dt(expires_at)}")

    return result["info"]["id"]


# ═══════════════════════════════════════════════════════════
#  EDIT KEY
# ═══════════════════════════════════════════════════════════
def edit_key(key_id):
    section(f"✏️  EDIT API KEY #{key_id}")

    with get_session() as s:
        key = s.get(ApiKey, key_id)
        if not key:
            cprint(f"  ❌ API key ID {key_id} tidak ditemukan", C.RED)
            return False

        cprint("  Data saat ini:", C.BOLD)
        print(f"    ID         : {key.id}")
        print(f"    Prefix     : {key.key_prefix}")
        print(f"    Name       : {key.name}")
        print(f"    Role       : {key.role}")
        print(f"    Rate limit : {key.rate_limit} req/menit")
        print(f"    Used       : {key.request_count or 0}")
        print(f"    Active     : {key.is_active}")
        print(f"    Expires    : {fmt_dt(key.expires_at)}  ({time_until(key.expires_at)})")
        print()

        cprint("  Yang mau diubah:", C.BOLD)
        print("    [1] Name")
        print("    [2] Rate limit")
        print("    [3] Expires")
        print("    [4] Role")
        print("    [5] Active (revoke/activate)")
        print("    [6] Semua")
        print("    [0] Batal")

        choice = input("  Pilih [0]: ").strip() or "0"

        if choice == "0":
            cprint("  ❌ Dibatalkan", C.YELLOW)
            return False

        changes = []

        def change_name():
            v = ask_text("Name baru", key.name or "")
            if v and v != key.name:
                key.name = v
                changes.append(f"name -> {v}")

        def change_limit():
            v = ask_text("Rate limit baru", str(key.rate_limit))
            try:
                val = int(v)
                if val != key.rate_limit:
                    key.rate_limit = val
                    changes.append(f"rate_limit -> {val}")
            except ValueError:
                cprint("  ⚠️  Bukan angka", C.YELLOW)

        def change_expires():
            print("  Format: kosong / 30 / 2026-12-31 / none")
            current = fmt_dt(key.expires_at) if key.expires_at else "none"
            v = ask_text("Expires baru", current)
            new_exp = parse_expires(v) if v != "none" else None
            key.expires_at = new_exp
            changes.append(f"expires -> {fmt_dt(new_exp)}")

        def change_role():
            print("    [1] user  [2] admin")
            v = input("  Role baru [1]: ").strip() or "1"
            new_role = "admin" if v == "2" else "user"
            if new_role != key.role:
                key.role = new_role
                changes.append(f"role -> {new_role}")

        def change_active():
            current = "ACTIVE" if key.is_active else "REVOKED"
            print(f"  Status saat ini: {current}")
            print("    [1] Aktifkan  [2] Revoke")
            v = input("  Pilih: ").strip()
            if v == "1" and not key.is_active:
                key.is_active = True
                changes.append("is_active -> True")
            elif v == "2" and key.is_active:
                key.is_active = False
                changes.append("is_active -> False")

        if choice == "1":
            change_name()
        elif choice == "2":
            change_limit()
        elif choice == "3":
            change_expires()
        elif choice == "4":
            change_role()
        elif choice == "5":
            change_active()
        elif choice == "6":
            change_name()
            change_limit()
            change_expires()
            change_role()
            change_active()

        if not changes:
            cprint("  ℹ️  Tidak ada perubahan", C.YELLOW)
            return False

        print()
        cprint("  Perubahan:", C.BOLD)
        for ch in changes:
            print(f"    • {ch}")

        if not ask_yes_no("Simpan?", default_yes=True):
            cprint("  ❌ Dibatalkan", C.YELLOW)
            s.rollback()
            return False

        s.commit()
        cprint("  ✅ API key berhasil diupdate", C.GREEN)
        return True


# ═══════════════════════════════════════════════════════════
#  DELETE KEY
# ═══════════════════════════════════════════════════════════
def delete_key(key_id, force=False):
    section(f"🗑️  HAPUS API KEY #{key_id}")

    with get_session() as s:
        key = s.get(ApiKey, key_id)
        if not key:
            cprint(f"  ❌ API key ID {key_id} tidak ditemukan", C.RED)
            return False

        cprint("  Data yang akan dihapus:", C.BOLD)
        print(f"    ID         : {key.id}")
        print(f"    Prefix     : {key.key_prefix}")
        print(f"    Name       : {key.name}")
        print(f"    Role       : {key.role}")
        print(f"    Rate limit : {key.rate_limit}")
        print()

        if not force:
            if not ask_confirm_delete(f"API key #{key_id} ({key.key_prefix})"):
                cprint("  ❌ Dibatalkan", C.YELLOW)
                return False

        s.delete(key)
        s.commit()

    cprint(f"  ✅ API key #{key_id} berhasil dihapus", C.GREEN)
    return True


# ═══════════════════════════════════════════════════════════
#  SET ACTIVE
# ═══════════════════════════════════════════════════════════
def set_active(key_id, active):
    action = "aktifkan" if active else "revoke"
    section(f"🔧 {action.upper()} API KEY #{key_id}")

    with get_session() as s:
        key = s.get(ApiKey, key_id)
        if not key:
            cprint(f"  ❌ API key ID {key_id} tidak ditemukan", C.RED)
            return False

        key.is_active = active
        s.commit()

        status = "AKTIF" if active else "REVOKED"
        icon = "✅" if active else "🚫"
        cprint(f"  {icon} API key #{key_id} ({key.key_prefix}...) -> {status}", C.GREEN)
        return True


# ═══════════════════════════════════════════════════════════
#  SET DEFAULT CONFIG ⭐ NEW
# ═══════════════════════════════════════════════════════════
def set_default_config():
    section("⚙️  SET DEFAULT CONFIG")

    cfg = load_default_config()

    cprint("  Config saat ini:", C.BOLD)
    print(f"    USER  : {cfg['user']['rate_limit']} req/menit, {cfg['user']['expires_days']} hari")
    print(f"    ADMIN : {cfg['admin']['rate_limit']} req/menit, {cfg['admin']['expires_days']} hari")
    print()

    cprint("  Set default untuk role:", C.BOLD)
    print("    [1] USER")
    print("    [2] ADMIN")
    print("    [3] Keduanya")
    print("    [0] Batal")

    choice = input("  Pilih [0]: ").strip() or "0"

    if choice == "0":
        cprint("  ❌ Dibatalkan", C.YELLOW)
        return

    roles_to_edit = []
    if choice == "1":
        roles_to_edit = ["user"]
    elif choice == "2":
        roles_to_edit = ["admin"]
    elif choice == "3":
        roles_to_edit = ["user", "admin"]

    for role in roles_to_edit:
        print()
        cprint(f"  ── Default untuk {role.upper()} ──", C.CYAN)

        current_limit = cfg[role]["rate_limit"]
        current_days = cfg[role]["expires_days"]

        limit_str = ask_text("Rate limit (req/menit)", str(current_limit))
        try:
            cfg[role]["rate_limit"] = int(limit_str)
        except ValueError:
            pass

        days_str = ask_text("Expires (hari, 0=none)", str(current_days or 0))
        try:
            cfg[role]["expires_days"] = int(days_str) if int(days_str) > 0 else None
        except ValueError:
            pass

    # Konfirmasi
    print()
    cprint("  Config baru:", C.BOLD)
    for role in ["user", "admin"]:
        exp_str = f"{cfg[role]['expires_days']} hari" if cfg[role]["expires_days"] else "∞"
        print(f"    {role.upper():<6}: {cfg[role]['rate_limit']} req/menit, {exp_str}")
    print()

    if not ask_yes_no("Simpan config?", default_yes=True):
        cprint("  ❌ Dibatalkan", C.YELLOW)
        return

    save_default_config(cfg)
    cprint("  ✅ Default config tersimpan", C.GREEN)
    print(f"  📁 File: {DEFAULT_CONFIG_FILE}")


# ═══════════════════════════════════════════════════════════
#  RESET ALL KEYS ⭐ NEW
# ═══════════════════════════════════════════════════════════
def reset_all_keys():
    section("🚨 RESET SEMUA API KEY")

    with get_session() as s:
        count = s.scalar(select(func.count()).select_from(ApiKey)) or 0

        if count == 0:
            cprint("  ℹ️  Tidak ada API key", C.YELLOW)
            return

        cprint(f"  ⚠️  Akan menghapus {count} API key!", C.RED)
        cprint(f"  ⚠️  Tindakan ini TIDAK BISA DIBATALKAN!", C.RED)
        print()

        # Konfirmasi 2 lapis
        if not ask_confirm_delete(f"SEMUA {count} API key"):
            cprint("  ❌ Dibatalkan", C.YELLOW)
            return

        # Lapis 2: ketik "DELETE"
        cprint("\n  Ketik 'DELETE' untuk konfirmasi final:", C.BOLD)
        confirm = input("  > ").strip()
        if confirm != "DELETE":
            cprint("  ❌ Dibatalkan (ketikan salah)", C.YELLOW)
            return

        # Hapus semua
        s.execute(delete(ApiKey))
        s.commit()

    cprint(f"\n  ✅ {count} API key berhasil dihapus", C.GREEN)


# ═══════════════════════════════════════════════════════════
#  DELETE USER ⭐ NEW
# ═══════════════════════════════════════════════════════════
def delete_user(user_id, force=False):
    section(f"🗑️  HAPUS USER #{user_id}")

    with get_session() as s:
        user = s.get(User, user_id)
        if not user:
            cprint(f"  ❌ User ID {user_id} tidak ditemukan", C.RED)
            return False

        # Cek jumlah API key milik user
        key_count = s.scalar(
            select(func.count()).select_from(ApiKey).where(ApiKey.user_id == user_id)
        ) or 0

        cprint("  Data yang akan dihapus:", C.BOLD)
        print(f"    ID         : {user.id}")
        print(f"    Username   : {user.username}")
        print(f"    Email      : {user.email or '-'}")
        print(f"    Role       : {user.role}")
        print(f"    Created    : {fmt_dt(user.created_at)}")
        print(f"    Last login : {fmt_dt(user.last_login)}")
        if key_count:
            cprint(f"    ⚠️  {key_count} API key milik user ini akan IKUT TERHAPUS", C.YELLOW)
        print()

        if not force:
            if not ask_confirm_delete(f"user '{user.username}'"):
                cprint("  ❌ Dibatalkan", C.YELLOW)
                return False

        # Hapus user (API key akan cascade delete karena FK ondelete="CASCADE")
        s.delete(user)
        s.commit()

    cprint(f"  ✅ User #{user_id} ({user.username}) berhasil dihapus", C.GREEN)
    if key_count:
        cprint(f"     + {key_count} API key ikut terhapus", C.DIM)
    return True


# ═══════════════════════════════════════════════════════════
#  STATS
# ═══════════════════════════════════════════════════════════
def show_stats():
    section("📊 STATISTIK")

    with get_session() as s:
        # API Key stats
        total_keys = s.scalar(select(func.count()).select_from(ApiKey)) or 0
        active_keys = s.scalar(
            select(func.count()).select_from(ApiKey).where(ApiKey.is_active == True)
        ) or 0
        revoked_keys = total_keys - active_keys

        # User stats
        total_users = s.scalar(select(func.count()).select_from(User)) or 0
        active_users = s.scalar(
            select(func.count()).select_from(User).where(User.is_active == True)
        ) or 0

        # Expired keys
        now = datetime.now(timezone.utc)
        all_keys = list(s.execute(select(ApiKey)).scalars())
        expired = 0
        soon = 0
        for k in all_keys:
            if k.expires_at:
                exp = k.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp < now:
                    expired += 1
                elif (exp - now).days <= 7:
                    soon += 1

        total_req = sum(k.request_count or 0 for k in all_keys)

    cprint("  🔑 API KEY", C.BOLD + C.CYAN)
    print(f"    Total       : {total_keys}")
    print(f"    {C.GREEN}Aktif{C.RESET}       : {active_keys}")
    print(f"    {C.RED}Revoked{C.RESET}     : {revoked_keys}")
    print(f"    {C.YELLOW}Expired{C.RESET}     : {expired}")
    print(f"    {C.YELLOW}Expiring soon{C.RESET}: {soon}  (< 7 hari)")
    print(f"    Total req   : {total_req}")
    print()

    cprint("  👤 USER", C.BOLD + C.CYAN)
    print(f"    Total       : {total_users}")
    print(f"    {C.GREEN}Aktif{C.RESET}       : {active_users}")


# ═══════════════════════════════════════════════════════════
#  MENU
# ═══════════════════════════════════════════════════════════
MENU = """
╔══════════════════════════════════════════════════════════════╗
║           🔑 ANIWATCH KEY MANAGER - v2                       ║
╠══════════════════════════════════════════════════════════════╣
║  API KEY                                                     ║
║    [1] 📋 List semua API key                                 ║
║    [2] ➕ Tambah API key baru                                ║
║    [3] ✏️  Edit API key                                      ║
║    [4] 🗑️  Hapus API key                                     ║
║    [5] 🚫 Revoke API key                                     ║
║    [6] ✅ Aktifkan API key                                   ║
║    [7] 🧹 Cleanup expired keys                               ║
║                                                              ║
║  CONFIG & BULK                                               ║
║    [8] ⚙️  Set default (limit + expired per role)            ║
║    [9] 🚨 Reset ALL keys (hapus semua)                       ║
║                                                              ║
║  USER                                                        ║
║    [10] 👤 List users                                        ║
║    [11] 🗑️  Hapus user                                       ║
║                                                              ║
║  INFO                                                        ║
║    [12] 📊 Statistik                                         ║
║    [0]  🚪 Keluar                                            ║
╚══════════════════════════════════════════════════════════════╝
"""


def cleanup_expired():
    section("🧹 CLEANUP EXPIRED KEYS")

    with get_session() as s:
        now = datetime.now(timezone.utc)
        keys = list(s.execute(select(ApiKey)).scalars())

        expired = []
        for k in keys:
            if k.expires_at:
                exp = k.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp < now:
                    expired.append(k)

        if not expired:
            cprint("  ✅ Tidak ada API key expired", C.GREEN)
            return

        cprint(f"  Ditemukan {len(expired)} API key expired:", C.YELLOW)
        for k in expired:
            print(f"    #{k.id} {k.key_prefix} ({k.name}) — {fmt_dt(k.expires_at)}")

        print()
        if not ask_confirm_delete(f"{len(expired)} API key expired"):
            cprint("  ❌ Dibatalkan", C.YELLOW)
            return

        for k in expired:
            s.delete(k)
        s.commit()

    cprint(f"  ✅ {len(expired)} API key dihapus", C.GREEN)


def interactive_menu():
    while True:
        print(MENU)
        choice = input(f"  {C.CYAN}Pilih menu [0]: {C.RESET}").strip() or "0"

        try:
            if choice == "0":
                cprint("\n  👋 Bye!", C.CYAN)
                break
            elif choice == "1":
                list_keys()
            elif choice == "2":
                add_key_interactive()
            elif choice == "3":
                list_keys()
                print()
                kid = ask_text("ID key yang mau diedit", "")
                if kid:
                    edit_key(int(kid))
            elif choice == "4":
                list_keys()
                print()
                kid = ask_text("ID key yang mau dihapus", "")
                if kid:
                    delete_key(int(kid))
            elif choice == "5":
                list_keys()
                print()
                kid = ask_text("ID key yang mau di-revoke", "")
                if kid:
                    set_active(int(kid), False)
            elif choice == "6":
                list_keys()
                print()
                kid = ask_text("ID key yang mau diaktifkan", "")
                if kid:
                    set_active(int(kid), True)
            elif choice == "7":
                cleanup_expired()
            elif choice == "8":
                set_default_config()
            elif choice == "9":
                reset_all_keys()
            elif choice == "10":
                list_users()
            elif choice == "11":
                list_users()
                print()
                uid = ask_text("ID user yang mau dihapus", "")
                if uid:
                    delete_user(int(uid))
            elif choice == "12":
                show_stats()
            else:
                cprint("  ❓ Pilihan tidak valid", C.YELLOW)
        except KeyboardInterrupt:
            cprint("\n  ⏸️  Dibatalkan", C.YELLOW)
            continue
        except Exception as e:
            cprint(f"  ❌ Error: {type(e).__name__}: {e}", C.RED)

        print()
        try:
            input(f"{C.DIM}  [Enter untuk lanjut]{C.RESET}")
        except KeyboardInterrupt:
            pass
        import os
        os.system("cls" if os.name == "nt" else "clear")


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(
        description="Manajemen API key AniWatch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--list", "-l", action="store_true")
    ap.add_argument("--add", "-a", action="store_true")
    ap.add_argument("--edit", "-e", type=int, metavar="ID")
    ap.add_argument("--delete", "-d", type=int, metavar="ID")
    ap.add_argument("--revoke", "-r", type=int, metavar="ID")
    ap.add_argument("--activate", type=int, metavar="ID")
    ap.add_argument("--cleanup", action="store_true")
    ap.add_argument("--default", action="store_true", help="Set default config")
    ap.add_argument("--reset", action="store_true", help="Reset SEMUA API key")
    ap.add_argument("--users", "-u", action="store_true", help="List users")
    ap.add_argument("--del-user", type=int, metavar="ID", help="Hapus user")
    ap.add_argument("--stats", "-s", action="store_true")
    ap.add_argument("--yes", "-y", action="store_true", help="Skip konfirmasi")
    args = ap.parse_args()

    if args.list:
        list_keys()
    elif args.add:
        add_key_interactive()
    elif args.edit is not None:
        edit_key(args.edit)
    elif args.delete is not None:
        delete_key(args.delete, force=args.yes)
    elif args.revoke is not None:
        set_active(args.revoke, False)
    elif args.activate is not None:
        set_active(args.activate, True)
    elif args.cleanup:
        cleanup_expired()
    elif args.default:
        set_default_config()
    elif args.reset:
        reset_all_keys()
    elif args.users:
        list_users()
    elif args.del_user is not None:
        delete_user(args.del_user, force=args.yes)
    elif args.stats:
        show_stats()
    else:
        interactive_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Interrupted\n")