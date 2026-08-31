import requests
import time
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo


# =====================================================
# EINSTELLUNGEN
# =====================================================

# HIER DEINEN NEUEN DISCORD WEBHOOK EINTRAGEN
WEBHOOK_URL = "https://discord.com/api/webhooks/1541600578340130897/f6xXG74cD3qIKlM28hv56FdxH0N__qaHlugIKC_oD5cd5XWzHKbANJhDEzJW9M0DJ1vl"

AES_URL = "https://fortnite-api.com/v2/aes"

ROLE_ID = "1523617106414014504"

CHECK_TIME = 30


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
# AES HOLEN
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

        if not isinstance(dynamic_keys, list):

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

    if key is None:

        return "UNKNOWN"

    key = str(key).strip()

    if not key:

        return "UNKNOWN"

    if not key.lower().startswith("0x"):

        key = "0x" + key

    return key


# =====================================================
# EINDEUTIGE AES-ID
# =====================================================

def get_uid(item):

    if not isinstance(item, dict):

        return ""

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

    # -------------------------------------------------
    # Kombination aus Pak + Key + GUID
    # -------------------------------------------------

    raw = f"{pak}|{key}|{guid}"

    if raw == "||":

        return ""

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


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

    key = str(
        item.get(
            "key",
            ""
        )
    ).strip()

    if not guid or not key:

        return "UNKNOWN"

    if key.lower().startswith("0x"):

        key = key[2:]

    return f"{guid}:{key}"


# =====================================================
# DISCORD SENDEN
# =====================================================

def send_discord(item, is_test=False):

    pak = str(
        item.get(
            "pakFilename",
            "UNKNOWN"
        )
    ).strip()

    raw_key = str(
        item.get(
            "key",
            "UNKNOWN"
        )
    ).strip()

    key = format_aes_key(
        raw_key
    )

    guid = str(
        item.get(
            "pakGuid",
            "UNKNOWN"
        )
    ).strip()

    keychain = create_keychain(
        item
    )

    # -------------------------------------------------
    # TITEL
    # -------------------------------------------------

    if is_test:

        title = "AES Bot • Test-Nachricht"

    else:

        title = "New Pak was decrypted!"

    # -------------------------------------------------
    # EMBED
    # -------------------------------------------------

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

    # -------------------------------------------------
    # PAYLOAD
    # -------------------------------------------------

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

    # -------------------------------------------------
    # SENDEN
    # -------------------------------------------------

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
    "================================"
)

print(
    "       FORTNITE AES BOT"
)

print(
    "================================"
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
        "[FEHLER] Bitte WEBHOOK_URL eintragen."
    )

    raise SystemExit


# =====================================================
# EINMALIGE TEST-NACHRICHT
# =====================================================

test_item = {

    "pakFilename":
        "TEST-pak-WindowsClient.pak",

    "key":
        "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",

    "pakGuid":
        "TEST_GUID"
}


print(
    "[TEST] Sende einmalige Test-Nachricht..."
)

test_success = send_discord(
    test_item,
    is_test=True
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
# SPAM-SCHUTZ
# =====================================================
#
# Hier werden ALLE bereits bekannten AES gespeichert.
#
# Eine UID kann innerhalb dieses laufenden
# Bot-Prozesses nur einmal verarbeitet werden.
# =====================================================

seen = set()


# =====================================================
# START-AES SPEICHERN
# =====================================================
#
# Alles, was beim Start bereits vorhanden ist,
# wird NICHT als neue AES gepostet.
# =====================================================

print()

print(
    "[START] Lade vorhandene AES..."
)

initial_aes = get_aes()

initial_count = 0

for item in initial_aes:

    uid = get_uid(item)

    if not uid:

        continue

    if uid not in seen:

        seen.add(uid)

        initial_count += 1


print(
    f"[START] {initial_count} vorhandene AES gespeichert."
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
    "[LIVE] Jede AES wird maximal EINMAL gepostet."
)

print(
    "[LIVE] Bereits vorhandene AES werden ignoriert."
)

print()


# =====================================================
# LIVE LOOP
# =====================================================

while True:

    try:

        # -------------------------------------------------
        # AES LADEN
        # -------------------------------------------------

        aes = get_aes()

        if not aes:

            print(
                "[LIVE] Keine AES erhalten."
            )

            time.sleep(
                CHECK_TIME
            )

            continue


        # -------------------------------------------------
        # DUPLIKATE INNERHALB DER API ANTWORT VERHINDERN
        # -------------------------------------------------

        processed_this_check = set()


        # -------------------------------------------------
        # ALLE AES
        # -------------------------------------------------

        for item in aes:

            if not isinstance(
                item,
                dict
            ):

                continue


            # =============================================
            # EINDEUTIGE ID
            # =============================================

            uid = get_uid(item)

            if not uid:

                continue


            # =============================================
            # SCHON IN DIESEM CHECK?
            # =============================================

            if uid in processed_this_check:

                continue

            processed_this_check.add(uid)


            # =============================================
            # SCHON GESENDET?
            # =============================================

            if uid in seen:

                continue


            # =============================================
            # SOFORT ALS BEKANNT MARKIEREN
            # =============================================
            #
            # WICHTIG:
            #
            # Noch VOR dem Discord-Versand.
            #
            # Dadurch kann dieselbe AES nicht durch
            # mehrere API-Einträge oder Checks doppelt
            # verarbeitet werden.
            # =============================================

            seen.add(uid)


            # =============================================
            # NEUE AES
            # =============================================

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
                "[NEW AES] Neue AES erkannt."
            )

            print(
                "[NEW AES] Sende EINMAL..."
            )

            print(
                "================================"
            )


            # =============================================
            # DISCORD
            # =============================================

            success = send_discord(
                item,
                is_test=False
            )


            # =============================================
            # ERGEBNIS
            # =============================================

            if success:

                print()

                print(
                    "[NEW AES] Nachricht erfolgreich gesendet."
                )

                print(
                    "[NEW AES] Diese AES wird NICHT erneut gesendet."
                )

            else:

                print()

                print(
                    "[WARNUNG] Discord-Versand fehlgeschlagen."
                )

                print(
                    "[WARNUNG] AES bleibt trotzdem gespeichert."
                )

                print(
                    "[WARNUNG] Keine erneute Nachricht."
                )


        # -------------------------------------------------
        # NÄCHSTER CHECK
        # -------------------------------------------------

        print()

        print(
            f"[LIVE] Nächster Check in {CHECK_TIME} Sekunden..."
        )

        time.sleep(
            CHECK_TIME
        )


    # =====================================================
    # STRG+C
    # =====================================================

    except KeyboardInterrupt:

        print()

        print(
            "[BOT] beendet."
        )

        break


    # =====================================================
    # FEHLER
    # =====================================================

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
