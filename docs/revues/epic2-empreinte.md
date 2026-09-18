# Revue — EPIC-2, regroupement des annonces par empreinte de contenu

Branche `epic2-empreinte`, commit `dda70ca`. Revue du 18 septembre 2026.
**Avis : à retravailler.**

Cette revue remplace une version précédente du même fichier (commit
`5030ee6`), qui concluait « fusionnable sous réserve » à partir d'un
échantillon réel de 55 annonces. Cette version-ci fait tourner le
regroupement sur les 1901 missions de `reprise/candidatures.db` — le jeu de
calibration complet, pas un échantillon du jour — et y trouve un
sur-regroupement massif que le petit échantillon n'a pas révélé (voir
critère 2). **EPIC-7** (`docs/epics.md`), écrit à partir de la revue
précédente, cite ses trois réserves mais pas celle-ci : il doit être relu à
la lumière de ce qui suit avant d'être lancé tel quel.

## Contenu livré

`src/grouping.py` (131 lignes), `tests/test_grouping.py` (243 lignes). Rien
d'autre — ni `src/store.py` ni `scripts/collect.py`, pourtant nommés par
l'epic comme fichiers concernés.

## Critères d'acceptation

**1. Deux annonces de sociétés différentes décrivant la même mission sont
regroupées — tenu sur les fixtures, pas garanti sur les données réelles.**
Sur les trois cas figés (Meudon, VOLT/AMIA, réassurance), tests verts et
recoupement fait avec `data/output/2026-09-08/veille.md` : les chiffres
collent. Mais exécution réelle sur les 1901 missions de
`reprise/candidatures.db` : seules 237 (12,5 %) ont un corps d'annonce non
vide. J'ai pris une paire identique aux fixtures (Meudon, Nicholson contre
Craftman) et vidé le corps d'un seul côté pour simuler ce cas majoritaire :
la similarité tombe de 0,26 (regroupé) à 0,021 (isolé). **Sur la majorité
réelle des annonces déjà collectées, deux publications identiques par deux
intermédiaires ne se regrouperont pas** si l'une des deux sources ne fournit
pas de corps de texte — preuve empirique, pas supposition.

**2. Deux missions réellement distinctes au titre proche ne sont pas
regroupées — tenu sur la fixture, contredit à grande échelle sur les
données réelles.** Le test négatif (Signe + / Hexagone Digitale) passe,
marge confortable (0,022 contre seuil 0,20). Mais en faisant tourner
`group_missions` sur les 1901 missions réelles (1,07 s, aucun plantage) :
**1237 groupes, dont un seul regroupe 293 annonces** — des « Data
Ingénieur », « Architecte solution », « Chef de projet SRE », « Data
Scientist », « Développeur IA », etc., de dizaines de sociétés distinctes
(STHREE, VISIAN, Freelance.com, Cherry Pick, PROPULSE IT…), avec un TJM
affiché de 950-1050 € (`.spread` = 950) alors que certaines annonces du même
« groupe » sont à 100-550 €. Ce ne sont manifestement pas 293 fois la même
mission. Cause identifiée par lecture de `_shingles` : avec un corps vide et
un titre court, le nombre de mots significatifs tombe sous la taille de
shingle (3), et la fonction se rabat silencieusement sur des mots isolés
(unigrammes) au lieu de trigrammes. Deux titres aussi génériques qu'« Architecte
Solution » et « Architecte Solutions » finissent alors à une similarité de
0,33, largement au-dessus du seuil de 0,20 — et la transitivité de
l'union-find propage l'erreur : A se regroupe avec B sur un mot, B avec C sur
un autre, jusqu'à un amalgame de 293 métiers sans rapport. **Le critère 2 est
massivement violé sur les données déjà en main**, pas dans un cas limite
théorique.

**3. Le groupe expose l'intermédiaire le mieux-disant et l'écart de TJM —
tenu au niveau de la structure, non vérifié dans un rapport puisqu'aucun
rapport ne consomme ce module** (voir Intégration ci-dessous). Et quand un
groupe est mal formé comme le méga-groupe de 293, `.best` et `.spread`
produisent un chiffre qui a l'air propre (950 € d'écart) mais qui ne veut
rien dire : le regroupement lui-même est le problème, pas seulement
l'affichage.

**4. Aucune annonce n'est supprimée ni masquée — tenu, vérifié par
exécution réelle, y compris dans le pire cas.** J'ai comparé le nombre de
missions en entrée (1901) à la somme des tailles de tous les groupes
produits, méga-groupe de 293 inclus : égalité exacte, 1901 = 1901. Aucune
perte, même quand le regroupement lui-même est erroné. C'est le point que tu
voulais voir vérifié en priorité — confirmé, y compris à l'échelle réelle,
pas seulement sur les fixtures.

**5. Tests sur les trois cas réels de septembre, données figées — tenu,
avec une réserve de fidélité.** Les faits (société, TJM, ville, dates)
correspondent aux `veille.md`. Le texte des `descr`, en revanche, est
reconstitué — les `veille.md` ne conservent pas le corps brut scrapé — donc
le calibrage du seuil 0,20 s'appuie sur du texte plausible et généreux en
mots-clés partagés, pas sur les octets réellement vus par le scraper.
Or c'est justement l'écart entre ce texte reconstitué (riche) et le texte
réel majoritairement vide qui explique pourquoi les tests passent alors que
le comportement réel diverge.

## Le point qui t'importe le plus — TJM incomparables

Aucune annonce ne disparaît structurellement, y compris avec des TJM
incomparables : vérifié à la fois en synthétique et sur des cas réels tirés
du regroupement des 1901 missions. Exemples réels trouvés dans les groupes
produits :

```
GROUPE (2) best=MoOngy spread=230
   SKILLWISE   None None | Développeur PYTHON SENIOR, environnement DATA
   MoOngy      500  730  | Développeur Python Senior

GROUPE (2) best=SKILLWISE spread=150
   AXONE BY SYNAPSE  None None | DATA PRODUCT OWNER INTERMODAL H/F
   SKILLWISE          400  550 | Data Product Owner
```

Dans les deux cas, l'annonce sans TJM (SKILLWISE, AXONE BY SYNAPSE) reste
bien présente dans `.missions` — rien n'est masqué. Mais `.spread` et
`.best` l'ignorent silencieusement : `spread` ne fait la différence que sur
les valeurs non nulles (`if m.tjm_min is not None`), donc un intermédiaire
qui ne communique pas son TJM disparaît du calcul d'écart sans que rien ne
le signale. Le nombre affiché a l'air complet ; il ne l'est pas.

Sur les fourchettes disjointes (deux TJM qui ne se recouvrent pas du tout),
même chose : j'ai trouvé dans les 1901 missions un groupe
« Lead business analyst » avec des fourchettes 1060-1560 € (ALLEGIS GROUP)
et 400-710 € (Groupe Aptenia) — aucun recouvrement, `spread` = 1160 sans
aucun signal que les deux plages ne se touchent même pas. Rien ne distingue,
dans le code, « deux devis qui se chevauchent pour la même mission » de
« deux plages totalement étrangères l'une à l'autre » — dans les deux cas on
obtient juste `max - min`. Et vu le taux de faux regroupements mesuré au
critère 2, une bonne partie de ces écarts spectaculaires sont probablement
des amalgames, pas de vrais écarts de négociation entre intermédiaires.

**Aucun de ces deux cas (TJM absent, fourchettes disjointes) n'est testé.**
Les cinq tests sur les cas réels utilisent des TJM systématiquement
renseignés des deux côtés.

## Substance des tests

Les tests contrôlent des valeurs précises, pas seulement l'absence de
plantage — `test_meudon_meilleur_intermediaire_et_ecart` vérifie un spread
à 214 exactement, `test_chaque_annonce_garde_sa_societe_et_son_tjm` vérifie
trois tuples TJM par société. Ce n'est pas du confort de façade dans
l'ensemble.

Une exception : `test_meudon_meilleur_intermediaire_et_ecart` fait
`assert grp.best.company in ("Nicholson SAS", "Craftman data")`. Le
docstring de `best` promet un départage déterministe (TJM haut le plus
élevé, TJM bas départageant les ex æquo). J'ai exécuté le code : il choisit
bien Nicholson de façon déterministe (tjm_min 500 contre 300 à tjm_max
égal). Mais le test accepterait tout aussi bien le résultat inverse — il ne
vérifie donc pas la règle de départage qu'il prétend couvrir. Une régression
sur le tie-break passerait inaperçue.

## Ce qui manque

- **Dégradation silencieuse trigramme → unigramme sur texte court.**
  `_shingles` retombe sur des mots isolés dès que le nombre de mots
  significatifs est sous 3, sans avertissement ni changement de seuil en
  conséquence. C'est la cause directe du méga-groupe de 293 annonces sur les
  données réelles (voir critère 2). Un garde-fou minimal — refuser de
  regrouper sur un fingerprint à un seul mot, ou exiger un nombre minimal de
  mots significatifs avant de comparer — n'existe pas.
- **Corps d'annonce vide ou tronqué : géré, mais mal.** Réponse directe à la
  question posée : `_normalize`/`_significant_words` acceptent une chaîne
  vide sans erreur (`fingerprint(titre, "")` fonctionne), mais le
  fingerprint qui en résulte, réduit au titre seul, se comporte différemment
  selon que le titre est spécifique (sous-regroupement, cas Meudon simulé
  vide) ou générique (sur-regroupement massif, cas réel des 293). Aucun test
  ne couvre ni l'un ni l'autre.
- **Missions réellement identiques, rédigées différemment, corps présent
  d'un côté seulement.** Deuxième question posée : c'est le cas majoritaire
  dans les données déjà collectées (1664 missions sur 1901 sans corps). Le
  module suppose implicitement une symétrie — les deux intermédiaires
  fournissent un texte comparable — qui ne correspond pas à ce que
  `scripts/collect.py`/les sources remontent aujourd'hui.
- **`spread` ne signale pas l'incomparabilité.** Ni TJM manquant, ni
  fourchettes disjointes ne sont distingués d'un écart réel et cohérent.
- **`DEFAULT_THRESHOLD = 0.20` non éprouvé au-delà des fixtures.** Sur les
  trois cas réels, la similarité positive mesurée est de 0,25 à 0,79 pour
  une marge de 0,05 à peine au-dessus du seuil côté Meudon — et l'exécution
  à l'échelle réelle montre que le seuil unique ne tient pas quand le texte
  se raccourcit.

## Intégration — n'est branché nulle part

`grep` sur tout le dépôt (hors `src/grouping.py` et son test) : aucune
référence à `group_missions` ou `MissionGroup`. Ni `scripts/collect.py`, ni
`src/store.py` — les deux fichiers que l'epic nomme explicitement comme
concernés — n'ont été modifiés ; `git diff main..epic2-empreinte --stat` le
confirme, seuls `src/grouping.py` et `tests/test_grouping.py` bougent. Le
rapport réellement produit aujourd'hui (`write_report` dans
`scripts/collect.py`, qui écrit `rapport.html`) liste toujours une ligne par
annonce brute, sans le moindre regroupement. **Ce que livre cette branche
est une bibliothèque autonome, testée en vase clos, que rien n'utilise.**
Aucun candidat n'a encore vu un rapport groupé ; la valeur métier décrite
dans l'epic — « choisir l'intermédiaire le mieux-disant » — n'existe pas
encore côté utilisateur.

## Avis : à retravailler

Le squelette (empreinte par n-grammes, Jaccard, union-find, non-suppression)
est propre et la non-suppression est solide, vérifiée jusque sur les 1901
missions réelles sans exception. Mais deux choses en bloquent la fusion en
l'état, pas une simple réserve cosmétique :

1. **Le critère 2 échoue à grande échelle sur les données déjà collectées** :
   un cinquième du corpus fini dans un unique amalgame de 293 métiers sans
   rapport entre eux, à cause de la dégradation trigramme → unigramme sur
   texte court ou vide. Ce n'est pas un cas limite théorique, c'est le
   comportement majoritaire vu que 87,5 % des missions historiques n'ont pas
   de corps d'annonce.
2. **Rien n'est branché.** Sans intégration dans `scripts/collect.py` (et la
   question du dédoublonnage dans `src/store.py`), l'epic ne produit aucune
   valeur observable — le rapport que l'utilisateur consulte n'a pas changé.

Avant de repasser cette branche en revue, il faudrait au minimum : un
garde-fou contre les fingerprints à un ou deux mots (refuser de comparer, ou
exiger une taille minimale de fingerprint avant d'appliquer le seuil), un
test qui rejoue le cas réel du corps vide asymétrique, et le branchement
effectif sur `scripts/collect.py` avec une preuve que le rapport produit
regroupe réellement sans rien masquer — pas seulement `MissionGroup` en
isolation.
