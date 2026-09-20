#!/usr/bin/env python3
"""
Évaluation de la personnalisation du CV par un modèle local (EPIC-14, étape 4).

Lecture seule sur data/radar.db. N'envoie rien, n'ouvre aucun site, ne modifie aucun CV maître.
Tout est écrit dans data/output/eval-epic14/ (ignoré par git).

  --selectionner       fige les 20 annonces (apply/shortlist, texte complet, 800 caractères minimum)
  --complement         8 annonces de plus (3 axe programme, 3 « lead », 2 « urbaniste »), texte >= 800 caractères
  --biais              3 passes sur les 20 annonces, ordre des titres alternatifs mélangé à chaque passe (graines 1, 2, 3),
                       « inchangé » toujours présenté en tête ; mesure la stabilité du titre choisi par annonce
  --final              version finale (garde de rôle, résumé figé) sur les 28 annonces, prises en ordre mélangé
                       (graine 20260920) pour mêler les axes ; les titres restent dans l'ordre du fichier

Le modèle est celui de config.yaml (llm.model). Un seul modèle chargé à la fois.
Modes retirés : la rédaction libre (passe1/, passe2/) et la référence TF-IDF (selection/), dont les résultats
restent dans docs/revues/epic14-evaluation.md.
"""
from __future__ import annotations
import argparse, json, os, random, re, sqlite3, statistics, subprocess, sys, time, urllib.request
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


MOT_ROLE = re.compile(r"projet|programme|pmo|directeur|delivery|chef|manager|pilot|transformation", re.I)
GRAINE_FINALE = 20260920
GRAINES_BIAIS = (1, 2, 3)


def _texte(raw: dict) -> str:
    comp = raw.get("skills") or []
    return raw.get("title", "") + "\n" + (f"Compétences : {', '.join(comp)}\n" if comp else "") + "\n" + (raw.get("descr") or "").strip()


def complement() -> list[dict]:
    """8 annonces de plus, texte >= 800 caractères, absentes des 20 premières, choisies à intervalle régulier par uid :
    3 dont l'axe est « programme » (avec un mot de rôle au titre, sinon l'annonce ne teste pas l'axe), 3 dont le titre
    contient « lead », 2 dont le TEXTE mentionne « urbaniste » (aucune annonce n'a ce mot au titre dans radar.db)."""
    deja = {a["uid"] for a in json.load(open(os.path.join(DOSSIER, "annonces.json"), encoding="utf-8"))}
    c = sqlite3.connect(f"file:{os.path.join(RACINE, 'data', 'radar.db')}?mode=ro", uri=True)
    lots: dict[str, list[dict]] = {"programme": [], "lead": [], "urbaniste": []}
    for uid, src, verdict, payload in c.execute("select uid, source, verdict, payload from seen order by uid"):
        d = json.loads(payload); raw, m = d["raw"], d["match"]
        descr, titre = (raw.get("descr") or "").strip(), raw.get("title", "")
        if len(descr) < MIN_CARS or uid in deja:
            continue
        a = {"uid": uid, "source": src, "verdict": verdict, "cv": os.path.basename(m["cv_path"]), "titre": titre,
             "annonce": _texte(raw), "axe_annonce": m["axis_id"]}
        if m["axis_id"] == "DIRECTEUR_PROGRAMME_DATA_IA" and MOT_ROLE.search(titre):
            lots["programme"].append({**a, "groupe": "programme"})
        if re.search(r"\blead\b", titre, re.I):
            lots["lead"].append({**a, "groupe": "lead"})
        if re.search(r"urbaniste", descr, re.I):
            lots["urbaniste"].append({**a, "groupe": "urbaniste"})
    choix, pris = [], set()
    for groupe, n in (("programme", 3), ("lead", 3), ("urbaniste", 2)):
        lot = [a for a in lots[groupe] if a["uid"] not in pris]
        pas = max(len(lot) / n, 1)
        for i in range(min(n, len(lot))):
            choix.append(lot[int(i * pas)]); pris.add(lot[int(i * pas)]["uid"])
    return choix


def executer(modele: str, annonces: list[dict], sortie: str, graine_options: int | None = None, verbeux: bool = True) -> list[dict]:
    """personnaliser() sur chaque annonce, dans l'ordre donné. `graine_options` mélange les titres alternatifs."""
    cfg = yaml.safe_load(open(os.path.join(RACINE, "config.yaml"), encoding="utf-8"))
    cfg["llm"]["model"] = modele
    llm = LLMLocal.depuis_config(cfg)
    rec = Enregistreur(llm)
    profil = json.load(open(os.path.join(RACINE, "profile", "master_profile.json"), encoding="utf-8"))
    os.makedirs(sortie, exist_ok=True)
    rng = random.Random(graine_options) if graine_options is not None else None
    resultats = []
    for i, a in enumerate(annonces, 1):
        avant = memoire(); rec.brut = None; llm.mesure = {}
        t0 = time.time()
        res = P.personnaliser(rec, os.path.join(RACINE, "cv_prets", a["cv"]), os.path.join(sortie, f"CV_{a['n']:02d}.docx"),
                              a["annonce"], profil, titre_annonce=a["titre"], melange=rng)
        r = {"n": a["n"], "uid": a["uid"], "titre_annonce": a["titre"], "groupe": a.get("groupe"), "verdict": a["verdict"],
             "cv": a["cv"], "cars_annonce": len(a["annonce"]), "total_s": round(time.time() - t0, 1), "brut": rec.brut,
             "mesure": dict(llm.mesure), "memoire_avant": avant, "memoire_apres": memoire(), "graine_options": graine_options,
             **{k: v for k, v in res.items() if k != "docx"}}
        resultats.append(r)
        if verbeux:
            print(f"{i:2d}/{len(annonces)} n°{a['n']:<2d} {a['cv'][:-5][:22]:22s} {r['total_s']:5.1f} s  {r['mode']:6s} "
                  f"« {(r.get('titre_apres') or '-')[:44]} »  ordre {r.get('ordre')}"
                  + (f"  GARDE({r['garde_role']['titre_refuse'][:30]})" if (r.get("garde_role") or {}).get("titre_refuse") else "")
                  + (f"  [{r['motif'][:60]}]" if r.get("motif") else ""), flush=True)
        json.dump(resultats, open(os.path.join(sortie, "resultats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return resultats


def _numeroter(annonces: list[dict], debut: int = 1) -> list[dict]:
    return [{**a, "n": debut + i} for i, a in enumerate(annonces)]


def _charger(nom: str) -> list[dict]:
    return json.load(open(os.path.join(DOSSIER, nom), encoding="utf-8"))


def biais(modele: str):
    """3 passes, titres alternatifs mélangés à chaque passe. Stabilité : même titre du modèle sur les 3 passes."""
    annonces = _numeroter(_charger("annonces.json"))
    decharger_tout()
    passes = {}
    for g in GRAINES_BIAIS:
        print(f"--- passe, graine {g}", flush=True)
        passes[g] = executer(modele, annonces, os.path.join(DOSSIER, "biais", f"graine{g}", modele.replace(":", "_")), graine_options=g)
    par_annonce = []
    for k, a in enumerate(annonces):
        modele_ = [passes[g][k]["titre_modele"] for g in GRAINES_BIAIS]
        final = [passes[g][k]["titre_apres"] for g in GRAINES_BIAIS]
        rang = []
        for g in GRAINES_BIAIS:
            o = passes[g][k].get("options") or []
            t = passes[g][k]["titre_modele"]
            rang.append(o.index(t) if t in o else 0)         # 0 = « inchangé » (titre actuel), 1 = première alternative…
        par_annonce.append({"n": a["n"], "titre_annonce": a["titre"], "titres_modele": modele_, "titres_ecrits": final,
                            "rang_choisi": rang, "stable_modele": len(set(modele_)) == 1, "stable_ecrit": len(set(final)) == 1,
                            "ordres": [passes[g][k]["ordre"] for g in GRAINES_BIAIS]})
    bilan = {"graines": list(GRAINES_BIAIS), "stables_titre_modele": sum(x["stable_modele"] for x in par_annonce),
             "stables_titre_ecrit": sum(x["stable_ecrit"] for x in par_annonce), "annonces": par_annonce,
             "part_premiere_alternative": [round(sum(1 for x in par_annonce if x["rang_choisi"][j] == 1) / len(par_annonce), 2) for j in range(3)],
             "duree_mediane_s": [statistics.median(r["total_s"] for r in passes[g]) for g in GRAINES_BIAIS]}
    json.dump(bilan, open(os.path.join(DOSSIER, "biais", "stabilite.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nstables (titre choisi par le modèle, 3 passes) : {bilan['stables_titre_modele']} / {len(annonces)}"
          f" ; titre écrit après garde : {bilan['stables_titre_ecrit']} / {len(annonces)}")
    subprocess.run(["ollama", "stop", modele], capture_output=True)


def final(modele: str):
    """Version finale sur 20 + 8 annonces, ordre des annonces mélangé, titres dans l'ordre du fichier."""
    annonces = _numeroter(_charger("annonces.json")) + _numeroter(_charger("annonces_complement.json"), 21)
    ordre = list(annonces); random.Random(GRAINE_FINALE).shuffle(ordre)
    decharger_tout()
    print(f"{len(ordre)} annonces, ordre mélangé (graine {GRAINE_FINALE}) : {[a['n'] for a in ordre]}", flush=True)
    res = executer(modele, ordre, os.path.join(DOSSIER, "finale", modele.replace(":", "_")))
    json.dump({"graine_ordre": GRAINE_FINALE, "ordre_de_passage": [a["n"] for a in ordre]},
              open(os.path.join(DOSSIER, "finale", "ordre.json"), "w"), indent=1)
    subprocess.run(["ollama", "stop", modele], capture_output=True)


def _modele() -> str:
    return yaml.safe_load(open(os.path.join(RACINE, "config.yaml"), encoding="utf-8"))["llm"]["model"]


def _garde_validee():
    statut = json.load(open(P.TITRES, encoding="utf-8")).get("_statut", "")
    if not statut.startswith("VALIDÉ"):
        sys.exit(f"liste de titres non validée par le candidat ({statut!r}) : évaluation refusée")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for opt in ("--selectionner", "--complement", "--biais", "--final"):
        ap.add_argument(opt, action="store_true")
    a = ap.parse_args()
    os.makedirs(DOSSIER, exist_ok=True)
    if a.selectionner:
        s = selectionner()
        json.dump(s, open(os.path.join(DOSSIER, "annonces.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(len(s), "annonces retenues :", {c: sum(1 for x in s if x["cv"][:-5] == c) for c in QUOTAS})
    elif a.complement:
        s = complement()
        json.dump(s, open(os.path.join(DOSSIER, "annonces_complement.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        for x in s:
            print(f"{x['groupe']:9s} {x['verdict']:9s} {x['cv'][:-5][:30]:30s} {len(x['annonce']):5d} car.  {x['titre'][:70]}")
    elif a.biais:
        _garde_validee(); biais(_modele())
    elif a.final:
        _garde_validee(); final(_modele())
    else:
        ap.print_help(); sys.exit(2)
