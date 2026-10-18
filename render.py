"""Crea il video della storia del giorno: out/storia.mp4 (1080x1920) + out/info.json.
Uso: python render.py [oggi]   (oggi = 1..7, 1 = lunedì; se manca usa la data di Roma)
"""
import asyncio, json, os, shutil, subprocess, sys
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright

FPS = 30
DURATA = int(os.environ.get("DURATA", "14"))  # secondi
QUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(QUI, "out")
FRAMES = os.path.join(OUT, "frames")
GIORNI = ["", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]


async def main(oggi):
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(FRAMES)
    url = "file://" + os.path.join(QUI, "programma.html") + f"?story=1&oggi={oggi}"
    async with async_playwright() as p:
        br = await p.chromium.launch()
        pg = await br.new_page(viewport={"width": 1080, "height": 1920})
        txt = open(os.path.join(QUI, "programma.txt"), encoding="utf-8").read()
        await pg.add_init_script("window.PROGRAMMA_TXT = " + json.dumps(txt) + ";")
        await pg.goto(url)
        await pg.wait_for_function("window.__pronto === true", timeout=15000)
        await pg.wait_for_timeout(300)
        righe = await pg.evaluate("ROWS")
        for i in range(FPS * DURATA):
            await pg.evaluate(
                f"document.getAnimations().forEach(a=>{{a.pause();a.currentTime={i * 1000 / FPS}}})")
            # due fotogrammi di attesa, altrimenti alcune righe restano vecchie
            await pg.evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
            await pg.screenshot(path=os.path.join(FRAMES, f"f{i:04d}.jpg"), type="jpeg", quality=94)
        await br.close()

    video = os.path.join(OUT, "storia.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-framerate", str(FPS), "-i", os.path.join(FRAMES, "f%04d.jpg"),
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-shortest", "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-crf", "19", "-preset", "medium", "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", video], check=True)
    shutil.rmtree(FRAMES)

    # testo per Telegram
    gruppi = sorted({r[3] for r in righe})
    gruppo = oggi if oggi in gruppi else (6 if oggi == 7 and 6 in gruppi else None)
    blocco = [r[0] for r in righe if r[3] == gruppo and r[2] == "i"]
    pausa = (not blocco) or any("pausa" in b.lower() for b in blocco)
    if oggi >= 6 and pausa:
        testo = "🕹️ Weekend di pausa, la settimana è finita!\n\n<b>SEE YOU NEXT WEEK</b> 👋"
    elif not blocco:
        testo = f"📅 <b>Oggi, {GIORNI[oggi]}</b>: niente live, ci vediamo al prossimo appuntamento! 👾"
    elif len(blocco) == 1:
        testo = f"📅 <b>Oggi, {GIORNI[oggi]}</b>\n🎮 {blocco[0]}"
    else:
        testo = f"📅 <b>Oggi, {GIORNI[oggi]}</b>\n🎮 " + "\n".join(blocco[:-1]) + f"\n⏰ {blocco[-1]}"
    with open(os.path.join(OUT, "info.json"), "w") as f:
        json.dump({"oggi": oggi, "giorno": GIORNI[oggi], "testo": testo}, f, ensure_ascii=False)
    print("Video pronto:", video, f"({os.path.getsize(video) // 1024} KB)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].strip():
        oggi = int(sys.argv[1])
    else:
        oggi = datetime.now(ZoneInfo("Europe/Rome")).isoweekday()
    asyncio.run(main(oggi))
