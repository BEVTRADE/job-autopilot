% RESTITUTION — EXPERT TECHNIQUE IA GÉNÉRATIVE, GTAR
% Hakim Arezki, PhD · Point du 8 septembre 2026

## Ce que j'ai compris du besoin

Le GTAR a déployé une solution d'IA générative open source sur des serveurs
on-premise. Les quatre équipes commencent à s'en saisir, et le poste est
rattaché à l'équipe transverse : le mandat n'est donc pas de construire une
solution de plus, mais de **faire tenir un usage partagé entre des équipes qui
n'ont ni les mêmes besoins ni le même niveau de maturité**.

Trois tensions me semblent structurer la mission.

**Mutualiser sans brider.** Les paramétrages, System Prompts et gabarits doivent
être communs pour être tenables, tout en laissant chaque équipe traiter ses cas
d'usage propres — conduite, MCO, appui aux ACR.

**Tenir la charge sur un parc fixe.** En on-premise, on ne rajoute pas une
instance quand la demande monte. L'adoption progresse, et l'infrastructure
devient le facteur limitant.

**Livrer transmissible.** Les agents et les pipelines doivent être documentés,
testés et repris en exploitation par les équipes du GTAR, dans un environnement
où la sûreté de fonctionnement prime.

## Ma lecture des sept objectifs

Ils se regroupent en trois blocs qui ne demandent pas les mêmes gestes.

**Socle commun** — objectifs 2 et 4. Paramétrages, System Prompts et gabarits
mutualisés, pipelines RAG et valorisation de la connaissance. C'est la
fondation : tant qu'elle n'existe pas, chaque équipe refait ses réglages dans
son coin et la charge explose sans que personne ne sache pourquoi.

**Cas d'usage** — objectifs 3 et 5. Agents développés sur les besoins remontés,
référencés et documentés au fil de l'eau. Le référencement n'est pas une tâche
de fin de projet : c'est ce qui permet de savoir ce qui tourne, pour qui, à
quel coût, et sous quelles obligations réglementaires.

**Adoption et coordination** — objectifs 1, 6 et 7. Formations de prise en main,
animation de la communauté des référents techniques, coordination avec Cœur IA
et Connect IA. Quatre des sept objectifs relèvent de cette dimension : c'est au
moins la moitié du poste.

## Où se situe généralement la saturation

Sur l'objectif 2, par ordre de fréquence sur les plateformes que j'ai
industrialisées :

- **Servage** — inférence sans batching continu : chaque requête mobilise le
  GPU pour elle seule, l'occupation reste basse pendant que la file s'allonge.
- **Modèles** — un seul modèle lourd pour tous les usages, sans quantification,
  là où une bonne part des demandes serait traitée par un modèle plus petit.
- **Contexte** — RAG peu sélectif et prompts longs : des milliers de tokens
  inutiles à chaque appel.
- **Cache** — absence de cache sémantique sur les questions récurrentes, et
  cache KV non exploité entre tours.
- **Agents** — boucles non bornées et appels en cascade : un agent mal cadré
  amplifie la charge d'un facteur cinq à dix.
- **File d'attente** — ni priorisation ni dégradation gracieuse : un usage
  exploratoire pénalise un usage d'exploitation.
- **Mesure** — pas d'observabilité par cas d'usage, donc dimensionnement à
  l'aveugle.

## Ma façon de procéder

**Mesurer avant de décider.** Profil de charge réel, latence aux percentiles 50,
95 et 99, tokens par cas d'usage, taux d'occupation GPU. Une à deux semaines.

**Chercher d'abord les gains sans matériel.** Batching continu, quantification,
routage par complexité de tâche, cache sémantique, réduction du contexte. C'est
là que se trouve l'essentiel, et c'est réversible.

**Construire le socle commun en parallèle.** System Prompts et gabarits
mutualisés, versionnés comme du code ; garde-fous et bornage des agents ;
référentiel des cas d'usage tenu au fil de l'eau plutôt qu'après coup.

**Faire adopter par les cas d'usage, pas par l'outil.** Deux ou trois usages à
valeur visible et courte boucle, réussis et documentés, servent ensuite
d'exemples. La communauté de référents techniques se construit autour de ces
réussites, pas autour d'une formation générique.

**Ne dimensionner que ce qui reste**, justifié par la mesure et non par
l'urgence.

## Ce que je souhaite confirmer avec vous

- Le parc GPU disponible et le moteur d'inférence en place aujourd'hui.
- Les modèles servis, leur nombre et leur variété.
- Le profil de charge : pics, concurrence, engagement de latence attendu.
- La répartition des usages entre les quatre équipes du GTAR, et leur maturité
  respective.
- Le partage des rôles avec Cœur IA et Connect IA : qui définit le cadre, qui
  valide l'ouverture d'un cas d'usage, et selon quels critères.

## Deux convictions

**La première réponse à un problème de charge est rarement d'acheter des GPU.**
Sur les plateformes Data et IA que j'ai industrialisées, le routage entre
modèles, la mise en cache et la maîtrise du contexte ont réduit le coût par
requête bien avant tout investissement matériel — et ces leviers se déploient
en semaines.

**Une solution d'IA n'est adoptée que si quelqu'un en porte l'usage.** C'est
pourquoi je traite la formation et l'animation de la communauté comme du
travail d'ingénierie, pas comme un accompagnement de fin de projet : les
gabarits, les garde-fous et la documentation d'exploitation sont ce qui rend
l'appropriation possible.
