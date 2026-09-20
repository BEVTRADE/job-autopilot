# Modèle de langage local — architecture et vérifications

Décision : ADR-011. Lot : EPIC-14. Mise à jour : 20 septembre 2026.

## Ce qui change, et ce qui ne change pas

Le moteur de décision reste sans modèle de langage (ADR-002) : collecte,
regroupement, notation, choix du CV, réponses filtrantes et soumission ne
changent pas. Le modèle local remplace Claude à deux endroits seulement.

| Rôle | Avant | Après |
|---|---|---|
| Agent de personnalisation du CV (EPIC-5) | `claude -p`, API Anthropic | Ollama sur le poste, `src/llm/local.py` |
| Agent de développement | Claude Code, modèle Anthropic | Claude Code branché sur Ollama, ou inchangé (voir plus bas) |

Motif : les CV, le profil maître et les annonces ne quittent plus le poste,
aucune clé d'API, aucun coût à l'usage, fonctionnement hors ligne.

## Chaîne de personnalisation (sélection, décision du 20/09/2026)

```
annonce + CV d'axe ──► titre actuel et paragraphes d'accroche     déterministe
        + liste des titres autorisés (axe, langue du CV)
                        │
                        ▼
                 Ollama /api/chat, format = schéma JSON            modèle local
                        │  {"titre": <option de la liste | "inchangé">,
                        │   "ordre_accroche": <permutation>, "ecarts": […]}
                        ▼
                 validation : titre dans la liste, permutation     déterministe
                 valide, sinon CV d'axe inchangé
                        │
                        ▼
                 serveur MCP docx-mcp-server : replace_text        déterministe
                 (titre), update_paragraph (accroche), tout ou
                 rien, fichier relu après écriture
                        │
                        ▼
                 LibreOffice ─► PDF ─► dossier client              déterministe
```

Le modèle n'écrit aucun texte. Il choisit un titre dans la liste
`profile/titres_autorises.json`, fixée par le candidat et attestée par chaque
CV d'axe, et un ordre pour les quatre paragraphes d'accroche, dont le texte
est déplacé tel quel. Le JSON est contraint au décodage (paramètre `format`
d'Ollama : le titre est une énumération, l'ordre une liste d'indices valides).
Toute défaillance du modèle — serveur arrêté, modèle absent, JSON invalide,
titre hors liste, permutation invalide, échec du serveur MCP — renvoie le CV
d'axe inchangé, et le motif figure dans le rapport.

Deux règles déterministes complètent la validation : le paragraphe 0 (le résumé) reste
toujours en tête, seuls les paragraphes 1 à n-1 sont permutables ; et une garde de rôle
impose qu'un titre choisi contienne « architecte » ou « architect » quand le titre de
l'annonce en contient (sinon le titre actuel est gardé).

Le client refuse toute adresse non locale : un modèle distant configuré par
erreur ne recevrait pas le profil.

## Vérifications faites le 19/09/2026

Sur une copie de `cv_prets/FR_ARCHITECTE_IA_GENAI.docx`.

| Composant | Résultat |
|---|---|
| `render.substitute` (existant) | **Échec silencieux sur le titre** : 19 segments, rien n'est remplacé, rien n'est signalé. Défaut latent d'EPIC-5. |
| Office-Word-MCP-Server 1.1.11 (GongRzhe) | Rejeté. Dépôt archivé le 03/03/2026 ; `search_and_replace` répond « No occurrences » sur le même titre. 54 outils, ~6 000 jetons. |
| docx-mcp-server 0.7.4 (SecurityRonin) | Retenu. Titre remplacé, mise en forme et nombre de paragraphes intacts, rendu PDF identique hors texte. |
| — contrainte 1 | Incompatible avec `mcp` 2.x (FastMCP renommé) : épingler `mcp<2`. |
| — contrainte 2 | Cible les paragraphes par `w14:paraId`, absent de nos CV : `docx_mcp.ajouter_para_ids` les ajoute sur une copie. |
| — contrainte 3 | 219 outils, ~28 000 jetons de description : jamais exposés tels quels à un modèle local. Sous-ensemble prévu : `OUTILS_AGENT` (6 outils). |
| Playwright MCP 0.0.82 | Fonctionne avec `--user-data-dir` (profil persistant). 25 outils, ~4 500 jetons. Un profil ne peut servir qu'à une instance à la fois. |
| Client Ollama + validation | 8 tests hors ligne sur faux serveur, dont bout en bout MCP réel. |
| Modèle réel, `qwen2.5-coder:14b`, `num_ctx` 8192 (Mac 24 Go, 19/09/2026) | **Vérifié**, 7/7 avec PDF. JSON contraint : 9 s. Bout en bout : 55 s, dont 54 s de modèle (prompt 3 796 jetons en 19 s, sortie 713 jetons en 35 s). 4 substitutions proposées, 1 acceptée, 3 refusées. Modèle chargé : 9,5 Go, 100 % GPU ; mémoire libre 68 % → 21 %. Avec `num_ctx` 16384 : 115 s. PDF de 4 pages, identique au CV d'axe hors accroche. **Réserve** : l'accroche acceptée écrit « 15 ans d'expérience », comme le résumé par défaut du profil maître, alors que le CV d'axe dit 12 ans (15 avec la recherche doctorale) : le validateur contrôle les mots, pas leur cohérence avec le CV. Écart profil/CV à trancher par le candidat. |
| `mistral-small3.2:24b` (16 Go) | **Abandonné** : deux dépassements de délai (300 s) sur un JSON trivial ; le modèle tourne à 14 % CPU / 86 % GPU et le swap dépasse 13 Go sur 15. Ne tient pas sur 24 Go. |

## Connexion aux sites

Rien ne change : les sessions restent tenues par Playwright avec le profil
persistant (ADR-001, EPIC-12), et la connexion reste faite par le candidat.
Le serveur Playwright MCP n'entre pas dans le chemin de candidature : un
modèle qui clique sur « Postuler » contredirait ADR-002 et ADR-007. Il sert
aux sondes de DOM pendant le développement, avec un profil distinct de
celui du radar.

## Choix du modèle

Selon la mémoire du Mac. Les tailles sont indicatives, à confirmer par
`ollama ps` une fois le modèle chargé.

| Mémoire | Modèle | Usage |
|---|---|---|
| 16 Go | `qwen3:8b` | Personnalisation du CV seulement |
| 24 à 32 Go | `gpt-oss:20b` (valeur par défaut) | Personnalisation du CV |
| 48 Go et plus | `qwen3-coder:30b` | Agent de développement, contexte 64 000 |

La personnalisation demande peu : un JSON court, contraint par schéma, sur
8 000 jetons de contexte (prompt complet : 3 800 à 5 000 jetons, à confirmer sur les annonces réelles). C'est l'agent de développement qui est exigeant.

## Agent de développement sur modèle local

Ollama (0.14 et suivantes) expose l'API Anthropic `/v1/messages` : Claude Code
peut s'y brancher sans intermédiaire.

```
ANTHROPIC_BASE_URL=http://localhost:11434 ANTHROPIC_AUTH_TOKEN=ollama \
  claude --model qwen3-coder:30b
```

Limites connues : pas de cache de prompt ni de comptage de jetons, appels
d'outils moins fiables, contexte à porter à 32 000 jetons au minimum
(64 000 conseillés) dans Ollama. Les epics de ce dépôt — sondes de DOM,
corrections sur plusieurs fichiers, tests — sont le cas le plus dur pour un
modèle local. Recommandation : basculer d'abord l'agent CV, mesurer, puis
tenter un epic simple (EPIC-6) avec l'agent de développement local avant de
généraliser.

## Mise en service sur le Mac

```
brew install ollama            # ou l'application depuis ollama.com
ollama pull gpt-oss:20b
make install                   # ajoute mcp<2 et docx-mcp-server
make verifier-llm              # 7 vérifications, rien n'est envoyé
```

## Décision du 20/09 : sélection plutôt que rédaction

**Constat** (`docs/revues/epic14-evaluation.md`, 20 annonces). En rédaction
libre, Qwen 2.5 Coder 14B voit 91 % de ses propositions refusées à raison :
il calque le titre de l'annonce (« Senior », « Expert », outils absents du
profil). Les substitutions acceptées comprennent des affirmations douteuses
(« Responsable de l'ensemble de la chaîne », un paragraphe réduit à un mot,
un titre en français sur un CV anglais). Mistral 7B fait moins bien (92 %,
et 3 propositions en anglais) ; Mistral 24B ne tient pas sur 24 Go.

**Décision.** Le modèle ne rédige plus. Il sélectionne : un titre dans une liste
autorisée, l'ordre de l'accroche. Qwen 2.5 Coder 14B est retenu, Mistral abandonné.

**Code retiré**, faute d'usage dans le chemin par défaut : le prompt de
rédaction, le schéma `substitutions`, `valider` (validation de vocabulaire),
`_formes` et `_localiser` (correctifs de faux refus). Ils n'ont pas été gardés « hors du
chemin » : du code mort demande des tests, et une voie de rédaction libre
qu'un réglage réactiverait rouvrirait le risque d'invention que l'ADR-011 exclut.
Dernier état, avec ses tests : commit `ad3bdf6`. Conservés : `mots` et
`vocabulaire`, qui servent à écarter les « écarts » que le profil couvre déjà.

**Ce que le profil maître ne conditionne plus.** Le profil n'est plus la
barrière de vocabulaire : il ne sert qu'à établir les écarts du rapport. La
présence de TypeScript ou de Java au profil (EPIC-14, reste à faire n° 4)
n'autorise plus rien, elle masquerait seulement un écart.

**Arbitrage du 20/09, après notation des 20 annonces.** Qwen 27/40 (3 choix nuisibles), référence
TF-IDF 17/40 (7 nuisibles) : Qwen est retenu, la référence est abandonnée pour cet étage et son code retiré
(dernier état : commit `7700467`). La liste des titres est VALIDÉE (`profile/titres_autorises.json`,
exceptions écrites dans `_valides_par_le_candidat`). Ajoutés : la garde de rôle « architecte » et le résumé figé en tête.

**Mesure du biais de position (20/09).** Trois passes, titres alternatifs mélangés : 13 annonces sur 20 stables
(14 après la garde), sous le seuil de 15 fixé par le candidat. Arrêt, en attente d'arbitrage ; la passe finale
sur 28 annonces n'est pas lancée. Détail : `docs/revues/epic14-evaluation.md`. L'étage « choix du CV » reste
non branché (étape 5).

**Expérience affichée.** Alignée sur les CV le 20/09 : 12 ans, 15 en incluant la recherche doctorale
(`identity.years_experience` 12, `identity.years_experience_avec_doctorat` 15, `summary_default` corrigé).
