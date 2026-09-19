# Prompt — EPIC-12, suite : durée de vie réelle de la session

À coller dans Claude Code depuis le dossier du projet. Remplace les étapes 2
et 3 de docs/prompt-epic12.md, rendues caduques par le diagnostic.

---

Tu reprends EPIC-12. Lis docs/epics.md (EPIC-12) puis, dans docs/sources.md,
la section « Diagnostic de session Free-Work — 19 septembre 2026 ».
Branche `epic-12-duree-session`, commits en français, un par étape.

Ce que l'on sait : le profil persistant conserve la connexion (hypothèse
infirmée, niveau 2 inutile). L'authentification repose sur trois cookies à
expiration : jwt_s et jwt_hp à 24 h, refresh_token à 48 h. Aucun
renouvellement observé en naviguant tant que jwt_s est valide.

La seule question qui reste : une fois jwt_s expiré, une visite du site
le renouvelle-t-elle à partir de refresh_token, et ce renouvellement
prolonge-t-il refresh_token ? Si oui, un passage quotidien du radar suffit à
garder la session indéfiniment, et EPIC-12 se ferme sans reconnexion
automatique. Si non, il faudra une reconnexion tous les deux jours, ou le
niveau 3 — que je trancherai.

ÉTAPE 1 — SONDE DE DURÉE
Étends scripts/diag_session.py : option --visiter qui ouvre une page
réservée aux connectés (/fr/tech-it/dashboard/applications), attend la fin
des requêtes, puis relève. Chaque relevé ajoute une ligne à
data/diag-session.jsonl : horodatage, connecté oui/non (marqueur
[data-testid='user-menu']), et pour jwt_s, jwt_hp, refresh_token : présence,
longueur, expiration. Jamais une valeur. Test hors ligne qui vérifie
qu'aucune valeur de cookie ne peut atterrir dans le fichier.
Ajoute `make diag-session`.

ÉTAPE 2 — MESURE SUR 72 HEURES
Écris un agent launchd temporaire (scripts/launchd/diag-session.plist,
cibles `make diag-planifier` et `make diag-deplanifier`) qui lance
`diag_session.py --visiter` toutes les 6 heures. Il ne doit pas croiser
l'exécution du matin : même verrou ~/.job-autopilot/verrou.
Demande-moi de faire make login, puis de lancer make diag-planifier.
Arrête-toi là : la mesure prend trois jours.

ÉTAPE 3 — CONCLUSION (quand je te le demande, après 72 h)
Lis data/diag-session.jsonl, fais le tableau des relevés et réponds :
jwt_s a-t-il été renouvelé après 24 h ? refresh_token a-t-il été prolongé ?
la session a-t-elle survécu au-delà de 48 h ? Écris la conclusion dans
docs/sources.md, retire l'agent (make diag-deplanifier).
- Si la session survit : ajoute au matin une visite de renouvellement avant
  toute candidature, et une alerte urgente quand refresh_token expire dans
  moins de 24 h. Tests.
- Sinon : arrête-toi et montre-moi la mesure. Pas de niveau 3 sans mon
  accord écrit.

RÈGLES
- Aucune valeur de cookie, jeton ou mot de passe affichée, écrite ou
  journalisée.
- Tu ne saisis jamais d'identifiant ; la connexion, c'est moi.
- CAPTCHA ou double authentification : arrêt et alerte.
- Ne touche pas à src/matching/.
- Deux échecs sur la même erreur : arrête-toi et explique.
