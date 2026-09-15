# Chantiers — spécifications et commande associée

Chaque chantier a une spécification et un point d'entrée. `make` seul liste
les cibles disponibles.

## En service

| Chantier | Spécification | Commande |
|---|---|---|
| Collecte et notation | `docs/sources.md`, `docs/README-architecture.md` | `make veille` |
| Chaîne du matin, sans envoi | `docs/autonomie.md` | `make simu` |
| Candidature réelle | `docs/autonomie.md` | `make candidater-pour-de-vrai` |
| Rapport consolidé | `docs/autonomie.md` | `make rapport`, `make attente` |
| Tests hors ligne | `docs/autonomie.md` | `make test` |
| Planification quotidienne | `docs/autonomie.md` | `make planifier`, `make deplanifier` |
| Arrêt d'urgence | `docs/README-architecture.md` | `make stop`, `make reprendre` |

## À faire

### Chantier 1 — première candidature réelle

Le seul blocage véritable. `scripts/apply.py` n'a jamais envoyé.
Spécification : `docs/autonomie.md`, étapes 1 à 4.
Commandes : `make install`, `make login`, `make test`, `make simu`, puis
`MAX=1 make candidater-pour-de-vrai` sur une mission peu stratégique.

### Chantier 2 — passe systématique sur le catalogue

Confronter les huit CV au vocabulaire des 1901 missions collectées. Trois
points aveugles trouvés en une seule journée début septembre : gouvernance IA,
fraude et LCB-FT, acculturation. Il en reste probablement.
Spécification à écrire : `docs/catalogue.md`.
Commande à créer : `make catalogue` s'appuyant sur `scripts/calibrate.py`.

### Chantier 3 — sources restantes

Freelance-Informatique, Freelance-Day, FreelanceRepublik, TED.
Spécification : `docs/sources.md`, section « à intégrer ».
Chaque source est une classe dans `src/sources/`, sur le modèle de
`freework.py`. La commande existe déjà : `make veille` les prendra
automatiquement une fois déclarées dans `scripts/collect.py`.

### Chantier 4 — empreinte de déduplication

Le regroupement se fait aujourd'hui sur titre et société. Une même mission
publiée par trois intermédiaires porte trois sociétés différentes et passe
trois fois — constaté les 8, 9 et 15 septembre. L'empreinte doit se calculer
sur le titre normalisé et le corps de l'annonce.
Fichier concerné : `src/store.py`.

### Chantier 5 — personnalisation du CV par mission

Aujourd'hui le CV d'axe part tel quel. Un appel à `claude -p` adapterait les
phrases avant envoi, sur l'abonnement Pro et non sur des crédits API.
À trancher après avoir observé la qualité des CV d'axe envoyés bruts.

### Chantier 6 — interface de validation

File d'attente des candidatures bloquées, visualisation des captures,
validation avant envoi. Le fichier `file_attente.json` en est la matière
première.
