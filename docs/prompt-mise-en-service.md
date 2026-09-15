# Prompt de mise en service

À coller dans Claude Code, lancé depuis le dossier du projet :

    cd ~/Projects/job-autopilot && claude

---

Tu travailles dans job-autopilot, un radar de missions freelance qui doit
tourner seul chaque matin sur ce Mac. Tout le code est écrit. Ton travail est
de le mettre en service, pas de le réécrire.

Commence par lire `docs/autonomie.md` : c'est la spécification de référence,
elle décrit la chaîne d'exécution, les réglages et les cinq étapes de mise en
service. Lis aussi `docs/README-architecture.md` pour les décisions
structurantes.

Déroule ensuite les étapes dans l'ordre, en t'arrêtant après chacune pour me
montrer ce que tu as obtenu.

**Étape 1 — installation.** Lance `bash scripts/setup.sh`. Si Playwright ou
Chromium échouent à s'installer, diagnostique et corrige avant de continuer.
Puis dis-moi de lancer moi-même `.venv/bin/python scripts/apply.py --login` :
la connexion Free-Work est manuelle, je la fais, tu ne la fais pas.

**Étape 2 — tests.** Lance `bash scripts/verifier.sh`. Les dix tests doivent
passer. Si l'un échoue, corrige le code fautif, pas le test — sauf si le test
lui-même est faux, auquel cas explique-moi pourquoi avant de le modifier.

**Étape 3 — simulation.** Lance `scripts/matin.sh` sans argument. C'est le
mode simulation : la chaîne va jusqu'à la capture d'écran et s'arrête avant le
clic d'envoi. Ensuite, ouvre les captures dans
`data/output/<jour>/candidatures/` et vérifie trois choses : le CV sélectionné
est bien celui attendu, les réponses aux questions filtrantes sont complètes et
pertinentes, le formulaire est bien celui de la candidature. Montre-moi ce que
tu vois, y compris ce qui cloche.

**Étape 4 — lis le rapport.** `data/output/<jour>/rapport-matin.md`. Dis-moi
combien de missions ont été retenues, combien auraient été tentées, et ce qui
figure en file d'attente manuelle avec le motif exact.

**Étape 5 — planification.** Seulement si les étapes précédentes sont propres.
Installe `scripts/fr.kiras.jobautopilot.plist` dans `~/Library/LaunchAgents/`
en remplaçant `REMPLACER_PAR_LE_CHEMIN` par le chemin réel, charge-le avec
`launchctl load`, puis déclenche-le une fois avec `launchctl start` pour
vérifier qu'il s'exécute. Le plist ne doit pas contenir `--envoyer`.

Règles, sans exception :

- **Ne lance jamais `--envoyer`.** L'envoi réel de candidatures est ma
  décision, mission par mission. Si tu penses que c'est le moment, demande.
- **Ne touche pas au moteur de décision** (`src/matching/`) ni aux seuils du
  catalogue. Il est calibré sur 1901 missions réelles.
- **Ne fais pas deviner de réponse au script.** Si une question de filtrage
  n'est pas dans la banque, le comportement correct est de bloquer la
  candidature. C'est voulu, ne le contourne pas.
- **Ne me dis pas qu'une étape a marché sans l'avoir vérifiée.** Montre la
  sortie réelle. En cas d'échec, dis-le franchement et propose un diagnostic.
- Si tu es bloqué sur la même erreur après deux tentatives, arrête-toi et
  explique-moi ce que tu as essayé.

En fin de parcours, résume en quelques lignes : ce qui fonctionne, ce qui ne
fonctionne pas, et ce qu'il me reste à faire moi-même.
