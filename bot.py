import requests
import time
import hashlib
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo


# =====================================================
# EINSTELLUNGEN
# =====================================================

# NEUEN DISCORD WEBHOOK EINTRAGEN
WEBHOOK_URL = "https://discord.com/api/webhooks/1541600578340130897/f6xXG74cD3qIKlM28hv56FdxH0N__qaHlugIKC_oD5cd5XWzHKbANJhDEzJW9M0DJ1vl"

AES_URL = "https://fortnite-api.com/v2/aes"

# Rolle für den Ping
ROLE_ID = "1523617106414014504"

# API alle 30 Sekunden prüfen
CHECK_TIME = 30

# Permanente Spam-Schutz-Datenbank
SENT_FILE = "sent_aes.json"


# =====================================================
# SESSION
# =====================================================

session = requests.Session()

session.headers.update({
    "User-Agent": "FortniteAESMonitor/1.0",
    "Accept": "application/json",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
})


# =====================================================
# AES KEY NORMALISIEREN
# =====================================================

def normalize_key(key):

    if key is None:
        return ""

    key = str(key).strip().lower()

    if key.startswith("0x"):
        key = key[2:]

    return key


# =====================================================
# EINDEUTIGE AES-ID
# =====================================================
#
# NUR DER AES-KEY zählt.
#
# Gleicher AES-Key = gleiche ID
# PAK und GUID sind für den Spam-Schutz egal.
# =====================================================

def get_uid(item):

    if not isinstance(item, dict):
        return ""

    key = normalize_key(
        item.get("key", "")
    )

    if not key:
        return ""

    return hashlib.sha256(
        key.encode("utf-8")
    ).hexdigest()


# =====================================================
# SPAM-DATENBANK LADEN
# =====================================================

def load_sent_aes():

    if not os.path.exists(SENT_FILE):

        print(
            "[SPAM] Keine Datenbank vorhanden."
        )

        return set()

    try:

        with open(
            SENT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, list):

            print(
                "[SPAM ERROR] Datenbank ist ungültig."
            )

            return set()

        seen = set()

        for value in data:

            if value:
                seen.add(str(value))

        print(
            f"[SPAM] {len(seen)} AES aus Datenbank geladen."
        )

        return seen

    except Exception as e:

        print(
            "[SPAM ERROR] Datenbank konnte nicht geladen werden:",
            e
        )

        return set()


# =====================================================
# SPAM-DATENBANK SPEICHERN
# =====================================================

def save_sent_aes(seen):

    temp_file = SENT_FILE + ".tmp"

    try:

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                sorted(seen),
                file,
                indent=2
            )

            file.flush()

            os.fsync(
                file.fileno()
            )

        os.replace(
            temp_file,
            SENT_FILE
        )

        return True

    except Exception as e:

        print(
            "[SPAM ERROR] Datenbank konnte nicht gespeichert werden:",
            e
        )

        try:

            if os.path.exists(temp_file):
                os.remove(temp_file)

        except Exception:
            pass

        return False


# =====================================================
# AES VON DER API HOLEN
# =====================================================

def get_aes():

    try:

        response = session.get(
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

        dynamic_keys = (
            data
            .get("data", {})
            .get("dynamicKeys", [])
        )

        if not isinstance(
            dynamic_keys,
            list
        ):

            print(
                "[AES ERROR] dynamicKeys ist keine Liste."
            )

            return []

        return dynamic_keys

    except Exception as e:

        print(
            "[AES ERROR]",
            e
        )

        return []


# =====================================================
# AES KEY FORMATIEREN
# =====================================================

def format_aes_key(key):

    key = normalize_key(key)

    if not key:
        return "UNKNOWN"

    return "0x" + key


# =====================================================
# BERLIN ZEIT
# =====================================================

def berlin_time():

    try:

        return datetime.now(
            ZoneInfo("Europe/Berlin")
        ).strftime(
            "%H:%M Uhr"
        )

    except Exception:

        return datetime.now().strftime(
            "%H:%M Uhr"
        )


# =====================================================
# KEYCHAIN
# =====================================================

def create_keychain(item):

    guid = str(
        item.get(
            "pakGuid",
            ""
        )
    ).strip()

    key = normalize_key(
        item.get(
            "key",
            ""
        )
    )

    if not guid or not key:
        return "UNKNOWN"

    return f"{guid}:{key}"


# =====================================================
# DISCORD SENDEN
# =====================================================

def send_discord(item):

    pak = str(
        item.get(
            "pakFilename",
            "UNKNOWN"
        )
    ).strip()

    key = format_aes_key(
        item.get(
            "key",
            ""
        )
    )

    guid = str(
        item.get(
            "pakGuid",
            "UNKNOWN"
        )
    ).strip()

    keychain = create_keychain(item)


    # =================================================
    # EMBED
    # =================================================

    embed = {

        "title": "New Pak was decrypted!",

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
    #
    # JEDER Send pingt die Rolle.
    # Auch die Test-Nachricht.
    # =================================================

    payload = {

        "content": f"<@&{ROLE_ID}>",

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

        response = session.post(
            WEBHOOK_URL,
            json=payload,
            timeout=20
        )

        if response.status_code in (
            200,
            204
        ):

            print(
                "[DISCORD] Nachricht gesendet."
            )

            return True

        print(
            "[DISCORD ERROR]",
            response.status_code
        )

        print(
            response.text
        )

        return False

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
    "========================================"
)

print(
    "       FORTNITE AES BOT"
)

print(
    "========================================"
)

print()


# =====================================================
# WEBHOOK PRÜFEN
# =====================================================

if (
    not WEBHOOK_URL
    or
    WEBHOOK_URL == "DEIN_NEUER_DISCORD_WEBHOOK"
):

    print(
        "[FEHLER] Bitte neuen Discord Webhook eintragen."
    )

    raise SystemExit


# =====================================================
# SPAM-DATENBANK LADEN
# =====================================================

seen = load_sent_aes()


# =====================================================
# START-TEST
# =====================================================
#
# Test-Nachricht pingt jetzt ebenfalls die Rolle.
# =====================================================

test_item = {

    "pakFilename":
        "TEST-pak-WindowsClient.pak",

    "key":
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",

    "pakGuid":
        "TEST_GUID"
}


print()

print(
    "[TEST] Sende Start-Testnachricht MIT Rollen-Ping..."
)

test_success = send_discord(
    test_item
)

if test_success:

    print(
        "[TEST] Erfolgreich gesendet."
    )

else:

    print(
        "[TEST] Senden fehlgeschlagen."
    )


# =====================================================
# START-AES
# =====================================================
#
# Bereits vorhandene AES werden als bekannt markiert.
# Sie werden beim Start NICHT gesendet.
# =====================================================

print()

print(
    "[START] Lade aktuelle AES..."
)

initial_aes = get_aes()

initial_count = 0

for item in initial_aes:

    if not isinstance(
        item,
        dict
    ):
        continue

    uid = get_uid(item)

    if not uid:
        continue

    if uid not in seen:

        seen.add(uid)

        initial_count += 1


if initial_count > 0:

    if save_sent_aes(seen):

        print(
            f"[START] {initial_count} vorhandene AES gespeichert."
        )

    else:

        print(
            "[START WARNUNG] Datenbank konnte nicht gespeichert werden."
        )

else:

    print(
        "[START] Keine neuen vorhandenen AES."
    )


# =====================================================
# LIVE
# =====================================================

print()

print(
    "[LIVE] Bot gestartet."
)

print(
    f"[LIVE] Prüfung alle {CHECK_TIME} Sekunden."
)

print(
    "[LIVE] SPAM-SCHUTZ AKTIV."
)

print(
    "[LIVE] Gleicher AES-Key wird nur EINMAL verarbeitet."
)

print(
    "[LIVE] 2 verschiedene AES = 2 separate Nachrichten."
)

print(
    f"[LIVE] Rollen-Ping aktiv: {ROLE_ID}"
)

print()


# =====================================================
# LIVE LOOP
# =====================================================

while True:

    try:

        # =============================================
        # API ABFRAGEN
        # =============================================

        aes = get_aes()

        if not aes:

            print(
                "[LIVE] Keine AES erhalten."
            )

            time.sleep(
                CHECK_TIME
            )

            continue


        # =============================================
        # DUPLIKATE DIESES CHECKS
        # =============================================

        processed_this_check = set()

        duplicate_count = 0

        new_count = 0


        # =============================================
        # ALLE API-EINTRÄGE
        # =============================================

        for item in aes:

            if not isinstance(
                item,
                dict
            ):
                continue


            # =========================================
            # AES-ID
            # =========================================

            uid = get_uid(item)

            if not uid:
                continue


            # =========================================
            # DUPLIKAT IM SELBEN API-CHECK
            # =========================================

            if uid in processed_this_check:

                duplicate_count += 1

                continue

            processed_this_check.add(uid)


            # =========================================
            # BEREITS GESENDET
            # =========================================

            if uid in seen:

                continue


            # =========================================
            # NEUE AES
            # =========================================

            new_count += 1

            pak_name = str(
                item.get(
                    "pakFilename",
                    "UNKNOWN"
                )
            ).strip()

            aes_key = format_aes_key(
                item.get(
                    "key",
                    ""
                )
            )

            guid = str(
                item.get(
                    "pakGuid",
                    "UNKNOWN"
                )
            ).strip()


            print()

            print(
                "========================================"
            )

            print(
                "[NEW AES]"
            )

            print(
                "[PAK]",
                pak_name
            )

            print(
                "[KEY]",
                aes_key
            )

            print(
                "[GUID]",
                guid
            )


            # =========================================
            # AES VOR DEM SENDEN SPEICHERN
            #
            # Das verhindert erneuten Versand.
            # =========================================

            print(
                "[SPAM-SCHUTZ] Markiere AES..."
            )

            seen.add(uid)

            saved = save_sent_aes(seen)


            # =========================================
            # DATENBANK FEHLER
            # =========================================

            if not saved:

                seen.discard(uid)

                print(
                    "[SPAM-SCHUTZ] Datenbankfehler."
                )

                print(
                    "[SPAM-SCHUTZ] AES wird NICHT gesendet."
                )

                continue


            # =========================================
            # DISCORD SENDEN
            # =========================================

            print(
                "[DISCORD] Sende neue AES MIT Rollen-Ping..."
            )

            success = send_discord(item)


            # =========================================
            # ERFOLG
            # =========================================

            if success:

                print(
                    "[NEW AES] Erfolgreich gesendet."
                )

                print(
                    "[SPAM-SCHUTZ] AES dauerhaft gespeichert."
                )

            else:

                print(
                    "[DISCORD ERROR] Nachricht konnte nicht gesendet werden."
                )

                print(
                    "[SPAM-SCHUTZ] AES bleibt gespeichert."
                )

                print(
                    "[SPAM-SCHUTZ] Kein erneuter Versand."
                )


        # =============================================
        # ZUSAMMENFASSUNG
        # =============================================

        print()

        if new_count > 0:

            print(
                f"[LIVE] {new_count} neue AES verarbeitet."
            )

        else:

            print(
                "[LIVE] Keine neuen AES."
            )

        if duplicate_count > 0:

            print(
                f"[SPAM-SCHUTZ] {duplicate_count} doppelte AES übersprungen."
            )


        # =============================================
        # WARTEN
        # =============================================

        print()

        print(
            f"[LIVE] Nächster Check in {CHECK_TIME} Sekunden..."
        )

        time.sleep(
            CHECK_TIME
        )


    # =================================================
    # STRG+C
    # =================================================

    except KeyboardInterrupt:

        print()

        print(
            "[BOT] Bot beendet."
        )

        break


    # =================================================
    # FEHLER
    # =================================================

    except Exception as e:

        print()

        print(
            "[LOOP ERROR]",
            repr(e)
        )

        print(
            "[LIVE] Bot läuft weiter..."
        )

        time.sleep(
            CHECK_TIME
        )
