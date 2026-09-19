# Dossier d'architecture — Radar de missions

Version publiée (page consultable) : voir l'artifact « Architecture du Radar ».

## Résumé des décisions

| # | Décision | Motif principal |
|---|---|---|
| ADR-001 | Agent local pour tout ce qui exige une session | Le service ne détient aucun identifiant de plateforme |
| ADR-002 | Aucun LLM dans le chemin de décision | Score auditable et rejouable sur 1901 cas |
| ADR-011 | Modèle local (Ollama) pour la rédaction ; édition Word par serveur MCP piloté par le code, jamais par le modèle | Données du candidat sur le poste ; substitutions validées contre le profil maître |
| ADR-003 | SQLite, pas davantage | Mono-utilisateur, refus du sur-dimensionnement |
| ADR-004 | Validation humaine obligatoire | ~6 dossiers/mois, CGU des plateformes |
| ADR-005 | Connecteurs déclarés par capacité | Sources hétérogènes (découvrir / lire / soumettre) |

## Exigences non fonctionnelles

- Exécution matinale < 10 min pour 400 URL candidates
- 1 req/s maximum par source, repli exponentiel
- Dédoublonnage sur 120 jours, inter-sources
- Arrêt d'urgence effectif en < 5 s
- 100 % des soumissions avec capture horodatée
- RPO 24 h

## Trajectoire

- **Vague 1 — acquis.** Moteur déterministe calibré, connecteurs Free-Work et BOAMP, historique SQLite, rapport HTML.
- **Vague 2.** API REST + interface : file de validation, différentiel de CV, réglage du moteur avec aperçu d'impact.
- **Vague 3.** Agent local : sources à session, soumission approuvée avec capture. Sources restantes.
