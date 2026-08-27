import requests
import json
import time

from datetime import datetime
from zoneinfo import ZoneInfo


# =====================================================
# EINSTELLUNGEN
# =====================================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1541600578340130897/f6xXG74cD3qIKlM28hv56FdxH0N__qaHlugIKC_oD5cd5XWzHKbANJhDEzJW9M0DJ1vl"

AES_URL = "https://fortnite-api.com/v2/aes"

ROLE_ID = "1523617106414014504"

CHECK_TIME = 30


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
# DISCORD SENDEN
# =====================================================

def send_discord(item, is_test=False):

    pak = item.get(
        "pakFilename",
        "UNKNOWN"
    )

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
    # TITEL
    # =================================================

    if is_test:

        title = "AES Bot • Test-Nachricht"

    else:

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

        "color": 5793266,

        "footer": {
            "text": (
                "made by @kiranfn • "
                f"heute um {berlin_time()}"
            )
        }

    }


    # =================================================
    # PAYLOAD
    # =================================================

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


    # =================================================
    # DISCORD SENDEN
    # =================================================

    try:

        response = requests.post(

            WEBHOOK_URL,

            json=payload,

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

if WEBHOOK_URL == "DEIN_NEUER_DISCORD_WEBHOOK":

    print()
    print(
        "[FEHLER] Bitte WEBHOOK_URL eintragen."
    )

    input(
        "ENTER zum Beenden..."
    )

    raise SystemExit


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


test_success = send_discord(
    test_item,
    is_test=True
)


if test_success:

    print(
        "[TEST] Fertig."
    )

else:

    print(
        "[TEST] Nachricht konnte nicht gesendet werden."
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


            # Bereits bekannt?
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


            # Discord senden

            success = send_discord(
                item,
                is_test=False
            )


            if not success:

                print(
                    "[WARNUNG] Discord-Nachricht fehlgeschlagen."
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
