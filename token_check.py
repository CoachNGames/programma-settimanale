"""Tiene d'occhio l'età del token Instagram (dura 60 giorni).
Salva in stato/token_ig.txt un'impronta corta del token (non il token!) e la data in cui è comparso.
A 50 giorni apre un avviso su GitHub (arriva per mail e nell'app); quando il token cambia lo chiude.
"""
import hashlib, json, os, subprocess
from datetime import date

AVVISO_DOPO = 50   # giorni
DURATA = 60
TITOLO = "🔑 Token Instagram in scadenza"
FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stato", "token_ig.txt")
REPO = os.environ.get("GITHUB_REPOSITORY", "CoachNGames/programma-settimanale")

tok = os.environ.get("IG_TOKEN", "").strip()
if not tok:
    raise SystemExit("IG_TOKEN mancante")
impronta = hashlib.sha256(tok.encode()).hexdigest()[:10]
oggi = date.today()


def gh(*a):
    return subprocess.run(["gh", *a, "--repo", REPO], capture_output=True, text=True).stdout


def avvisi_aperti():
    out = gh("issue", "list", "--state", "open", "--search", f"{TITOLO} in:title", "--json", "number")
    return [i["number"] for i in json.loads(out or "[]")]


vecchia, dal = "", oggi
if os.path.exists(FILE):
    parti = open(FILE).read().split()
    if len(parti) == 2:
        vecchia, dal = parti[0], date.fromisoformat(parti[1])

if impronta != vecchia:
    dal = oggi
    with open(FILE, "w") as f:
        f.write(f"{impronta} {oggi.isoformat()}\n")
    for n in avvisi_aperti():
        gh("issue", "close", str(n), "--comment", "Token Instagram nuovo trovato ✔ Il conto dei 60 giorni riparte da oggi.")
    print("Token nuovo: conto dei giorni ripartito da oggi")

eta = (oggi - dal).days
scade = date.fromordinal(dal.toordinal() + DURATA)
print(f"Token Instagram in uso da {eta} giorni, scade circa il {scade:%d/%m/%Y}")

if eta >= AVVISO_DOPO and not avvisi_aperti():
    corpo = f"""@CoachNGames il token Instagram scade circa il **{scade:%d/%m/%Y}** (dura 60 giorni).
Dopo quella data la storia delle 10:30 smette di uscire su Instagram (Telegram continua).

**Come rinnovarlo (5 minuti):**
1. developers.facebook.com → app **Overlay Follower CRT** → Casi d'uso → **Configurazione dell'API con Instagram Login**
2. Accanto a **coach_n_games** premi **Genera token** e copialo
3. Qui su GitHub: Settings → Secrets and variables → Actions → **IG_TOKEN** → ✏️ → incolla → Update secret

Questo avviso si chiude da solo la mattina dopo, quando il token nuovo viene usato.
(Il token nuovo va bene anche per il contatore follower in OBS.)"""
    gh("issue", "create", "--title", TITOLO, "--body", corpo)
    print("Avviso di scadenza aperto")
