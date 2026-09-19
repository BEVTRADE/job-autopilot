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

## Reconnaissance du 18 septembre 2026 — les deux sources restantes

Vérification faite avant d'écrire les extracteurs, pour ne pas construire sur
une hypothèse.

### FreelanceRepublik — automatisable, à intégrer

**Le domaine du registre était faux.** Le site est `freelancerepublik.com`,
sans tiret. `freelance-republik.com` ne résout pas.

Les missions sont **publiques, sans connexion**. Chaque annonce de la liste
porte le titre, la ville, la modalité de télétravail, la durée en mois et le
TJM. Les pages de détail suivent `/missions/<titre-slugifie>-<id hexadécimal>`,
par exemple `/missions/data-analyst-f075f842`.

Rien ne s'oppose à un extracteur sur le modèle de `freework.py`.

### Freelance-Day — à reclasser en canal entrant

`freelance-day.eu/missions/` renvoie une **page de connexion**, pas une liste.
L'accès aux missions suppose un compte et une authentification.

Cela le sort de la catégorie « à intégrer » : un extracteur exigerait de
stocker et rejouer des identifiants, ce que le système ne fait pour aucune
source. Freelance-Day rejoint la catégorie des **canaux entrants non
automatisables**, au même titre que Malt ou Comet — consultable à la main,
pas par le radar.

C'est d'autant plus notable que l'annonce Enedis repérée le 7 septembre
provenait de ce site : le canal a de la valeur, il n'est simplement pas
automatisable dans les termes actuels.

### Conséquence sur EPIC-3

Le périmètre passe de quatre sources à trois : Freelance-Informatique et TED,
déjà écrites, plus FreelanceRepublik. Freelance-Day sort du lot.

### Limite de la reconnaissance

Faite depuis un agent, qui ne peut pas récupérer le HTML brut : les domaines
sont refusés par la politique de sortie côté conteneur, et le shell de la
machine n'a pas de réseau. Les pages de référence nécessaires aux tests
d'extraction doivent être enregistrées depuis le Mac.

## Diagnostic de session Free-Work — 19 septembre 2026 (EPIC-12, niveau 1)

Mesuré avec `scripts/diag_session.py`, sur le profil persistant
`~/.job-autopilot/browser-profile`, ouvert avec les paramètres exacts
d'`apply.py` et de la sonde. Le script n'affiche et n'enregistre que le nom, la
longueur et l'expiration de chaque élément, jamais une valeur.

### Ce qui porte l'authentification

Trois cookies sur `www.free-work.com`, tous **à date d'expiration**, aucun
cookie de session :

| Cookie | Rôle | Durée mesurée | Drapeaux |
|---|---|---|---|
| `jwt_s` | jeton d'accès | 24 h après la connexion | HttpOnly, Secure |
| `jwt_hp` | jeton associé, lisible côté page | 24 h | Secure |
| `refresh_token` | renouvellement | 48 h | HttpOnly, Secure |

Le reste des 13 cookies du domaine (`_gcl_au`, `_rdt_*`, `posthog`, `AWSALB*`,
`_pk_*`, `cc_cookie`, `locale`) relève de la mesure d'audience, du consentement
et de la répartition de charge : aucun ne porte la connexion. Le stockage local
(2 clés : `_gcl_ls`, `POSTBACK_AGGREGATOR_PERSIST`), le stockage de session
(5 clés, mesure d'audience et version de l'application) et IndexedDB (aucune
base) ne contiennent rien d'authentifiant.

### Fermer, rouvrir, comparer

Relevé n° 1 après `make login` (navigateur déjà fermé une fois), relevé n° 2
après une seconde fermeture : **connecté aux deux, aucun cookie disparu**. Seules
les dates d'expiration de cookies d'audience et de répartition de charge ont
glissé d'une minute. Les trois cookies d'authentification sont identiques à la
minute près : ils ne se renouvellent pas en naviguant.

### Conclusion

**L'hypothèse est infirmée.** Chromium ne perd pas la connexion à la fermeture :
il n'y a pas de cookie de session à perdre, et le profil persistant conserve
tout ce qui compte. Enregistrer l'état dans un fichier (niveau 2) ne
changerait rien, puisque le profil le fait déjà.

Ce que la mesure établit à la place : la connexion a une **durée de vie bornée
côté serveur, 24 h pour le jeton d'accès et 48 h pour le renouvellement**, et
aucun renouvellement n'a été observé pendant la navigation. Une connexion faite
un jour n'est donc garantie que jusqu'au surlendemain, quoi qu'on fasse du
côté du navigateur.

### Non mesuré

- Si le site renouvelle `jwt_s` à partir de `refresh_token` une fois le jeton
  d'accès expiré, et si ce renouvellement prolonge lui-même le
  `refresh_token`. C'est la question qui décide si une session peut vivre au-delà
  de 48 h. Il faut pour cela un relevé après 24 h, puis après 48 h.
- La cause exacte de la demande de connexion du 19 septembre : la date de la
  connexion précédente n'est pas consignée. Un écart de plus de 48 h avec
  `make login` suffirait à l'expliquer, sans que ce soit établi.

## Reconnaissance du 19 septembre 2026 — Indeed

**Candidature automatisée : interdite.** Les conditions d'utilisation
d'Indeed, section chercheurs d'emploi, disent : « Use of any automation,
scripting, or bots to automate the Indeed Apply process outside of Indeed's
official vendors and tooling is prohibited »
(https://www.indeed.com/legal). Le risque est la fermeture du compte du
candidat.

**API : aucune pour les candidats.** Les API d'Indeed sont réservées aux
partenaires — employeurs, cabinets, éditeurs d'ATS. Il n'existe pas d'API de
recherche d'offres ouverte aux chercheurs d'emploi.

**Voie retenue : les alertes e-mail.** Le candidat configure ses alertes
Indeed ; les courriels, déposés en `.eml` dans `data/alertes/indeed/`, sont
lus par `src/sources/alertes_indeed.py`. Aucune visite du site, aucun appel
réseau. L'identifiant d'offre `jk` sert de clé ; l'URL canonique est
reconstruite. La candidature est préparée par `src/apply/indeed.py` — lien,
CV recommandé — et présentée dans le rapport, section « À envoyer à la
main ».

**À valider** : l'extracteur a été écrit sans courriel d'alerte réel. Déposer
une vraie alerte dans `data/alertes/indeed/` et vérifier l'extraction avant
de s'y fier.
