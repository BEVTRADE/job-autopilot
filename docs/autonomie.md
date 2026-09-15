# Spécification — exécution autonome du radar

Objectif : un radar qui tourne seul chaque matin sur le Mac, sans Claude dans
la boucle, et qui rend compte. Document de référence pour la mise en service.

## Principe

Le système décide seul, agit seul, mais ne dissimule rien et ne devine jamais.
Trois règles tiennent l'ensemble :

1. **Rien ne part sans vérification.** Une candidature n'est comptée envoyée
   qu'après relecture du formulaire et confirmation dans « Mes candidatures ».
2. **Face à l'inconnu, on s'arrête.** Une question de filtrage hors banque
   interrompt la candidature et la met en file d'attente manuelle. Le script
   n'improvise pas de réponse.
3. **Tout est tracé.** Une ligne JSON par tentative dans `data/journal.jsonl`,
   une capture d'écran avant envoi, un rapport consolidé chaque matin.

## Chaîne d'exécution

    scripts/matin.sh
      1. collecte      scripts/collect.py    → data/output/<jour>/retenues.json
      2. candidatures  scripts/apply.py      → data/journal.jsonl + captures
      3. rapport       src/report/digest.py  → rapport-matin.md, file_attente.json

Chaque étape journalise dans `data/logs/<jour>.log` et n'interrompt pas les
suivantes en cas d'échec : une collecte ratée produit quand même un rapport
qui dit qu'elle a raté.

### Réglages

Variables d'environnement, avec leurs valeurs par défaut :

| Variable | Défaut | Rôle |
|---|---|---|
| `MAX` | 3 | Candidatures maximum par exécution |
| `MIN_FIT` | 70 | Adéquation minimale pour tenter |
| `CV` | `FR_ARCHITECTE_IA_GENAI.pdf` | CV envoyé |
| `SANS_OUVERTURE` | vide | À 1, n'ouvre pas le rapport à l'écran |

Le mode par défaut est la simulation. L'envoi réel exige `--envoyer`.

## Mise en service, dans l'ordre

### Étape 1 — installation et connexion

    bash scripts/setup.sh
    .venv/bin/python scripts/apply.py --login

La connexion Free-Work est manuelle et faite une seule fois : la session est
conservée dans `~/.job-autopilot/browser-profile`.

### Étape 2 — tests hors ligne

    bash scripts/verifier.sh

Aucun réseau, aucun navigateur, aucune candidature. Couvre la banque de
réponses, le moteur de décision et le rapport. Doit passer avant toute suite.

### Étape 3 — première exécution en simulation

    scripts/matin.sh

Va jusqu'à la capture d'écran et s'arrête avant le clic d'envoi. Vérifier les
captures dans `data/output/<jour>/candidatures/` : le bon CV est-il sélectionné,
les réponses sont-elles complètes, le formulaire est-il celui attendu.

### Étape 4 — première candidature réelle

    MAX=1 scripts/matin.sh --envoyer

Une seule mission, choisie parmi les moins stratégiques. Vérifier ensuite à la
main dans « Mes candidatures » que l'envoi est bien enregistré.

### Étape 5 — automatisation

    cp scripts/fr.kiras.jobautopilot.plist ~/Library/LaunchAgents/
    # remplacer REMPLACER_PAR_LE_CHEMIN par le chemin réel du projet
    launchctl load ~/Library/LaunchAgents/fr.kiras.jobautopilot.plist

Déclenchement à 7h30. Pour déclencher immédiatement et vérifier :

    launchctl start fr.kiras.jobautopilot

Pour désactiver :

    launchctl unload ~/Library/LaunchAgents/fr.kiras.jobautopilot.plist

Le `plist` livré ne contient pas `--envoyer`. C'est délibéré : il faut
plusieurs matins de simulation avant de lever le dry-run dans la tâche
planifiée.

## Contraintes d'exploitation

**Le Mac doit être allumé et la session ouverte.** Le profil Chrome persistant
ne se lance pas sur une session verrouillée. `launchd` ne rattrape pas les
déclenchements manqués avec cette configuration.

**Un seul emplacement de CV sur Free-Work.** Chaque candidature écrase le CV
partagé. Le script restaure un CV de repos en fin de série. Deux exécutions
simultanées se marcheraient dessus : ne pas lancer `matin.sh` à la main pendant
que la tâche planifiée tourne.

**Le réseau.** La collecte fonctionne depuis le Mac. Elle ne fonctionne pas
depuis un agent distant : free-work.com y est refusé par la politique de sortie.

**Arrêt d'urgence.**

    touch ~/.job-autopilot/STOP

Toute exécution en cours s'interrompt à la prochaine vérification, et les
suivantes ne démarrent pas. Retirer le fichier pour reprendre.

## Ce qui reste hors du périmètre automatique

L'accord de présentation à un client final. Le script candidate, ce qui n'est
que la première étape avant l'entretien ESN. Donner son accord pour être
présenté chez un client reste une décision humaine, une seule fois par client.

La personnalisation fine du CV par mission. Le script envoie le CV d'axe choisi
par le moteur. Un appel à `claude -p` pourrait adapter les phrases avant envoi,
sur l'abonnement Pro. À trancher après avoir observé la qualité des CV d'axe.

## Tests

`tests/` couvre ce qui peut l'être sans réseau :

| Fichier | Ce qui est vérifié |
|---|---|
| `test_answers.py` | Les questions connues sont reconnues, les inconnues refusées, la limite de longueur tenue |
| `test_matcher.py` | Hiérarchie des scores, milieu de fourchette et non plancher, mode contact, effectivité de `dataclasses.replace` |
| `test_digest.py` | Le rapport ne mélange pas les dates, remonte la file d'attente, dit quand rien n'a tourné |

Ces tests encodent des régressions réelles rencontrées en septembre : le calcul
sur le plancher au lieu du milieu de fourchette, les paramètres de sous-classe
silencieusement ignorés, et le faux négatif de la banque de réponses.

Ce qui n'est pas testé automatiquement : la soumission elle-même. Elle dépend
du DOM de Free-Work, qui change sans préavis. C'est le rôle de la relecture
bloquante et de la vérification dans « Mes candidatures ».
