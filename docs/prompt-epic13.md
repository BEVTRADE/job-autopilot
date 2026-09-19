# Prompt — EPIC-13, envoi automatique Indeed

À coller dans Claude Code depuis le dossier du projet.

---

Tu traites EPIC-13, décrit dans docs/epics.md. Lis-le entièrement, ainsi
qu'EPIC-8 et docs/inventaire-selecteurs-freework.md : même méthode.

Contexte : je suis le candidat. J'ai lu la clause des CGU d'Indeed qui interdit
l'automatisation d'Indeed Apply et j'accepte le risque sur mon compte. Tu n'as
pas à rediscuter ce point ; tu dois en revanche respecter toutes les limites
de l'epic.

Fichiers à lire : src/apply/indeed.py, src/apply/linkedin.py (modèle de
capacité et de plafond), src/apply/freework.py, src/apply/base.py,
scripts/apply.py, src/sources/alertes_indeed.py, tests/test_indeed.py.

ÉTAPE 0 — SESSION
Ajoute une cible `make login-indeed` qui ouvre https://secure.indeed.com/ avec
le profil persistant et attend que je me connecte moi-même. Tu ne saisis
jamais d'identifiant. Dis-moi quand lancer la cible, puis attends.

ÉTAPE 1 — SONDE
Écris scripts/sonde_indeed.py. Prends une offre « Candidature simplifiée » en
Île-de-France (je t'en donne une si tu n'en trouves pas). Parcours chaque écran
et enregistre HTML + PNG dans tests/pages/indeed/NN-etape.*. Vérifie dans le
code, avant de lancer, que la sonde ne clique jamais sur le bouton final
d'envoi. Remplace e-mail, téléphone et adresse dans les HTML avant commit.
Si un CAPTCHA ou une vérification apparaît : arrête-toi et préviens-moi, ne
tente rien.

ÉTAPE 2 — INVENTAIRE
Écris docs/inventaire-selecteurs-indeed.md : pour chaque écran, les éléments
utiles et leurs sélecteurs stables (data-testid, id, rôle), relevés dans les
instantanés.

ÉTAPE 3 — CODE ET TESTS
Implémente la capacité `soumettre` dans src/apply/indeed.py selon l'epic
(paramètre `indeed.autoriser_soumission`, plafond 3/jour, arrêt sur CAPTCHA
avec fichier de suspension, questions répondues seulement depuis `answers`).
Branche-la dans scripts/apply.py. Écris les tests sur instantanés listés dans
les critères. Lance `make test`.

ÉTAPE 4 — SIMULATION
Lance une simulation (sans --envoyer) sur une offre et montre-moi les
captures. N'envoie rien : l'envoi réel, c'est moi qui le décide.

Commite à chaque étape, message en français.
