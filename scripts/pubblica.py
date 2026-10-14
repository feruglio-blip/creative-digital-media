"""Pubblica su Instagram i post di calendario.json arrivati all'orario.

Gira su GitHub Actions. Legge il token dal secret INSTAGRAM_ACCESS_TOKEN.
Pubblica solo i post approvati, con orario passato da meno di FINESTRA_MIN minuti,
e non ancora presenti in pubblicati.json. Scrive l'esito in pubblicati.json.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API = "https://graph.instagram.com/v23.0"
FINESTRA_MIN = int(os.environ.get("FINESTRA_MIN", "120"))
ANTICIPO_MIN = int(os.environ.get("ANTICIPO_MIN", "20"))  # GitHub lancia il cron ogni 30-35 minuti: si parte un po' prima
TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
SOLO_ID = [x.strip() for x in os.environ.get("SOLO_ID", "").split(",") if x.strip()]  # uno o più post, separati da virgola
PROVA = os.environ.get("PROVA", "false").lower() == "true"  # prepara il post su Instagram senza pubblicarlo


def chiama(metodo, percorso, **parametri):
    parametri["access_token"] = TOKEN
    dati = urllib.parse.urlencode(parametri).encode()
    if metodo == "GET":
        req = urllib.request.Request(f"{API}/{percorso}?{dati.decode()}")
    else:
        req = urllib.request.Request(f"{API}/{percorso}", data=dati, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{metodo} {percorso}: {e.code} {e.read().decode()[:400]}")


def aspetta_pronto(contenitore):
    for _ in range(30):
        stato = chiama("GET", contenitore, fields="status_code").get("status_code")
        if stato == "FINISHED":
            return
        if stato == "ERROR":
            raise RuntimeError(f"contenitore {contenitore} in errore")
        time.sleep(5)
    raise RuntimeError(f"contenitore {contenitore} non pronto dopo 150 secondi")


def pubblica(post, base_url, utente, prova=False):
    urls = [base_url + p for p in post["immagini"]]
    if len(urls) == 1:
        c = chiama("POST", f"{utente}/media", image_url=urls[0], caption=post["caption"])["id"]
    else:
        figli = []
        for u in urls:
            f = chiama("POST", f"{utente}/media", image_url=u, is_carousel_item="true")["id"]
            figli.append(f)
        for f in figli:
            aspetta_pronto(f)
        c = chiama("POST", f"{utente}/media", media_type="CAROUSEL",
                   children=",".join(figli), caption=post["caption"])["id"]
    aspetta_pronto(c)
    if prova:
        return None  # contenitore pronto: immagini e caption accettate, ma niente pubblicazione
    return chiama("POST", f"{utente}/media_publish", creation_id=c)["id"]


def main():
    cal = json.load(open("calendario.json", encoding="utf-8"))
    reg = json.load(open("pubblicati.json", encoding="utf-8"))
    fuso = ZoneInfo(cal["fuso"])
    adesso = datetime.now(fuso)
    utente = chiama("GET", "me", fields="user_id,username")
    uid = utente["user_id"]
    print(f"Account: @{utente.get('username')} · ora {adesso:%Y-%m-%d %H:%M %Z}")

    da_fare = []
    for p in cal["post"]:
        if p["id"] in reg["pubblicati"] or not p.get("approvato"):
            continue
        quando = datetime.strptime(p["quando"], "%Y-%m-%d %H:%M").replace(tzinfo=fuso)
        if SOLO_ID:
            if p["id"] in SOLO_ID:
                da_fare.append(p)
        elif quando - timedelta(minutes=ANTICIPO_MIN) <= adesso < quando + timedelta(minutes=FINESTRA_MIN):
            da_fare.append(p)

    if not da_fare:
        print("Niente da pubblicare adesso.")
        return 0

    errori = 0
    for p in da_fare:
        print(f"Pubblico {p['id']} ({p['rubrica']} {p['numero']}, {len(p['immagini'])} immagini)")
        try:
            mid = pubblica(p, cal["base_url"], uid, prova=PROVA)
            if PROVA:
                print("  prova riuscita: Instagram ha accettato immagini e caption, post NON pubblicato")
                continue
            reg["pubblicati"][p["id"]] = {"media_id": mid, "il": datetime.now(fuso).isoformat(timespec="minutes")}
            print(f"  pubblicato, media {mid}")
        except Exception as e:  # un post fallito non blocca gli altri
            errori += 1
            print(f"  ERRORE: {e}")
    json.dump(reg, open("pubblicati.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
