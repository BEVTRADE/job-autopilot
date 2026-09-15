# Registre des sources

État au 6 septembre 2026. Une source se qualifie sur trois critères :
**volume utile** sur les axes visés, **faisabilité technique**, et **modèle**
— sortant (on postule) ou entrant (on est contacté).

## Intégrées

| Source | Accès | Capacités | Note |
|---|---|---|---|
| **Free-Work** | 6 sitemaps XML publics, sans compte | `decouvrir` `lire` `soumettre` | Le meilleur volume et le seul à afficher des TJM (~50 % des annonces). Agrège des dizaines d'intermédiaires — LeHibou, SKILL EXPERT, CELAD, Deodis. Une intégration en couvre beaucoup. |
| **BOAMP** | API Opendatasoft, open data, sans clé | `decouvrir` `lire` | Marchés publics. Volume faible, aucune friction technique, aucune ambiguïté juridique. Urbanisation SI et schémas directeurs y sont récurrents. |

## À intégrer, par ordre de priorité

| # | Source | Accès | Pourquoi |
|---|---|---|---|
| 1 | **Freelance-Informatique** | rendu serveur, sans compte, URL prédictibles | ~450 missions actives. Coût d'intégration marginal une fois Free-Work en place. |
| 2 | **Freelance-Day** | compte requis, rendu JavaScript | ~17 900 missions annoncées, mais **forte rediffusion** : un seul profil y publie 15 477 annonces. Volume trompeur, dédoublonnage indispensable. À traiter comme un filet, pas comme une source primaire. |
| 3 | **FreelanceRepublik** | aperçu public, compte pour la liste complète | Le seul de la strate premium dont les TJM affichés atteignent le seuil (600-770 € observés). Liste explicitement architectes et managers de transition. |
| 4 | **TED (Europa)** | API REST publique documentée | Grands programmes SI européens. Rapport signal/bruit médiocre : filtrage CPV strict et cadence hebdomadaire, pas quotidienne. |
| 5 | **LinkedIn** | `decouvrir` et `lire` seulement | Les missions off-market les mieux payées y circulent. **La soumission reste désactivée** : contraire aux CGU, détection active, risque de restriction du compte. |

## Non automatisables — modèle entrant

Aucune liste de missions à parcourir : la valeur est dans le profil que
l'algorithme ou l'équipe de matching voit. L'investissement rentable est un
profil optimisé, pas un robot.

**Malt** et **Malt Strategy** — `robots.txt` interdit `/api/`, `/mission/`,
`/missions` ; Cloudflare actif ; sur Malt Strategy le profil n'est même pas
public. Malt Strategy est le vrai canal ≥ 650 € pour un directeur de programme.
**Comet** — matching algorithmique, aucune mission publique, tests à l'entrée.
**Crème de la Crème** — 10 % d'acceptation, trois profils proposés en 48 h.
**LeHibou** — pas de liste propre, mais republie sur Free-Work : couvert indirectement.
**Talent.io** — marketplace inversée, peu d'architecture d'entreprise.
**LittleBig Connection** — 650-1000 €, cœur de cible CAC40, compte obligatoire,
missions non publiques. Zone grise CGU si automatisé.
**Cabinets de management de transition** (Valtus, Delville, X-PM, Uman Partners)
— le segment le mieux payé pour « Directeur de programme Data & IA ».
Inscription au vivier et entretien : non automatisable, et probablement le
meilleur retour sur temps investi.

## Écartées

| Source | Motif |
|---|---|
| APEC, Welcome to the Jungle | orientées CDI, très peu de freelance senior |
| StaffMe | jobbing étudiant, hors segment |
| Silkhom, Urban Linker, Beager | cabinets de recrutement CDI |
| XXE, Choose Your Boss | faible différenciation avec Free-Work |
| France Travail (API) | excellente faisabilité, mais quasi rien en freelance sur ce profil |
| PLACE / marches-publics.gouv.fr | pas d'API de consultations en cours ; les DECP ne portent que des marchés déjà attribués. Le point d'entrée programmable des marchés publics est BOAMP. |

## La rediffusion, et ce qu'elle impose

Une même mission circule chez plusieurs intermédiaires et sur plusieurs
plateformes. Exemple vérifié le 6 septembre : la mission Enedis « Expert en IA
Générative » est publiée par **nahange** sur Free-Work, par **Yélé Consulting**
en approche directe, et par un profil de rediffusion sur **Freelance-Day**.

**Postuler chez plusieurs intermédiaires pour une même mission n'est ni risqué
ni déloyal.** Candidater n'engage rien : l'intermédiaire qualifie le profil lors
d'un entretien, puis demande l'accord du consultant avant toute présentation au
client final. Le consultant garde la main.

Le point de vigilance se situe donc **un cran plus loin, au moment de
l'autorisation de présentation** — et il n'est pas automatisable, il relève de
la décision.

Ce que le système doit faire, en conséquence :

1. **Regrouper plutôt que supprimer.** Une mission repérée sur plusieurs sources
   forme un seul dossier avec plusieurs canaux. On ne jette pas les doublons :
   ils permettent de comparer les intermédiaires et de retenir celui qui propose
   les meilleures conditions.
2. **Identifier le client final**, quand il est déductible du descriptif, et le
   tracer dans le dossier client. C'est lui qui compte, pas l'émetteur de
   l'annonce.
3. **Alerter au moment de l'accord**, pas de la candidature : si une
   autorisation de présentation est déjà accordée à un intermédiaire pour un
   client donné, le signaler avant d'en accorder une seconde.

L'empreinte de dédoublonnage doit donc porter sur le **titre normalisé et le
contenu**, pas sur le couple titre + société : la société varie d'une source à
l'autre pour une mission identique.

## Rappel de marché

Les missions d'architecture et de direction de programme au-delà de 800 € sont
largement **off-market** : réseau, cooptation, cabinets de transition. Ce radar
garantit de ne rien rater de ce qui est publié — ce qui a de la valeur — mais
ne remplace pas ces canaux.
