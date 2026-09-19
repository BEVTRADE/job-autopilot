#!/usr/bin/env python3
"""
Vérification de la chaîne « modèle local + MCP » sur ce poste. N'envoie rien,
n'ouvre aucun site, ne modifie aucun CV maître : tout est écrit dans
data/output/<date>/verif-llm/.

  1. serveur Ollama joignable, version, modèle présent
  2. réponse JSON conforme au schéma, temps mesuré
  3. serveur MCP docx : démarrage, nombre d'outils, poids des descriptions
  4. serveur MCP Playwright : démarrage et outils (sans navigation)
  5. bout en bout : CV d'axe + annonce d'exemple -> CV adapté + PDF
"""
from __future__ import annotations
import asyncio, datetime as dt, json, os, shutil, sys, time
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
import yaml
from src.llm.local import LLMLocal, LLMIndisponible
from src.cv import personnaliser as P
from src.cv.docx_mcp import commande_serveur

ANNONCE = """Lead MLOps / Architecte IA — mission freelance, Paris, 12 mois.
Industrialisation de modèles et d'agents LLM, pipelines CI/CD, Kubernetes,
observabilité, gouvernance des modèles en environnement bancaire régulé."""
bilan = []


def etape(nom, ok, detail=""):
    bilan.append((nom, ok)); print(f"[{'ok ' if ok else 'KO '}] {nom}{' — ' + detail if detail else ''}")
    return ok


async def outils(cmd, args):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    async with stdio_client(StdioServerParameters(command=cmd, args=args)) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            t = (await s.list_tools()).tools
            return len(t), len(json.dumps([{"n": x.name, "d": x.description, "s": x.inputSchema} for x in t])) // 4


def main():
    cfg = yaml.safe_load(open(os.path.join(RACINE, "config.yaml"), encoding="utf-8"))
    if "--modele" in sys.argv:                       # ex. --modele mistral-small3.2:24b
        cfg["llm"]["model"] = sys.argv[sys.argv.index("--modele") + 1]
    try:
        llm = LLMLocal.depuis_config(cfg)
    except ValueError as e:
        etape("configuration llm", False, str(e)); return 2
    try:
        v = llm._post("/api/version").get("version", "?")
        etape("serveur Ollama", True, f"version {v} sur {llm.base_url}")
    except LLMIndisponible as e:
        etape("serveur Ollama", False, f"{e} — lancez l'application Ollama ou « ollama serve »"); return 2
    ok, motif = llm.disponible()
    if not etape(f"modèle {llm.model}", ok, motif if not ok else f"contexte demandé {llm.num_ctx}"):
        return 2
    t0 = time.time()
    try:
        r = llm.json("Réponds en JSON.", "Donne deux compétences MLOps.",
                     {"type": "object", "properties": {"competences": {"type": "array", "items": {"type": "string"}}},
                      "required": ["competences"]})
        etape("sortie JSON contrainte", isinstance(r.get("competences"), list), f"{time.time()-t0:.1f} s : {r}")
    except LLMIndisponible as e:
        etape("sortie JSON contrainte", False, str(e))

    cmd, args = commande_serveur()
    try:
        n, jetons = asyncio.run(outils(cmd, args))
        etape("MCP docx-mcp-server", n > 0, f"{n} outils, ~{jetons} jetons de description"
              + (" — trop pour un modèle local : n'exposer que OUTILS_AGENT" if jetons > 4000 else ""))
    except Exception as e:                                               # noqa: BLE001
        etape("MCP docx-mcp-server", False, f"{type(e).__name__}: {e} — pip install 'mcp<2' docx-mcp-server")

    npx = shutil.which("npx")
    if npx:
        try:
            n, jetons = asyncio.run(outils(npx, ["-y", "@playwright/mcp@latest", "--headless", "--isolated"]))
            etape("MCP Playwright", n > 0, f"{n} outils, ~{jetons} jetons — usage réservé aux sondes (ADR-011)")
        except Exception as e:                                           # noqa: BLE001
            etape("MCP Playwright", False, f"{type(e).__name__}: {e}")
    else:
        etape("MCP Playwright", False, "npx absent (facultatif)")

    cv = os.path.join(RACINE, "cv_prets", cfg.get("llm", {}).get("cv_test", "FR_ARCHITECTE_IA_GENAI.docx"))
    sortie = os.path.join(RACINE, "data", "output", dt.date.today().isoformat(), "verif-llm",
                          llm.model.replace(":", "_").replace("/", "_"))
    os.makedirs(sortie, exist_ok=True)
    profil = json.load(open(os.path.join(RACINE, "profile", "master_profile.json"), encoding="utf-8"))
    t0 = time.time()
    res = P.personnaliser(llm, cv, os.path.join(sortie, "CV_verif.docx"), ANNONCE, profil)
    json.dump(res, open(os.path.join(sortie, "bilan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    etape("bout en bout", res["mode"] in ("adapte", "axe") and "motif" not in res,
          f"{time.time()-t0:.0f} s dont modèle {res['duree_modele_s']} s, mode {res['mode']}, "
          f"{res['nb_propositions']} proposée(s), {len(res['appliquees'])} acceptée(s), "
          f"{len(res['refus'])} refusée(s), écarts {res['ecarts']}"
          + (f", écarts à tort {res['ecarts_a_tort']}" if res["ecarts_a_tort"] else "")
          + (f" — {res['motif']}" if "motif" in res else ""))
    for a in res["appliquees"]:
        print(f"      « {a['avant']} » -> « {a['apres']} »")
    for r in res["refus"]:
        print(f"      refus : « {r.get('apres')} » ({r.get('motif')})")
    try:
        from src.cv.render import to_pdf
        pdf = to_pdf(res["docx"], sortie); etape("PDF", True, pdf)
    except Exception as e:                                               # noqa: BLE001
        etape("PDF", False, str(e))
    ko = [n for n, ok in bilan if not ok and n != "MCP Playwright"]
    reussies = sum(1 for _, ok in bilan if ok)
    print(f"\n{reussies}/{len(bilan)} vérifications réussies (Playwright facultatif). Modèle {llm.model}. Fichiers : {sortie}")
    return 1 if ko else 0


if __name__ == "__main__":
    sys.exit(main())
