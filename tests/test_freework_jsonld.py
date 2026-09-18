"""Extraction du corps d'annonce et de la société depuis le JSON-LD
JobPosting de Free-Work, plutôt que depuis le texte de la page entière.

Trouvé en vérifiant la collecte réelle d'EPIC-7 : le texte de page entier
(nav, pied de page, liens promotionnels, quasi identiques d'une annonce à
l'autre) polluait l'empreinte de contenu et provoquait un sur-regroupement
d'annonces sans rapport. Données figées, sans réseau.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.sources.base import html_to_text
from src.sources.freework import FreeWork

PAGE_AVEC_LD = """<!doctype html><html><head>
<script type="application/ld+json">
{"@context": "http://schema.org/", "@type": "JobPosting",
 "title": "Architecte d\\u2019Int\\u00e9gration SaaS",
 "description": "<p>Nous recherchons un architecte d&#039;int\\u00e9gration exp\\u00e9riment\\u00e9, mission chez un client final.</p><p><strong>Stack</strong> : Java, Kafka.</p>",
 "hiringOrganization": {"@type": "Organization", "name": "LENA IT"},
 "baseSalary": {"@type": "MonetaryAmount", "value": {"value": 750, "unitText": "DAY"}}}
</script>
</head><body>
<nav>Free Work — Nos offres emploi | Inscrivez-vous | Devenez Free Worker | CVthèque gratuite</nav>
<h1>Architecte d'Intégration SaaS</h1>
<footer>Free Work — Barometre IT — Forum — Blog — Toutes nos offres emploi freelance</footer>
</body></html>"""

PAGE_SANS_LD = """<!doctype html><html><body>
<h1>Architecte réseau</h1>
<p>Société : Craftman data</p>
<p>Mission de six mois pour un opérateur télécom.</p>
</body></html>"""


def test_descr_vient_du_json_ld_quand_present():
    ld = FreeWork._job_posting_ld(PAGE_AVEC_LD)
    assert ld is not None
    descr = FreeWork._descr_from(ld, html_to_text(PAGE_AVEC_LD))
    assert "Kafka" in descr
    assert "architecte d'intégration expérimenté" in descr.lower()
    # le bruit de page ne doit plus polluer le corps
    assert "Free Work" not in descr
    assert "CVthèque" not in descr
    assert "Barometre" not in descr


def test_company_vient_du_hiring_organization():
    ld = FreeWork._job_posting_ld(PAGE_AVEC_LD)
    company = FreeWork._company_from(ld, html_to_text(PAGE_AVEC_LD))
    assert company == "LENA IT"


def test_repli_sur_le_texte_de_page_sans_json_ld():
    ld = FreeWork._job_posting_ld(PAGE_SANS_LD)
    assert ld is None
    text = html_to_text(PAGE_SANS_LD)
    descr = FreeWork._descr_from(ld, text)
    company = FreeWork._company_from(ld, text)
    assert "Mission de six mois" in descr
    assert company == "Craftman data"


def test_json_ld_invalide_ne_plante_pas():
    page = '<script type="application/ld+json">{ceci n\'est pas du json}</script><h1>X</h1>'
    assert FreeWork._job_posting_ld(page) is None
