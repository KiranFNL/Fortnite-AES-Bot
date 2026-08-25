import requests
import json
import time
import os
from datetime import datetime


# ============================================================
# EINSTELLUNGEN
# ============================================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1541600578340130897/f6xXG74cD3qIKlM28hv56FdxH0N__qaHlugIKC_oD5cd5XWzHKbANJhDEzJW9M0DJ1vl"

AES_URL = "https://fortnite-api.com/v2/aes"

SEEN_FILE = "seen.json"

CHECK_TIME = 30


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
            return []

        return dynamic_keys

    except Exception as e:
        print("[AES] Fehler:", e)
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

    try:

        temp_file = SEEN_FILE + ".tmp"

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

    except Exception as e:

        print(
            "[SEEN] Speicherfehler:",
            e
        )


# ============================================================
# DISCORD SENDEN
# ============================================================

def send_discord(item):

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


    # --------------------------------------------------------
    # AKTUELLE UHRZEIT
    # --------------------------------------------------------

    now = datetime.now()

    current_time = now.strftime(
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
    # PAYLOAD
    # --------------------------------------------------------

    payload = {

        "content":
            "@aes-tracker",


        "embeds": [
            embed
        ],


        "allowed_mentions": {
            "parse": []
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


        if response.status_code == 204:

            print(
                "[DISCORD] Nachricht gesendet"
            )

            return True


        # Rate Limit
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
# Dadurch wird beim Neustart NICHT alles erneut gepostet.
#
# ============================================================

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


print(
    "[LIVE] Warte auf neue AES..."
)


# ============================================================
# LIVE LOOP
# ============================================================

while True:

    try:

        aes = get_aes()

        if not aes:

            print(
                "[CHECK] Keine AES-Daten"
            )

            time.sleep(
                CHECK_TIME
            )

            continue


        found_new = False


        for item in aes:

            uid = get_uid(item)


            # ----------------------------------------------
            # SCHON GESENDET?
            # ----------------------------------------------

            if uid in seen:
                continue


            # ----------------------------------------------
            # NEUER PAK
            # ----------------------------------------------

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


            # ----------------------------------------------
            # SOFORT ALS BEKANNT MARKIEREN
            # ----------------------------------------------
            #
            # Wichtig gegen Spam:
            # Selbst wenn Discord später einen Fehler
            # zurückgibt, wird derselbe Key nicht
            # bei jedem 30-Sekunden-Check erneut gesendet.
            #
            # ----------------------------------------------

            seen.add(uid)

            save_seen(seen)


            # ----------------------------------------------
            # DISCORD
            # ----------------------------------------------

            send_discord(item)


            # Kleine Pause zwischen mehreren neuen Keys
            time.sleep(2)


        if not found_new:

            print(
                "[CHECK] Keine neuen AES"
            )


        # ----------------------------------------------
        # NÄCHSTER CHECK
        # ----------------------------------------------

        time.sleep(
            CHECK_TIME
        )


    except KeyboardInterrupt:

        print("")
        print(
            "[BOT] Manuell gestoppt"
        )

        break


    except Exception as e:

        print(
            "[LOOP] Fehler:",
            e
        )

        time.sleep(30)
