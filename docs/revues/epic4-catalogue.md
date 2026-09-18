# Revue — EPIC-4, passe systématique sur le catalogue

Branche `epic4-catalogue`, commit `bc15b39`. Revue du 18 septembre 2026.
**Avis : fusionnable sous réserve.**

## Contenu livré

`scripts/catalogue.py` (232 lignes), `tests/test_catalogue.py`,
`docs/catalogue.md`, huit lignes ajoutées à `src/matching/matcher.py`
(`Matcher.covers`), `Makefile` et `docs/chantiers.md` mis à jour.

## Critères d'acceptation

**1. `make catalogue` produit un rapport de termes manquants — tenu.**
Exécution réelle de `scripts/catalogue.py` sur `reprise/candidatures.db`,
1901 missions confirmées par requête SQL : 609 étiquettes distinctes,
348 absentes du catalogue, 62 candidats et 3 hors-profil au seuil par défaut
de 5. Sortie écrite dans `data/catalogue.md`.

**2. Fréquence, TJM médian et exemple d'annonce par terme — tenu.**
Vérifié dans le code (`tableau()`, `fmt_exemple`) et par test :
`test_candidat_vs_hors_profil` contrôle la fréquence, la médiane et la société
d'exemple sur un jeu de données construit à la main.

**3. Distinction compétence réelle / hors profil — tenu.**
Par recoupement avec `domain_exclusions` du catalogue. Testé : Paie classé hors
profil, MLOps classé candidat.

**4. Aucune modification automatique du catalogue — tenu.**
`CATALOG` n'est jamais ouvert en écriture ; seul `OUT`, soit
`data/catalogue.md`, l'est. Aucun appel d'écriture vers
`profile/cv_catalog.json` nulle part dans le script.

## Substance des tests

Les quatre tests reposent sur une fixture SQLite et JSON minimale mais
réaliste — six missions, quatre étiquettes dont une couverte, une rare, une
hors profil — et vérifient des valeurs précises : médiane à 600, société
d'exemple au TJM maximal. Pas de faux confort détecté.

Réserve mineure : `covers()` n'a pas de test unitaire direct sur `Matcher`, il
n'est exercé qu'indirectement par `test_couvert_absent_du_rapport`. Suffisant,
pas généreux.

## Ce qui manque

- **Médiane vide indiscernable de zéro.** Si un terme n'a aucune mission avec
  TJM renseigné, `med([])` renvoie 0, affiché « 0 € » dans le tableau. Aucun
  cas réel aujourd'hui, vérifié sur les 609 étiquettes. Défaut latent, pas
  actif.
- **`data/catalogue.md` n'est pas ignoré par git**, contrairement à
  `data/output/` et `data/*.db`, alors qu'il est régénéré à chaque exécution.
  D'où le fichier non suivi visible sur `main`.
- **Coquille dans l'aide du Makefile** : `make catalogue` y est annoncé comme
  produisant `docs/catalogue.md`, alors que la sortie réelle est
  `data/catalogue.md`. La cible elle-même l'annonce correctement.

## Point d'attention — `Matcher.covers()`

Le moteur est calibré sur 1901 missions et ne doit pas bouger. Vérifié de deux
façons complémentaires.

**Lecture du code.** `covers()` appelle `self._skill_score(...)` existant et en
lit le résultat. Aucune écriture d'état, aucune modification de
`_skill_score`. Les huit lignes sont additives et pures.

**Preuve empirique.** `scripts/calibrate.py`, qui rejoue le scoring sur les
1901 missions, a été exécuté sur `main` et sur `epic4-catalogue`, et les deux
sorties diffées : identiques. Le moteur ne bouge pas.

**Pourrait-on s'en passer ?** `covers()` dépend de `self._norm_axis` et
`self.aliases`, construits à l'initialisation à partir du catalogue et des huit
fiches CV — état interne à `Matcher`. L'écrire dans `scripts/catalogue.py`
obligerait soit à exposer ces structures privées, soit à dupliquer la logique
de correspondance : sous-chaîne, alias, pondération core, plus et blob,
indépendamment de `_skill_score`.

Le risque concret est la dérive : si `_skill_score` évolue — nouvelle règle
d'alias, nouvelle pondération — sans que la copie externe suive, le rapport
dirait « manquant » pour un terme que le matching couvre déjà, ou l'inverse.
Pour huit lignes en lecture seule, garder une seule définition de « couvert »
dans la classe qui la calcule déjà est le compromis le moins cher : pas de
duplication, pas de fuite d'encapsulation au-delà d'une méthode publique
dédiée.

## `docs/catalogue.md` et `data/catalogue.md` — pas un doublon

Deux objets différents. `docs/catalogue.md`, suivi par git, est la
spécification du mécanisme : pourquoi, comment, et ce que le rapport ne fait
pas. `data/catalogue.md`, non suivi, est la sortie d'une exécution, au même
titre que `data/output/`. Les deux doivent exister ; seul le second doit
rejoindre le `.gitignore`.

## Réserves à lever avant fusion

1. Ajouter `data/catalogue.md` au `.gitignore`.
2. Corriger le libellé de l'aide du Makefile, `docs/` devient `data/`.

Aucune de ces réserves ne touche à la correction du moteur ni à la valeur du
rapport.
