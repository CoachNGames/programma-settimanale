# Storia "Programma settimanale" automatica

Ogni mattina alle **10:30 (ora di Roma)** GitHub crea il video del giorno e lo pubblica:
- nelle **storie Instagram** di @coach_n_games
- nel **gruppo Telegram**, argomento "When sono in Live e Dove"

I giorni passati diventano grigi, oggi ha le frecce verdi; sabato e domenica esce "SEE YOU NEXT WEEK".
Funziona a Mac spento.

## Impostazione (una volta sola)

1. **Repository** pubblico su GitHub con questi file (nessun dato segreto è nei file).
2. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
3. **Settings → Secrets and variables → Actions → New repository secret:**
   - `TELEGRAM_TOKEN` = token del bot @BorijaBot (da @BotFather → /mybots → API Token)
   - `IG_TOKEN` = token Instagram **con permesso di pubblicazione** (vedi sotto)
   - facoltativi: `TELEGRAM_CHAT` (predefinito `@Boris_el_machico`), `TELEGRAM_THREAD` (predefinito `10`),
     `GH_PAT` (token GitHub con permesso "Secrets: write" su questo repo, per salvare da solo il token Instagram rinnovato ogni lunedì)
4. **Token Instagram** (developers.facebook.com → app "Overlay Follower CRT" → Casi d'uso → API con Instagram Login → Personalizza):
   aggiungi il permesso `instagram_business_content_publish`, poi "Genera token" per coach_n_games.
5. **Prova:** Actions → "Storia programma settimanale" → Run workflow
   (spunta "solo Telegram" per la prima prova; "Giorno da simulare" 6 = sabato).

## Cambiare il programma (dal telefono)
1. App **GitHub** (o github.com) → repository **programma-settimanale** → file **programma.txt** → matita ✏️.
2. Una riga per giorno: `GIORNO | gioco | altra riga | orario`. I giorni senza live si tolgono.
   `SABATO - DOMENICA | Pausa` = weekend con "SEE YOU NEXT WEEK".
3. **Commit changes**. Dalla mattina dopo la storia usa il programma nuovo; l'impaginazione si adatta da sola.

Promemoria: la domenica sera, se programma.txt non è cambiato da 5 giorni, GitHub apre un avviso
"📅 Programma della settimana nuova?" (arriva per mail / notifica dell'app GitHub). Si chiude da solo quando salvi il programma.

## Qualità del video
Il video è disegnato al doppio (2160×3840) e ridotto a 1080×1920, il massimo che Instagram accetta per le storie:
scritte e bordi più nitidi. Per questo la preparazione parte prima (avvii alle 06:40 e 07:40 UTC) e aspetta le 10:30.

## Scadenza del token Instagram
Il token dura 60 giorni. `token_check.py` ricorda da quando è in uso (in `stato/token_ig.txt` c'è solo un'impronta, non il token)
e dopo 50 giorni apre l'avviso "🔑 Token Instagram in scadenza" con le istruzioni. Quando cambi IG_TOKEN l'avviso si chiude da solo.

## Se qualcosa non va
GitHub manda una mail quando un'esecuzione fallisce. In Actions, il passo "Pubblica Instagram + Telegram" spiega il motivo (✘ …).
- Il token Instagram dura 60 giorni: senza `GH_PAT` va rigenerato a mano prima della scadenza.
- Limite Instagram: 50 pubblicazioni via API ogni 24 ore (qui ne usiamo 1).
