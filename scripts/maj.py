"""Mise à jour automatique du portail (lancée chaque jour par GitHub Actions).

- vérifie que chaque appli répond (pastille « Hors ligne » sinon)
- lit la date de dernière modification (GitHub, Netlify)
- repère les nouvelles applis : dépôts GitHub publiés, dossiers d'isole-x, sites Netlify
- refait les captures d'écran le lundi, ou quand une capture manque (option --captures pour forcer)

Résultat : donnees/auto.json et captures/<id>.jpg
Variables : GH_TOKEN (fourni par GitHub), NETLIFY_TOKEN (facultatif, secret du dépôt)
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GH = "https://mike8999.github.io/"
COMPTE = "mike8999"
IGNORE = {"arduino", "portail", "STI2D_BTS_BUT"}
DOSSIERS_IGNORES = {"netlify", "node_modules", ".github", "scripts", "donnees", "captures", "icones", "assets"}
GH_TOKEN = os.environ.get("GH_TOKEN", "")
NETLIFY_TOKEN = os.environ.get("NETLIFY_TOKEN", "")
MAINTENANT = dt.datetime.now(dt.timezone.utc)
AUJOURDHUI = MAINTENANT.date().isoformat()


def chemin(*p):
    return os.path.join(RACINE, *p)


def lire(nom, defaut):
    try:
        with open(chemin(nom), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return defaut


def api(url, jeton=""):
    req = urllib.request.Request(url, headers={"User-Agent": "portail-mike8999", "Accept": "application/json"})
    if jeton:
        req.add_header("Authorization", "Bearer " + jeton)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except (urllib.error.URLError, ValueError, TimeoutError) as e:
        print("  API indisponible :", url, e)
        return None


def statut(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 portail-mike8999"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def cle(u):
    return re.sub(r"/?$", "/", (u or "").lower().replace("http:", "https:"))


def joli(n):
    n = re.sub(r"[-_]+", " ", n).strip()
    return n[:1].upper() + n[1:]


def main():
    forcer_captures = "--captures" in sys.argv
    apps = lire("apps.json", {"apps": []})["apps"]
    reg = lire("reglages.json", {})
    avant = lire("donnees/auto.json", None)
    vus_avant = {k: v.get("vu") for k, v in ((avant or {}).get("apps") or {}).items()}

    liste = [dict(a) for a in apps] + [dict(a, host="netlify" if "netlify.app" in a["url"] else "github") for a in reg.get("ajouts", [])]
    connues = {cle(u) for a in liste for u in (a.get("url"), a.get("alt")) if u}

    # ── Dépôts GitHub publiés ──
    print("GitHub…")
    depots = {}
    for page in (1, 2, 3):
        r = api(f"https://api.github.com/users/{COMPTE}/repos?per_page=100&page={page}", GH_TOKEN) or []
        for d in r:
            depots[d["name"]] = d
        if len(r) < 100:
            break
    trouvees = []
    for nom, d in depots.items():
        if d.get("has_pages") and not d.get("fork") and not d.get("archived") and nom not in IGNORE:
            url = GH + nom + "/"
            if cle(url) not in connues:
                trouvees.append({"id": "gh-" + nom, "nom": joli(nom), "desc": (d.get("description") or "")[:140], "url": url, "host": "github"})

    # ── Dossiers d'isole-x (une appli par dossier, sans les anciennes versions -v1, -v2…) ──
    contenu = api(f"https://api.github.com/repos/{COMPTE}/isole-x/contents", GH_TOKEN) or []
    for e in contenu:
        n = e.get("name", "")
        if e.get("type") != "dir" or n in DOSSIERS_IGNORES or n.startswith(".") or re.search(r"-v\d+$", n):
            continue
        url = f"{GH}isole-x/{n}/"
        if cle(url) in connues:
            continue
        sous = api(e["url"], GH_TOKEN) or []
        if any(s.get("name") == "index.html" for s in sous):
            trouvees.append({"id": "ix-" + n, "nom": joli(n), "desc": "", "url": url, "host": "github", "depot": "isole-x", "dossier": n})

    # ── Sites Netlify (seulement si le secret NETLIFY_TOKEN est configuré) ──
    sites = {}
    if NETLIFY_TOKEN:
        print("Netlify…")
        for s in api("https://api.netlify.com/api/v1/sites?per_page=100&filter=all", NETLIFY_TOKEN) or []:
            sites[s["name"]] = s
            url = (s.get("ssl_url") or s.get("url") or "").replace("http:", "https:")
            if url and cle(url) not in connues:
                trouvees.append({"id": "nl-" + s["name"], "nom": joli(s["name"]), "desc": "", "url": url + ("" if url.endswith("/") else "/"), "host": "netlify", "netlify": s["name"]})

    # ── Statut et date de modification ──
    print("Vérification des applis…")
    etat = {}
    for a in liste + trouvees:
        st = statut(a["url"])
        modif = None
        if a.get("netlify") and a["netlify"] in sites:
            modif = (sites[a["netlify"]].get("published_deploy") or {}).get("published_at") or sites[a["netlify"]].get("updated_at")
        elif a.get("depot") and a.get("dossier"):
            c = api(f"https://api.github.com/repos/{COMPTE}/{a['depot']}/commits?path={a['dossier']}&per_page=1", GH_TOKEN)
            if c:
                modif = c[0]["commit"]["committer"]["date"]
        elif a.get("depot") in depots:
            modif = depots[a["depot"]].get("pushed_at")
        vu = vus_avant.get(a["id"]) or ("initial" if avant is None else AUJOURDHUI)
        etat[a["id"]] = {"statut": st, "modif": (modif or "")[:10] or None, "vu": vu}
        print(f"  {st}  {a['id']}")

    # Une « nouveauté » qui ne répond pas n'est pas proposée
    trouvees = [t for t in trouvees if 200 <= etat[t["id"]]["statut"] < 400]

    os.makedirs(chemin("donnees"), exist_ok=True)
    with open(chemin("donnees", "auto.json"), "w", encoding="utf-8") as f:
        json.dump({"maj": MAINTENANT.isoformat(timespec="minutes"), "apps": etat, "trouvees": trouvees}, f, ensure_ascii=False, indent=1)

    # ── Captures d'écran ──
    lundi = MAINTENANT.weekday() == 0
    a_faire = [a for a in liste + trouvees
               if 200 <= etat[a["id"]]["statut"] < 400 and (forcer_captures or lundi or not os.path.exists(chemin("captures", a["id"] + ".jpg")))]
    if a_faire:
        captures(a_faire)


def captures(apps):
    from PIL import Image
    from playwright.sync_api import sync_playwright
    os.makedirs(chemin("captures"), exist_ok=True)
    print(f"Captures ({len(apps)})…")
    with sync_playwright() as p:
        nav = p.chromium.launch()
        for a in apps:
            page = nav.new_page(viewport={"width": 1280, "height": 800})
            try:
                page.goto(a["url"], timeout=30000, wait_until="load")
                page.wait_for_timeout(2500)
                tmp = chemin("captures", a["id"] + ".png")
                page.screenshot(path=tmp)
                Image.open(tmp).convert("RGB").resize((480, 300), Image.LANCZOS).save(chemin("captures", a["id"] + ".jpg"), quality=78, optimize=True)
                os.remove(tmp)
                print("  ok", a["id"])
            except Exception as e:
                print("  échec", a["id"], str(e)[:80])
            page.close()
        nav.close()


if __name__ == "__main__":
    main()
