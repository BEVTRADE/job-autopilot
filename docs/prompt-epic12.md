# Prompt — EPIC-12, session durable

À coller dans Claude Code depuis le dossier du projet.

---

Tu traites EPIC-12, décrit dans docs/epics.md. Lis-le entièrement : il est
construit en trois niveaux, et on ne passe au suivant que si le précédent ne
suffit pas, preuve à l'appui.

Contexte : le 19 septembre, un envoi réel a demandé une connexion alors que
make login avait été fait. Tous les scripts ouvrent le profil persistant
~/.job-autopilot/browser-profile via launch_persistent_context — voir
scripts/apply.py, scripts/sonde_freework.py, src/apply/base.py. L'hypothèse
est que Chromium ne conserve pas les cookies de session à la fermeture. C'est
une hypothèse : vérifie-la.

ÉTAPE 1 — DIAGNOSTIC
Écris scripts/diag_session.py. Il ouvre le profil persistant, vérifie la
connexion avec session_active() de src/apply/freework.py, puis inventorie ce
qui porte l'authentification : chaque cookie du domaine free-work.com avec son
nom, son domaine, sa date d'expiration ou l'indication « session », et les clés
du stockage local et du stockage de session. N'affiche jamais la valeur d'un
jeton : seulement son nom, sa longueur et son expiration.

Demande-moi de faire make login, puis lance le diagnostic une première fois,
ferme le navigateur, relance-le une seconde fois, et compare. Dis-moi ce qui a
disparu entre les deux. Écris ce diagnostic dans docs/sources.md.

ÉTAPE 2 — PERSISTANCE DE L'ÉTAT
Si l'hypothèse se confirme, implémente le niveau 2 : enregistrer l'état de
connexion complet, cookies de session compris, en fin d'exécution réussie,
dans ~/.job-autopilot/etat-session.json avec des droits 600, et le réinjecter
à l'ouverture. Factorise l'ouverture du navigateur dans une seule fonction,
utilisée par apply.py, la sonde et le diagnostic : aujourd'hui elle est
dupliquée.

Tests hors ligne : aller-retour d'un état enregistré puis réinjecté, droits du
fichier, comportement si le fichier est absent ou corrompu.

Puis la preuve réelle : une connexion, trois exécutions de make simu
successives avec le navigateur fermé entre chaque, zéro demande de connexion.

ÉTAPE 3 — SEULEMENT SI L'ÉTAPE 2 NE SUFFIT PAS
Si la session expire malgré tout — jeton de courte durée, par exemple —,
arrête-toi et montre-moi la mesure. Le niveau 3, reconnexion automatique avec
identifiants dans le Trousseau macOS via la bibliothèque keyring, demande mon
accord explicite avant d'être écrit.

RÈGLES
- N'affiche, n'écris et ne journalise jamais la valeur d'un cookie, d'un jeton
  ou d'un mot de passe. Ajoute un test qui cherche un motif de jeton dans
  data/, tests/pages/ et les journaux.
- Ne saisis jamais toi-même d'identifiant. La connexion, c'est moi, via make
  login.
- Face à un CAPTCHA ou une double authentification : arrêt et alerte, aucune
  tentative de contournement.
- Ne touche pas à src/matching/.
- Commit par étape, messages en français.
- Si tu es bloqué deux fois sur la même erreur, arrête-toi et explique.
