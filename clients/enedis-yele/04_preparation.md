% PRÉPARATION DU POINT DE RESTITUTION
% Enedis via Yélé Consulting · lundi 8 septembre 2026

## Où vous en êtes

Vous n'êtes pas candidat, vous êtes sollicité. Le recruteur vous a contacté le
4 septembre, le démarrage est annoncé au 21 septembre, soit dans deux semaines.
Un intermédiaire qui appelle à quinze jours du démarrage n'est pas en position
de marchander.

L'exercice de lundi n'est pas un examen technique. Un cabinet de conseil vous
demande de restituer votre compréhension d'un besoin : il teste votre façon de
structurer un problème avant de vous présenter à son client.

---

## Vos cinq points d'appui

### 1. MCP en production, sur deux contextes

C'est devenu votre différenciateur le plus rare, et il tombe exactement sur ce
que l'annonce demande — des agents « capables d'exploiter des bases
documentaires métiers et d'accéder à des APIs internes ».

- **TotalEnergies** : serveurs MCP exposant les données de forage, pour
  l'analyse automatisée des rapports journaliers et des incidents par des
  agents IA. Contexte industriel, données d'exploitation. C'est votre
  meilleure référence sur cette mission, devant tout le reste.
- **BIL** : serveurs MCP exposant les métadonnées clients issues de Snowflake.
  Deuxième contexte, secteur régulé — ce n'est donc pas un coup unique.

Très peu de candidats auront MCP en production. Ne le laissez pas passer
comme une ligne parmi d'autres.

### 2. La réversibilité, et l'argument que personne d'autre ne fera

L'annonce l'exige explicitement : « garantir la réversibilité des solutions
mises en place ». Or MCP en est précisément un levier — exposer les API
internes derrière un protocole ouvert plutôt que derrière des connecteurs
propres à un framework permet de changer d'orchestrateur, de framework ou de
modèle sans réécrire les intégrations.

Chez un opérateur d'infrastructure dont les systèmes vivent des décennies et
survivront à plusieurs générations de modèles, ce n'est pas une commodité,
c'est un choix d'architecture.

> « MCP m'intéresse surtout pour la réversibilité que vous demandez : je m'en
> suis servi chez TotalEnergies pour exposer les données de forage aux agents,
> et c'est ce qui permet de changer d'orchestrateur sans refaire les
> intégrations. »

### 3. L'acculturation, qui pèse la moitié du poste

Relisez l'annonce : identifier les cas d'usage, former les utilisateurs,
sensibiliser aux risques de l'IA, animer une communauté technique, organiser
des ateliers, favoriser le partage de retours d'expérience. C'est du transfert
de compétence, pas de l'ingénierie — et c'est écrit comme une responsabilité à
part entière.

Six formations professionnelles conçues et animées pour SQLI Institute et
FItec. Intervenant à Big Data Paris. Encadrement d'une équipe pluridisciplinaire
d'une vingtaine de personnes chez TotalEnergies.

**À dire explicitement.** Peu de profils techniques savent faire adopter un
outil. C'est un argument qu'il faut sortir, pas espérer qu'il soit deviné.

### 4. Le secteur

Cinq ans chez TotalEnergies sur des plateformes Data et IA en environnement
industriel. Un opérateur de réseau électrique partage les mêmes contraintes :
criticité, sûreté de fonctionnement, patrimoine applicatif ancien, données
d'exploitation. Les rapports de forage et les rapports d'incidents relèvent de
la même famille de documents que ce qu'ils veulent traiter.

### 5. La performance sous charge

C'est le sujet réel qu'on vous a donné à l'oral, et c'est là que votre parcours
est le plus solide sans que ça se voie au premier regard : orchestration
multi-LLM avec routage, mise en cache, repli et maîtrise de la latence ;
optimisation GPU avec CUDA, FSDP, DeepSpeed, Ray et profilage torch.profiler
et Nsight.

**Formulation à retenir** : « la première réponse à un problème de charge est
rarement d'acheter des GPU ». Puis dérouler : mesurer, batching continu,
quantification, routage par complexité, cache — et ne dimensionner que ce qui
reste.

---

## Le seul manque : LangGraph

MCP n'est plus un sujet. LangGraph reste le seul élément listé comme
rédhibitoire que vous n'avez pas pratiqué.

À dire en une phrase, sans s'excuser :

> « LangGraph, pas en production. LangChain et LlamaIndex oui, quotidiennement.
> C'est une surcouche d'orchestration à états — graphe, cycles, points de
> contrôle, reprise, validation humaine — sur des concepts que je pratique.
> Ce n'est pas un obstacle à quinze jours. »

Si on creuse : l'intérêt de LangGraph en production tient aux points de
contrôle, qui permettent de reprendre après incident sans tout rejouer, à
`interrupt_before` pour la validation humaine, et au bornage des exécutions —
plafond d'itérations, budget de tokens, délai de garde — qui est exactement la
réponse au risque d'agent en boucle non bornée. Donc à la charge.

---

## Cohérence avec le CV envoyé

Le CV transmis vous positionne comme **architecte et lead technique**, pas
comme responsable de programme. Les intitulés de poste ont changé en
conséquence. Tenez ce registre à l'oral : vous concevez et vous construisez,
vous ne pilotez pas seulement.

Trois affirmations du CV que vous devez pouvoir défendre :

1. **« Une quinzaine de cas d'usage industrialisés » chez TotalEnergies** —
   soyez prêt à en citer cinq ou six de mémoire.
2. **« Déployés en environnement maîtrisé, on-premise comme cloud »** — si on
   vous interroge, distinguez ce que vous avez servi sur infrastructure
   interne de ce qui tournait en cloud.
3. **Linux** — défendable en usage applicatif ; ne prétendez pas à
   l'administration système fine.

---

## Ce qu'il ne faut pas faire

- **Ne pas arriver avec une solution.** Ils testent la structuration d'un
  problème. Vos quatre questions de cadrage valent mieux que dix
  recommandations.
- **Ne pas survendre l'on-premise.** « J'ai déployé Mistral et LLaMA ;
  l'on-premise change l'exploitation, pas les principes » est vrai et suffit.
- **Ne pas parler TJM en premier.** Le sujet vient en fin d'échange, après
  qu'ils ont mesuré l'apport.
- **Ne pas oublier de nommer Cœur IA et Connect IA.** Ce sont les deux cellules
  transverses citées dans l'annonce. Les mentionner montre que vous avez lu
  au-delà du titre.

---

## Questions probables et angles de réponse

**« Comment aborderiez-vous le problème de charge ? »**
Mesurer d'abord : latence aux percentiles 50, 95 et 99, tokens par cas
d'usage, taux d'occupation GPU, profil de concurrence. Une à deux semaines.
Puis les leviers sans matériel, par rendement décroissant : batching continu,
quantification, routage par complexité, cache sémantique, réduction du
contexte. Le matériel en dernier, justifié par la mesure.

**« Quelle est votre expérience du on-premise ? »**
Mistral, LLaMA et Hugging Face déployés ; l'essentiel de mon exploitation est
cloud. Sur la charge, les leviers sont les mêmes — et la contrainte de parc
fixe rend justement l'optimisation plus décisive que dans le cloud, où l'on
peut ajouter des instances.

**« Connaissez-vous MCP ? »**
Oui, en production sur deux contextes. Puis raconter le forage.

**« Et LangGraph ? »**
Voir plus haut. Une phrase, sans détour.

**« Comment feriez-vous adopter ces outils ? »**
Par les cas d'usage, pas par l'outil. Deux ou trois usages à valeur visible et
courte boucle, les réussir, les documenter, puis s'appuyer dessus. En
parallèle, une communauté de praticiens et un format court de formation.
J'ai animé six formations professionnelles, le cadre m'est familier.

**« Comment traitez-vous la conformité AI Act ? »**
Classification par niveau de risque à l'entrée du cas d'usage, puis déduction
des obligations : documentation technique, qualité des données, traçabilité,
transparence, supervision humaine. Et surtout, transformer chaque obligation
en critère de passage en production — sinon elle reste déclarative.
À noter : le pilotage d'un réseau électrique relève de l'infrastructure
critique au sens du règlement. Le sujet n'est pas théorique ici, et le dire de
vous-même montre que vous avez saisi l'enjeu réel.

**« Comment garantissez-vous la réversibilité ? »**
Découplage du fournisseur de modèle par une couche d'abstraction, protocoles
ouverts type MCP plutôt que connecteurs propriétaires, formats portables pour
les prompts, index et embeddings, et documentation des évaluations pour
pouvoir comparer un modèle de remplacement.

**« Quel est votre TJM ? »**
« Quel budget avez-vous prévu sur cette mission ? » Si insistance : 700 €.

---

## Les questions à poser

Sur le besoin, à poser pendant l'échange :

1. Quel est le parc GPU disponible et le moteur d'inférence en place ?
2. Combien de modèles Mistral servis, et quelle variété ?
3. Quel profil de charge — pics, concurrence, engagement de latence attendu ?
4. Qui décide de l'ouverture d'un nouveau cas d'usage, et selon quels critères ?
   Cœur IA, Connect IA, ou le département lui-même ?

Sur le cadre commercial, hors présence du client :

5. Combien d'intermédiaires entre moi et Enedis ?
6. Mon profil a-t-il déjà été présenté, ou va-t-il l'être ?
7. Quel est le budget du client sur la mission ?

---

## Sur le TJM

Ne donnez pas le premier chiffre. Demandez leur fourchette.

S'ils insistent : **700 €**, plancher à 650.

Le raisonnement, si vous devez le justifier : le baromètre du marché donne
680 € via intermédiaire pour ce type de profil senior, vous avez quinze ans
d'expérience et un doctorat, le client est un grand compte, et le besoin est
urgent. L'annonce cible 5 à 10 ans d'expérience — c'est le budget de l'ESN,
pas votre valeur.

Et gardez en tête que la chaîne compte : chaque étage prend entre 10 et 20 %.
Si Enedis paie 900 € et qu'il y a deux intermédiaires, il vous reste 650. S'il
n'y en a qu'un, 750 à 800. D'où l'intérêt de la question 5.
