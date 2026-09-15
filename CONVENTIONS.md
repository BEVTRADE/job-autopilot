# Conventions de rangement

## Un document, un seul emplacement

Chaque fichier vit à **un seul endroit**. Pas de copie « pour faciliter » :
une copie devient une divergence dès la première correction.

## Où va quoi

| Contenu | Emplacement |
|---|---|
| Dossier d'une mission ou d'un client | `clients/<client>-<intermediaire>/` |
| CV maîtres, les 8 variantes | `cv_prets/` et `cv_prets/pdf/` |
| Sources markdown des CV | `cv_prets/sources/` |
| Rapports quotidiens du radar | `data/output/<date>/` |
| Données collectées, brutes ou notées | `data/live/` |
| Historique et journal | `data/radar.db`, `data/journal.jsonl` |
| Code | `src/`, `scripts/` |
| Référentiel de compétences | `profile/` |

**Un CV adapté à une mission appartient au dossier client**, pas à
`data/output/`. Ce dernier ne contient que les rapports du radar, qui sont
datés et jetables.

## Structure d'un dossier client

```
clients/<client>-<intermediaire>/
  00_suivi.md        identité, journal, points ouverts, règles de conduite
  01_contexte.md     le besoin écrit, l'angle réel, les écarts avec le profil
  03_cv/             le CV adapté à cette mission
  04_preparation.md  points d'appui, pièges, questions probables et à poser
  05_autotest.md     auto-évaluation sur le terrain technique de la mission
  06_echanges/       messages, comptes rendus, pièces reçues
  restitution.*      les livrables produits pour le client
```

## Fichiers temporaires

LibreOffice laisse des `.tmp` et des `.~lock…#`. Le générateur de PDF
(`src/cv/render.py`) convertit désormais dans un répertoire temporaire puis
recopie, ce qui évite d'en semer dans les dossiers de travail. Ceux qui
subsistent sont à balayer périodiquement.

## Ce qui arrive dans Téléchargements

Les cartes de fichier affichées dans la conversation sont un **aperçu**.
Le bouton de téléchargement en fait une copie dans `~/Downloads`, mais
l'original est déjà dans le projet. Il n'y a rien à récupérer depuis
Téléchargements — et ces copies peuvent être supprimées sans risque.
