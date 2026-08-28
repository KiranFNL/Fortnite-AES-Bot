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
# AES KEY MIT 0x FORMATIEREN
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

    # Falls GUID oder KEY fehlt
    if not guid or not key:

        return "UNKNOWN"

    # 0x beim Key entfernen,
    # damit der Keychain sauber bleibt
    if key.lower().startswith("0x"):

        key = key[2:]

    # KEYCHAIN FORMAT:
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

    raise SystemExit


# =====================================================
# TEST-NACHRICHT
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


# =====================================================
# BEREITS VORHANDENE AES SPEICHERN
# =====================================================
#
# Alles was beim Start bereits vorhanden ist,
# wird NICHT als neue AES Nachricht gesendet.
#
# Nur AES Keys, die später neu erscheinen,
# werden an Discord gesendet.
# =====================================================

initial_aes = get_aes()


for item in initial_aes:

    uid = get_uid(
        item
    )

    seen.add(
        uid
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

print(

    "[LIVE] Nur neue AES werden gesendet."

)


# =====================================================
# LOOP
# =====================================================

while True:

    try:

        aes = get_aes()


        for item in aes:


            # -----------------------------------------
            # EINDEUTIGE ID
            # -----------------------------------------

            uid = get_uid(
                item
            )


            # -----------------------------------------
            # BEREITS BEKANNT?
            # -----------------------------------------

            if uid in seen:

                continue


            # -----------------------------------------
            # NEUER AES
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

                "[NEW AES] Neue Entschlüsselung erkannt"

            )

            print(

                "[NEW AES] Sende Discord-Nachricht..."

            )

            print(

                "================================"

            )


            # -----------------------------------------
            # DEBUG:
            # Zeigt die echten API-Daten an
            # -----------------------------------------

            print()

            print(

                "[DEBUG] AES ITEM:"

            )

            print(

                item

            )

            print()


            # -----------------------------------------
            # DISCORD SENDEN
            # -----------------------------------------

            success = send_discord(

                item,

                is_test=False

            )


            # -----------------------------------------
            # NUR BEI ERFOLGREICHEM SENDEN SPEICHERN
            # -----------------------------------------

            if success:

                seen.add(
                    uid
                )

                print(

                    "[NEW AES] Nachricht genau einmal gesendet."

                )

            else:

                print(

                    "[WARNUNG] Discord-Nachricht fehlgeschlagen."

                )

                print(

                    "[WARNUNG] Wird beim nächsten Check erneut versucht."

                )


        # ---------------------------------------------
        # NÄCHSTER CHECK
        # ---------------------------------------------

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

        print(

            "[LOOP ERROR]",

            e

        )

        time.sleep(

            CHECK_TIME

        )
