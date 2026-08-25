import requests
import json
import time
import os
import io

from datetime import datetime
from PIL import Image, ImageDraw


# =====================================================
# EINSTELLUNGEN
# =====================================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1541600578340130897/f6xXG74cD3qIKlM28hv56FdxH0N__qaHlugIKC_oD5cd5XWzHKbANJhDEzJW9M0DJ1vl"

AES_URL = "https://fortnite-api.com/v2/aes"

ROLE_ID = "1523617106414014504"

CHECK_TIME = 30

# Hosting Schreibschutz Fix
SEEN_FILE = "seen.json"


# =====================================================
# AES HOLEN
# =====================================================

def get_aes():

    try:

        r = requests.get(
            AES_URL,
            timeout=15
        )

        if r.status_code != 200:
            return []

        data = r.json()

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
# EINDEUTIGE ID
# =====================================================

def get_uid(item):

    return (

        str(item.get("pakFilename",""))

        + "|"

        + str(item.get("pakGuid",""))

        + "|"

        + str(item.get("key",""))

    )



# =====================================================
# SEEN
# =====================================================

def load_seen():

    try:

        if not os.path.exists(SEEN_FILE):
            return set()


        with open(
            SEEN_FILE,
            "r"
        ) as f:

            return set(
                json.load(f)
            )


    except:

        return set()



def save_seen(seen):

    try:

        with open(
            SEEN_FILE,
            "w"
        ) as f:

            json.dump(
                list(seen),
                f
            )


    except Exception as e:

        print(
            "[SAVE ERROR]",
            e
        )



# =====================================================
# PAK INFO
# =====================================================

def get_pak_info(pak):

    # Hier kommt später echte Pak Analyse rein

    return {

        "count":
            "Scanning...",

        "size":
            "Scanning..."

    }



# =====================================================
# TEST BILD
# =====================================================

def create_preview():

    img = Image.new(
        "RGB",
        (900,500),
        (25,25,45)
    )


    draw = ImageDraw.Draw(img)


    draw.text(
        (40,40),
        "MIDNIGHT SUN",
        fill="white"
    )


    draw.text(
        (40,90),
        "New Pak decrypted",
        fill="cyan"
    )


    draw.rectangle(
        (500,0,900,500),
        fill=(40,200,200)
    )


    draw.ellipse(
        (680,100,750,170),
        fill="white"
    )


    draw.line(
        (715,170,715,320),
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

def send_discord(item):


    pak = item.get(
        "pakFilename",
        "UNKNOWN"
    )


    key = item.get(
        "key",
        "UNKNOWN"
    )


    guid = item.get(
        "pakGuid",
        "UNKNOWN"
    )


    keychain = item.get(
        "keychain",
        key
    )


    info = get_pak_info(
        pak
    )


    embed = {


        "title":
            "New Pak was decrypted!",



        "description":

            (

            f"**{pak}**\n"
            f"{key}\n\n"


            f"**Keychain**\n"
            f"{keychain}\n\n"


            f"**GUID**\n"
            f"{guid}\n\n"


            f"**File Count**                 **File Size**\n"
            f"{info['count']}                         {info['size']}"

            ),



        "color":
            5793266,


        "image":

            {
                "url":
                "attachment://pak.png"
            },


        "footer":

            {
                "text":
                f"made by @kiranfn • heute um {datetime.now().strftime('%H:%M Uhr')}"
            }

    }



    payload = {


        "content":

            f"<@&{ROLE_ID}>",



        "embeds":

            [
                embed
            ],


        "allowed_mentions":

            {

            "roles":
                [
                    ROLE_ID
                ]

            }

    }



    image = create_preview()



    requests.post(

        WEBHOOK_URL,

        data={

            "payload_json":
            json.dumps(payload)

        },

        files={

            "file":

            (
                "pak.png",
                image,
                "image/png"
            )

        },

        timeout=20

    )


    print(
        "[DISCORD] gesendet"
    )



# =====================================================
# START
# =====================================================

print("====================")
print(" FORTNITE AES BOT ")
print("====================")


seen = load_seen()


# Test Nachricht

test = {

    "pakFilename":
        "packchunk1013-WindowsClient.pak",

    "key":
        "TEST_KEY",

    "keychain":
        "TEST_KEYCHAIN",

    "pakGuid":
        "TEST_GUID"

}


send_discord(test)



# aktuelle AES speichern

for item in get_aes():

    seen.add(
        get_uid(item)
    )


save_seen(seen)



print(
    "[LIVE] gestartet"
)



# =====================================================
# LOOP
# =====================================================

while True:


    try:


        aes = get_aes()


        for item in aes:


            uid = get_uid(item)


            if uid in seen:
                continue



            seen.add(uid)

            save_seen(seen)


            print(
                "[NEW AES]",
                item.get("pakFilename")
            )


            send_discord(item)



        time.sleep(
            CHECK_TIME
        )



    except Exception as e:


        print(
            "[LOOP ERROR]",
            e
        )


        time.sleep(30)
