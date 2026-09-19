"""Indeed : offres lues dans les alertes e-mail, candidature jamais automatisée."""
import json, os, sys, tempfile, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.sources.alertes_indeed import extraire, collecter, cle_offre
from src.apply import indeed as indeed_apply

JK1, JK2 = "a1b2c3d4e5f60718", "0f1e2d3c4b5a6978"


def _eml(expediteur="Indeed <alert@indeed.com>", corps=None):
    corps = corps or f"""
    <html><body>
      <a href="https://fr.indeed.com/rc/clk?jk={JK1}&amp;from=ja">Architecte Solutions IA &amp; Data</a>
      <a href="https://fr.indeed.com/viewjob?jk={JK2}">Tech Lead <b>MLOps</b></a>
      <a href="https://fr.indeed.com/rc/clk?jk={JK1}&amp;from=ja2">Architecte Solutions IA &amp; Data</a>
      <a href="https://fr.indeed.com/preferences">Gérer mes alertes</a>
      <a href="https://example.com/autre">Publicité</a>
    </body></html>"""
    return (f"From: {expediteur}\nTo: moi@example.com\nSubject: Nouvelles offres\n"
            f"Date: Sat, 19 Sep 2026 07:00:00 +0200\nMIME-Version: 1.0\n"
            f"Content-Type: text/html; charset=utf-8\n\n{corps}").encode("utf-8")


def test_extrait_les_offres_et_dedoublonne():
    offres = extraire(_eml())
    assert [o.title for o in offres] == ["Architecte Solutions IA & Data", "Tech Lead MLOps"]
    assert offres[0].url == f"https://fr.indeed.com/viewjob?jk={JK1}"
    assert all(o.source == "indeed" for o in offres)


def test_ignore_les_liens_sans_offre():
    titres = [o.title for o in extraire(_eml())]
    assert "Gérer mes alertes" not in titres and "Publicité" not in titres


def test_ignore_un_courriel_qui_ne_vient_pas_d_indeed():
    assert extraire(_eml(expediteur="Inconnu <x@example.com>")) == []


def test_cle_dans_un_lien_de_suivi_encode():
    lien = "https://track.example.com/c?url=" + "https%3A%2F%2Ffr.indeed.com%2Fviewjob%3Fjk%3D" + JK2
    assert cle_offre(lien) == JK2


def test_cle_invalide_refusee():
    assert cle_offre("https://fr.indeed.com/viewjob?jk=trop-court") is None


def test_collecte_dossier_dedoublonne_entre_courriels():
    with tempfile.TemporaryDirectory() as d:
        for i in range(2):
            open(os.path.join(d, f"a{i}.eml"), "wb").write(_eml())
        assert len(collecter(d)) == 2


def test_aucune_soumission_possible():
    assert indeed_apply.CAPACITES == frozenset({"preparer"})
    assert "soumettre" not in indeed_apply.Indeed.capacites


def test_postuler_ne_fait_que_journaliser_a_faire_manuel():
    import src.apply.base as base
    with tempfile.TemporaryDirectory() as d:
        ancien = base.ROOT
        base.ROOT = d
        try:
            r = indeed_apply.Indeed().postuler(f"https://fr.indeed.com/viewjob?jk={JK1}",
                                               "u1", "Architecte", cv="FR_ARCHITECTE_IA_GENAI.pdf")
        finally:
            base.ROOT = ancien
    assert r.status == "a_faire_manuel"
    assert "à la main" in r.detail and "FR_ARCHITECTE_IA_GENAI.pdf" in r.detail


def test_module_sans_acces_reseau():
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "src", "sources", "alertes_indeed.py"), encoding="utf-8").read()
    for interdit in ("urlopen", "requests", "http.client", "playwright", "goto("):
        assert interdit not in src, interdit
