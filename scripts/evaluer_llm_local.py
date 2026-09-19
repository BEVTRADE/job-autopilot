#!/usr/bin/env python3
"""
Évaluation de la personnalisation du CV par un modèle local (EPIC-14, étape 4).

Lecture seule sur data/radar.db. N'envoie rien, n'ouvre aucun site, ne modifie aucun CV maître.
Tout est écrit dans data/output/eval-epic14/ (ignoré par git).

  evaluer_llm_local.py --selectionner              fige les 20 annonces (texte complet, 800 caractères minimum)
  evaluer_llm_local.py --modele M --passe 1        personnalise le CV d'axe pour chaque annonce, un seul modèle chargé
  evaluer_llm_local.py --revalider --passe 1       rejoue la validation sur les réponses brutes déjà enregistrées

La sortie brute du modèle est conservée : corriger le validateur ne demande pas de relancer le modèle.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, re, sqlite3, subprocess, sys, time, urllib.request
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
import yaml
from src.llm.local import LLMLocal
from src.cv import personnaliser as P

DOSSIER = os.path.join(RACINE, "data", "output", "eval-epic14")
MIN_CARS = 800
# 20 annonces : de quoi voir tous les CV d'axe, pas seulement le plus fréquent (78 des 99 éligibles sont « urbaniste »).
QUOTAS = {"FR_ARCHITECTE_IA_GENAI": 8, "FR_CONSULTANT_DATA_BI": 2, "EN_ENTERPRISE_ARCHITECT": 2,
          "FR_ARCHITECTE_ENTREPRISE_URBANISTE": 8}


def selectionner() -> list[dict]:
    """Annonces apply/shortlist au texte complet, réparties par CV d'axe, choix régulier et reproductible."""
    c = sqlite3.connect(f"file:{os.path.join(RACINE, 'data', 'radar.db')}?mode=ro", uri=True)
    par_cv: dict[str, list[dict]] = {}
    for uid, src, verdict, payload in c.execute(
            "select uid, source, verdict, payload from seen where verdict in ('apply','shortlist') order by uid"):
        d = json.loads(payload); raw, m = d["raw"], d["match"]
        descr = (raw.get("descr") or "").strip()
        if len(descr) < MIN_CARS:
            continue
        cv = os.path.basename(m["cv_path"])
        comp = raw.get("skills") or []
        texte = raw.get("title", "") + "\n" + (f"Compétences : {', '.join(comp)}\n" if comp else "") + "\n" + descr
        par_cv.setdefault(cv[:-5], []).append({"uid": uid, "source": src, "verdict": verdict, "cv": cv,
                                               "titre": raw.get("title", ""), "annonce": texte})
    choix = []
    for cv, n in QUOTAS.items():
        lot = par_cv.get(cv, [])
        pas = max(len(lot) / n, 1)
        choix += [lot[int(i * pas)] for i in range(min(n, len(lot)))]
    return choix


def memoire() -> dict:
    """État du poste : swap utilisé, mémoire libre, modèles chargés (taille en Go)."""
    swap = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True).stdout
    m = re.search(r"used = ([\d.]+)M", swap)
    libre = re.search(r"free percentage: (\d+)%",
                      subprocess.run(["memory_pressure"], capture_output=True, text=True).stdout)
    try:
        ps = json.load(urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5))["models"]
    except Exception:                                                     # noqa: BLE001
        ps = []
    return {"swap_utilise_mo": float(m.group(1)) if m else None, "memoire_libre_pct": int(libre.group(1)) if libre else None,
            "charge": [{"modele": x["name"], "taille_go": round(x["size"] / 1e9, 1),
                        "vram_go": round(x.get("size_vram", 0) / 1e9, 1)} for x in ps]}


def decharger_tout():
    for x in memoire()["charge"]:
        subprocess.run(["ollama", "stop", x["modele"]], capture_output=True)
    time.sleep(2)


class Enregistreur:
    """Enveloppe LLMLocal : garde la réponse brute du modèle, avant toute validation."""
    def __init__(self, llm): self.llm, self.brut = llm, None
    def json(self, *a, **k): self.brut = self.llm.json(*a, **k); return self.brut
    @property
    def mesure(self): return self.llm.mesure


def evaluer(modele: str, passe: str):
    cfg = yaml.safe_load(open(os.path.join(RACINE, "config.yaml"), encoding="utf-8"))
    cfg["llm"]["model"] = modele
    llm = LLMLocal.depuis_config(cfg)
    rec = Enregistreur(llm)
    sel = json.load(open(os.path.join(DOSSIER, "annonces.json"), encoding="utf-8"))
    profil = json.load(open(os.path.join(RACINE, "profile", "master_profile.json"), encoding="utf-8"))
    sortie = os.path.join(DOSSIER, f"passe{passe}", modele.replace(":", "_").replace("/", "_"))
    os.makedirs(sortie, exist_ok=True)
    decharger_tout()                                   # un seul modèle chargé à la fois
    resultats = []
    print(f"modèle {modele}, num_ctx {llm.num_ctx}, {len(sel)} annonces -> {sortie}", flush=True)
    for i, a in enumerate(sel, 1):
        avant = memoire(); rec.brut = None; llm.mesure = {}
        t0 = time.time()
        res = P.personnaliser(rec, os.path.join(RACINE, "cv_prets", a["cv"]),
                              os.path.join(sortie, f"CV_{i:02d}.docx"), a["annonce"], profil)
        total = round(time.time() - t0, 1)
        apres = memoire()
        r = {"n": i, "uid": a["uid"], "titre": a["titre"], "verdict": a["verdict"], "cv": a["cv"],
             "cars_annonce": len(a["annonce"]), "total_s": total, "brut": rec.brut,
             "mesure": dict(llm.mesure), "memoire_avant": avant, "memoire_apres": apres,
             **{k: v for k, v in res.items() if k != "docx"}}
        resultats.append(r)
        print(f"{i:2d}/{len(sel)} {a['cv'][:-5][:28]:28s} {total:6.1f} s  mode {res['mode']:6s} "
              f"prop {res['nb_propositions']} acc {len(res['appliquees'])} ref {len(res['refus'])}"
              + (f"  [{res['motif'][:70]}]" if "motif" in res else "")
              + f"  jetons {llm.mesure.get('jetons_prompt')}  swap {apres['swap_utilise_mo']} Mo", flush=True)
        json.dump(resultats, open(os.path.join(sortie, "resultats.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    subprocess.run(["ollama", "stop", modele], capture_output=True)   # libère la mémoire pour le suivant


def revalider(passe: str):
    """Rejoue valider() sur les réponses brutes enregistrées, avec le code actuel du validateur."""
    profil = json.load(open(os.path.join(RACINE, "profile", "master_profile.json"), encoding="utf-8"))
    sel = {a["uid"]: a for a in json.load(open(os.path.join(DOSSIER, "annonces.json"), encoding="utf-8"))}
    for dossier in sorted(os.listdir(os.path.join(DOSSIER, f"passe{passe}"))):
        chemin = os.path.join(DOSSIER, f"passe{passe}", dossier, "resultats.json")
        if not os.path.exists(chemin):
            continue
        sortie = []
        for r in json.load(open(chemin, encoding="utf-8")):
            if not isinstance(r.get("brut"), dict):
                continue
            z = P.zone(os.path.join(RACINE, "cv_prets", sel[r["uid"]]["cv"]))
            ok, refus = P.valider(r["brut"], z, P.vocabulaire(profil, *z))
            sortie.append({"n": r["n"], "acceptees": ok, "refus": refus})
        json.dump(sortie, open(os.path.join(DOSSIER, f"passe{passe}", dossier, "revalidation.json"), "w",
                               encoding="utf-8"), ensure_ascii=False, indent=1)
        print(dossier, "acceptées", sum(len(s["acceptees"]) for s in sortie),
              "refusées", sum(len(s["refus"]) for s in sortie))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selectionner", action="store_true")
    ap.add_argument("--modele"); ap.add_argument("--passe", default="1")
    ap.add_argument("--revalider", action="store_true")
    a = ap.parse_args()
    os.makedirs(DOSSIER, exist_ok=True)
    if a.selectionner:
        s = selectionner()
        json.dump(s, open(os.path.join(DOSSIER, "annonces.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(s), "annonces retenues :", {c: sum(1 for x in s if x["cv"][:-5] == c) for c in QUOTAS})
        print("verdicts :", {v: sum(1 for x in s if x["verdict"] == v) for v in ("apply", "shortlist")},
              "| sources :", {v: sum(1 for x in s if x["source"] == v) for v in {x["source"] for x in s}})
        print("longueur (caractères) min/max :", min(len(x["annonce"]) for x in s), max(len(x["annonce"]) for x in s))
    elif a.revalider:
        revalider(a.passe)
    elif a.modele:
        evaluer(a.modele, a.passe)
    else:
        ap.print_help(); sys.exit(2)
