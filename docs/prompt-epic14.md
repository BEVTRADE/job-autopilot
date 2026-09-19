# Prompt — EPIC-14, modèle local et édition Word par MCP

À coller dans Claude Code depuis le dossier du projet.

---

Tu traites EPIC-14, décrit dans docs/epics.md. Lis-le, puis docs/llm-local.md
(décision ADR-011 et constats du 19/09). Travaille sur une branche
`epic-14-llm-local`, commits en français, un par étape.

Un premier jet existe, écrit hors de ce poste et jamais exécuté avec un vrai
modèle : src/llm/local.py, src/cv/docx_mcp.py, src/cv/personnaliser.py,
scripts/verifier_llm_local.py, tests/test_llm_local.py. Tu en es
propriétaire : relis-le d'un œil critique, garde ce qui tient, corrige ou
réécris le reste. Ne le considère pas comme validé.

Règles : ne touche pas à src/matching/ ni aux seuils. Aucun envoi de
candidature. Aucune donnée du candidat vers une adresse non locale. Deux
échecs sur la même erreur : arrête-toi et explique.

ÉTAPE 1 — ENVIRONNEMENT
Vérifie qu'Ollama tourne et que le modèle de config.yaml est présent
(`ollama list`). S'il manque, dis-moi quelle commande lancer et attends ;
indique la mémoire du Mac (`sysctl hw.memsize`) et le modèle conseillé dans
docs/llm-local.md. Puis `make install`.

ÉTAPE 2 — TESTS
`make test` : la suite complète, pas seulement test_llm_local.py. Montre la
sortie. Corrige ce qui échoue sur macOS.

ÉTAPE 3 — VÉRIFICATION RÉELLE
`make verifier-llm`. Montre la sortie complète, le temps de réponse du
modèle et les substitutions proposées, acceptées, refusées. Ouvre le PDF
produit dans data/output/<date>/verif-llm/ et décris ce que tu vois.
Reporte les mesures dans docs/llm-local.md (tableau des vérifications).

ÉTAPE 4 — ÉVALUATION SUR 20 ANNONCES
Prends 20 annonces notées « apply » ou « shortlist » dans data/live/.
Pour chacune : substitutions acceptées, refusées avec motif, écarts, durée.
Écris le bilan dans docs/revues/epic14-evaluation.md. Signale toute
substitution acceptée qui affirme une compétence douteuse. Si plus d'une
substitution sur deux est refusée, arrête-toi : il faut changer de modèle,
c'est à moi d'arbitrer.

ÉTAPE 5 — BRANCHEMENT
Seulement si l'étape 4 est concluante : appelle personnaliser dans l'étage
« choix du CV » (scripts/apply.py, cv_pour_mission) derrière un paramètre
`llm.personnaliser: false` par défaut. CV adapté dans le dossier client ;
écarts et refus dans le rapport du matin (src/report/digest.py). Tests.

Termine par un résumé : ce qui marche, ce qui reste, et ce que tu attends
de moi.
