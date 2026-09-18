# Revue — EPIC-2, regroupement par empreinte de contenu

Branche `epic2-empreinte`, commit `dda70ca`, un seul commit issu de `main`.
Revue du 18 septembre 2026.
**Avis : fusionnable sous réserve, mais sans effet tant que le module n'est
pas branché.**

## Contenu livré

`src/grouping.py` (131 lignes) et `tests/test_grouping.py` (243 lignes).
Rien d'autre. Le lot est strictement contenu.

Mécanique : normalisation du texte (accents, casse, ponctuation), retrait de
mots vides métier — *mission*, *poste*, *profil*, *contexte* —, n-grammes de
trois mots sur le titre et le corps, similarité de Jaccard, seuil à 0,20, et
regroupement transitif par union-find. La société est explicitement exclue de
l'empreinte, ce qui est la décision juste : c'est elle qui varie d'un
intermédiaire à l'autre pour une mission identique.

## Critères d'acceptation

**1. Annonces de sociétés différentes décrivant la même mission regroupées —
tenu.** Les trois cas réels de septembre sont rejoués en fixtures : Meudon à
trois intermédiaires, VOLT/AMIA en deux grades, réassurance KEONI contre
CAT-AMANIA.

**2. Missions distinctes aux titres proches non regroupées — tenu.**
Test négatif présent. Vérifié aussi en dehors des fixtures : deux annonces sans
rapport donnent une similarité inférieure à 0,1.

**3. Le groupe expose le mieux-disant et l'écart — tenu sur le principe,
défaillant sur les bords.** Voir la réserve ci-dessous.

**4. Aucune annonce supprimée ni masquée — tenu, vérifié empiriquement.**
Exécution sur les 55 annonces réelles présentes dans `data/` : 51 groupes
formés, 4 groupes multi-annonces, **55 annonces conservées sur 55**. Rien ne
disparaît.

**5. Tests sur les trois cas réels, en données figées — tenu.**
11 tests, tous passants.

## Substance des tests

Ils vérifient des valeurs précises, pas l'absence de plantage : l'ensemble
exact des sociétés d'un groupe, `spread == 214` pour Meudon (500 moins 286,
conforme à la veille du 8 septembre), `spread == 250` pour la réassurance, le
TJM conservé société par société, et le total d'annonces avant et après
regroupement. Deux tests couvrent l'empreinte elle-même — insensibilité aux
accents et à la casse, similarité nulle sur des missions sans rapport.
Pas de faux confort.

## Comportement sur données réelles

Sur les 55 annonces collectées, quatre groupes se forment, tous plausibles :

| Annonces | Mission | Écart |
|---|---|---|
| 2 | Architecte IA (H/F) — STORM GROUP 600-700, Freelance.com 400-700 | 300 € |
| 2 | Tech Lead Data Cloud Senior Azure/Databricks — Signe +, EterniTech | n.c. |
| 2 | Architecte d'entreprise Supply Chain — Hibyrd, FRISBEE PROFILING | 50 € |
| 2 | Urbanisation SI / Architecture d'Entreprise — n.c., RIDCHA DATA | 230 € |

Aucun regroupement abusif visible. Le seuil de 0,20 paraît bien réglé sur ce
jeu.

## Ce qui manque

**L'écart est faux quand une annonce du groupe n'a pas de TJM.** Cas vérifié :
un groupe où A n'affiche aucun TJM et B affiche 600-650 renvoie
`spread = 50`. Ce n'est pas un écart entre intermédiaires, c'est la largeur de
la fourchette de B, présentée comme s'il s'agissait d'une comparaison. Le
tableau ci-dessus en contient un cas réel, la ligne Supply Chain. C'est
trompeur pour la décision, et c'est précisément l'usage du champ.
Correction attendue : ne calculer l'écart que sur les annonces ayant un TJM, et
indiquer combien d'annonces du groupe n'en ont pas.

**Le mieux-disant est arbitraire quand aucune annonce n'a de TJM.** Le tri
retombe sur `-1` pour tous, et `max` renvoie le premier rencontré. Le groupe
Tech Lead Data Cloud du tableau est dans ce cas. Ce n'est pas faux, c'est
indéterminé — mais rien ne le signale.

**Un corps d'annonce vide rend l'empreinte purement titulaire.** Deux annonces
au même titre et sans corps atteignent une similarité de 1,0. À l'inverse, la
même mission avec et sans corps tombe à 0,125, sous le seuil, donc **ne se
regroupe pas**. Le module est donc sensible à la qualité d'extraction du corps :
une source qui remonte mal les descriptions cassera le regroupement sans
qu'aucune erreur ne soit levée. À documenter au minimum, à traiter avant
EPIC-3 qui ajoute quatre sources.

## Intégration — le point qui change la portée de la fusion

**`src/grouping.py` n'est appelé nulle part.** Ni `scripts/collect.py` ni
`src/store.py` ne le référencent sur la branche. La déduplication réelle
continue de se faire sur `uid`, donc sur l'URL.

Le module est correct, testé, et inerte. Fusionner cette branche ne change
strictement rien au comportement du radar : la même mission publiée par trois
intermédiaires passera toujours trois fois.

Il manque un lot de branchement — appeler le regroupement dans la chaîne de
collecte et afficher les groupes dans le rapport plutôt que les annonces
isolées. C'est le complément naturel d'EPIC-2, et il conditionne toute la
valeur annoncée.

## Réserves à lever

1. Corriger le calcul de l'écart en présence d'annonces sans TJM, et signaler
   leur nombre.
2. Marquer le mieux-disant comme indéterminé quand aucune annonce n'a de TJM.
3. Documenter, ou traiter, la sensibilité de l'empreinte à un corps d'annonce
   absent — avant EPIC-3.
4. Prévoir le lot de branchement, sans lequel la fusion est sans effet.
