# Passe systématique sur le catalogue de compétences

Spécification du chantier 2 (`docs/chantiers.md`), correspond à EPIC-4
(`docs/epics.md`).

## Problème

`profile/cv_catalog.json` déclare, par axe de CV, les intitulés qui
déclenchent l'axe et les compétences (`core`, `plus`) qui font monter le
score d'adéquation. Trois manques ont été trouvés par hasard début
septembre 2026 — gouvernance IA, fraude et LCB-FT, acculturation. L'un
faisait passer une mission de 51 à 90 une fois ajouté au catalogue. Rien ne
garantit qu'il n'en reste pas d'autres : la détection n'a rien de
méthodique tant qu'elle dépend d'une lecture manuelle de quelques annonces.

## Principe

`scripts/catalogue.py` confronte deux vocabulaires :

- **Le vocabulaire déclaré** : les intitulés (`titles`), compétences
  signature (`core`) et renforçantes (`plus`) des quatre axes de
  `profile/cv_catalog.json`, plus le texte intégral des huit fiches CV
  (FR et EN de chaque axe, `reprise/cv_sources/*.md`). Le texte des CV
  élargit la couverture au-delà des seules listes de mots-clés du JSON —
  une compétence peut être écrite en prose sans figurer dans `core`/`plus`.
- **Le vocabulaire des missions** : les étiquettes de compétence
  (`mission_skills.skill`) des 1901 missions de `reprise/candidatures.db`.
  Ce sont des étiquettes structurées, posées par les sites sources, pas du
  texte libre extrait des annonces — c'est ce qui les rend comparables
  terme à terme au catalogue sans travail de reconnaissance d'entités.
  Conséquence assumée : un terme qui n'existe que dans le titre ou le corps
  d'une annonce, sans étiquette associée, n'est pas vu par cette passe.

Un terme de mission est déclaré **couvert** s'il correspond — par
inclusion de sous-chaîne, dans un sens ou dans l'autre, après normalisation
(minuscules, accents supprimés) — à un `titles`/`core`/`plus` d'un axe, à
un alias déclaré, ou au texte d'une des huit fiches CV. C'est exactement la
règle utilisée par `Matcher._skill_score` au moment de noter une mission
réelle (`src/matching/matcher.py`, méthode publique `Matcher.covers`) : un
terme jugé « couvert » par le rapport l'est aussi au moment du matching, et
inversement un terme signalé comme manquant est un terme qui, aujourd'hui,
fait vraiment baisser le score de FIT de toute mission qui le porte.

Les termes non couverts sont ensuite filtrés par fréquence — au moins 5
missions distinctes par défaut (`--min-freq`) — pour séparer un point
aveugle réel d'un outil cité une seule fois. En dessous du seuil, le signal
est trop faible pour agir dessus.

## Distinction candidat / hors profil

Chaque terme manquant et fréquent est classé :

- **Candidat à examiner** : ne recoupe aucun groupe de
  `domain_exclusions` dans `profile/cv_catalog.json`. Peut être une
  compétence réelle non déclarée (cas de gouvernance IA, LCB-FT,
  acculturation en septembre) ou un outil hors sujet non encore listé
  comme tel — le rapport ne tranche pas, il fournit fréquence, TJM médian
  et un exemple réel pour que la décision humaine soit rapide.
- **Hors profil** : recoupe un groupe `domain_exclusions` déjà déclaré
  (EPC, broadcast, ERP fonctionnel, BPM/case management, comptabilité,
  réseau/infra). Listé pour transparence — le terme a bien été vu — mais
  pas comme candidat à l'ajout.

Cette distinction s'appuie uniquement sur ce que le catalogue déclare déjà
hors profil. Elle ne préjuge pas des candidats : un outil de développement
générique (Java, React) peut être fréquent et bien payé sans pour autant
relever du profil visé — c'est à la lecture humaine de le dire, pas à une
règle supplémentaire inventée pour l'occasion.

## Classement

Par TJM médian décroissant, puis par fréquence. Un terme absent porté par
des missions à 800 € coûte plus cher, en missions qualifiées invisibles,
qu'un terme absent à 400 €.

## Ce que le rapport ne fait pas

- Il ne modifie jamais `profile/cv_catalog.json`. Ajouter un terme à
  `core`/`plus`/`aliases` reste un geste humain, dans l'éditeur, comme
  aujourd'hui.
- Il ne rejoue pas le score de décision complet (FIT + VALEUR) : il mesure
  la couverture du vocabulaire, pas le verdict `apply`/`shortlist`/`reject`
  d'une mission donnée. `scripts/calibrate.py` reste l'outil pour ça.

## Commande

```
make catalogue
```

Exécute `scripts/catalogue.py`, écrit `data/catalogue.md` et affiche un
résumé (comptes, top 15 candidats) sur la sortie standard.

## Sortie

`data/catalogue.md` : deux tableaux — candidats à examiner, hors profil
connu — chacun avec TJM médian, fréquence, terme, et un exemple d'annonce
réelle (titre, société, fourchette de TJM).
