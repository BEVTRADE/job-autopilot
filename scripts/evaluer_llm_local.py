#!/usr/bin/env python3
"""
Évaluation de la personnalisation du CV par un modèle local (EPIC-14, étape 4).

Lecture seule sur data/radar.db. N'envoie rien, n'ouvre aucun site, ne modifie aucun CV maître.
Tout est écrit dans data/output/eval-epic14/ (ignoré par git).

  evaluer_llm_local.py --selectionner     fige les 20 annonces (texte complet, 800 caractères minimum)
  evaluer_llm_local.py --modele M         SÉLECTION (décision du 20/09) : titre choisi dans profile/titres_autorises.json
                                          et ordre de l'accroche, un seul modèle chargé, résultats dans selection/
  evaluer_llm_local.py --reference        même sélection sans modèle (TF-IDF), pour comparer
  L'ancien mode (rédaction libre, validateur de vocabulaire) est retiré ; ses résultats restent dans
  passe1/ et passe2/ et dans docs/revues/epic14-evaluation.md.
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


def evaluer(modele: str | None):
    """Une exécution par annonce : avec `modele`, personnaliser() ; sans modèle, la référence TF-IDF seule."""
    cfg = yaml.safe_load(open(os.path.join(RACINE, "config.yaml"), encoding="utf-8"))
    sel = json.load(open(os.path.join(DOSSIER, "annonces.json"), encoding="utf-8"))
    profil = json.load(open(os.path.join(RACINE, "profile", "master_profile.json"), encoding="utf-8"))
    etiquette = (modele or "reference-tfidf").replace(":", "_").replace("/", "_")
    sortie = os.path.join(DOSSIER, "selection", etiquette)
    os.makedirs(sortie, exist_ok=True)
    if modele:
        cfg["llm"]["model"] = modele
        llm = LLMLocal.depuis_config(cfg)
        rec = Enregistreur(llm)
        decharger_tout()                               # un seul modèle chargé à la fois
        print(f"modèle {modele}, num_ctx {llm.num_ctx}, {len(sel)} annonces -> {sortie}", flush=True)
    resultats = []
    for i, a in enumerate(sel, 1):
        cv = os.path.join(RACINE, "cv_prets", a["cv"])
        if not modele:
            _, _, titres = P.titres_du_cv(cv)
            actuel = P.zone(cv)[0][1]
            t0 = time.time()
            ref = P.reference_titre(a["annonce"], [actuel] + [t for t in titres if t != actuel])
            r = {"n": i, "uid": a["uid"], "titre_annonce": a["titre"], "cv": a["cv"], "titre_avant": actuel,
                 "titre_reference": ref, "total_s": round(time.time() - t0, 3)}
        else:
            avant = memoire(); rec.brut = None; llm.mesure = {}
            t0 = time.time()
            res = P.personnaliser(rec, cv, os.path.join(sortie, f"CV_{i:02d}.docx"), a["annonce"], profil)
            total = round(time.time() - t0, 1)
            r = {"n": i, "uid": a["uid"], "titre_annonce": a["titre"], "verdict": a["verdict"], "cv": a["cv"],
                 "cars_annonce": len(a["annonce"]), "total_s": total, "brut": rec.brut, "mesure": dict(llm.mesure),
                 "memoire_avant": avant, "memoire_apres": memoire(), **{k: v for k, v in res.items() if k != "docx"}}
        resultats.append(r)
        print(f"{i:2d}/{len(sel)} {a['cv'][:-5][:24]:24s} {r['total_s']:6.1f} s  mode {r.get('mode', '-'):6s} "
              f"titre « {(r.get('titre_apres') or r['titre_reference'])[:52]} »  ordre {r.get('ordre')}"
              + (f"  [{r['motif'][:60]}]" if r.get("motif") else ""), flush=True)
        json.dump(resultats, open(os.path.join(sortie, "resultats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if modele:
        subprocess.run(["ollama", "stop", modele], capture_output=True)   # libère la mémoire pour le suivant


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selectionner", action="store_true")
    ap.add_argument("--modele"); ap.add_argument("--reference", action="store_true")
    a = ap.parse_args()
    os.makedirs(DOSSIER, exist_ok=True)
    if a.selectionner:
        s = selectionner()
        json.dump(s, open(os.path.join(DOSSIER, "annonces.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(s), "annonces retenues :", {c: sum(1 for x in s if x["cv"][:-5] == c) for c in QUOTAS})
    elif a.reference:
        evaluer(None)
    elif a.modele:
        evaluer(a.modele)
    else:
        ap.print_help(); sys.exit(2)
