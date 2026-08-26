import requests
import json
import time
import os
import io
import subprocess
import re

from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw


# =====================================================
# EINSTELLUNGEN
# =====================================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1541600578340130897/f6xXG74cD3qIKlM28hv56FdxH0N__qaHlugIKC_oD5cd5XWzHKbANJhDEzJW9M0DJ1vl"

AES_URL = "https://fortnite-api.com/v2/aes"

ROLE_ID = "1523617106414014504"

CHECK_TIME = 30


# =====================================================
# FORTNITE PAK ORDNER
# =====================================================

PAK_DIR = r"C:\Program Files\Epic Games\Fortnite\FortniteGame\Content\Paks"


# =====================================================
# UNREALPAK.EXE
# =====================================================

UNREALPAK_EXE = (
    r"C:\Program Files\Epic Games\Fortnite"
    r"\FortniteGame\Binaries\Win64\UnrealPak.exe"
)


# =====================================================
# AES HOLEN
# =====================================================

def get_aes():

    try:

        response = requests.get(
            AES_URL,
            timeout=15
        )

        if response.status_code != 200:

            print(
                "[AES ERROR]",
                response.status_code
            )

            return []

        data = response.json()

        return (
            data
            .get("data", {})
            .get("dynamicKeys", [])
        )

    except Exception as e:

        print(
            "[AES ERROR]",
            e
        )

        return []


# =====================================================
# AES KEY MIT 0x
# =====================================================

def format_aes_key(key):

    if key is None:
        return "UNKNOWN"

    key = str(key).strip()

    if not key:
        return "UNKNOWN"

    if not key.lower().startswith("0x"):
        key = "0x" + key

    return key


# =====================================================
# EINDEUTIGE ID
# =====================================================

def get_uid(item):

    pak = str(
        item.get(
            "pakFilename",
            ""
        )
    ).strip().lower()

    key = str(
        item.get(
            "key",
            ""
        )
    ).strip().lower()

    guid = str(
        item.get(
            "pakGuid",
            ""
        )
    ).strip().lower()

    return (
        pak
        + "|"
        + key
        + "|"
        + guid
    )


# =====================================================
# DATEIGRÖSSE
# =====================================================

def format_size(size_bytes):

    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} KB"

    if size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"

    if size_bytes < 1024 ** 4:
        return f"{size_bytes / (1024 ** 3):.2f} GB"

    if size_bytes < 1024 ** 5:
        return f"{size_bytes / (1024 ** 4):.2f} TB"

    return f"{size_bytes / (1024 ** 5):.2f} PB"


# =====================================================
# PAK SUCHEN
# =====================================================

def find_pak(pak_filename):

    if not pak_filename:
        return None

    direct_path = os.path.join(
        PAK_DIR,
        pak_filename
    )

    if os.path.isfile(direct_path):
        return direct_path

    if not os.path.isdir(PAK_DIR):
        return None

    try:

        for root, dirs, files in os.walk(PAK_DIR):

            if pak_filename in files:

                return os.path.join(
                    root,
                    pak_filename
                )

    except Exception as e:

        print(
            "[PAK SEARCH ERROR]",
            e
        )

    return None


# =====================================================
# FILE COUNT MIT UNREALPAK
# =====================================================

def get_file_count(pak_path):

    if not os.path.isfile(
        UNREALPAK_EXE
    ):

        print(
            "[PAK ERROR] UnrealPak.exe nicht gefunden:"
        )

        print(
            UNREALPAK_EXE
        )

        return None

    try:

        print(
            "[PAK] Scanne PAK mit UnrealPak..."
        )

        result = subprocess.run(

            [
                UNREALPAK_EXE,
                pak_path,
                "-List"
            ],

            capture_output=True,

            text=True,

            encoding="utf-8",

            errors="ignore",

            timeout=300
        )

        output = (
            result.stdout
            + "\n"
            + result.stderr
        )

        if result.returncode != 0:

            print(
                "[UNREALPAK ERROR]"
            )

            print(
                output[-2000:]
            )

            return None


        patterns = [

            r"files\s+listed\s*[:=]\s*(\d+)",

            r"files\s+found\s*[:=]\s*(\d+)",

            r"files\s+in\s+pak\s*[:=]\s*(\d+)",

            r"entries\s*[:=]\s*(\d+)"

        ]


        for pattern in patterns:

            match = re.search(
                pattern,
                output,
                re.IGNORECASE
            )

            if match:

                count = int(
                    match.group(1)
                )

                if count > 0:
                    return count


        # =================================================
        # FALLBACK
        # =================================================

        count = 0

        for line in output.splitlines():

            line = line.strip()

            if not line:
                continue

            lower = line.lower()

            if lower.startswith("log"):
                continue

            if "unrealpak" in lower:
                continue

            if "files listed" in lower:
                continue

            if "total" in lower:
                continue

            if line.startswith(
                "----------"
            ):
                continue

            if "/" in line or "\\" in line:
                count += 1


        if count > 0:
            return count

        return None


    except subprocess.TimeoutExpired:

        print(
            "[PAK ERROR] UnrealPak Scan Timeout"
        )

        return None


    except Exception as e:

        print(
            "[PAK SCAN ERROR]",
            e
        )

        return None


# =====================================================
# ECHTE PAK INFORMATIONEN
# =====================================================

def get_pak_info(pak_filename):

    print()
    print(
        "[SCAN]",
        pak_filename
    )

    pak_path = find_pak(
        pak_filename
    )

    if not pak_path:

        print(
            "[PAK] Nicht gefunden:",
            pak_filename
        )

        return {
            "count": "Nicht gefunden",
            "size": "Nicht gefunden"
        }


    print(
        "[PAK] Gefunden:",
        pak_path
    )


    # =================================================
    # ECHTE DATEIGRÖSSE
    # =================================================

    try:

        size_bytes = os.path.getsize(
            pak_path
        )

        size = format_size(
            size_bytes
        )

    except Exception as e:

        print(
            "[SIZE ERROR]",
            e
        )

        size = "Fehler"


    # =================================================
    # ECHTER FILE COUNT
    # =================================================

    count = get_file_count(
        pak_path
    )


    if count is None:

        count_text = "Nicht ermittelbar"

    else:

        count_text = f"{count:,}"


    print()
    print(
        "========== PAK INFO =========="
    )

    print(
        "File Count:",
        count_text
    )

    print(
        "File Size:",
        size
    )

    print(
        "=============================="
    )


    return {
        "count": count_text,
        "size": size
    }


# =====================================================
# BERLIN ZEIT
# =====================================================

def berlin_time():

    try:

        return datetime.now(
            ZoneInfo(
                "Europe/Berlin"
            )
        ).strftime(
            "%H:%M Uhr"
        )

    except Exception:

        return datetime.now().strftime(
            "%H:%M Uhr"
        )


# =====================================================
# PREVIEW BILD
# =====================================================

def create_preview():

    img = Image.new(
        "RGB",
        (900, 500),
        (25, 25, 45)
    )

    draw = ImageDraw.Draw(
        img
    )

    draw.text(
        (40, 40),
        "MIDNIGHT SUN",
        fill="white"
    )

    draw.text(
        (40, 90),
        "New Pak decrypted",
        fill="cyan"
    )

    draw.rectangle(
        (500, 0, 900, 500),
        fill=(40, 200, 200)
    )

    draw.ellipse(
        (680, 100, 750, 170),
        fill="white"
    )

    draw.line(
        (715, 170, 715, 320),
        fill="white",
        width=18
    )

    data = io.BytesIO()

    img.save(
        data,
        "PNG"
    )

    data.seek(0)

    return data


# =====================================================
# DISCORD SENDEN
# =====================================================

def send_discord(item, is_test=False):

    pak = item.get(
        "pakFilename",
        "UNKNOWN"
    )


    # =================================================
    # AES KEY
    # =================================================

    key = format_aes_key(
        item.get(
            "key",
            "UNKNOWN"
        )
    )


    guid = item.get(
        "pakGuid",
        "UNKNOWN"
    )


    keychain = item.get(
        "keychain",
        key
    )


    # =================================================
    # TEST ODER ECHTER SCAN
    # =================================================

    if is_test:

        info = {
            "count": "TEST",
            "size": "TEST"
        }

        title = "AES Bot • Test-Nachricht"

    else:

        info = get_pak_info(
            pak
        )

        title = "New Pak was decrypted!"


    # =================================================
    # DISCORD EMBED
    # =================================================

    embed = {

        "title": title,


        "description": (
            f"**{pak}**\n"
            f"`{key}`\n\n"

            f"**Keychain**\n"
            f"`{keychain}`\n\n"

            f"**GUID**\n"
            f"`{guid}`"
        ),


        # =================================================
        # WICHTIG:
        # ECHTE INLINE FIELDS
        # =================================================

        "fields": [

            {
                "name": "File Count",
                "value": f"`{info['count']}`",
                "inline": True
            },

            {
                "name": "File Size",
                "value": f"`{info['size']}`",
                "inline": True
            }

        ],


        "color": 5793266,


        "image": {
            "url": "attachment://pak.png"
        },


        "footer": {
            "text": (
                "made by @kiranfn • "
                f"heute um {berlin_time()}"
            )
        }

    }


    # =====================================================
    # PAYLOAD
    # =====================================================

    payload = {

        "content":
            f"<@&{ROLE_ID}>",

        "embeds": [
            embed
        ],

        "allowed_mentions": {
            "roles": [
                ROLE_ID
            ]
        }

    }


    image = create_preview()


    # =====================================================
    # DISCORD SENDEN
    # =====================================================

    try:

        response = requests.post(

            WEBHOOK_URL,

            data={
                "payload_json":
                    json.dumps(
                        payload
                    )
            },

            files={
                "file": (
                    "pak.png",
                    image,
                    "image/png"
                )
            },

            timeout=20

        )


        if response.status_code not in (
            200,
            204
        ):

            print(
                "[DISCORD ERROR]",
                response.status_code
            )

            print(
                response.text
            )

            return False


        print(
            "[DISCORD] gesendet"
        )

        return True


    except Exception as e:

        print(
            "[DISCORD ERROR]",
            e
        )

        return False


# =====================================================
# START
# =====================================================

print(
    "================================"
)

print(
    "       FORTNITE AES BOT"
)

print(
    "================================"
)


# =====================================================
# KONFIGURATION PRÜFEN
# =====================================================

if not os.path.isdir(
    PAK_DIR
):

    print()
    print(
        "[WARNUNG] PAK-Ordner nicht gefunden:"
    )

    print(
        PAK_DIR
    )


if not os.path.isfile(
    UNREALPAK_EXE
):

    print()
    print(
        "[WARNUNG] UnrealPak.exe nicht gefunden:"
    )

    print(
        UNREALPAK_EXE
    )


# =====================================================
# TEST-NACHRICHT
# =====================================================

test_item = {

    "pakFilename":
        "TEST-pak-WindowsClient.pak",

    "key":
        "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",

    "keychain":
        "TEST_KEYCHAIN",

    "pakGuid":
        "TEST_GUID"

}


print()
print(
    "[TEST] Sende Test-Nachricht..."
)


send_discord(
    test_item,
    is_test=True
)


print(
    "[TEST] Fertig."
)


# =====================================================
# SPAM-SCHUTZ
# =====================================================

seen = set()


# Bereits vorhandene AES beim Start merken.
# Diese werden NICHT erneut gesendet.

initial_aes = get_aes()


for item in initial_aes:

    seen.add(
        get_uid(item)
    )


print(
    f"[AES] {len(seen)} vorhandene Keys gespeichert"
)


# =====================================================
# LIVE
# =====================================================

print(
    "[LIVE] Bot gestartet"
)

print(
    f"[LIVE] Prüfung alle {CHECK_TIME} Sekunden"
)


# =====================================================
# LOOP
# =====================================================

while True:

    try:

        aes = get_aes()


        for item in aes:

            uid = get_uid(
                item
            )


            # Bereits gesendet?
            if uid in seen:
                continue


            # Sofort merken
            seen.add(
                uid
            )


            pak_name = item.get(
                "pakFilename",
                "UNKNOWN"
            )


            print()
            print(
                "================================"
            )

            print(
                "[NEW AES]",
                pak_name
            )

            print(
                "[NEW AES] Neue Entschlüsselung erkannt"
            )

            print(
                "================================"
            )


            # Einmal scannen
            # Einmal Discord senden

            send_discord(
                item,
                is_test=False
            )


        print(
            f"[LIVE] Nächster Check in {CHECK_TIME} Sekunden..."
        )


        time.sleep(
            CHECK_TIME
        )


    except KeyboardInterrupt:

        print()
        print(
            "[BOT] beendet."
        )

        break


    except Exception as e:

        print(
            "[LOOP ERROR]",
            e
        )

        time.sleep(
            CHECK_TIME
        )
