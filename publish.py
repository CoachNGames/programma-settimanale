"""Pubblica out/storia.mp4: storia Instagram + video nel gruppo Telegram.
Variabili (segreti GitHub): TELEGRAM_TOKEN, TELEGRAM_CHAT, TELEGRAM_THREAD, IG_TOKEN, VIDEO_URL, SOLO_TELEGRAM
"""
import json, os, sys, time
import requests

QUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(QUI, "out")
VIDEO = os.path.join(OUT, "storia.mp4")
info = json.load(open(os.path.join(OUT, "info.json")))
errori = []


def telegram():
    tok = os.environ.get("TELEGRAM_TOKEN", "").strip()
    if not tok:
        errori.append("Telegram: manca il segreto TELEGRAM_TOKEN")
        return
    dati = {
        "chat_id": os.environ.get("TELEGRAM_CHAT", "").strip() or "@Boris_el_machico",
        "caption": info["testo"], "parse_mode": "HTML",
        "supports_streaming": "true", "width": 1080, "height": 1920,
    }
    thread = os.environ.get("TELEGRAM_THREAD", "").strip() or "10"
    if thread != "0":
        dati["message_thread_id"] = thread
    with open(VIDEO, "rb") as f:
        r = requests.post(f"https://api.telegram.org/bot{tok}/sendVideo", data=dati,
                          files={"video": ("programma.mp4", f, "video/mp4")}, timeout=180)
    j = r.json()
    if j.get("ok"):
        print("Telegram ✔")
    else:
        errori.append(f"Telegram: {j.get('description', r.text)[:300]}")


def instagram():
    tok = os.environ.get("IG_TOKEN", "").strip()
    url = os.environ.get("VIDEO_URL", "").strip()
    if not tok:
        errori.append("Instagram: manca il segreto IG_TOKEN")
        return
    G = "https://graph.instagram.com"
    me = requests.get(f"{G}/me", params={"fields": "user_id,username", "access_token": tok}, timeout=30).json()
    if "error" in me:
        errori.append(f"Instagram (token): {me['error'].get('message')}")
        return
    uid = me.get("user_id") or me.get("id")
    print("Instagram:", me.get("username"))

    c = requests.post(f"{G}/{uid}/media", data={
        "media_type": "STORIES", "video_url": url, "access_token": tok}, timeout=60).json()
    if "id" not in c:
        errori.append(f"Instagram (contenitore): {c.get('error', c)}")
        return
    cid = c["id"]
    stato = ""
    for _ in range(40):  # fino a ~7 minuti
        time.sleep(10)
        s = requests.get(f"{G}/{cid}", params={"fields": "status_code,status", "access_token": tok}, timeout=30).json()
        stato = s.get("status_code", "")
        print("  stato video:", stato)
        if stato == "FINISHED":
            break
        if stato in ("ERROR", "EXPIRED"):
            errori.append(f"Instagram (elaborazione): {s.get('status')}")
            return
    if stato != "FINISHED":
        errori.append("Instagram: il video non è stato elaborato in tempo")
        return
    p = requests.post(f"{G}/{uid}/media_publish", data={"creation_id": cid, "access_token": tok}, timeout=60).json()
    if "id" in p:
        print("Instagram storia ✔", p["id"])
    else:
        errori.append(f"Instagram (pubblicazione): {p.get('error', p)}")
        return

    # il token dura 60 giorni: il lunedì lo rinnovo (il workflow lo salva se c'è GH_PAT)
    if info["oggi"] == 1:
        r = requests.get(f"{G}/refresh_access_token",
                         params={"grant_type": "ig_refresh_token", "access_token": tok}, timeout=30).json()
        if r.get("access_token"):
            with open(os.path.join(OUT, "nuovo_token.txt"), "w") as f:
                f.write(r["access_token"])
            print("Token Instagram rinnovato (scade tra", r.get("expires_in", 0) // 86400, "giorni)")


if os.environ.get("SOLO_TELEGRAM", "false").lower() != "true":
    instagram()
telegram()

if errori:
    print("\n".join("✘ " + e for e in errori))
    sys.exit(1)
