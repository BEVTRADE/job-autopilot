"""Rapport du matin : ne rien inventer, tout remonter."""
import json, os, sys, tempfile, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import src.report.digest as digest


def _fixture(tmp, jour):
    os.makedirs(os.path.join(tmp, "data", "output", jour), exist_ok=True)
    journal = os.path.join(tmp, "data", "journal.jsonl")
    lignes = [
        {"uid": "a", "url": "http://x/a", "title": "Architecte IA", "status": "envoyee",
         "detail": "confirmée", "cv": "FR_ARCHITECTE_IA_GENAI.pdf",
         "horodatage": f"{jour}T08:12:00"},
        {"uid": "b", "url": "http://x/b", "title": "Tech Lead IA", "status": "bloquee",
         "detail": "question sans réponse en banque", "cv": None,
         "horodatage": f"{jour}T08:20:00"},
        {"uid": "c", "url": "http://x/c", "title": "Vieux truc", "status": "envoyee",
         "detail": "", "cv": None, "horodatage": "2020-01-01T08:00:00"},
    ]
    with open(journal, "w", encoding="utf-8") as f:
        for l in lignes:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
    retenues = [
        {"match": {"decision_score": 80, "title": "Architecte IA"}, "raw": {"url": "http://x/a"}},
        {"match": {"decision_score": 74, "title": "Tech Lead IA"}, "raw": {"url": "http://x/b"}},
        {"match": {"decision_score": 71, "title": "Non tentée"}, "raw": {"url": "http://x/z"}},
    ]
    json.dump(retenues, open(os.path.join(tmp, "data", "output", jour, "retenues.json"),
                             "w", encoding="utf-8"))


def test_rapport_complet():
    jour = dt.date.today().isoformat()
    with tempfile.TemporaryDirectory() as tmp:
        digest.ROOT = tmp
        _fixture(tmp, jour)
        texte, brut = digest.construire(jour)
        assert brut["tentees"] == 2, "le journal d'une autre date a fui dans le rapport"
        assert brut["retenues"] == 3
        assert brut["compte"]["envoyee"] == 1
        assert brut["compte"]["bloquee"] == 1
        assert len(brut["attente"]) == 1
        assert "Non tentée" in texte
        assert "À reprendre à la main" in texte


def test_jour_vide():
    with tempfile.TemporaryDirectory() as tmp:
        digest.ROOT = tmp
        texte, brut = digest.construire("2026-01-01")
        assert brut["tentees"] == 0 and brut["retenues"] == 0
        assert "n'a probablement pas tourné" in texte


def test_ecriture_fichiers():
    jour = dt.date.today().isoformat()
    with tempfile.TemporaryDirectory() as tmp:
        digest.ROOT = tmp
        _fixture(tmp, jour)
        md, js = digest.ecrire(jour)
        assert os.path.exists(md) and os.path.exists(js)
        assert json.load(open(js, encoding="utf-8"))[0]["titre"] == "Tech Lead IA"
