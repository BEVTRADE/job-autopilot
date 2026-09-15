# job-autopilot — radar de missions

Surveille plusieurs sources de missions freelance, note chacune contre vos 4 axes
de CV, et remonte un rapport quotidien des rares opportunités qui valent le coup.

**Ce n'est pas un automate de candidature de masse.** La calibration sur vos 1901
candidatures réelles montre qu'au plancher de 650 €, le marché produit environ
6 missions qualifiées par mois. Le rôle du robot est de n'en rater aucune.

## Démarrage

```bash
cd ~/Projects/job-autopilot
python3 scripts/collect.py --source freework --limit 40 --no-store --open
```

Aucune dépendance à installer : tout est en bibliothèque standard Python.
Aucune candidature n'est envoyée — le script ne fait que remonter et classer.

Une fois le résultat satisfaisant, retirez `--no-store` pour activer
l'historique et le dédoublonnage, et montez `--limit`.

## Commandes

| Commande | Effet |
|---|---|
| `python3 scripts/collect.py` | toutes les sources, historique actif |
| `python3 scripts/collect.py --source boamp` | une seule source |
| `python3 scripts/collect.py --limit 40 --no-store` | essai rapide, sans écriture |
| `python3 scripts/calibrate.py` | rejoue le moteur sur les 1901 candidatures historiques |

Le rapport HTML atterrit dans `data/output/<date>/rapport.html`,
les données brutes dans `retenues.json`.

## Structure

```
profile/
  master_profile.json    profil consolidé
  cv_catalog.json        les 4 axes : intitulés, compétences signature, fichiers CV
src/
  matching/text.py       normalisation, TF-IDF, cosinus — stdlib
  matching/matcher.py    moteur FIT / VALEUR / décision
  sources/base.py        socle : fetch, HTML→texte, extraction TJM/durée/remote
  sources/freework.py    découverte par sitemap + pré-filtre famille de métier
  sources/boamp.py       API open data des marchés publics
  store.py               SQLite : historique, dédoublonnage 120 jours
scripts/
  collect.py             pipeline complet + rapport HTML
  calibrate.py           validation sur l'historique
reprise/
  candidatures.db        1901 candidatures Free-Work, 12 clusters
  cv_finaux/             les 8 CV Word
  cv_sources/            sources markdown des CV
```

## Réglages

`src/matching/matcher.py`, classe `Params` :

```python
tjm_floor_hard = 600      # en dessous : rejet sec
tjm_floor_soft = 650      # plancher "haut de gamme"
tjm_target     = 850      # au-delà : valeur maximale
min_fit        = 45       # adéquation minimale pour être considéré
min_decision_shortlist = 60
min_decision_apply     = 72
```

Les familles de métier scannées sur Free-Work : `src/sources/freework.py`,
constante `FAMILY_KEYWORDS`. Rendements mesurés sur l'historique :

| Famille | ≥ 650 € |
|---|---|
| Manager de transition | 67 % |
| Architecte d'entreprise / urbaniste SI | 42 % |
| Consultant en architecture | 39 % |
| Architecte de base de données | 25 % |

## Sources

| Source | État | Accès |
|---|---|---|
| Free-Work | intégrée | sitemaps XML publics, sans compte |
| BOAMP (marchés publics) | intégrée | API open data, sans clé |
| Freelance-Informatique | à faire | rendu serveur, sans compte |
| FreelanceRepublik | à faire | compte requis |
| TED (UE) | à faire | API publique |

Non automatisables — fonctionnement *inbound*, aucune liste à parcourir :
Malt et Malt Strategy, Comet, Crème de la Crème, LeHibou, Talent.io.
Pour celles-là, l'investissement rentable est un profil optimisé, pas un robot.
