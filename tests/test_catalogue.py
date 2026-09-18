"""Passe catalogue (EPIC-4) : couverture, seuil de fréquence, hors profil."""
import json, os, sqlite3, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scripts.catalogue as catalogue

CATALOG = {
    "axes": [{
        "id": "TEST_AXE",
        "label": "Axe de test",
        "clusters": [0],
        "priority": 1,
        "titles": ["consultant test"],
        "core": ["python", "kubernetes"],
        "plus": ["docker"],
        "files": {"fr": "reprise/cv_finaux/FR_TEST.docx", "en": "reprise/cv_finaux/EN_TEST.docx"},
        "strategic_boost": 0,
    }],
    "aliases": {},
    "domain_exclusions": {
        "groups": {"comptabilite": ["comptabilite", "paie"]},
        "penalty_per_group": 18,
        "max_penalty": 36,
    },
}


def _fixture(tmp):
    src = os.path.join(tmp, "reprise", "cv_sources")
    os.makedirs(src, exist_ok=True)
    open(os.path.join(src, "FR_TEST.md"), "w", encoding="utf-8").write("mission conseil python")
    open(os.path.join(src, "EN_TEST.md"), "w", encoding="utf-8").write("consulting python")

    cat_path = os.path.join(tmp, "cv_catalog.json")
    json.dump(CATALOG, open(cat_path, "w", encoding="utf-8"))

    db_path = os.path.join(tmp, "candidatures.db")
    con = sqlite3.connect(db_path)
    con.executescript("""
        create table missions(aid integer primary key, title text, company text,
                               tjm_min integer, tjm_max integer);
        create table mission_skills(aid integer, skill text);
    """)
    missions = [
        (1, "Architecte IA", "Alpha", 700, 800),
        (2, "Architecte IA", "Beta", 600, 650),
        (3, "Architecte IA", "Gamma", 500, 550),
        (4, "Architecte IA", "Delta", 900, 950),
        (5, "Architecte IA", "Epsilon", 400, 420),
        (6, "Comptable senior", "Zeta", 300, 350),
    ]
    con.executemany("insert into missions values (?,?,?,?,?)", missions)
    skills = [
        # "Kubernetes" déjà couvert par le catalogue -> ne doit pas apparaître
        (1, "Kubernetes"),
        # "MLOps" absent, fréquent (5 missions) -> candidat
        (1, "MLOps"), (2, "MLOps"), (3, "MLOps"), (4, "MLOps"), (5, "MLOps"),
        # "COBOL" absent mais rare (1 mission) -> sous le seuil, ignoré
        (1, "COBOL"),
        # "Paie" absent, hors profil (groupe comptabilite), fréquent
        (6, "Paie"), (1, "Paie"), (2, "Paie"), (3, "Paie"), (4, "Paie"),
    ]
    con.executemany("insert into mission_skills values (?,?)", skills)
    con.commit()
    con.close()

    return cat_path, src, db_path


def test_couvert_absent_du_rapport():
    with tempfile.TemporaryDirectory() as tmp:
        cat_path, src, db_path = _fixture(tmp)
        catalogue.CATALOG, catalogue.SRC, catalogue.DB = cat_path, src, db_path
        res = catalogue.analyser(min_freq=5)
        termes = {r["terme"] for r in res["candidats"] + res["hors_profil"]}
        assert "Kubernetes" not in termes, "un terme déjà couvert ne doit pas être signalé"


def test_seuil_de_frequence():
    with tempfile.TemporaryDirectory() as tmp:
        cat_path, src, db_path = _fixture(tmp)
        catalogue.CATALOG, catalogue.SRC, catalogue.DB = cat_path, src, db_path
        res = catalogue.analyser(min_freq=5)
        termes = {r["terme"] for r in res["candidats"] + res["hors_profil"]}
        assert "COBOL" not in termes, "un terme vu une seule fois est sous le seuil"


def test_candidat_vs_hors_profil():
    with tempfile.TemporaryDirectory() as tmp:
        cat_path, src, db_path = _fixture(tmp)
        catalogue.CATALOG, catalogue.SRC, catalogue.DB = cat_path, src, db_path
        res = catalogue.analyser(min_freq=5)

        mlops = next(r for r in res["candidats"] if r["terme"] == "MLOps")
        assert mlops["frequence"] == 5
        assert mlops["tjm_median"] == 600  # médiane de 700,600,500,900,400
        assert mlops["exemple"]["societe"] == "Delta"  # tjm_min le plus haut

        paie = next(r for r in res["hors_profil"] if r["terme"] == "Paie")
        assert paie["groupes"] == ["comptabilite"]
        assert not any(r["terme"] == "Paie" for r in res["candidats"])


def test_classement_par_tjm_decroissant():
    with tempfile.TemporaryDirectory() as tmp:
        cat_path, src, db_path = _fixture(tmp)
        catalogue.CATALOG, catalogue.SRC, catalogue.DB = cat_path, src, db_path
        res = catalogue.analyser(min_freq=1)
        medianes = [r["tjm_median"] for r in res["candidats"]]
        assert medianes == sorted(medianes, reverse=True)
