"""Sélecteurs de src/apply/freework.py contre le DOM réel — EPIC-8.

Chaque test charge l'instantané de l'étape concernée
(tests/pages/freework/<n>-<étape>.html, produit par scripts/sonde_freework.py)
et vérifie que le sélecteur y trouve exactement l'élément attendu : le bon
bouton, pas le premier qui ressemble.

Aucun réseau : JavaScript désactivé et toute requête coupée. Le navigateur
ne sert qu'à évaluer les sélecteurs Playwright (:has-text, :has) sur une page
locale. Si le site évolue, `make sonde` régénère les instantanés et ces tests
disent quel sélecteur ne trouve plus son élément.
"""
import atexit, glob, os, re, sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
from src.apply import freework                       # noqa: E402
from src.apply.freework import SEL, BASE             # noqa: E402

PAGES = os.path.join(RACINE, "tests", "pages", "freework")
SIMU = "CV_Hakim_Arezki_Architecte_Domaine_Simulation.pdf"
REPOS = "FR_ARCHITECTE_ENTREPRISE_URBANISTE.pdf"
CV_ATTENDUS = ["EN_AI_GENAI_ARCHITECT.pdf", REPOS, "FR_DIRECTEUR_PROGRAMME_DATA_IA.pdf",
               "FR_ARCHITECTE_IA_GENAI.pdf", "CV_Hakim_Arezki_Architecte_IA_MLOps.pdf", SIMU]

_pw = _ctx = None
_pages: dict[int, object] = {}


def _arreter():
    if _ctx:
        _ctx.browser.close()
    if _pw:
        _pw.stop()


def page_de(etape: int):
    """Page Playwright chargée avec l'instantané de l'étape. Mise en cache."""
    global _pw, _ctx
    if etape in _pages:
        return _pages[etape]
    if _ctx is None:
        try:
            from playwright.sync_api import sync_playwright
            _pw = sync_playwright().start()
            navigateur = _pw.chromium.launch()
        except Exception as e:                                   # noqa: BLE001
            raise RuntimeError("Playwright/Chromium indisponible, les tests de DOM "
                               f"ne peuvent pas tourner (make install) : {e}") from e
        _ctx = navigateur.new_context(java_script_enabled=False)
        _ctx.route("**/*", lambda r: r.abort())
        atexit.register(_arreter)
    fichiers = glob.glob(os.path.join(PAGES, f"{etape:02d}-*.html"))
    assert len(fichiers) == 1, f"instantané de l'étape {etape} : {fichiers}"
    p = _ctx.new_page()
    p.set_content(open(fichiers[0], encoding="utf-8").read())
    _pages[etape] = p
    return p


def sel(cle: str) -> str:
    return SEL[cle]


def texte(loc) -> str:
    return re.sub(r"\s+", " ", loc.inner_text()).strip()


# ---------------------------------------------------------------- page d'offre

def test_message_une_zone_de_saisie_a_l_etape_2():
    loc = page_de(2).locator(sel("message"))
    assert loc.count() == 1
    assert loc.evaluate("e => e.tagName") == "TEXTAREA"


def test_submit_est_le_seul_je_postule_et_reste_hors_de_la_modale():
    for etape in (2, 4):                     # formulaire seul, puis modale ouverte
        loc = page_de(etape).locator(sel("submit"))
        assert loc.count() == 1, f"étape {etape}"
        assert texte(loc) == "Je postule"
        assert loc.evaluate("e => !e.closest('fw-modal')")


def test_editer_cv_est_le_bouton_du_cv_partage_pas_celui_du_profil():
    loc = page_de(2).locator(sel("editer_cv"))
    assert loc.count() == 1
    assert texte(loc) == "Éditer"
    # deux boutons « Éditer » coexistent, Profil puis CV : c'est le second
    tous = page_de(2).locator("form button:has-text('Éditer')")
    assert tous.count() == 2
    assert loc.evaluate("(a, b) => a === b", tous.nth(1).element_handle())


def test_cv_partage_lien_donne_le_nom_du_cv_partage():
    assert texte(page_de(2).locator(sel("cv_partage_lien"))) == REPOS
    assert page_de(2).locator(sel("cv_partage_lien")).count() == 1
    # après confirmation (étape 9), le lien désigne le CV de simulation
    assert texte(page_de(9).locator(sel("cv_partage_lien"))) == SIMU


def test_session_marqueur_present_connecte():
    for etape in (2, 11):
        assert page_de(etape).locator(sel("session")).count() == 1


# ---------------------------------------------------------------- modale des CV

def test_modale_cv_seulement_quand_ouverte():
    assert page_de(2).locator(sel("modale_cv")).count() == 0
    assert page_de(3).locator(sel("modale_cv")).count() == 0      # modale Profil : non
    for etape in (4, 5, 6, 7, 8):
        assert page_de(etape).locator(sel("modale_cv")).count() == 1, f"étape {etape}"
    assert page_de(9).locator(sel("modale_cv")).count() == 0      # refermée


def test_carte_fichier_six_cartes_dans_l_ordre():
    cartes = page_de(4).locator(sel("carte_fichier"))
    assert cartes.count() == len(CV_ATTENDUS)
    noms = [texte(cartes.nth(i).locator(sel("nom_fichier"))) for i in range(cartes.count())]
    assert noms == CV_ATTENDUS


def test_nom_fichier_une_seule_legende_par_carte():
    cartes = page_de(4).locator(sel("carte_fichier"))
    for i in range(cartes.count()):
        assert cartes.nth(i).locator(sel("nom_fichier")).count() == 1


def test_carte_fichier_absente_hors_de_la_modale():
    for etape in (2, 3, 9):
        assert page_de(etape).locator(sel("carte_fichier")).count() == 0, f"étape {etape}"


def test_ajouter_cv_est_le_bouton_ajouter_un_cv_pas_ajouter_un_document():
    loc = page_de(4).locator(sel("ajouter_cv"))
    assert loc.count() == 1
    assert texte(loc) == "Ajouter un CV"
    assert page_de(2).locator(sel("ajouter_cv")).count() == 0


def test_partager_cv_desactive_a_l_ouverture_actif_apres_selection():
    ouverture = page_de(4).locator(sel("partager_cv"))
    assert ouverture.count() == 1 and texte(ouverture) == "Partager le CV"
    assert ouverture.is_disabled()
    selection = page_de(8).locator(sel("partager_cv"))
    assert selection.count() == 1 and texte(selection) == "Partager le CV"
    assert selection.is_enabled()


def test_partager_cv_ne_confond_pas_avec_mettre_a_jour_du_profil():
    """Le 19/09, valider_modale prenait « Mettre à jour » dans la modale Profil."""
    assert page_de(3).locator(sel("partager_cv")).count() == 0
    assert page_de(3).locator(sel("envoyer_cv")).count() == 0


def test_parcourir_visible_a_l_ouverture_absent_quand_l_accordeon_est_ferme():
    ouverture = page_de(4).locator(sel("parcourir"))
    assert ouverture.count() == 1 and texte(ouverture) == "Parcourir…"
    assert page_de(5).locator(sel("parcourir")).count() == 0     # refermé par Ajouter un CV
    assert page_de(6).locator(sel("parcourir")).count() == 1


def test_envoyer_cv_inactif_puis_actif_apres_choix_du_fichier():
    avant = page_de(4).locator(sel("envoyer_cv"))
    assert avant.count() == 1 and texte(avant) == "Envoyer mon CV" and avant.is_disabled()
    apres = page_de(6).locator(sel("envoyer_cv"))
    assert apres.count() == 1 and texte(apres) == "Envoyer mon CV" and apres.is_enabled()
    assert page_de(5).locator(sel("envoyer_cv")).count() == 0


def test_partager_et_envoyer_sont_deux_boutons_distincts():
    """valider_modale renvoyait les deux : le sélecteur devait les séparer."""
    p = page_de(6)
    a, b = p.locator(sel("partager_cv")), p.locator(sel("envoyer_cv"))
    assert a.count() == 1 and b.count() == 1
    assert texte(a) != texte(b)


# ---------------------------------------------------------------- Mes candidatures

def test_url_mes_candidatures_est_celle_qui_ne_renvoie_pas_404():
    assert freework.CANDIDATURES == f"{BASE}/fr/applications"
    p = page_de(11)
    assert "404" not in texte(p.locator("body"))[:200]
    assert "Mes candidatures" in [texte(h) for h in p.locator("h1").all()]


# ---------------------------------------------------------------- garanties sur SEL

def test_toute_entree_de_SEL_est_couverte_par_un_test():
    """Critère 2 : chaque sélecteur de SEL a au moins un test sur instantané."""
    source = open(__file__, encoding="utf-8").read()
    non_couvertes = [k for k in SEL if f'sel("{k}")' not in source]
    assert not non_couvertes, f"entrées de SEL sans test : {non_couvertes}"


def test_aucune_entree_de_SEL_ne_repose_sur_un_libelle_sauf_parcourir():
    """Critère 3 : data-testid, id ou name plutôt qu'un libellé. Parcourir…
    n'a pas d'attribut propre : il est ancré sur le conteneur data-testid,
    le libellé ne sert qu'à le distinguer de « Changer »."""
    fautives = [k for k, v in SEL.items() if "has-text" in v and k != "parcourir"]
    assert not fautives, f"sélecteurs par libellé : {fautives}"
