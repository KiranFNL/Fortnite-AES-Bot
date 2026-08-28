import requests
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
# EINDEUTIGE ID FÜR SPAM-SCHUTZ
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

    return f"{pak}|{key}|{guid}"


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
# KEYCHAIN ERSTELLEN
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

    # Falls API-Key bereits 0x enthält,
    # 0x für den Keychain entfernen

    if key.lower().startswith("0x"):

        key = key[2:]

    # Echter Keychain:
    # GUID:KEY

    return f"{guid}:{key}"


# =====================================================
# DISCORD SENDEN
# =====================================================

def send_discord(item, is_test=False):

    # -------------------------------------------------
    # PAK NAME
    # -------------------------------------------------

    pak = str(
        item.get(
            "pakFilename",
            "UNKNOWN"
        )
    ).strip()


    # -------------------------------------------------
    # AES KEY
    # -------------------------------------------------

    raw_key = str(
        item.get(
            "key",
            "UNKNOWN"
        )
    ).strip()

    key = format_aes_key(
        raw_key
    )


    # -------------------------------------------------
    # GUID
    # -------------------------------------------------

    guid = str(
        item.get(
            "pakGuid",
            "UNKNOWN"
        )
    ).strip()


    # -------------------------------------------------
    # KEYCHAIN
    # -------------------------------------------------

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
    # DISCORD PAYLOAD
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

            "[DISCORD] Nachricht gesendet."

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
# WEBHOOK PRÜFEN
# =====================================================

if WEBHOOK_URL == "DEIN_NEUER_DISCORD_WEBHOOK":

    print()

    print(

        "[FEHLER] Bitte WEBHOOK_URL eintragen."

    )

    raise SystemExit


# =====================================================
# EINMALIGE TEST-NACHRICHT
# =====================================================
#
# Dieser Block befindet sich außerhalb der while-Schleife.
#
# Deshalb wird die Test-Nachricht nur EINMAL gesendet:
# direkt beim Start des Bots.
# =====================================================

test_item = {

    "pakFilename":

        "TEST-pak-WindowsClient.pak",

    "key":

        "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",

    "pakGuid":

        "TEST_GUID"

}


print()

print(

    "[TEST] Sende einmalige Test-Nachricht..."

)


test_success = send_discord(

    test_item,

    is_test=True

)


if test_success:

    print(

        "[TEST] Test-Nachricht erfolgreich gesendet."

    )

else:

    print(

        "[TEST] Test-Nachricht konnte nicht gesendet werden."

    )


# =====================================================
# SPAM-SCHUTZ
# =====================================================

seen = set()


# =====================================================
# BEREITS VORHANDENE AES SPEICHERN
# =====================================================
#
# Alles, was beim Start bereits in der API vorhanden ist,
# wird als bekannt gespeichert.
#
# Dadurch werden alte AES NICHT als "neue AES" gemeldet.
# =====================================================

initial_aes = get_aes()


for item in initial_aes:

    uid = get_uid(
        item
    )

    seen.add(
        uid
    )


print()

print(

    f"[AES] {len(seen)} vorhandene AES gespeichert."

)


# =====================================================
# LIVE START
# =====================================================

print()

print(

    "[LIVE] Bot gestartet."

)

print(

    f"[LIVE] Prüfung alle {CHECK_TIME} Sekunden."

)

print(

    "[LIVE] Nur neue AES werden gemeldet."

)

print(

    "[LIVE] Jede AES wird maximal einmal gemeldet."

)

print(

    "[LIVE] Test-Nachricht wird nicht erneut gesendet."

)

print()


# =====================================================
# LIVE LOOP
# =====================================================

while True:

    try:

        # ---------------------------------------------
        # AES AKTUELL HOLEN
        # ---------------------------------------------

        aes = get_aes()


        # ---------------------------------------------
        # ALLE AES DURCHGEHEN
        # ---------------------------------------------

        for item in aes:


            # -----------------------------------------
            # EINDEUTIGE ID
            # -----------------------------------------

            uid = get_uid(
                item
            )


            # -----------------------------------------
            # SCHON BEKANNT?
            # -----------------------------------------

            if uid in seen:

                continue


            # -----------------------------------------
            # SOFORT ALS BEKANNT MARKIEREN
            # -----------------------------------------
            #
            # WICHTIG:
            # Die AES wird VOR dem Discord-Versand
            # gespeichert.
            #
            # Dadurch kann dieselbe AES nicht zweimal
            # gemeldet werden.
            # -----------------------------------------

            seen.add(
                uid
            )


            # -----------------------------------------
            # NEUE AES
            # -----------------------------------------

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

                "[NEW AES] Sende Discord-Nachricht..."

            )

            print(

                "================================"

            )


            # -----------------------------------------
            # DISCORD SENDEN
            # -----------------------------------------

            success = send_discord(

                item,

                is_test=False

            )


            # -----------------------------------------
            # ERGEBNIS
            # -----------------------------------------

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

                    "[WARNUNG] Discord-Nachricht fehlgeschlagen."

                )

                print(

                    "[WARNUNG] AES bleibt trotzdem als verarbeitet markiert."

                )

                print(

                    "[WARNUNG] Dadurch wird keine Doppel-Nachricht erzeugt."

                )


        # ---------------------------------------------
        # NÄCHSTER CHECK
        # ---------------------------------------------

        print()

        print(

            f"[LIVE] Nächster Check in {CHECK_TIME} Sekunden..."

        )


        time.sleep(

            CHECK_TIME

        )


    # =================================================
    # BOT MANUELL BEENDEN
    # =================================================

    except KeyboardInterrupt:

        print()

        print(

            "[BOT] beendet."

        )

        break


    # =================================================
    # FEHLER
    # =================================================

    except Exception as e:

        print()

        print(

            "[LOOP ERROR]",

            e

        )

        time.sleep(

            CHECK_TIME

        )
