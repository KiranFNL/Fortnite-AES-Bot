import json
import os
import time
import requests
from datetime import datetime


# =========================================================
# KONFIGURATION
# =========================================================

API_URL = "https://fortnite-api.com/v2/aes"

# DEINEN DISCORD WEBHOOK HIER EINTRAGEN
WEBHOOK_URL = "https://discord.com/api/webhooks/1541537331272745061/blf3OerlkhCNMg0iSwwtk-EsVCkhvdJVcd-CTS9ToKPRZrsHqE4A2LmRT9GyLtqPiuwq"

ROLE_ID = "1523617106414014504"

CHECK_INTERVAL = 30
WEBHOOK_COOLDOWN = 3

DATABASE_FILE = "seen_paks.json"
IMAGE_FILE = "pak_preview.png"

last_webhook = 0


# =========================================================
# SEEN PAKS LADEN
# =========================================================

def load_seen():
    if not os.path.exists(DATABASE_FILE):
        return set()

    try:
        with open(
            DATABASE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return set(data)

    except Exception as error:

        print(
            f"[-] Fehler beim Laden der Datenbank: {error}"
        )

        return set()


# =========================================================
# SEEN PAKS SPEICHERN
# =========================================================

def save_seen(seen):

    try:

        with open(
            DATABASE_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                list(seen),
                file,
                indent=2,
                ensure_ascii=False
            )

    except Exception as error:

        print(
            f"[-] Fehler beim Speichern: {error}"
        )


# =========================================================
# API
# =========================================================

def get_paks():

    print(
        "[*] Fortnite API wird abgefragt..."
    )

    response = requests.get(
        API_URL,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    paks = data.get(
        "data",
        {}
    ).get(
        "dynamicKeys",
        []
    )

    print(
        f"[+] {len(paks)} PAKs gefunden"
    )

    return paks


# =========================================================
# PAK ID
# =========================================================

def get_pak_id(pak):

    filename = str(
        pak.get(
            "pakFilename",
            ""
        )
    )

    guid = str(
        pak.get(
            "pakGuid",
            ""
        )
    )

    key = str(
        pak.get(
            "key",
            ""
        )
    )

    return (
        f"{filename}|"
        f"{guid}|"
        f"{key}"
    )


# =========================================================
# FILE INFORMATION
# =========================================================

def get_file_info(pak):

    file_id = pak.get(
        "fileId",
        pak.get(
            "pakGuid",
            "N/A"
        )
    )

    file_count = pak.get(
        "fileCount",
        "N/A"
    )

    file_size = pak.get(
        "fileSize",
        "N/A"
    )

    # Falls vorhanden: verschachtelte File-Daten
    file_data = pak.get("file")

    if isinstance(
        file_data,
        dict
    ):

        file_id = file_data.get(
            "id",
            file_id
        )

        file_count = file_data.get(
            "count",
            file_count
        )

        file_size = file_data.get(
            "size",
            file_size
        )

    return (
        file_id,
        file_count,
        file_size
    )


# =========================================================
# DISCORD SENDEN
# =========================================================

def send_pak(
    pak,
    test=False
):

    global last_webhook

    filename = pak.get(
        "pakFilename",
        "Unknown.pak"
    )

    guid = pak.get(
        "pakGuid",
        "N/A"
    )

    key = pak.get(
        "key",
        "N/A"
    )

    key = str(
        key
    ).upper()

    # -----------------------------------------------------
    # FILE INFORMATION
    # -----------------------------------------------------

    file_id, file_count, file_size = (
        get_file_info(pak)
    )

    # -----------------------------------------------------
    # COOLDOWN
    # -----------------------------------------------------

    wait = (
        WEBHOOK_COOLDOWN
        -
        (
            time.time()
            -
            last_webhook
        )
    )

    if wait > 0:

        time.sleep(
            wait
        )

    # -----------------------------------------------------
    # UHRZEIT
    # -----------------------------------------------------

    now = datetime.now().strftime(
        "%H:%M"
    )

    # -----------------------------------------------------
    # TITEL
    # -----------------------------------------------------

    title = "New Pak was decrypted!"

    if test:

        title += " • TEST"

    # -----------------------------------------------------
    # EMBED
    # -----------------------------------------------------

    embed = {

        "title": title,

        "description": (
            f"**{filename}**\n"
            f"`0x{key}`\n\n"

            f"**Keychain**\n"
            f"`{key}`\n\n"

            f"**GUID**\n"
            f"`{guid}`\n\n"

            f"**File Id**\n"
            f"`{file_id}`\n\n"

            f"**File Count**"
            f"　　　　　　　　 "
            f"**File Size**\n"
            f"`{file_count}`"
            f"　　　　　　　　 "
            f"`{file_size}`"
        ),

        "color": 0x3498DB,

        "footer": {
            "text": (
                f"made by @kiranfn • "
                f"heute um {now} Uhr"
            )
        }
    }

    # -----------------------------------------------------
    # BILD
    # -----------------------------------------------------

    image_path = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        IMAGE_FILE
    )

    has_image = os.path.isfile(
        image_path
    )

    if has_image:

        embed["image"] = {
            "url": (
                f"attachment://"
                f"{IMAGE_FILE}"
            )
        }

    else:

        print(
            f"[!] Bild nicht gefunden: "
            f"{image_path}"
        )

    # -----------------------------------------------------
    # PAYLOAD
    # -----------------------------------------------------

    payload = {

        "content": (
            f"<@&{ROLE_ID}>"
        ),

        "embeds": [
            embed
        ],

        "allowed_mentions": {
            "roles": [
                ROLE_ID
            ]
        }
    }

    # -----------------------------------------------------
    # SENDEN
    # -----------------------------------------------------

    try:

        if has_image:

            with open(
                image_path,
                "rb"
            ) as image_file:

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
                            IMAGE_FILE,
                            image_file,
                            "image/png"
                        )
                    },

                    timeout=15
                )

        else:

            response = requests.post(

                WEBHOOK_URL,

                json=payload,

                timeout=15
            )

        # -------------------------------------------------
        # ERFOLG
        # -------------------------------------------------

        if response.status_code == 204:

            last_webhook = time.time()

            if test:

                print(
                    "[+] TEST erfolgreich gesendet!"
                )

            else:

                print(
                    f"[+] GESENDET: {filename}"
                )

            return True

        # -------------------------------------------------
        # RATE LIMIT
        # -------------------------------------------------

        if response.status_code == 429:

            try:

                retry = (
                    response
                    .json()
                    .get(
                        "retry_after",
                        5
                    )
                )

            except Exception:

                retry = 5

            print(
                f"[!] Discord Rate Limit: "
                f"{retry}s"
            )

            time.sleep(
                float(retry)
            )

            return False

        # -------------------------------------------------
        # FEHLER
        # -------------------------------------------------

        print(
            f"[-] Discord Fehler: "
            f"{response.status_code}"
        )

        print(
            response.text
        )

        return False

    except requests.RequestException as error:

        print(
            f"[-] Webhook Fehler: "
            f"{error}"
        )

        return False


# =========================================================
# START-TEST
# =========================================================

def startup_test(paks):

    if not paks:

        print(
            "[-] Keine PAKs für den Start-Test."
        )

        return

    pak = paks[0]

    print()
    print(
        "[*] START-TEST"
    )

    print(
        f"[*] Sende: "
        f"{pak.get('pakFilename', 'Unknown.pak')}"
    )

    send_pak(
        pak,
        test=True
    )

    print()


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print(
        "======================================"
    )
    print(
        "        FORTNITE AES TRACKER"
    )
    print(
        "======================================"
    )
    print()

    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

    seen = load_seen()

    print(
        f"[+] {len(seen)} gespeicherte PAKs geladen"
    )

    print(
        "[+] Spam-Schutz: AKTIV"
    )

    print(
        f"[+] API-Check: "
        f"{CHECK_INTERVAL}s"
    )

    print()

    # -----------------------------------------------------
    # ERSTER API CHECK
    # -----------------------------------------------------

    try:

        paks = get_paks()

    except requests.RequestException as error:

        print(
            f"[-] API Fehler: {error}"
        )

        return

    except Exception as error:

        print(
            f"[-] Fehler: {error}"
        )

        return

    # -----------------------------------------------------
    # AKTUELLE PAKS SPEICHERN
    # -----------------------------------------------------

    current_ids = set()

    for pak in paks:

        pak_id = get_pak_id(
            pak
        )

        if pak_id:

            current_ids.add(
                pak_id
            )

    new_entries = (
        current_ids - seen
    )

    if new_entries:

        seen.update(
            new_entries
        )

        save_seen(
            seen
        )

    print()
    print(
        f"[*] Erster Check: "
        f"{len(paks)} PAKs gespeichert"
    )

    print(
        "[*] Alte PAKs werden "
        "NICHT automatisch gesendet"
    )

    # -----------------------------------------------------
    # SOFORT EIN TEST
    # -----------------------------------------------------

    startup_test(
        paks
    )

    print(
        "[+] Live-Tracker gestartet!"
    )

    print()

    # -----------------------------------------------------
    # LIVE LOOP
    # -----------------------------------------------------

    while True:

        try:

            time.sleep(
                CHECK_INTERVAL
            )

            paks = get_paks()

            new_count = 0

            for pak in paks:

                pak_id = get_pak_id(
                    pak
                )

                if not pak_id:

                    continue

                # Bereits bekannt
                if pak_id in seen:

                    continue

                filename = pak.get(
                    "pakFilename",
                    "Unknown.pak"
                )

                print()
                print(
                    f"[+] NEUE PAK: "
                    f"{filename}"
                )

                # -------------------------------------------------
                # DISCORD
                # -------------------------------------------------

                success = send_pak(
                    pak,
                    test=False
                )

                # -------------------------------------------------
                # NUR BEI ERFOLG SPEICHERN
                # -------------------------------------------------

                if success:

                    seen.add(
                        pak_id
                    )

                    save_seen(
                        seen
                    )

                    new_count += 1

            print(
                f"[*] {len(paks)} Einträge | "
                f"{new_count} neue gesendet"
            )

        except requests.RequestException as error:

            print(
                f"[-] API Fehler: {error}"
            )

        except KeyboardInterrupt:

            print()
            print(
                "[*] Tracker beendet."
            )

            break

        except Exception as error:

            print(
                f"[-] Fehler: {error}"
            )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()