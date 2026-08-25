import requests
import json
import time
import os
from datetime import datetime


# ============================================================
# EINSTELLUNGEN
# ============================================================

# NEUEN DISCORD WEBHOOK HIER EINTRAGEN
WEBHOOK_URL = "https://discord.com/api/webhooks/1541600578340130897/f6xXG74cD3qIKlM28hv56FdxH0N__qaHlugIKC_oD5cd5XWzHKbANJhDEzJW9M0DJ1vl"

# Fortnite AES API
AES_URL = "https://fortnite-api.com/v2/aes"

# Discord Rollen-ID
ROLE_ID = "1523617106414014504"

# Wichtig:
# /app ist auf deinem Hosting schreibgeschützt.
# /tmp ist beschreibbar.
SEEN_FILE = "/tmp/seen.json"

# Alle 30 Sekunden prüfen
CHECK_TIME = 30


# ============================================================
# TEST-BILD
# ============================================================
#
# Hier kannst du eine öffentlich erreichbare Bild-URL
# für die Testnachricht eintragen.
#
# Beispiel:
#
# TEST_IMAGE_URL = "https://example.com/test.png"
#
# Wenn du keine URL hast, einfach leer lassen.
#

TEST_IMAGE_URL = ""


# ============================================================
# AES ABRUFEN
# ============================================================

def get_aes():

    try:

        response = requests.get(
            AES_URL,
            timeout=15
        )

        if response.status_code != 200:

            print(
                "[AES] HTTP Fehler:",
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

            print(
                "[AES] Keine gültigen Dynamic Keys"
            )

            return []

        return dynamic_keys

    except Exception as e:

        print(
            "[AES] Fehler:",
            e
        )

        return []


# ============================================================
# EINDEUTIGE ID
# ============================================================

def get_uid(item):

    pak = str(
        item.get(
            "pakFilename",
            ""
        )
    )

    guid = str(
        item.get(
            "pakGuid",
            ""
        )
    )

    key = str(
        item.get(
            "key",
            ""
        )
    )

    return (
        pak
        + "|"
        + guid
        + "|"
        + key
    )


# ============================================================
# SEEN LADEN
# ============================================================

def load_seen():

    if not os.path.exists(SEEN_FILE):

        return set()

    try:

        with open(
            SEEN_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):

            return set(data)

    except Exception as e:

        print(
            "[SEEN] Ladefehler:",
            e
        )

    return set()


# ============================================================
# SEEN SPEICHERN
# ============================================================

def save_seen(seen):

    temp_file = SEEN_FILE + ".tmp"

    try:

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                list(seen),
                file,
                indent=2
            )

        os.replace(
            temp_file,
            SEEN_FILE
        )

        return True

    except Exception as e:

        print(
            "[SEEN] Speicherfehler:",
            e
        )

        try:

            if os.path.exists(temp_file):

                os.remove(temp_file)

        except Exception:

            pass

        return False


# ============================================================
# DISCORD SENDEN
# ============================================================

def send_discord(item):

    if not WEBHOOK_URL:

        print(
            "[DISCORD] Kein Webhook eingetragen!"
        )

        return False


    # --------------------------------------------------------
    # DATEN
    # --------------------------------------------------------

    pak_filename = str(
        item.get(
            "pakFilename",
            "UNKNOWN"
        )
    )

    key = str(
        item.get(
            "key",
            "UNKNOWN"
        )
    )

    guid = str(
        item.get(
            "pakGuid",
            "UNKNOWN"
        )
    )

    keychain = str(
        item.get(
            "keychain",
            key
        )
    )

    image_url = str(
        item.get(
            "image",
            ""
        )
    )


    # --------------------------------------------------------
    # UHRZEIT
    # --------------------------------------------------------

    current_time = datetime.now().strftime(
        "%H:%M Uhr"
    )


    # --------------------------------------------------------
    # EMBED
    # --------------------------------------------------------

    embed = {

        "title":
            "New Pak was decrypted!",

        "description":

            f"**{pak_filename}**\n"
            f"{key}\n\n"

            f"**Keychain**\n"
            f"{keychain}\n\n"

            f"**GUID**\n"
            f"{guid}",

        "color":
            5793266,

        "footer": {

            "text":
                f"made by @kiranfn • "
                f"heute um {current_time}"
        }
    }


    # --------------------------------------------------------
    # BILD
    # --------------------------------------------------------

    if image_url:

        embed["image"] = {
            "url": image_url
        }


    # --------------------------------------------------------
    # DISCORD PAYLOAD
    # --------------------------------------------------------
    #
    # Rolle wird hier gepingt:
    #
    # <@&1523617106414014504>
    #
    # allowed_mentions erlaubt genau diesen Rollen-Ping.
    #

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


    # --------------------------------------------------------
    # DISCORD POST
    # --------------------------------------------------------

    try:

        response = requests.post(

            WEBHOOK_URL,

            json=payload,

            timeout=15
        )


        # ----------------------------------------------------
        # ERFOLG
        # ----------------------------------------------------

        if response.status_code == 204:

            print(
                "[DISCORD] Nachricht gesendet"
            )

            return True


        # ----------------------------------------------------
        # RATE LIMIT
        # ----------------------------------------------------

        if response.status_code == 429:

            try:

                retry_after = (
                    response
                    .json()
                    .get(
                        "retry_after",
                        5
                    )
                )

            except Exception:

                retry_after = 5


            print(
                f"[DISCORD] Rate Limit - "
                f"{retry_after} Sekunden"
            )

            time.sleep(
                float(retry_after)
            )

            return False


        # ----------------------------------------------------
        # ANDERER FEHLER
        # ----------------------------------------------------

        print(
            "[DISCORD] Fehler:",
            response.status_code
        )

        print(
            response.text
        )

        return False


    except Exception as e:

        print(
            "[WEBHOOK] Fehler:",
            e
        )

        return False


# ============================================================
# BOT START
# ============================================================

print(
    "======================================"
)

print(
    "       FORTNITE AES BOT"
)

print(
    "======================================"
)

print(
    "[BOT] Gestartet"
)


# ============================================================
# START-TEST
# ============================================================
#
# Beim Start wird EINMAL eine Testnachricht gesendet.
# Danach läuft der Bot normal weiter.
#

print(
    "[TEST] Sende Testnachricht an Discord..."
)


test_item = {

    "pakFilename":
        "packchunk1013-WindowsClient.pak",

    "key":
        "TEST_KEY",

    "keychain":
        "TEST_KEYCHAIN",

    "pakGuid":
        "TEST_GUID",

    "image":
        TEST_IMAGE_URL
}


test_result = send_discord(
    test_item
)


if test_result:

    print(
        "[TEST] Discord-Test erfolgreich!"
    )

else:

    print(
        "[TEST] Discord-Test fehlgeschlagen!"
    )


print(
    "[TEST] Bot läuft jetzt normal weiter..."
)


# ============================================================
# BEKANNTE AES LADEN
# ============================================================

seen = load_seen()

print(
    f"[SEEN] {len(seen)} bekannte AES geladen"
)


# ============================================================
# AKTUELLEN BESTAND ÜBERNEHMEN
# ============================================================
#
# Beim Start werden bereits vorhandene AES als bekannt
# gespeichert.
#
# Dadurch werden beim Neustart nicht alle alten AES
# erneut gepostet.
#

initial_aes = get_aes()


if initial_aes:

    new_saved = 0

    for item in initial_aes:

        uid = get_uid(item)

        if uid not in seen:

            seen.add(uid)

            new_saved += 1


    save_seen(seen)


    print(
        f"[START] {new_saved} vorhandene "
        f"AES gespeichert"
    )

else:

    print(
        "[START] Keine AES gefunden"
    )


# ============================================================
# LIVE
# ============================================================

print(
    "[LIVE] Warte auf neue AES..."
)


# ============================================================
# LIVE LOOP
# ============================================================

while True:

    try:

        aes = get_aes()


        # ----------------------------------------------------
        # KEINE AES-DATEN
        # ----------------------------------------------------

        if not aes:

            print(
                "[CHECK] Keine AES-Daten"
            )

            time.sleep(
                CHECK_TIME
            )

            continue


        found_new = False


        # ----------------------------------------------------
        # AES PRÜFEN
        # ----------------------------------------------------

        for item in aes:

            uid = get_uid(item)


            # ------------------------------------------------
            # BEREITS BEKANNT
            # ------------------------------------------------

            if uid in seen:

                continue


            # ------------------------------------------------
            # NEUER PAK
            # ------------------------------------------------

            found_new = True


            print("")

            print(
                "[AES] Neuer Pak gefunden!"
            )


            print(
                "[AES] Pak:",
                item.get(
                    "pakFilename",
                    "UNKNOWN"
                )
            )


            print(
                "[AES] GUID:",
                item.get(
                    "pakGuid",
                    "UNKNOWN"
                )
            )


            # ------------------------------------------------
            # SOFORT ALS BEKANNT MARKIEREN
            # ------------------------------------------------

            seen.add(uid)

            save_seen(seen)


            # ------------------------------------------------
            # DISCORD
            # ------------------------------------------------

            send_discord(item)


            # Kleine Pause zwischen Nachrichten
            time.sleep(2)


        # ----------------------------------------------------
        # KEINE NEUEN AES
        # ----------------------------------------------------

        if not found_new:

            print(
                "[CHECK] Keine neuen AES"
            )


        # ----------------------------------------------------
        # 30 SEKUNDEN WARTEN
        # ----------------------------------------------------

        time.sleep(
            CHECK_TIME
        )


    # ========================================================
    # MANUELLER STOP
    # ========================================================

    except KeyboardInterrupt:

        print("")

        print(
            "[BOT] Manuell gestoppt"
        )

        break


    # ========================================================
    # FEHLER
    # ========================================================

    except Exception as e:

        print(
            "[LOOP] Fehler:",
            e
        )

        print(
            "[LOOP] Bot läuft in 30 Sekunden weiter..."
        )

        time.sleep(30)
