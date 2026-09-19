# Epics

Six lots de travail, rédigés pour être passés à Spec Kit. Chaque epic est
autonome : il peut être spécifié, planifié et implémenté sans attendre les
autres, sauf dépendance indiquée.

L'ordre recommandé est celui de la numérotation. EPIC-1 conditionne la valeur
de tous les autres : tant qu'aucune candidature n'est partie, le reste
améliore un système qui ne produit rien.

---

## EPIC-1 — Première candidature vérifiée de bout en bout

**Problème.** Le pipeline de soumission est écrit, testé unitairement, jamais
exécuté en envoi réel. Le DOM de Free-Work a pu changer depuis l'écriture du
code début septembre. Quatre missions préparées attendent depuis une semaine.

**Valeur.** Passer d'un système qui prépare à un système qui agit.

**Périmètre.** Exécuter `make simu` de bout en bout, diagnostiquer et corriger
tout écart entre le code et le formulaire réel, puis envoyer une candidature
unique sur une mission peu stratégique et la vérifier.

**Critères d'acceptation.**

1. `make simu` s'exécute sans erreur technique et produit un log, au moins une
   capture d'écran et un rapport.
2. Sur la capture, le CV sélectionné est celui décidé par le moteur, les
   réponses aux questions filtrantes sont présentes et complètes.
3. Une candidature réelle est envoyée et apparaît dans « Mes candidatures ».
4. Le journal contient une ligne de statut `envoyee` pour cette mission.
5. Le CV de repos est restauré après la série.

**Hors périmètre.** L'envoi en série, la planification automatique.

**Risque identifié.** Les sélecteurs CSS de `src/apply/freework.py` sont
datés du 4 septembre. Les corriger fait partie du lot.

---

## EPIC-2 — Regroupement des annonces par empreinte de contenu

**Problème.** L'identité d'une mission est aujourd'hui son URL. La même
mission publiée par trois intermédiaires produit trois entrées distinctes :
observé le 8 septembre (Meudon, trois ESN, 286 à 500 €), le 9 (VOLT/AMIA en
deux grades) et le 15 (réassurance, KEONI 750 € contre CAT-AMANIA 500-720 €).

**Valeur.** Ne plus candidater deux fois au même client final, et surtout
choisir l'intermédiaire le mieux-disant — l'écart observé atteint 250 € par
jour pour un travail identique.

**Périmètre.** Calculer une empreinte sur le titre normalisé et le corps de
l'annonce. Regrouper sans supprimer : chaque annonce du groupe reste visible
avec sa société et son TJM. Le rapport affiche le groupe, pas la première
annonce vue.

**Critères d'acceptation.**

1. Deux annonces de sociétés différentes décrivant la même mission sont
   regroupées.
2. Deux missions réellement distinctes au titre proche ne sont pas regroupées.
3. Le groupe expose l'intermédiaire le mieux-disant et l'écart de TJM.
4. Aucune annonce n'est supprimée ni masquée.
5. Des tests couvrent les trois cas réels d'septembre, en données figées.

**Dépendances.** Aucune. `src/store.py` et `scripts/collect.py`.

---

## EPIC-3 — Sources supplémentaires

**Problème.** Deux sources actives, Free-Work et BOAMP. Le registre
`docs/sources.md` en liste quatre à intégrer : Freelance-Informatique,
Freelance-Day, FreelanceRepublik, TED.

**Valeur.** Free-Work seul donne environ six missions qualifiées par mois au
plancher de 650 €. Élargir le flux est le seul moyen d'augmenter ce chiffre
sans baisser le plancher.

**Périmètre.** Une classe par source dans `src/sources/`, sur le modèle de
`freework.py` : découverte des URL, lecture d'une annonce, extraction du
titre, de la société, du TJM, du lieu, du télétravail et de la durée.
Déclaration dans `scripts/collect.py`.

**Critères d'acceptation.**

1. Chaque source implémentée remonte au moins vingt annonces réelles.
2. Le TJM est extrait correctement, y compris les fourchettes et les
   séparateurs typographiques inhabituels.
3. Une source en panne n'interrompt pas la collecte des autres.
4. Des tests d'extraction tournent sur des pages enregistrées, sans réseau.

**Dépendances.** EPIC-2 de préférence : multiplier les sources multiplie les
doublons.

---

## EPIC-4 — Passe systématique sur le catalogue de compétences

**Problème.** Trois points aveugles trouvés en une seule journée début
septembre — gouvernance IA, fraude et LCB-FT, acculturation. Chacun faisait
chuter le score d'adéquation de missions pertinentes, l'un de 51 à 90 après
correction. Ils ont été trouvés par hasard.

**Valeur.** Un point aveugle coûte des missions qualifiées invisibles. Les
chercher méthodiquement vaut mieux que les découvrir par accident.

**Périmètre.** Confronter le vocabulaire des huit CV à celui des 1901 missions
déjà collectées. Produire la liste des termes fréquents dans les missions et
absents du catalogue, classés par fréquence et par TJM médian associé.

**Critères d'acceptation.**

1. Une commande `make catalogue` produit un rapport de termes manquants.
2. Chaque terme est accompagné de sa fréquence, du TJM médian des missions qui
   le portent, et d'un exemple d'annonce.
3. Le rapport distingue ce qui relève d'une compétence réelle non déclarée de
   ce qui est hors profil.
4. Aucune modification automatique du catalogue : la décision reste humaine.

**Dépendances.** Aucune. `scripts/calibrate.py` fournit la matière.

---

## EPIC-5 — Personnalisation du CV par mission

**Problème.** Le script envoie le CV d'axe tel quel. Les CV adaptés à la main
— Enedis, KEONI, BTI, CAT-AMANIA, VISIAN — sont nettement plus proches de
l'annonce, mais demandent une intervention humaine à chaque fois.

**Valeur.** Rapprocher la qualité automatique de la qualité manuelle sans
intervention.

**Périmètre.** Appeler `claude -p` depuis le script pour produire les
substitutions à appliquer au CV d'axe : titre, accroche, ordre des sections de
compétences. Le rendu reste assuré par `src/cv/render.py`, par remplacement
XML, afin de préserver la mise en forme.

**Critères d'acceptation.**

1. Le CV produit est un docx valide, sans gras ajouté, mise en forme préservée.
2. Aucune compétence absente du profil maître n'apparaît dans le CV généré.
3. En cas d'échec ou d'indisponibilité de `claude -p`, le CV d'axe est envoyé
   tel quel et le rapport le signale.
4. Le coût tire sur l'abonnement, pas sur des crédits API.
5. Un mode de comparaison permet de juger CV d'axe contre CV adapté avant de
   généraliser.

**Dépendances.** EPIC-1. Inutile tant que rien ne part.

---

## EPIC-6 — File d'attente et validation

**Problème.** Les candidatures bloquées — question hors banque, relecture
discordante, CV non basculé — atterrissent dans `file_attente.json` et n'en
ressortent que si quelqu'un lit le fichier.

**Valeur.** Une candidature bloquée est une mission perdue si personne ne la
reprend. C'est aussi la matière première pour enrichir la banque de réponses.

**Périmètre.** Une vue des candidatures en attente, avec pour chacune le
motif, la capture d'écran, l'annonce et le CV prévu. Une action simple pour
ajouter une réponse à la banque et reprendre la candidature.

**Critères d'acceptation.**

1. Chaque candidature bloquée est visible avec son motif et sa capture.
2. Une question hors banque peut être répondue et la réponse ajoutée au
   référentiel `profile/reponses_types.json`.
3. Une candidature reprise après enrichissement aboutit sans repartir de zéro.
4. Rien n'est envoyé depuis cette interface sans action humaine explicite.

**Dépendances.** EPIC-1.

---

## EPIC-7 — Branchement du regroupement dans la chaîne

**Problème.** `src/grouping.py` est correct, testé, et inerte : rien ne
l'appelle. La revue du 18 septembre l'a établi — ni `scripts/collect.py` ni
`src/store.py` ne le référencent. La déduplication réelle continue de se faire
sur l'URL, donc la même mission publiée par trois intermédiaires passe toujours
trois fois.

**Valeur.** C'est ce lot, et non EPIC-2, qui produit l'effet annoncé :
candidater une seule fois par mission, et chez l'intermédiaire le mieux-disant.

**Périmètre.** Appeler le regroupement dans la chaîne de collecte, après la
lecture des annonces et avant la notation. Le rapport affiche les groupes, pas
les annonces isolées : une ligne par mission, avec les intermédiaires en
regard, leurs TJM, et l'écart. La notation s'applique au groupe, en retenant
l'annonce du mieux-disant.

Trois correctifs à porter en même temps, issus de la revue :

- L'écart ne doit être calculé que sur les annonces ayant un TJM, et le nombre
  d'annonces sans TJM doit être indiqué. Aujourd'hui un groupe où une seule
  annonce affiche 600-650 renvoie un écart de 50, qui n'est pas un écart entre
  intermédiaires mais la largeur d'une fourchette.
- Le mieux-disant doit être marqué indéterminé quand aucune annonce du groupe
  n'affiche de TJM, au lieu d'être choisi arbitrairement.
- La sensibilité de l'empreinte à un corps d'annonce absent doit être traitée
  ou documentée : deux annonces identiques dont l'une sans description tombent
  sous le seuil et ne se regroupent pas.

**Critères d'acceptation.**

1. Une collecte réelle produit un rapport dont les lignes sont des groupes.
2. Une mission publiée par plusieurs intermédiaires n'apparaît qu'une fois,
   avec tous ses intermédiaires visibles et leurs TJM.
3. La notation s'applique au groupe, sur l'annonce du mieux-disant.
4. L'écart affiché ne mélange jamais largeur de fourchette et écart entre
   intermédiaires.
5. Un groupe sans aucun TJM est signalé comme tel.
6. L'historique ne déclenche pas deux candidatures pour deux annonces du même
   groupe.
7. Des tests couvrent le passage collecte, regroupement, notation, rapport,
   sur données figées.

**Dépendances.** EPIC-2 fusionnée. À faire avant EPIC-3 : ajouter quatre
sources avant le branchement multiplierait les doublons au lieu de les réduire.

---

## EPIC-8 — Validation du parcours de candidature sur le site réel

**Problème.** Le 19 septembre, trois allers-retours pour déposer un seul CV.
À chaque fois : correction écrite à l'aveugle depuis un agent distant, exécution
sur le Mac, échec, lecture d'un instantané HTML partiel, nouvelle correction.
Le deuxième instantané montrait même un état que le bug précédent avait
lui-même provoqué. Trois défauts découverts ainsi, un par exécution :

- le dépôt cliquait « Ajouter un document » au lieu de « Ajouter un CV » ;
- la confirmation cherchait « Partager le CV », qui n'existe pas — le bouton
  réel est « Joindre le document ». Le basculement de CV n'avait donc jamais
  fonctionné ; les simulations du 18 passaient parce que le bon CV était déjà
  partagé ;
- deux boutons « Éditer » coexistent, Profil puis CV partagé, et le dépôt était
  tenté dans la modale du profil.

Aucun test ne couvre le parcours réel. Les tests existants vérifient la logique,
jamais les sélecteurs contre le DOM.

**Valeur.** Remplacer la boucle « corriger à l'aveugle, exécuter, échouer » par
une seule exploration qui capture tous les états, puis des tests hors ligne
qui garantissent que chaque sélecteur trouve son élément.

**Périmètre.**

1. Une **sonde** : `scripts/sonde_freework.py`, qui parcourt le formulaire de
   candidature étape par étape sur une offre réelle, **sans jamais cliquer sur
   l'envoi**, et enregistre à chaque étape le HTML et une capture dans
   `tests/pages/freework/<étape>.html` et `.png`. Étapes au minimum : page
   d'offre, panneau de candidature, modale Profil, modale CV à l'ouverture,
   modale CV après clic sur « Ajouter un CV », après choix d'un fichier, après
   sélection d'une carte, après confirmation, champs de questions filtrantes,
   page « Mes candidatures ».
2. Un **inventaire des sélecteurs** : chaque entrée de `SEL` dans
   `src/apply/freework.py` est rattachée à l'étape où elle doit trouver un
   élément.
3. Des **tests hors ligne sur les instantanés** : pour chaque sélecteur, un
   test charge l'HTML de l'étape concernée et vérifie que le sélecteur y trouve
   exactement l'élément attendu — le bon bouton, pas le premier qui ressemble.
4. Une **cible** `make sonde` qui relance l'exploration, pour détecter une
   évolution du site : si les tests échouent sur de nouveaux instantanés, le
   DOM a changé, on le sait avant un envoi raté.
5. Correction de `src/apply/freework.py` sur la base des instantanés réels.

**Critères d'acceptation.**

1. `make sonde` produit un instantané par étape, sans envoyer de candidature.
2. Chaque sélecteur de `SEL` est couvert par au moins un test sur instantané.
3. Aucun sélecteur ne repose sur un libellé ambigu quand un attribut stable
   existe (`data-testid`, `id`, `name`).
4. Le basculement de CV est démontré de bout en bout en simulation : un CV
   différent du CV partagé est sélectionné, confirmé, et relu.
5. Le dépôt d'un CV local est démontré de bout en bout : fichier déposé, visible
   dans la liste, sélectionné.
6. Une candidature réelle est envoyée et confirmée dans « Mes candidatures ».
7. Les tests sur instantanés tournent dans `make test`, sans réseau.

**Contrainte d'exécution.** Ce lot doit être mené **depuis Claude Code sur le
Mac**, qui dispose de la session Free-Work, du réseau et de Playwright. Un agent
distant ne peut ni ouvrir le site ni observer le DOM, ce qui a produit la
boucle du 19 septembre.

**Dépendances.** Aucune. Prioritaire sur tout le reste : EPIC-5 et EPIC-6
reposent sur un parcours de candidature fiable.

---

## EPIC-9 — Autonomie d'exploitation

**Problème.** La chaîne tourne, mais seulement quand quelqu'un la lance et la
regarde. Trois manques empêchent qu'elle tourne seule chaque matin sans
surveillance : elle ne sait pas que sa session Free-Work a expiré, elle ne
prévient personne de ce qu'elle a fait, et sa planification n'a jamais été
vérifiée.

**Valeur.** Passer d'un outil qu'on lance à un système qui travaille pendant
qu'on dort, et qui dit le matin ce qu'il a fait.

**Périmètre.**

1. **Détection de session expirée.** Avant toute candidature, vérifier que la
   session Free-Work est active. Si elle ne l'est pas : aucune tentative, une
   alerte explicite, et un statut dédié dans le journal — pas une série
   d'échecs incompréhensibles.
2. **Notification du matin.** Une notification macOS en fin d'exécution :
   nombre de candidatures envoyées, bloquées, et en file d'attente. Et une
   alerte distincte quand quelque chose demande une action humaine — session
   expirée, question hors banque, dépôt de CV raté.
3. **Planification vérifiée.** `make planifier`, puis un déclenchement manuel,
   puis la preuve qu'une exécution planifiée a bien produit son log. Le plist
   ne contient pas `--envoyer` : il faut une décision explicite pour lever le
   dry-run dans la tâche planifiée, après plusieurs matins de simulation
   propres.
4. **Garde-fous de volume.** Plafond quotidien respecté même si la tâche est
   déclenchée deux fois, par un verrou d'exécution. Pas de seconde candidature
   à une mission du même groupe, déjà garanti par EPIC-7 et à vérifier en
   conditions réelles.

**Critères d'acceptation.**

1. Une session expirée produit une alerte et zéro tentative.
2. Chaque exécution se termine par une notification lisible.
3. La tâche planifiée s'exécute à l'heure prévue, vérifié par son log.
4. Deux lancements simultanés ne produisent qu'une seule exécution.
5. Cinq matins consécutifs de simulation sans intervention, avant de lever le
   dry-run.

**Dépendances.** EPIC-8. Rien ne sert d'automatiser un parcours qui ne sait
pas encore basculer de CV.

---

## EPIC-10 — Plusieurs candidats, plusieurs profils

**Problème.** Tout le système est construit pour un seul candidat : un profil
maître, un catalogue d'axes, huit CV, une banque de réponses, une session
Free-Work, un historique. Le servir à plusieurs personnes aux profils
différents — un architecte freelance, une développeuse en recherche de CDI,
un chef de projet en transition — suppose que chacun ait son propre
périmètre, sans aucune fuite d'un candidat vers un autre.

**Valeur.** Réutiliser la chaîne entière — collecte, regroupement, notation,
candidature, rapport — pour d'autres personnes, sans la réécrire.

**Le risque qui gouverne tout le lot.** Envoyer le CV d'une personne sur la
candidature d'une autre est une faute grave, pas un bug : données personnelles
divulguées, candidat discrédité, recruteur trompé. L'isolation n'est pas une
fonctionnalité parmi d'autres, c'est la condition d'existence du lot.

**Périmètre.**

1. **Un dossier par candidat** : `candidats/<identifiant>/`, contenant son
   profil maître, son catalogue d'axes, ses CV, sa banque de réponses, ses
   paramètres de recherche, ses consentements, et son historique. Aucun fichier
   partagé entre candidats hormis le code et les sources.
2. **Des paramètres de recherche par candidat** : type de contrat recherché —
   freelance, CDI, ou les deux —, plancher et cible en TJM ou en salaire annuel,
   zone géographique, télétravail, séniorité, langues, secteurs exclus.
3. **Une session par candidat et par site** : `~/.job-autopilot/<candidat>/
   browser-profile/<site>`. Chaque candidat se connecte lui-même, une fois.
   **Le système ne stocke jamais aucun mot de passe.**
4. **Un journal, un historique et un rapport par candidat**, et un plafond
   quotidien par candidat.
5. **La chaîne du matin itère sur les candidats actifs**, avec un verrou et un
   kill-switch par candidat en plus du kill-switch global.
6. **Migration** du candidat actuel vers `candidats/hakim-arezki/`, sans
   rupture : les commandes existantes continuent de fonctionner.

**Consentement et données personnelles.** Traiter les CV et les candidatures
d'autres personnes fait de l'opérateur du système un responsable de
traitement au sens du RGPD. Le lot doit prévoir, pour chaque candidat :

- un consentement écrit, daté, conservé dans son dossier, qui précise ce que le
  système fait en son nom — collecter, noter, candidater, et sur quels sites ;
- la possibilité de suspendre ou de supprimer toutes ses données ;
- la règle déjà appliquée : **une seule autorisation de présentation par client
  final**, décidée par le candidat, jamais par le système.

Ce cadrage juridique est à faire valider — ce document n'est pas un avis
juridique.

**Critères d'acceptation.**

1. Deux candidats fictifs aux profils opposés produisent, sur les mêmes
   annonces, des notations et des sélections différentes.
2. Un test vérifie qu'aucun chemin de code ne peut sélectionner un CV hors du
   dossier du candidat courant. Test négatif explicite : un CV d'un candidat A
   demandé pendant l'exécution du candidat B est refusé.
3. Les journaux, historiques et rapports sont strictement séparés.
4. Un candidat sans consentement enregistré n'est jamais exécuté.
5. Le kill-switch d'un candidat n'arrête que lui ; le kill-switch global arrête
   tout.
6. Les commandes actuelles fonctionnent à l'identique pour le candidat migré.
7. Le moteur de décision reste calibré : les paramètres par défaut du candidat
   migré reproduisent exactement les scores actuels, vérifié par
   `scripts/calibrate.py` avant et après.

**Dépendances.** EPIC-8 et EPIC-9. Multiplier les candidats sur un parcours
qui ne sait pas encore basculer de CV multiplierait les échecs.

---

## EPIC-11 — Offres en CDI et nouvelles sources, dont LinkedIn

**Problème.** Le système ne connaît que la mission freelance : ses sources, sa
notation par TJM, son vocabulaire. Un candidat en recherche de CDI n'y trouve
rien — ni les bons sites, ni une notation qui comprenne un salaire annuel.

**Valeur.** Ouvrir la chaîne aux candidats salariés, et élargir le flux pour
tous.

**Périmètre.**

1. **Le type de contrat devient une dimension de l'annonce** : freelance, CDI,
   CDD, portage. Extrait par chaque source, filtré selon les paramètres du
   candidat.
2. **La notation de la valeur accepte un salaire annuel** : conversion entre
   salaire et TJM seulement pour comparer, jamais pour afficher. Plancher et
   cible dans l'unité du candidat. Le calcul actuel par TJM reste inchangé pour
   les candidats freelance — même contrainte de calibrage qu'en EPIC-10.
3. **France Travail, source prioritaire pour le CDI.** Une API officielle et
   gratuite existe, l'API Offres d'emploi, publiée sur francetravail.io et
   référencée sur data.gouv.fr. Accès par inscription développeur et jeton
   OAuth. C'est la voie la plus propre : pas de scraping, un contrat d'usage
   explicite, des offres structurées. À vérifier à l'inscription : quotas,
   conditions d'usage, champs disponibles.
4. **Autres sites CDI** — Welcome to the Jungle, APEC, HelloWork, Indeed — à
   évaluer un par un avant toute implémentation, sur le modèle de la
   reconnaissance du 18 septembre : accès public ou connexion requise,
   conditions d'utilisation, structure des pages. Aucun extracteur sans cette
   reconnaissance écrite dans `docs/sources.md`.
5. **LinkedIn : lecture par les alertes, jamais d'automatisation du site.**
   Voir la section dédiée ci-dessous.

### LinkedIn — la limite, et la voie qui la respecte

Les conditions d'utilisation de LinkedIn interdisent les logiciels et
extensions qui automatisent l'activité sur le site, y compris la navigation et
la candidature. Les comptes qui le font s'exposent à des restrictions. Avec
plusieurs candidats, le risque se multiplie, et c'est le compte personnel de
chaque candidat qui paie. Ce choix était déjà acté dans
`src/apply/linkedin.py` : soumission délibérément non implémentée.

La voie propre passe par **la boîte mail du candidat** : chaque candidat
configure ses alertes d'emploi LinkedIn, qui lui arrivent par courriel. Le
système lit ces courriels — avec l'accord du candidat, sur sa propre
messagerie — en extrait les offres, et les injecte dans la chaîne comme
n'importe quelle source. **La candidature LinkedIn reste manuelle** : le
rapport du matin fournit le lien, le CV recommandé et le message, le candidat
clique.

Le même mécanisme vaut pour tout site qui envoie des alertes par courriel mais
ne se prête pas à l'automatisation.

**Critères d'acceptation.**

1. Chaque annonce collectée porte son type de contrat.
2. Un candidat CDI ne reçoit que des offres CDI, un candidat freelance que des
   missions, un candidat mixte les deux.
3. La notation d'une offre CDI utilise le salaire, et les scores freelance
   existants sont inchangés.
4. France Travail remonte des offres réelles, avec tests sur réponses d'API
   enregistrées, sans réseau.
5. Les alertes LinkedIn d'une boîte de test sont lues et transformées en
   annonces, sans aucun appel au site LinkedIn.
6. Aucun code ne soumet de candidature sur LinkedIn.
7. Chaque nouveau site CDI est précédé de sa reconnaissance dans
   `docs/sources.md`.

**Dépendances.** EPIC-10 pour le filtrage par candidat. France Travail peut
démarrer avant, en source commune.
