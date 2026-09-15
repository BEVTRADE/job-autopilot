# Reprise — Ciblage missions Free-Work et CV multi-axes

Document de reprise pour poursuivre le travail dans une nouvelle session.

## 1. Objectif du chantier

Analyser l'historique de candidatures Free-Work de Hakim Arezki, en dégager les familles
de missions par clustering, confronter ces familles aux CV existants, puis produire des
versions de CV alignées et des règles de matching mission vers CV.

## 2. Données collectées

Source : API Free-Work, compte utilisateur 1340051.
Point d'entrée découvert : `/api/users/{id}/applications`
Paramètres utiles : `step` et `jobPosting.status`, pagination plafonnée à 30 par page.

- `step=pending` et `jobPosting.status=published` donne les 67 candidatures en cours
- `step=pending` et `jobPosting.status=expired` donne les 1664 archivées
- `step=refused` donne les 170 non retenues
- `step=accepted` ne renvoie rien

Total collecté : 1901 candidatures, du 25 février 2025 au 27 août 2026.

Base SQLite `candidatures.db`, trois tables :

- `missions` : 21 colonnes, une ligne par candidature, avec titre, société, TJM min et max,
  salaire, durée, télétravail, lieu, compétences, description tronquée à 1500 caractères
- `mission_skills` : 5721 lignes, compétences éclatées pour le comptage
- `clusters` : affectation de chaque mission à l'un des 12 clusters, avec libellé

## 3. Résultats de l'analyse

### Volumétrie et prix

1901 candidatures sur 18 mois, environ 100 par mois. TJM médian visé 600 euros,
quartiles 550 et 675, maximum 1310.

Le filtre pertinent pour isoler le haut de gamme est le **plancher** de la fourchette
(`tjm_min >= 650`), qui retient 331 missions. Le plafond (`tjm_max >= 650`) ne discrimine
rien puisqu'il retient 79 pour cent des missions.

### Les 12 clusters, triés par propension à franchir le plancher 650

| Cluster | n | en cours | plancher >=650 | TJM moyen |
|---|---|---|---|---|
| Directeur de projet & programme | 110 | 1 | 32,7 % | 672 |
| Manager transition & Produit | 129 | 5 | 27,1 % | 642 |
| Architecte Solution & Entreprise, urbanisme, TOGAF | 268 | 4 | 23,1 % | 620 |
| IA / Data Science / GenAI | 152 | 17 | 17,8 % | 611 |
| Chef de projet IT & Data | 164 | 2 | 17,7 % | 617 |
| Data lead / Consulting / Gouvernance | 368 | 15 | 16,8 % | 611 |
| Cloud GCP & Platform | 97 | 4 | 16,5 % | 610 |
| Dev Python / LLM / MLOps | 142 | 2 | 12,7 % | 597 |
| Cloud & DevOps Azure/AWS | 159 | 6 | 12,6 % | 596 |
| BI / Power BI / Analytics | 119 | 5 | 10,9 % | 578 |
| Business Analyst / Finance | 55 | 2 | 10,9 % | 608 |
| Data Engineering | 138 | 4 | 5,1 % | 566 |

### Constats principaux

Les trois familles les mieux payées ne totalisent que 10 candidatures en cours sur 67.
L'effort se concentre sur IA et Data Science, avec 17 candidatures en cours, pour un taux
de haut de gamme de seulement 17,8 pour cent.

Le sous-ensemble Architecte d'entreprise et Urbaniste SI affiche le meilleur taux de toutes
les sous-familles d'architecture, 36,8 pour cent au-dessus du plancher 650 avec un TJM
médian de 725, alors qu'aucune candidature en cours ne le vise.

Le Data Engineering est l'angle mort tarifaire : 222 candidatures pour 5,1 pour cent
au-dessus du plancher.

TOGAF apparaît dans 17 des 62 missions d'architecture à plancher 650. C'est le marqueur
de séniorité le plus demandé sur ce segment et il est absent des CV. Question ouverte :
certification détenue ou non.

### Confrontation aux CV existants

Six fichiers trouvés dans Téléchargements, correspondant en réalité à deux positionnements
seulement, avec des variantes cosmétiques : AI Platform Manager et Data Platform Product
Manager, tous deux en anglais.

Scores de similarité cosinus entre CV et centroïdes de clusters : les trois clusters les
mieux payés obtiennent des scores de 0,04 à 0,07, soit une correspondance quasi nulle.
Les CV couvrent correctement Data lead à 0,338, BI et Power BI à 0,274, et Data Engineering
à 0,226, c'est-à-dire les trois clusters les moins rémunérateurs.

## 4. CV produits

Quatre axes, en français et en anglais, huit fichiers. Faits, missions, dates et
technologies strictement identiques dans les quatre ; seuls changent le titre, l'accroche,
l'ordre des rubriques et le vocabulaire des réalisations.

- Directeur de programme Data et IA, orienté pilotage, trajectoire, arbitrages,
  business cases, vagues de migration, conduite du changement
- Architecte d'entreprise et Urbaniste SI, orienté vues métier applicative données
  technique, autorité de conception, cartographie de portefeuille, livrables d'architecture
- Architecte IA et IA générative, orienté agentique, RAG, LLMOps, métriques d'évaluation
- Consultant Data et BI, orienté Power BI, DAX, ETL, Snowflake, Dataiku, migration Cognos

Points restés à traiter : remplacer les placeholders de contact, corriger la date de
disponibilité qui indique encore le 1er septembre 2026, trancher la question TOGAF.

## 5. Étape suivante prévue

Écriture des règles de matching mission vers CV : un scoring qui, pour une mission donnée,
indique lequel des quatre CV envoyer et avec quel niveau de confiance. Toute la matière
nécessaire est dans `candidatures.db`.

## 6. Contenu du paquet

- `candidatures.db` : base SQLite des 1901 candidatures avec clusters
- `freework_candidatures.json` : export brut de l'API
- `cv_finaux/` : les 8 CV au format Word
- `cv_sources/` : les sources markdown des 8 CV et le fichier de style Word
- `cv_originaux/` : les 6 CV d'origine convertis en texte
