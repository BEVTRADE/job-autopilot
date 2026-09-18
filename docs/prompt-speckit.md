# Prompt — mise en place de Spec Kit et spécification des epics

À coller dans Claude Code, lancé depuis le dossier du projet :

    cd ~/Projects/job-autopilot && claude

---

Tu vas mettre en place Spec Kit sur ce dépôt et spécifier les six epics du
projet. Ne développe rien tant que je ne te l'ai pas demandé : ce tour-ci
produit des spécifications, pas du code.

CONTEXTE À LIRE D'ABORD
- docs/epics.md : les six epics, avec problème, périmètre et critères
  d'acceptation. C'est la matière première.
- docs/autonomie.md : la spécification du système en service.
- docs/chantiers.md : le lien entre spécifications et commandes make.
- docs/README-architecture.md : les décisions structurantes, ADR-001 à ADR-010.
- CONVENTIONS.md : les règles de rangement.
- Le Makefile : tous les points d'entrée existants.

ÉTAPE 1 — INSTALLATION
Installe Spec Kit :

    uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

Si uv n'est pas présent, installe-le d'abord. Puis, dans le dépôt :

    specify init --here --ai claude

Le dépôt contient déjà du code et trois commits : vérifie que l'initialisation
n'écrase rien. Montre-moi `git status` avant de committer quoi que ce soit.
Les commandes ajoutées sont des slash commands préfixées `/speckit.`.

ÉTAPE 2 — CONSTITUTION
Lance /speckit.constitution et rédige-la à partir de ce qui existe déjà dans
le projet, pas d'un modèle générique. Elle doit inscrire au minimum :

- Rien ne part sans vérification : une candidature n'est comptée envoyée
  qu'après relecture du formulaire et confirmation dans « Mes candidatures ».
- Face à l'inconnu, on s'arrête : une question de filtrage hors banque bloque
  la candidature, le système n'improvise jamais de réponse.
- Tout est tracé : une ligne JSON par tentative, une capture avant envoi, un
  rapport quotidien.
- Le moteur de décision est calibré sur 1901 missions réelles. On ne modifie
  ni ses poids ni ses seuils sans recalibrage documenté.
- Aucune compétence non détenue n'apparaît jamais dans un CV généré.
- L'accord de présentation à un client final reste une décision humaine.
- Les tests tournent hors ligne, sans réseau ni navigateur.

ÉTAPE 3 — SPÉCIFICATION DES EPICS
Pour chaque epic de docs/epics.md, dans l'ordre, lance /speckit.specify en
reprenant son énoncé. N'invente pas de besoin : les critères d'acceptation
sont déjà écrits, reprends-les tels quels et complète seulement ce qui manque
pour qu'ils soient vérifiables.

Après chaque /speckit.specify, lance /speckit.clarify et montre-moi les
questions soulevées avant de continuer. Si une ambiguïté touche à une décision
métier — quel intermédiaire privilégier, quel seuil retenir — pose-la-moi, ne
la tranche pas.

Traite les epics dans cet ordre : EPIC-1, EPIC-2, EPIC-4, EPIC-3, EPIC-6,
EPIC-5. EPIC-1 d'abord parce que tout le reste améliore un système qui ne
produit encore rien.

ÉTAPE 4 — PLAN POUR EPIC-1 SEULEMENT
Lance /speckit.plan puis /speckit.tasks sur EPIC-1 uniquement. Les autres
attendent. Montre-moi la liste des tâches et arrête-toi là.

ÉTAPE 5 — COMMIT
Un commit par epic spécifié, plus un pour l'installation de Spec Kit et un
pour la constitution. Messages en français, qui disent ce qui change et
pourquoi. Ne commit aucun fichier de données.

RÈGLES, SANS EXCEPTION
- Ne lance pas /speckit.implement. Le développement est un tour séparé.
- Ne lance jamais make candidater-pour-de-vrai.
- Ne touche pas à src/matching/ ni aux seuils du catalogue.
- Ne remplace pas les documents existants par des modèles Spec Kit. Les
  spécifications nouvelles s'ajoutent, docs/autonomie.md et
  docs/README-architecture.md restent la référence du système en service.
- Si Spec Kit veut réorganiser le dépôt, montre-moi ce qu'il propose avant.
- Si tu es bloqué deux fois sur la même erreur, arrête-toi et explique.

En fin de parcours, résume : ce qui a été installé, les six spécifications
produites avec leur emplacement, les questions restées ouvertes, et la
prochaine commande à lancer.
