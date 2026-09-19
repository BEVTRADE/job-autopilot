# Prompt — EPIC-8, validation du parcours de candidature

À coller dans Claude Code depuis le dossier du projet.

---

Tu traites EPIC-8, décrit dans docs/epics.md. Lis-le entièrement d'abord : la
section « Problème » explique pourquoi ce lot existe et ce qui a échoué.

Tu travailles sur le Mac, avec le réseau, Playwright, et une session Free-Work
déjà connectée dans le profil ~/.job-autopilot/browser-profile. Tu peux donc
observer le site réel toi-même. C'est tout l'enjeu : ne corrige plus rien sans
l'avoir vu dans le DOM.

Fichiers à lire : src/apply/freework.py, src/apply/base.py, scripts/apply.py,
et l'instantané data/output/2026-09-19/candidatures/depot-echec.html.

ÉTAPE 1 — LA SONDE
Écris scripts/sonde_freework.py. Elle ouvre l'offre
https://www.free-work.com/fr/tech-it/job-mission/architecte-de-base-de-donnees/architecte-de-domaine-simulation
avec le profil persistant, puis parcourt le formulaire étape par étape. À chaque
étape, enregistre le HTML et une capture pleine page dans
tests/pages/freework/<numéro>-<étape>.html et .png.

Étapes : page d'offre, panneau de candidature, modale Profil, modale CV à
l'ouverture, après clic sur « Ajouter un CV », après choix du fichier
clients/simulation-atos/03_cv/CV_Hakim_Arezki_Architecte_Domaine_Simulation.pdf,
après sélection d'une carte de CV, après confirmation, champs de questions
filtrantes s'il y en a, et la page « Mes candidatures ».

La sonde ne clique JAMAIS sur « Je postule ». Vérifie-le dans le code avant de
la lancer.

Lance-la, puis montre-moi la liste des instantanés produits et, pour chaque
étape, ce que tu observes : quels boutons existent, avec quels attributs.

ÉTAPE 2 — L'INVENTAIRE
Pour chaque entrée de SEL dans src/apply/freework.py, indique l'étape où elle
doit trouver un élément, et si elle le trouve réellement dans l'instantané. Pour
chaque sélecteur qui échoue ou qui est ambigu, propose le sélecteur correct, en
privilégiant data-testid, id ou name sur les libellés.

ÉTAPE 3 — LES TESTS
Écris tests/test_freework_dom.py : pour chaque sélecteur, un test charge
l'instantané de l'étape concernée et vérifie qu'il trouve exactement l'élément
attendu. Utilise Playwright sur page locale (page.set_content) ou un parseur
HTML, sans réseau. Les tests doivent échouer sur les sélecteurs actuellement
faux, avant correction.

ÉTAPE 4 — LA CORRECTION
Corrige src/apply/freework.py sur la base des instantanés. Les tests de
l'étape 3 doivent passer. Ajoute la cible make sonde au Makefile.

ÉTAPE 5 — LA DÉMONSTRATION
Lance la candidature en simulation, sans --envoyer :

.venv/bin/python scripts/apply.py --from clients/simulation-atos/cible.json --max 1 --min-fit 0 --cv-fichier clients/simulation-atos/03_cv/CV_Hakim_Arezki_Architecte_Domaine_Simulation.pdf

Le CV doit être déposé, sélectionné, confirmé et relu. Montre-moi la capture
finale. Si elle est propre, dis-le et ARRÊTE-TOI : c'est moi qui lance l'envoi
réel.

RÈGLES
- Aucun clic sur « Je postule » en dehors de ma demande explicite.
- Ne touche pas à src/matching/.
- Chaque correction de sélecteur doit citer l'instantané qui la justifie.
- Commit par étape, messages en français.
- Si tu es bloqué deux fois sur la même erreur, arrête-toi et explique.
