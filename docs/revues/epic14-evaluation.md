# Évaluation — EPIC-14, personnalisation du CV par un modèle local

Branche `epic-14-llm-local`. Évaluation du 19 septembre 2026, Mac 24 Go.
**Conclusion : la règle d'arrêt s'applique. Plus d'une proposition sur deux est refusée à raison, pour les deux modèles (91 % et 92 %). L'étape 5 (branchement) n'est pas commencée ; l'arbitrage est au candidat.**

## Méthode

- **20 annonces**, texte complet (1 093 à 6 029 caractères, minimum fixé à 800), lues dans `data/radar.db` en lecture seule. Aucune page n'a été relue sur Free-Work. 89 annonces `apply` ou `shortlist` répondaient au critère de longueur ; 20 retenues (1 `apply`, 19 `shortlist`), réparties par CV d'axe : 8 IA/GenAI, 8 urbaniste, 2 Data/BI, 2 Enterprise Architect en anglais. La répartition est volontairement équilibrée, pas représentative du flux (78 des 99 annonces `apply`/`shortlist` sont sur l'axe urbaniste).
- **Entrée du modèle** : titre, compétences listées, description complète, zone modifiable du CV d'axe (titre et accroche), profil maître complet sans coordonnées. Sortie en JSON contraint par schéma, température 0.
- **Modèles** : `qwen2.5-coder:14b` (9,5 Go) et `mistral:7b-instruct-v0.3-q4_K_M` (5,1 Go). `num_ctx` 8192 pour les deux. Un seul modèle chargé à la fois (`ollama stop` avant chaque lot, contrôlé par `/api/ps`). Mistral 24B, abandonné (voir `docs/llm-local.md`).
- **Deux passes.** Passe 1 : validateur d'origine, sert de référence « avant ». Passe 2 : validateur corrigé, sert de résultat final. Les réponses brutes des modèles sont conservées (`data/output/eval-epic14/`, ignoré par git) ; rejouer le validateur sur elles donne exactement les chiffres de la passe 2 (Qwen 7 acceptées / 73 refusées, Mistral 6 / 71).
- Scripts : `scripts/evaluer_llm_local.py` (`--selectionner`, `--modele`, `--revalider`).

## Refus : vrais et faux, avant et après correction

Définition retenue : **vrai refus** = la proposition emploie un mot ou cite un texte absent du profil maître ou du CV ; **faux refus** = le validateur se trompe (pluriel, singulier, féminin, casse, apostrophe, mot outil).

| | Qwen avant | Qwen après | Mistral avant | Mistral après |
|---|--:|--:|--:|--:|
| Propositions | 80 | 80 | 77 | 77 |
| Acceptées | 3 | 7 | 5 | 6 |
| Refus, vrais | 73 | 73 | 71 | 71 |
| Refus, faux | **4** | 0 | **1** | 0 |
| Part des propositions refusées à raison | 91 % | 91 % | 92 % | 92 % |
| — dont motif « termes absents du profil » (vrais refus seuls) | 73 | 73 | 44 | 45 |
| — dont motif « texte d'origine absent de la zone » | – | – | 26 | 25 |
| — dont motif « vide ou identique » | – | – | 1 | 1 |

**Les 5 faux refus, tous relus à la main :**

| Modèle | Annonces | Proposition | Cause du faux refus |
|---|---|---|---|
| Qwen | 1, 2, 4, 8 | « Responsable de l'ensemble de la chaîne **opérationnelle** » | « opérationnelle » refusé, le CV dit « Opérationnel » (féminin) |
| Mistral | 2 | avant : « Lead technique » | le CV écrit « lead technique » en minuscules (casse) |

Deux effets secondaires sans changement de décision : 27 autres refus de Qwen (et 16 de Mistral) citaient à tort au moins un mot (« bancaires », « environnements », « cibles »…) mais contenaient aussi de vrais termes absents ; et l'annonce 7 de Mistral (« Architecte IA ET IA GÉNÉRATIVE… » pour un titre en capitales) était refusée pour la casse alors qu'elle l'est à raison, à cause du mot « expert ».

**Correction** (`src/cv/personnaliser.py`, un test par cas dans `tests/test_llm_local.py`) :

1. `_formes` : un mot est admis si sa forme fléchie (pluriel, féminin `-el`/`-elle`, `-é`/`-ée`) est au profil. Aucun mot n'est ajouté au vocabulaire ; aucun mot de l'annonce n'est utilisé. Gardes de longueur pour ne pas rapprocher « sas » de « sa » ni « domaine » de « domain » (testés).
2. `_localiser` : le texte « avant » recopié avec une autre casse, d'autres espaces ou l'apostrophe droite est retrouvé dans le CV ; c'est l'extrait réel du CV qui est envoyé au serveur MCP.

**Rien d'autre n'a été touché**, faute de cas observé : aucun faux refus dû au trait d'union ni à un accent (« œuvre » est absent du profil sous les deux graphies). Les mots outils « ainsi », « notamment », « lorsque », « jusqu' » figurent parmi les termes refusés mais dans aucun refus à eux seuls : `MOTS_OUTILS` est inchangé.

### Ce que sont les vrais refus

Qwen, 73 refus : 65 contiennent au moins un mot repris de l'annonce, 22 un niveau ou une expertise (`expert`, `senior`, `staff`, `confirmé`, `expertise`), 8 sont des paraphrases du modèle qui ne sont ni dans l'annonce ni au profil (`robuste`, `infrastructure`, `assurant`). Le modèle cherche à calquer l'annonce : « Architecte IAM Senior », « Expert fonctionnel senior CSM Pro ServiceNow ». Le validateur remplit son rôle : ces intitulés affirmeraient des compétences que le profil n'atteste pas.

Mistral 7B, 71 refus : 25 recopient du texte de l'annonce comme s'il venait du CV (« avant » invalide), dont trois propositions rédigées en anglais (« We accompany major players… »), 45 emploient des mots hors profil, 1 est vide.

## Substitutions acceptées

13 au total, aucune n'est à envoyer sans relecture. **Compétences ou affirmations douteuses :**

| Modèle | Annonce | Substitution acceptée | Réserve |
|---|---|---|---|
| Qwen | 1 | Accroche remplacée par le résumé par défaut du profil : « Lead Tech IA \| Lead Data Scientist avec **15 ans** d'expérience… Expérience significative en Python, Databricks… » | Texte issu du profil (`summary_default`), donc pas inventé. Mais il **écrase l'accroche propre à l'axe** (IA générative, régulé) et contredit le CV d'axe : 12 ans, 15 avec la recherche doctorale. Aucune adaptation à l'annonce. Écart entre profil et CV à trancher par le candidat. |
| Qwen | 1, 2, 4, 8 | « **Responsable** de l'ensemble de la chaîne opérationnelle », avec « gestion des agents IA » ou « gestion du risque d'hallucination » | Affirmation de responsabilité absente du profil. « responsable » n'est admis que par « IA responsable » : autre sens du mot. **Faille du validateur, non corrigée** (il juge des mots, pas leur sens). |
| Qwen | 11 (CV anglais) | Titre « LEAD ARCHITECTE CLOUD AZURE » à la place de « ENTERPRISE ARCHITECT — IT URBANISATION, DATA AND AI » | Titre en français sur un CV anglais, axe d'urbanisation abandonné, leadership Azure non attesté (le profil ne liste que des services Azure). |
| Mistral | 2 | Paragraphe « Socle Data solide (Snowflake, Databricks, dbt, Power BI) garantissant… » remplacé par le seul mot « **Snowflake** » | **Destructeur** : un paragraphe entier réduit à un mot. Accepté car tous les mots sont au profil. |
| Mistral | 2 | « lead technique » → « Cadrage technique & architecture IA » | Donne « Architecte et Cadrage technique & architecture IA IA, 12 ans… » : agrammatical, « IA » doublé. Cette substitution était un faux refus ; elle passe maintenant, avec ce résultat. |

Acceptables : Qwen n° 5, titre « LEAD IA / ARCHITECTE IA & MLOPS », composé de titres cibles du profil (`target_titles`), à confirmer par le candidat. Mistral n° 14 (4 substitutions) : abrègements sans apport, dont « 12 ans d'expérience » sans la parenthèse doctorale, plutôt plus prudent que le CV.

Nouvelles lacunes du validateur, à décider : aucun garde-fou sur la longueur (un paragraphe peut être vidé), sur la langue (français sur CV anglais) ni sur le sens d'un mot. Je n'y ai pas touché : la consigne était de ne corriger que les faux refus.

## Qualité du français

- **Qwen 2.5 Coder 14B** : français correct et fluide, aucune proposition en anglais sur les 72 destinées à des CV français. Défauts : reprend le vocabulaire de l'annonce (refusé par le validateur) ; au moins une proposition acceptée en français sur un CV anglais (annonce 11).
- **Mistral 7B** : 3 propositions sur 69 en anglais, une faute (« Formaler »), une substitution agrammaticale acceptée (annonce 2), des citations du texte de l'annonce prises pour du texte du CV.
- **Écarts signalés** (compétences demandées et absentes du profil) : Qwen en donne pour 18 annonces sur 20, dont 4 à tort ; Mistral 14 annonces, dont 35 à tort (Airflow, Gouvernance de l'IA, Copilot Studio : présents au profil).

## Durée par annonce

| | Qwen 14B | Mistral 7B |
|---|--:|--:|
| Durée totale par annonce, min / médiane / moyenne / max | 26 / 33 / 36 / 65 s | 8 / 18,5 / 19,5 / 36 s |
| 20 annonces | 12 min | 6,5 min |
| Dont analyse du prompt, médiane | 3,9 s | 3,1 s |
| Dont génération, médiane | 27 s | 13 s |
| Chargement à froid, maximum | 6,3 s | 3,6 s |
| Jetons du prompt, min / médiane / max | 3 897 / 4 264 / 4 946 | 4 604 / 5 018 / 5 848 |
| Jetons de sortie, médiane / max | 550 / 797 | 472 / 652 |

Le prompt complet fait 3 900 à 5 800 jetons selon le modèle (le tokenizer de Mistral en compte davantage) : le « environ 5 000 » se confirme. Avec la sortie, le maximum est de 6 500 jetons, sous les 8 192 : aucune troncature. À 16 384 de contexte, Qwen mettait 115 s au lieu de 55 s sur l'annonce de test.

## Mémoire

| | Qwen 14B | Mistral 7B |
|---|---|---|
| Taille chargée | 9,5 Go, 100 % GPU | 5,1 Go, 100 % GPU |
| Mémoire libre pendant le lot (passe 2) | 22 à 45 % | 41 à 55 % |
| Swap utilisé pendant le lot (passe 2) | 8,9 à 9,9 Go | 8,1 à 8,9 Go |
| Passe 1 (swap) | 9,8 à 11,7 Go | 10,0 à 10,1 Go |

Le swap n'est pas imputable aux modèles : il était déjà à 7,2 Go avant le premier chargement, Ollama vide, et n'est pas redescendu entre les lots. Le poste est chargé par autre chose. Pour mémoire, Mistral 24B tournait à 14 % CPU / 86 % GPU avec 13,7 à 14,2 Go de swap et dépassait 300 s.

## Détail par annonce (passe 2)

Colonnes de résultats : durée, puis propositions / acceptées / refusées.

| n | CV d'axe | Source | Note | Annonce (car.) | Qwen | Mistral |
|--:|---|---|---|--:|---|---|
| 1 | IA/GenAI | FreelanceRepublik | shortlist | 2570 | 65 s, 4/2/2 | 28 s, 4/0/4 |
| 2 | IA/GenAI | Free-Work | shortlist | 2215 | 38 s, 4/1/3 | 19 s, 4/2/2 |
| 3 | IA/GenAI | Free-Work | shortlist | 1888 | 30 s, 4/0/4 | 19 s, 3/0/3 |
| 4 | IA/GenAI | Free-Work | shortlist | 2828 | 40 s, 4/1/3 | 16 s, 4/0/4 |
| 5 | IA/GenAI | Free-Work | shortlist | 3888 | 32 s, 4/1/3 | 20 s, 4/0/4 |
| 6 | IA/GenAI | FreelanceRepublik | shortlist | 2326 | 35 s, 4/0/4 | 13 s, 4/0/4 |
| 7 | IA/GenAI | Free-Work | shortlist | 1212 | 31 s, 4/0/4 | 18 s, 4/0/4 |
| 8 | IA/GenAI | Free-Work | shortlist | 2129 | 43 s, 4/1/3 | 20 s, 3/0/3 |
| 9 | Data/BI | Free-Work | shortlist | 1162 | 41 s, 4/0/4 | 30 s, 4/0/4 |
| 10 | Data/BI | FreelanceRepublik | shortlist | 2226 | 27 s, 4/0/4 | 16 s, 4/0/4 |
| 11 | EN Ent.Arch. | Freelance-Informatique | shortlist | 6029 | 48 s, 4/1/3 | 36 s, 4/0/4 |
| 12 | EN Ent.Arch. | Free-Work | shortlist | 1441 | 26 s, 4/0/4 | 15 s, 4/0/4 |
| 13 | Urbaniste | Free-Work | apply | 1247 | 45 s, 4/0/4 | 29 s, 4/0/4 |
| 14 | Urbaniste | Free-Work | shortlist | 1255 | 30 s, 4/0/4 | 19 s, 4/4/0 |
| 15 | Urbaniste | Free-Work | shortlist | 1912 | 30 s, 4/0/4 | 15 s, 4/0/4 |
| 16 | Urbaniste | Free-Work | shortlist | 2561 | 34 s, 4/0/4 | 18 s, 4/0/4 |
| 17 | Urbaniste | FreelanceRepublik | shortlist | 2318 | 32 s, 4/0/4 | 11 s, 3/0/3 |
| 18 | Urbaniste | FreelanceRepublik | shortlist | 2666 | 28 s, 4/0/4 | 8 s, 4/0/4 |
| 19 | Urbaniste | Free-Work | shortlist | 3452 | 38 s, 4/0/4 | 23 s, 4/0/4 |
| 20 | Urbaniste | Free-Work | shortlist | 1093 | 27 s, 4/0/4 | 15 s, 4/0/4 |

Annonces où le CV est réellement adapté : Qwen 6 sur 20, Mistral 2 sur 20. Aucune défaillance du modèle ni du serveur MCP : les 40 exécutions ont abouti, le CV d'axe est rendu inchangé quand tout est refusé.

## Limites de cette évaluation

- Une seule exécution par annonce et par modèle, à température 0. La passe 2 confirme la passe 1 (mêmes acceptations une fois le validateur corrigé).
- Le texte des annonces est celui conservé par le radar (le détail d'origine n'est pas archivé), pas une relecture des pages.
- Le PDF n'a été inspecté que sur la vérification de l'étape 3 (première page sur 4), pas sur ces 40 CV.
- Pas de note de qualité chiffrée du français : jugement du relecteur sur les propositions.

## Options pour l'arbitrage

1. **Changer la consigne, garder Qwen 14B.** Interdire explicitement de reprendre les mots de l'annonce, ajouter deux exemples de substitution valide, demander de ne réordonner que des mots du CV et du profil. Coût faible, gain incertain : les refus viennent d'un comportement de calque.
2. **Passer d'une rédaction libre à une sélection.** Le modèle choisit un intitulé parmi `target_titles` du profil et l'ordre des blocs de l'accroche ; il n'écrit plus de texte. Zéro invention possible, refus quasi nuls, mais adaptation plus limitée. C'est un changement de conception d'EPIC-14.
3. **Accepter le taux actuel** : 6 CV adaptés sur 20 avec Qwen, dont plusieurs à ne pas envoyer sans relecture. Seul, ce résultat ne justifie pas de brancher l'étage.
4. **Renforcer le validateur** (longueur, langue, sens) avant toute décision : à faire dans tous les cas si l'option 1 ou 3 est retenue, car les lacunes ci-dessus laissent passer des remplacements destructeurs.

Pas de modèle plus grand : le 24 Go ne tient pas Mistral 24B.
