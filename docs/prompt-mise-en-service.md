# Prompt de mise en service

À coller dans Claude Code, lancé depuis le dossier du projet :

    cd ~/Projects/job-autopilot && claude

---

Tu travailles dans job-autopilot, un radar de missions freelance qui doit
tourner seul chaque matin sur ce Mac. Tout le code est écrit et versionné. Ton
travail est de le mettre en service, pas de le réécrire.

Commence par lire, dans cet ordre : docs/autonomie.md (la spécification de
référence), docs/chantiers.md (le lien entre chaque spécification et sa
commande), et le Makefile. Lance ensuite `make` sans argument pour voir les
cibles. Tout passe par make : n'invente pas de commandes à la main.

Déroule les étapes dans l'ordre, en t'arrêtant après chacune pour me montrer
ce que tu as obtenu.

ÉTAPE 0 — ÉTAT DES LIEUX
Lance : make etat
Dis-moi ce qui est déjà en place et ce qui manque. Le dossier
_a_supprimer/git-locks/ contient des verrous git laissés par un montage
distant : supprime-le, il ne sert à rien.

ÉTAPE 1 — INSTALLATION
Lance : make install
Si Playwright ou Chromium échouent, diagnostique et corrige avant de
continuer.
Puis dis-moi de lancer moi-même : make login
La connexion Free-Work est manuelle, je la fais, tu ne la fais pas.

ÉTAPE 2 — TESTS
Lance : make test
Les dix tests doivent passer. Si l'un échoue, corrige le code fautif, pas le
test — sauf si le test lui-même est faux, auquel cas explique-moi pourquoi
avant de le modifier.

ÉTAPE 3 — SIMULATION
Lance : make simu
La chaîne va jusqu'à la capture d'écran et s'arrête avant le clic d'envoi.
Ouvre ensuite les captures dans data/output/<jour>/candidatures/ et vérifie
trois choses : le CV sélectionné est bien celui attendu, les réponses aux
questions filtrantes sont complètes et pertinentes, le formulaire est bien
celui de la candidature. Montre-moi ce que tu vois, y compris ce qui cloche.

ÉTAPE 4 — RAPPORT
Lance : make rapport puis make attente
Dis-moi combien de missions ont été retenues, combien auraient été tentées, et
ce qui figure en file d'attente manuelle avec le motif exact.

ÉTAPE 5 — PLANIFICATION
Seulement si les étapes précédentes sont propres.
Lance : make planifier
Puis vérifie que la tâche s'exécute : launchctl start fr.kiras.jobautopilot
La tâche planifiée ne doit pas envoyer de candidatures. Vérifie-le dans le
plist installé.

ÉTAPE 6 — COMMIT
Si tu as modifié du code, commit avec un message qui dit ce qui a changé et
pourquoi. Un commit par sujet. Ne commit pas les fichiers de données.

RÈGLES, SANS EXCEPTION
- Ne lance jamais make candidater-pour-de-vrai. L'envoi réel est ma décision,
  mission par mission. Si tu penses que c'est le moment, demande.
- Ne touche pas au moteur de décision (src/matching/) ni aux seuils du
  catalogue. Il est calibré sur 1901 missions réelles.
- Ne fais pas deviner de réponse au script. Si une question de filtrage n'est
  pas dans la banque, le comportement correct est de bloquer la candidature.
  C'est voulu, ne le contourne pas.
- Ne me dis pas qu'une étape a marché sans l'avoir vérifiée. Montre la sortie
  réelle. En cas d'échec, dis-le franchement et propose un diagnostic.
- Si tu es bloqué sur la même erreur après deux tentatives, arrête-toi et
  explique-moi ce que tu as essayé.

En fin de parcours, résume en quelques lignes : ce qui fonctionne, ce qui ne
fonctionne pas, et ce qu'il me reste à faire moi-même.
