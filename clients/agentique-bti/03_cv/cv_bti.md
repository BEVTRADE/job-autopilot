% HAKIM AREZKI, PhD
% ARCHITECTE SOLUTIONS IA — SYSTÈMES AGENTIQUES EN ENVIRONNEMENT CRITIQUE ET RÉGULÉ

Paris / Île-de-France, Freelance, 06 33 66 12 48, harezki@kiras.fr, Disponible immédiatement

Architecte et lead technique IA, 12 ans d'expérience professionnelle en Data et intelligence artificielle (15 en incluant la recherche doctorale), dont 5 ans dans l'énergie et l'industrie (TotalEnergies) et 8 ans en environnement régulé (BIL, BPCE). Docteur de CentraleSupélec.

Conception, développement et industrialisation de solutions d'IA générative bâties sur des modèles open source — Mistral, LLaMA, Hugging Face — et propriétaires, déployés en environnement maîtrisé, on-premise comme cloud, avec sélection du modèle selon les exigences de qualité, de confidentialité, de latence et de coût.

Opérationnel sur toute la chaîne : paramétrage et optimisation de modèles, prompt engineering avancé et System Prompts mutualisés ; développement d'agents IA avec orchestration, gestion d'état, sélection d'outils, mémoire, garde-fous et validation humaine ; serveurs MCP exposant données et API internes aux agents ; pipelines RAG complets, de l'ingestion à l'évaluation ; industrialisation LLMOps sur Docker, Kubernetes et Linux.

Conçoit les systèmes agentiques pour des environnements où l'erreur se paie : orchestration multi-agents bornée, validation humaine sur les actions sensibles, moindre privilège sur les outils et les sources, traçabilité et auditabilité de bout en bout, classification des cas d'usage par niveau de risque et traduction en contrôles vérifiables. La conformité n'est pas une couche ajoutée en fin de projet, elle est une contrainte d'architecture.

## Réalisations en IA générative

- BIL, Banque Internationale à Luxembourg (depuis 2026) — plateforme Data et IA d'entreprise : architecture multi-LLM intégrant Mistral et LLaMA, pipelines RAG et Document AI, agents IA, serveurs MCP exposant les métadonnées clients issues de Snowflake, System Prompts mutualisés, LLMOps, gouvernance de l'IA, RBAC et sécurité au niveau ligne, RGPD, DORA.
- TotalEnergies (2020-2025) — industrialisation des cas d'usage d'IA générative à l'échelle du groupe : agents IA, pipelines RAG, Document AI multimodal combinant OCR, vision et LLM. Exposition des données de forage via serveurs MCP pour l'analyse automatisée des rapports journaliers et des incidents d'exploitation par des agents IA.

En amont de l'IA générative, quinze ans de Machine Learning et de Data Science industrialisés en environnement critique : supervision temps réel de mobilité multimodale (RATP, Alstom, Renault, IRT SystemX), détection de criminalité financière et de fraude en banque (BPCE), maintenance prédictive et vision par ordinateur dans l'industrie.

## Compétences clés

### LLM open source, paramétrage et prompt engineering

- Déploiement et exploitation de modèles open source, Mistral, LLaMA, Hugging Face, et propriétaires
- Paramétrage et configuration des modèles servis en interne
- Sélection du modèle selon la complexité de la tâche, la confidentialité, la latence et le coût
- Prompt engineering avancé, conception et mutualisation de System Prompts, gabarits de prompts, versionnement
- Sorties structurées et contrôle de cohérence
- Garde-fous et réduction des hallucinations

### Architecture agentique

- Développement d'agents IA, orchestration, gestion d'état, sélection et appel d'outils, mémoire
- Model Context Protocol, conception de serveurs exposant données métiers et API internes aux agents
- Tool calling et intégration d'API REST
- Validation humaine dans la boucle et bornage des exécutions
- Observabilité des agents, traces, coût, latence, taux d'échec
- Agents documentés, testés et transmissibles

### Chaîne RAG complète

- Ingestion et parsing documentaire
- Découpage et stratégies de chunking
- Embeddings et indexation
- Recherche vectorielle et hybride BM25
- Filtrage par métadonnées et contrôle d'accès au niveau du document
- Reranking, génération et post-traitement
- Document AI, OCR et modèles vision-langage

### Sécurité, souveraineté et exposition maîtrisée

- Orchestration multi-agents bornée : plafond d'itérations, budget de jetons, délai maximal, arrêt sur échec
- Validation humaine dans la boucle sur les actions sensibles, points d'interruption explicites dans le graphe d'exécution
- Moindre privilège sur les outils et les sources, contrôle des accès au niveau du document et de la ligne
- Défense contre l'injection de prompt, cloisonnement des contenus non fiables, contrôle des sorties avant action
- Prévention de l'exfiltration par les outils, validation des appels sortants
- Traces d'audit exploitables : qui, quand, avec quelles données, quel modèle, quelle décision
- Gestion des identités et des accès, intégration aux dispositifs IAM existants, exposition via API Management
- Souveraineté et confidentialité : déploiement on-premise ou en environnement maîtrisé, modèles open source, formats portables
- Gestion de corpus versionnés, traçabilité des sources et reproductibilité des réponses
- AI Act, RGPD, DORA, NIS2 : classification par niveau de risque et déclinaison en contrôles techniques

### Évaluation des systèmes IA

- Retrieval, Hit Rate, Recall@k, MRR, nDCG
- RAG, Context Precision, Context Recall, Faithfulness, Answer Relevancy, RAGAS
- LLM, qualité, factualité, taux d'hallucination, latence p50/p95, coût unitaire
- Jalons d'évaluation conditionnant la mise en production

### Accompagnement, formation et animation de communauté technique

- Ateliers de prise en main de l'IA générative et du prompt engineering, construits sur les usages réels des équipes plutôt que sur l'outil
- Animation de référents techniques en relais dans les équipes, diffusion des bonnes pratiques et partage des retours d'expérience
- Accompagnement des équipes métiers et techniques dans l'adoption des services d'IA, jusqu'à la reprise en autonomie
- Conception et animation de six formations professionnelles en Machine Learning, Python, Kafka, ELK et DataViz, SQLI Institute et FItec
- Sensibilisation aux limites des modèles, hallucinations, incohérences, périmètre de validité
- Coordination entre équipes aux besoins et aux niveaux de maturité différents, arbitrage entre socle mutualisé et spécificités
- Intervenant Big Data Paris

### Industrialisation et exploitation

- Conteneurisation et orchestration, Docker, Kubernetes, Linux
- Routage entre modèles, mise en cache et repli pour maîtriser latence, qualité et coût
- Intégration et déploiement continus pour les modèles et les prompts
- Supervision, indicateurs p50/p95, taux d'erreur, consommation, coût unitaire
- Architecture conçue pour une montée en charge progressive

### Sécurité, gouvernance et conformité des cas d'usage

- Risques propres aux LLM, hallucinations, injection de prompt, fuite de données, exfiltration par les outils
- Contrôle des accès aux outils et aux sources
- Garde-fous, validation humaine, auditabilité et traçabilité des sorties
- RGPD, DORA, AI Act, classification des cas d'usage par niveau de risque et traduction en contrôles vérifiables
- Référencement et documentation des cas d'usage au fil de l'eau, registre des usages, propriétaire, données mobilisées, obligations applicables
- RBAC et sécurité au niveau ligne

### Documentation, réversibilité et transfert

- Documentation d'architecture, des agents et des API
- Guides d'exploitation et de maintenance
- Conception modulaire et découplage du fournisseur de modèle
- Réversibilité, formats portables pour prompts, index et embeddings, protocoles ouverts plutôt que connecteurs propriétaires
- Transfert de compétences et reprise en maintenance par les équipes internes

## Environnement technique

- IA générative : Mistral, LLaMA, Hugging Face, OpenAI, Azure OpenAI, Claude, Amazon Bedrock, Copilot et Copilot Studio
- Frameworks et protocoles : LangChain, LlamaIndex, Semantic Kernel, MCP (Model Context Protocol), MLflow, PyTorch, TensorFlow, scikit-learn
- RAG et recherche : FAISS, PGVector, OpenSearch, BM25, recherche hybride, reranking, RAGAS
- Document AI : Azure Document Intelligence, modèles vision-langage, Docling, Tesseract, OpenCV
- Infrastructure : Linux, Docker, Kubernetes, GPU, Terraform, GitHub Actions, GitLab CI/CD
- Observabilité : Langfuse, Arize, OpenTelemetry, Prometheus, Grafana, MLflow
- Data : Snowflake, Databricks, dbt, Python, SQL, Spark, PySpark, Kafka, Airflow
- API : FastAPI, API REST, architectures événementielles
- Versionnage : Git

## Expérience professionnelle

### Architecte et Lead technique IA — BIL, Banque Internationale à Luxembourg
*Janvier 2026 à aujourd'hui*

Conception, développement et exploitation de GENIA, plateforme Data et IA d'entreprise mettant à disposition des domaines métiers des capacités d'IA générative gouvernées, en environnement bancaire régulé.

- Architecture et exploitation d'une plateforme multi-LLM intégrant plusieurs modèles propriétaires et open source, notamment Mistral et LLaMA, sélectionnés selon les exigences de qualité, de confidentialité, de coût et de latence.
- Développement des mécanismes de routage, de mise en cache et de repli permettant de maîtriser la latence, la qualité et le coût des requêtes, avec suivi des indicateurs p50/p95, du taux d'erreur, de la consommation et du coût unitaire.
- Conception et développement de serveurs MCP exposant les métadonnées clients issues de Snowflake, pour leur extraction et leur exploitation par les agents IA de la plateforme.
- Développement d'agents IA interrogeant les modèles, les bases documentaires et les API internes, avec gestion d'état, sélection d'outils, garde-fous et validation humaine sur les actions sensibles.
- Construction de pipelines RAG et Document AI : ingestion, parsing, chunking, embeddings, indexation, recherche hybride, reranking, génération — avec filtrage par métadonnées et contrôle d'accès au niveau du document.
- Conception des System Prompts mutualisés et des gabarits réutilisables, versionnés au même titre que le code, avec sorties structurées et contrôles de cohérence.
- Mise en place du cadre d'évaluation : métriques de retrieval, métriques RAG et suivi de la factualité, du taux d'hallucination, de la latence et du coût, avec jalons conditionnant le passage en production.
- Industrialisation LLMOps : conteneurisation, déploiement continu des modèles et des prompts, observabilité et supervision.
- Traitement des risques propres à l'IA : hallucinations, injection de prompt, contrôle des accès aux outils, auditabilité et traçabilité des sorties.
- Conformité RBAC, sécurité au niveau ligne, chiffrement, RGPD et exigences bancaires dont DORA.
- Coordination d'équipes pluridisciplinaires réunissant experts Data, IA, architecture, ingénierie et DevOps.

### Architecte et Lead technique Data & IA — TotalEnergies
*Décembre 2020 à décembre 2025*

Industrialisation à l'échelle du groupe des cas d'usage Machine Learning et IA générative, sur une plateforme Data d'entreprise servant plusieurs domaines métiers : opérations industrielles, distribution, ressources humaines.

- Industrialisation d'une quinzaine de cas d'usage Data, Machine Learning et IA, de l'expérimentation à la production : opérations industrielles, maintenance prédictive, vision par ordinateur, Document AI et IA générative.
- Conception et développement de serveurs MCP exposant les données de forage, permettant à des agents IA d'analyser automatiquement les rapports journaliers et les incidents d'exploitation.
- Conception et industrialisation de pipelines Document AI, OCR et RAG pour le traitement de corpus documentaires techniques et opérationnels.
- Développement d'agents IA et de solutions multimodales combinant OCR, vision et LLM pour l'automatisation documentaire et l'aide à la décision.
- Développement des pipelines d'entraînement, d'évaluation et de déploiement intégrant MLflow, intégration et déploiement continus, supervision et versionnement.
- Construction des pipelines Data sur Databricks, PySpark, Airflow et dbt, et des architectures événementielles Kafka.
- Industrialisation de l'infrastructure via Terraform, Docker et pipelines de déploiement continu, avec observabilité et optimisation des performances.
- Définition des standards d'architecture, des décisions structurantes formalisées en ADR et des pratiques MLOps du groupe, et diffusion auprès des équipes des différentes entités.
- Encadrement d'une équipe pluridisciplinaire d'une vingtaine de personnes réunissant métiers, Data Engineering, Data Science, architecture, cloud et DevOps.
- Accompagnement des équipes métiers dans l'adoption des services d'IA : ateliers de prise en main, gabarits de prompts mutualisés, guides d'exploitation, et transfert des solutions aux équipes internes.

### Lead technique Data et IA, programme MSM — RATP, avec Alstom, Renault et IRT SystemX
*Août 2018 à décembre 2020*

Programme de mobilité multimodale réunissant plusieurs partenaires industriels et un institut de recherche technologique.

- Conception d'architectures en microservices pour la supervision temps réel et la gestion des incidents.
- Construction et déploiement d'un lac de données multi-couches pour l'ingestion, le traitement et l'analyse à l'échelle, avec intégration de flux Kafka sécurisés.
- Développement de modèles prédictifs pour les flux voyageurs, la durée des incidents et la planification opérationnelle.
- Mise en œuvre de la détection d'anomalies et de l'analyse de journaux pour la qualité des données et la conformité.
- Livraison d'un démonstrateur opérationnel de supervision de mobilité déployé à Paris-La Défense.
- Formation des équipes métiers et techniques aux plateformes d'IA et à la visualisation de données.
- Publication IEEE (DSD 2020) sur l'architecture de supervision hybride temps réel et prédictif.

### Lead Data Science et gouvernance — BPCE, banque et assurance
*Janvier 2017 à août 2018*

Lutte contre le blanchiment et le financement du terrorisme, criblage des sanctions et embargos, détection de fraude, conformité RGPD des traitements financiers.

- Construction d'un moteur de détection de fraude de bout en bout et automatisation des flux de gestion des alertes, sanctions et embargos.
- Développement d'un moteur de matching exact, flou et phonétique entre entités suspectes et clients.
- Réduction des faux positifs par TF-IDF, vectorisation par hachage et analyse des matrices de confusion.
- Déploiement du dictionnaire de données d'entreprise et du lignage sur Apache Atlas et ELK.
- Mise en conformité RGPD des chaînes de traitement : contrôle d'accès, traçabilité, protection des données.

### Lead Data Science — Distribution de luxe
*Septembre 2015 à janvier 2017*

- Construction d'un moteur d'intelligence client : classification des profils, prédiction de comportement, modélisation de l'attrition, moteur de recommandation par filtrage collaboratif.
- Migration de bases relationnelles vers NoSQL et capture de flux asynchrones via Kafka.
- Industrialisation et refactorisation du code des modèles pour la mise à l'échelle.

### Data Scientist — Beamlabs / Française des Jeux
*Novembre 2014 à septembre 2015*

- Construction d'un socle Big Data pour le marketing temps réel : architecture distribuée, ingestion en flux, indexation ElasticSearch.
- Développement d'un moteur de recommandation temps réel et de modèles de marketing prédictif.

### Ingénieur R&D, doctorat — CentraleSupélec, Université Paris-Saclay
*Février 2010 à octobre 2014*

- Application du Machine Learning à l'optimisation de cellules photovoltaïques et à la modélisation de transistors.
- Développement d'algorithmes de simulation et d'analyse de données scientifiques.

## Formation

Doctorat, CentraleSupélec — Université Paris-Saclay, Orsay, 2011-2014
Master of Sciences, Université Pierre et Marie Curie, Paris VI, 2010-2011
Maîtrise en Sciences de l'ingénieur, Université Paris Diderot, Paris VII, 2009-2010

## Publications et interventions

18 articles scientifiques publiés dans des revues internationales, 7 participations à des conférences, *Architecture of a Public Transport Supervision System Using Hybridization Models Based on Real and Predictive Data*, DSD 2020, Intervenant Big Data Paris 2018

## Langues

Français bilingue, Anglais courant
