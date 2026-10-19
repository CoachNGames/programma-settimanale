"""Reel nuovi di Instagram → gruppo Telegram (argomento "Clip e video").
Gira ogni 15 minuti su GitHub. Ricorda i reel già visti in stato/reel_visti.txt.
La prima volta segna come visti quelli che ci sono già, senza mandarli.
Variabili: IG_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT, REEL_THREAD, REEL_REINVIA (= "1" rimanda l'ultimo reel, per prova)
"""
import html, json, os, sys, tempfile
import requests

QUI = os.path.dirname(os.path.abspath(__file__))
VISTI = os.path.join(QUI, "stato", "reel_visti.txt")
IG = "https://graph.instagram.com"
MAX_UPLOAD = 49 * 1024 * 1024  # i bot Telegram possono caricare file fino a 50 MB

ig_tok = os.environ.get("IG_TOKEN", "").strip()
tg_tok = os.environ.get("TELEGRAM_TOKEN", "").strip()
chat = os.environ.get("TELEGRAM_CHAT", "").strip() or "@Boris_el_machico"
thread = os.environ.get("REEL_THREAD", "").strip() or "141"
reinvia = os.environ.get("REEL_REINVIA", "") == "1"
if not ig_tok or not tg_tok:
    sys.exit("Mancano IG_TOKEN o TELEGRAM_TOKEN")

r = requests.get(f"{IG}/me/media", params={
    "fields": "id,media_type,media_product_type,permalink,caption,timestamp,media_url,thumbnail_url",
    "limit": 15, "access_token": ig_tok}, timeout=30).json()
if "error" in r:
    sys.exit(f"Instagram: {r['error'].get('message')}")
reel = [m for m in r.get("data", []) if m.get("media_product_type") == "REELS"]
reel.sort(key=lambda m: m.get("timestamp", ""))  # dal più vecchio al più nuovo
print(f"Reel trovati negli ultimi contenuti: {len(reel)}")

prima_volta = not os.path.exists(VISTI)
visti = set(open(VISTI).read().split()) if not prima_volta else set()

if prima_volta:
    da_mandare = []
    print("Prima volta: segno come già visti i reel esistenti, senza mandarli")
elif reinvia and reel:
    da_mandare = [reel[-1]]
    print("Prova: rimando l'ultimo reel")
else:
    da_mandare = [m for m in reel if m["id"] not in visti]


def testo(m):
    cap = (m.get("caption") or "").strip()
    if len(cap) > 700:
        cap = cap[:700].rsplit(" ", 1)[0] + "…"
    t = "🎬 <b>Nuovo reel su Instagram!</b>"
    if cap:
        t += "\n\n" + html.escape(cap)
    return t


def tasto(m):
    return json.dumps({"inline_keyboard": [[{"text": "▶️ Guarda su Instagram", "url": m["permalink"]}]]})


def manda(m):
    base = {"chat_id": chat, "message_thread_id": thread, "parse_mode": "HTML",
            "caption": testo(m), "reply_markup": tasto(m)}
    api = f"https://api.telegram.org/bot{tg_tok}"
    # 1) il video vero, caricato da qui (si vede direttamente nel gruppo)
    url = m.get("media_url")
    if url:
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
                with requests.get(url, stream=True, timeout=120) as v:
                    v.raise_for_status()
                    n = 0
                    for blocco in v.iter_content(1 << 20):
                        n += len(blocco)
                        if n > MAX_UPLOAD:
                            raise ValueError("video troppo grande per Telegram")
                        f.write(blocco)
                f.flush(); f.seek(0)
                files = {"video": ("reel.mp4", f, "video/mp4")}
                thumb = None
                if m.get("thumbnail_url"):
                    thumb = requests.get(m["thumbnail_url"], timeout=30).content
                    files["thumbnail"] = ("copertina.jpg", thumb, "image/jpeg")
                j = requests.post(f"{api}/sendVideo", data={**base, "supports_streaming": "true"},
                                  files=files, timeout=300).json()
                if j.get("ok"):
                    return True
                print("  sendVideo non riuscito:", j.get("description"))
        except Exception as e:
            print("  video non caricato:", e)
    # 2) ripiego: copertina + bottone
    if m.get("thumbnail_url"):
        j = requests.post(f"{api}/sendPhoto", data={**base, "photo": m["thumbnail_url"]}, timeout=60).json()
        if j.get("ok"):
            return True
        print("  sendPhoto non riuscito:", j.get("description"))
    # 3) solo testo con il link
    base.pop("caption")
    j = requests.post(f"{api}/sendMessage", data={**base, "text": testo(m)}, timeout=60).json()
    if j.get("ok"):
        return True
    print("  sendMessage non riuscito:", j.get("description"))
    return False


errori = 0
for m in da_mandare:
    print("Mando", m["permalink"])
    if manda(m):
        visti.add(m["id"])
    else:
        errori += 1

for m in reel if prima_volta else []:
    visti.add(m["id"])

os.makedirs(os.path.dirname(VISTI), exist_ok=True)
with open(VISTI, "w") as f:
    f.write("\n".join(sorted(visti)) + "\n")
print(f"Mandati: {len(da_mandare) - errori}, errori: {errori}")
sys.exit(1 if errori else 0)
