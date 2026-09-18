"""Regroupement des annonces par empreinte de contenu (EPIC-2).

Données figées, sans réseau : les trois cas réels documentés dans
data/output/2026-09-08, -09 et -15/veille.md, plus le cas inverse (deux
missions distinctes à titre proche qui ne doivent pas être regroupées).

L'empreinte porte sur le titre normalisé et le corps de l'annonce, jamais sur
l'URL ni sur le couple titre+société (docs/sources.md).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.sources.base import RawMission
from src.grouping import fingerprint, similarity, group_missions, MissionGroup


# --------------------------------------------------------------------------- #
#  Cas réel 1 — 8 septembre : AI Agent Architect, Meudon, trois intermédiaires
# --------------------------------------------------------------------------- #

MEUDON_NICHOLSON = RawMission(
    source="freework", url="https://free-work.com/m/meudon-nicholson",
    title="351 - AI Agent Architect", company="Nicholson SAS",
    tjm_min=500, tjm_max=500, loc="Meudon",
    descr=("Mission chez un grand opérateur télécom à Meudon. Conception et "
           "intégration de capacités agentiques pour automatiser les tâches "
           "opérationnelles des équipes IT Réseau. Stack attendue : LangChain, "
           "LangGraph, CrewAI, n8n, Airflow, Python, Docker, Kubernetes, "
           "MLflow, Bedrock ou Azure OpenAI. Trois jours sur site, deux jours "
           "de télétravail par semaine. Cinq à dix ans d'expérience, dont "
           "deux à trois ans sur des systèmes agentiques en production."))

MEUDON_CRAFTMAN = RawMission(
    source="freework", url="https://free-work.com/m/meudon-craftman",
    title="AI Agent Architect, Orchestration & IA agentique", company="Craftman data",
    tjm_min=300, tjm_max=500, loc="Meudon", dur_val=3, dur_per="mois",
    descr=("Pour un opérateur télécom basé à Meudon, nous recherchons un "
           "architecte capable de concevoir et d'intégrer des capacités "
           "agentiques afin d'automatiser les tâches opérationnelles des "
           "équipes IT Réseau. Environnement technique : LangChain, "
           "LangGraph, CrewAI, n8n, Airflow, Python, Docker, Kubernetes, "
           "MLflow, Bedrock ou Azure OpenAI. Rythme trois jours sur site à "
           "Meudon, deux jours de télétravail. Profil senior, cinq à dix "
           "ans, dont deux à trois ans d'agentique en production."))

MEUDON_SIGNEPLUS = RawMission(
    source="freework", url="https://free-work.com/m/meudon-signeplus",
    title="Architecte IA Agentique", company="Signe +",
    tjm_min=286, tjm_max=450, loc="Meudon", dur_val=24, dur_per="mois",
    descr=("Client final : opérateur télécom, site de Meudon. La mission "
           "consiste à concevoir et intégrer des capacités agentiques pour "
           "automatiser les tâches opérationnelles des équipes IT Réseau, "
           "sur la stack LangChain, LangGraph, CrewAI, n8n, Airflow, Python, "
           "Docker, Kubernetes, MLflow, avec Bedrock ou Azure OpenAI. "
           "Présence attendue trois jours par semaine à Meudon, deux jours "
           "en télétravail. Cinq à dix ans d'expérience requis, deux à "
           "trois ans sur l'agentique en production."))

MEUDON_GROUP = [MEUDON_NICHOLSON, MEUDON_CRAFTMAN, MEUDON_SIGNEPLUS]


# --------------------------------------------------------------------------- #
#  Cas réel 2 — 9 septembre : programme CSC VOLT / AMIA, deux grades
# --------------------------------------------------------------------------- #

VOLT_TECH_LEAD = RawMission(
    source="freework", url="https://free-work.com/m/volt-amia-techlead",
    title="Tech Lead IA, programme CSC VOLT / AMIA", company="Craftman data",
    tjm_min=500, tjm_max=640, loc="Colombes", dur_val=18, dur_per="mois",
    descr=("Pour la DSIN Commerce, dans le cadre du programme CSC VOLT / "
           "AMIA, concevoir et structurer un catalogue de compétences "
           "agentiques. Inventaire et qualification des composants "
           "agentiques, définition du processus d'onboarding et de "
           "publication, mise en place des chaînes CI/CD avec contrôles "
           "qualité et sécurité, revues de code, mise à disposition du "
           "catalogue auprès des équipes techniques et métiers. Stack : "
           "Python, TypeScript, Java, protocole MCP, JSON Schema, GitLab "
           "CI, SonarQube, DevSecOps. Cinq à dix ans d'expérience demandés."))

VOLT_IA_ENGINEER = RawMission(
    source="freework", url="https://free-work.com/m/volt-amia-engineer",
    title="IA Engineer CSC VOLT / AMIA", company="Craftman data",
    tjm_min=460, tjm_max=610, loc="Colombes", dur_val=18, dur_per="mois",
    descr=("Pour la DSIN Commerce, dans le cadre du programme CSC VOLT / "
           "AMIA, participer à la structuration du catalogue de compétences "
           "agentiques sous la supervision du tech lead. Inventaire et "
           "qualification des composants agentiques, contribution au "
           "processus d'onboarding et de publication, chaînes CI/CD avec "
           "contrôles qualité et sécurité, revues de code, mise à "
           "disposition du catalogue auprès des équipes techniques et "
           "métiers. Stack : Python, TypeScript, Java, protocole MCP, JSON "
           "Schema, GitLab CI, SonarQube, DevSecOps. Grade C, profil un peu "
           "moins senior."))

VOLT_GROUP = [VOLT_TECH_LEAD, VOLT_IA_ENGINEER]


# --------------------------------------------------------------------------- #
#  Cas réel 3 — 9 et 15 septembre : réassurance, KEONI contre CAT-AMANIA
# --------------------------------------------------------------------------- #

REASSURANCE_KEONI = RawMission(
    source="freework", url="https://free-work.com/m/reassurance-keoni",
    title="Consultant Expert Référent IA Senior", company="KEONI CONSULTING",
    tjm_min=750, tjm_max=750, loc="Paris", dur_val=18, dur_per="mois",
    descr=("Secteur réassurance. Identifier les opportunités d'intégration "
           "de l'IA auprès des directions métiers et des équipes IT, "
           "études de faisabilité, cadrage fonctionnel, pilotage des "
           "initiatives Data, Analytics et IA. Compétences attendues : "
           "architectures de données, IA générative, Machine Learning, NLP "
           "et analyse sémantique, connaissance des métiers de l'assurance. "
           "Plus de dix ans d'expérience, télétravail partiel, démarrage "
           "dès que possible."))

REASSURANCE_CATAMANIA = RawMission(
    source="freework", url="https://free-work.com/m/reassurance-catamania",
    title="Consultant Senior IA & Data - Réassurance", company="CAT-AMANIA",
    tjm_min=500, tjm_max=720, loc="Paris", dur_val=12, dur_per="mois",
    descr=("Secteur réassurance. Identifier les opportunités d'intégration "
           "de l'IA auprès des directions métiers et des équipes IT, "
           "études de faisabilité, cadrage fonctionnel, pilotage des "
           "initiatives Data, Analytics et IA. Compétences attendues : "
           "architectures de données, IA générative, Machine Learning, NLP "
           "et analyse sémantique, connaissance des métiers de l'assurance. "
           "Plus de dix ans d'expérience, télétravail partiel, démarrage "
           "dès que possible."))

REASSURANCE_GROUP = [REASSURANCE_KEONI, REASSURANCE_CATAMANIA]


# --------------------------------------------------------------------------- #
#  Cas inverse — deux missions distinctes, titres proches
#  "Architecte IA Agentique" (Signe +, Meudon, 8/09) et "Architecte IA
#  agentique" (Hexagone Digitale, Levallois, 26/08, cf. veille du 8/09
#  "Reste ouvert depuis les jours précédents") : même intitulé quasi
#  identique, client, lieu, secteur et stack totalement différents.
# --------------------------------------------------------------------------- #

LEVALLOIS_HEXAGONE = RawMission(
    source="freework", url="https://free-work.com/m/levallois-hexagone",
    title="Architecte IA Agentique", company="Hexagone Digitale",
    tjm_min=600, tjm_max=700, loc="Levallois-Perret",
    descr=("Client final : grand groupe de distribution, siège à "
           "Levallois-Perret. La mission consiste à définir l'architecture "
           "d'une plateforme IA interne mutualisée pour les directions "
           "métiers, gouvernance des modèles, catalogue de cas d'usage, "
           "choix de la stack MLOps, arbitrage build vs buy sur les briques "
           "IA générative. Environnement Azure, Databricks, MLflow, "
           "gouvernance des données. Dix ans d'expérience minimum, "
           "télétravail partiel, présentiel deux jours à Levallois."))


# --------------------------------------------------------------------------- #
#  Critère 1 — annonces de sociétés différentes décrivant la même mission
# --------------------------------------------------------------------------- #

def test_meudon_trois_intermediaires_regroupes():
    groups = group_missions(MEUDON_GROUP)
    assert len(groups) == 1
    assert {m.company for m in groups[0].missions} == {"Nicholson SAS", "Craftman data", "Signe +"}


def test_volt_amia_deux_grades_regroupes():
    groups = group_missions(VOLT_GROUP)
    assert len(groups) == 1
    assert len(groups[0].missions) == 2


def test_reassurance_keoni_catamania_regroupes():
    groups = group_missions(REASSURANCE_GROUP)
    assert len(groups) == 1
    assert {m.company for m in groups[0].missions} == {"KEONI CONSULTING", "CAT-AMANIA"}


# --------------------------------------------------------------------------- #
#  Critère 2 — cas inverse : titres proches, missions réellement distinctes
# --------------------------------------------------------------------------- #

def test_titres_proches_missions_distinctes_non_regroupees():
    groups = group_missions([MEUDON_SIGNEPLUS, LEVALLOIS_HEXAGONE])
    assert len(groups) == 2


def test_lot_complet_ne_croise_pas_les_groupes():
    """Les trois cas réels et le cas inverse mélangés ensemble : cinq
    groupes, pas de fuite d'un cas vers l'autre."""
    lot = MEUDON_GROUP + VOLT_GROUP + REASSURANCE_GROUP + [LEVALLOIS_HEXAGONE]
    groups = group_missions(lot)
    tailles = sorted(len(g.missions) for g in groups)
    assert tailles == [1, 2, 2, 3]


# --------------------------------------------------------------------------- #
#  Critère 3 — le groupe expose l'intermédiaire le mieux-disant et l'écart
# --------------------------------------------------------------------------- #

def test_meudon_meilleur_intermediaire_et_ecart():
    groups = group_missions(MEUDON_GROUP)
    grp = groups[0]
    assert grp.best.company in ("Nicholson SAS", "Craftman data")
    assert grp.best.tjm_max == 500
    assert grp.spread == 214           # 500 (haut) - 286 (bas), cf. veille du 8/09


def test_reassurance_meilleur_intermediaire_et_ecart():
    groups = group_missions(REASSURANCE_GROUP)
    grp = groups[0]
    assert grp.best.company == "KEONI CONSULTING"
    assert grp.spread == 250           # 750 - 500, cf. veille du 9/09


# --------------------------------------------------------------------------- #
#  Critère 4 — rien n'est supprimé ni masqué
# --------------------------------------------------------------------------- #

def test_aucune_annonce_supprimee():
    lot = MEUDON_GROUP + VOLT_GROUP + REASSURANCE_GROUP + [LEVALLOIS_HEXAGONE]
    groups = group_missions(lot)
    total = sum(len(g.missions) for g in groups)
    assert total == len(lot)


def test_chaque_annonce_garde_sa_societe_et_son_tjm():
    groups = group_missions(MEUDON_GROUP)
    par_societe = {m.company: (m.tjm_min, m.tjm_max) for m in groups[0].missions}
    assert par_societe["Nicholson SAS"] == (500, 500)
    assert par_societe["Craftman data"] == (300, 500)
    assert par_societe["Signe +"] == (286, 450)


# --------------------------------------------------------------------------- #
#  Empreinte : détail des fonctions
# --------------------------------------------------------------------------- #

def test_empreinte_insensible_aux_accents_et_a_la_casse():
    a = fingerprint("Architecte IA Générative", "Mission d'architecture IA générative RAG agents")
    b = fingerprint("architecte ia generative", "mission d architecture ia generative rag agents")
    assert similarity(a, b) == 1.0


def test_empreinte_missions_sans_rapport_similarite_nulle():
    a = fingerprint(MEUDON_NICHOLSON.title, MEUDON_NICHOLSON.descr)
    b = fingerprint(REASSURANCE_KEONI.title, REASSURANCE_KEONI.descr)
    assert similarity(a, b) < 0.1


# --------------------------------------------------------------------------- #
#  EPIC-7 — correctif 1 : écart calculé seulement sur les annonces avec TJM,
#  et nombre d'annonces sans TJM indiqué (docs/revues/epic2-empreinte.md)
# --------------------------------------------------------------------------- #

DATA_SEUL_TJM = RawMission(
    source="freework", url="https://free-work.com/m/dpo-axone",
    title="Data Product Owner Intermodal", company="AXONE BY SYNAPSE",
    tjm_min=600, tjm_max=650, loc="Paris",
    descr=("Data Product Owner pour une plateforme logistique intermodale. "
           "Pilotage du backlog produit data, cadrage des cas d'usage "
           "analytics, coordination avec les équipes ingénierie data et les "
           "métiers logistique. Compétences attendues : gouvernance de "
           "données, modélisation, animation d'ateliers, priorisation."))

DATA_SANS_TJM_A = RawMission(
    source="freework", url="https://free-work.com/m/dpo-skillwise",
    title="Data Product Owner Intermodal", company="SKILLWISE",
    tjm_min=None, tjm_max=None, loc="Paris",
    descr=("Data Product Owner pour une plateforme logistique intermodale. "
           "Pilotage du backlog produit data, cadrage des cas d'usage "
           "analytics, coordination avec les équipes ingénierie data et les "
           "métiers logistique. Compétences attendues : gouvernance de "
           "données, modélisation, animation d'ateliers, priorisation."))

DATA_SANS_TJM_B = RawMission(
    source="freework", url="https://free-work.com/m/dpo-hunteed",
    title="Data Product Owner Intermodal", company="HUNTEED",
    tjm_min=None, tjm_max=None, loc="Paris",
    descr=("Data Product Owner pour une plateforme logistique intermodale. "
           "Pilotage du backlog produit data, cadrage des cas d'usage "
           "analytics, coordination avec les équipes ingénierie data et les "
           "métiers logistique. Compétences attendues : gouvernance de "
           "données, modélisation, animation d'ateliers, priorisation."))


def test_ecart_non_calcule_avec_une_seule_annonce_a_tjm():
    """Une seule annonce affichant 600-650 ne doit pas rendre un écart de
    50 : ce serait la largeur de sa fourchette, pas un écart entre
    intermédiaires (revue EPIC-2, critère 1)."""
    groups = group_missions([DATA_SEUL_TJM, DATA_SANS_TJM_A, DATA_SANS_TJM_B])
    assert len(groups) == 1
    grp = groups[0]
    assert grp.spread is None
    assert grp.nb_sans_tjm == 2
    assert grp.best.company == "AXONE BY SYNAPSE"


def test_ecart_ignore_les_annonces_sans_tjm_quand_deux_ou_plus_en_ont():
    grp = group_missions(MEUDON_GROUP)[0]
    assert grp.nb_sans_tjm == 0
    assert grp.spread == 214


# --------------------------------------------------------------------------- #
#  EPIC-7 — correctif 2 : mieux-disant indéterminé si aucun TJM dans le groupe
# --------------------------------------------------------------------------- #

def test_mieux_disant_indetermine_sans_aucun_tjm():
    groups = group_missions([DATA_SANS_TJM_A, DATA_SANS_TJM_B])
    grp = groups[0]
    assert grp.best is None
    assert grp.spread is None
    assert grp.nb_sans_tjm == 2
    # le titre du groupe reste accessible même sans mieux-disant déterminé
    assert grp.title == "Data Product Owner Intermodal"


# --------------------------------------------------------------------------- #
#  EPIC-7 — correctif 4 (ajouté à la revue d'EPIC-2, garde-fou hors des
#  trois correctifs listés dans docs/epics.md) : dégradation trigramme ->
#  unigramme sur texte court, cause du mega-groupe de 293 annonces mesuré
#  sur les 1901 missions réelles (docs/revues/epic2-empreinte.md, critère 2)
# --------------------------------------------------------------------------- #

ARCHITECTE_SOLUTION_A = RawMission(
    source="freework", url="https://free-work.com/m/architecte-solution-a",
    title="Architecte Solution", company="STHREE", descr="")

ARCHITECTE_SOLUTION_B = RawMission(
    source="freework", url="https://free-work.com/m/architecte-solution-b",
    title="Architecte Solutions", company="VISIAN", descr="")


def test_titres_generiques_courts_sans_corps_non_regroupes():
    """Deux titres génériques et courts, sans corps, ne doivent jamais se
    regrouper : sans garde-fou, _shingles retombe sur des unigrammes et
    'architecte'/'solution(s)' suffisent à dépasser le seuil, amalgamant des
    métiers sans rapport (cause du mega-groupe de 293 annonces à l'échelle
    réelle)."""
    a = fingerprint(ARCHITECTE_SOLUTION_A.title, ARCHITECTE_SOLUTION_A.descr)
    b = fingerprint(ARCHITECTE_SOLUTION_B.title, ARCHITECTE_SOLUTION_B.descr)
    assert similarity(a, b) == 0.0
    groups = group_missions([ARCHITECTE_SOLUTION_A, ARCHITECTE_SOLUTION_B])
    assert len(groups) == 2


def test_garde_fou_ninterfere_pas_avec_les_cas_reels():
    """Le garde-fou ne doit pas casser les regroupements réels déjà
    couverts : ils ont assez de mots significatifs pour former des
    trigrammes."""
    for lot in (MEUDON_GROUP, VOLT_GROUP, REASSURANCE_GROUP):
        assert len(group_missions(lot)) == 1
