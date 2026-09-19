# Suivi — Architecte de Domaine Simulation

| | |
|---|---|
| **Intermédiaire** | Atos, filiale Eviden |
| **Client final probable** | Constructeur ferroviaire, Saint-Ouen-sur-Seine — siège d'Alstom. Non confirmé par l'annonce |
| **TJM affiché** | 600-920 € |
| **TJM visé** | 850 €, plancher 750 € |
| **Durée** | 90 jours renouvelable |
| **Lieu** | Saint-Ouen-sur-Seine, télétravail partiel |
| **Démarrage** | Affiché au 31/08/2026, donc déjà dépassé : besoin non pourvu |
| **Séniorité** | 12 à 20 ans, plus de 10 ans affichés |
| **Source** | Free-Work, simulée le 18/09/2026 dans la chaîne du matin |
| **URL** | https://www.free-work.com/fr/tech-it/job-mission/architecte-de-base-de-donnees/architecte-de-domaine-simulation |
| **CV** | CV_Hakim_Arezki_Architecte_Domaine_Simulation.pdf |
| **Questions filtrantes** | Aucune, constaté sur capture |

## Le besoin

Structurer le domaine Simulation d'une ingénierie ferroviaire : simulation
dynamique, structure, crash, aérodynamique, acoustique, thermique, CEM.
Rationaliser le portefeuille applicatif et définir l'architecture cible, en
architecte de domaine rattaché à l'équipe Engineering IT, avec rôle de design
authority.

Livrables : cartographie applicative, diagnostic, dossier d'architecture
cible, roadmap, référentiel de standards, ADR, reporting, dossier de transfert.

**Exclus explicitement** : études de simulation métier et administration
courante des plateformes.

## Adéquation

**Forte sur la moitié architecture**, qui est le cœur du rôle : cartographie,
rationalisation, architecture cible sur quatre vues, roadmap, design
authority, ADR, standards, transfert. C'est l'axe
ARCHITECTE_ENTREPRISE_URBANISTE, mot pour mot.

**Deux points d'appui spécifiques** : le programme MSM de la RATP avec Alstom
comme partenaire, et la plateforme multi-sites de TotalEnergies. Plus le
doctorat, qui donne une pratique réelle de la simulation numérique.

## Écarts à assumer

- **3DEXPERIENCE, Ansys, CAO, Matlab, HPC** : non pratiqués. Absents du CV,
  à ne pas revendiquer.
- **Simulation numérique** : la pratique est scientifique, issue du doctorat —
  physique des composants — pas mécanique ni CAE ferroviaire. L'annonce demande
  12 à 20 ans « associant pratique de simulation numérique et architecture SI ».
  Écart réel, à cadrer ainsi : **l'annonce exclut elle-même les études de
  simulation métier**. Le rôle demande de comprendre les équipes de calcul, pas
  de faire leurs calculs.
- **Formation** : l'annonce cite mécanique, systèmes ou informatique
  scientifique. Le doctorat relève de la troisième.

## Journal

**18/09/2026** — Mission retenue par le moteur, simulée par la chaîne du matin,
CV d'axe générique sélectionné, formulaire sans question filtrante. Capture
`verif-atos-zero-champ.png`.

**19/09/2026** — Décision de candidater. CV dédié produit.

## Règles de conduite

1. Une seule autorisation de présentation par client final. Si le client est
   bien Alstom, vérifier qu'aucune autre ESN n'a présenté le profil.
2. Ne jamais laisser entendre une pratique de 3DEXPERIENCE ou d'Ansys.
3. TJM : la fourchette est large. Viser 850 €, justifié par la double lecture
   simulation et architecture que peu de profils cumulent.

**19/09/2026, 9h50** — Premier envoi bloqué : « CV partagé non basculé ». Le
CV dédié n'était pas déposé sur Free-Work. Rien n'est parti. Chemin de dépôt
ajouté au script dans la foulée, option `--cv-fichier`.
