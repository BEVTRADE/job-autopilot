# Points d'entrée du radar. Chaque cible correspond à une spécification.
#
#   make            liste les cibles
#   make install    installe l'environnement
#   make test       tests hors ligne
#   make sonde      relève le DOM réel de Free-Work, sans candidater
#   make simu       exécution du matin, sans envoi
#
# La cible d'envoi réel est délibérément verbeuse : elle ne doit pas être
# tapée par réflexe.

SHELL := /bin/bash
PY := $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
JOUR := $(shell date +%F)

.DEFAULT_GOAL := aide
.PHONY: aide install login test sonde veille simu candidater-pour-de-vrai rapport \
        attente catalogue verifier-llm planifier deplanifier etat stop reprendre propre \
        diag-session diag-planifier diag-deplanifier

aide:
	@echo "Radar de missions — cibles disponibles"
	@echo
	@echo "  Mise en service        spécification : docs/autonomie.md"
	@echo "    make install         environnement, Playwright, Chromium"
	@echo "    make login           connexion Free-Work, manuelle, une fois"
	@echo "    make test            tests hors ligne, sans réseau (Chromium local pour le DOM)"
	@echo "    make sonde           relève le DOM réel de Free-Work, aucune candidature"
	@echo
	@echo "  Exploitation           spécification : docs/autonomie.md"
	@echo "    make veille          collecte seule, aucune candidature"
	@echo "    make simu            chaîne complète, arrêt avant envoi"
	@echo "    make rapport         rapport du jour"
	@echo "    make attente         candidatures à reprendre à la main"
	@echo "    make catalogue       écart vocabulaire CV / missions, data/catalogue.md"
	@echo "    make verifier-llm    modèle local Ollama + serveurs MCP, rien n'est envoyé"
	@echo
	@echo "  Mesure de durée de session (EPIC-12, temporaire)"
	@echo "    make diag-session    une visite de connecté, une ligne dans data/diag-session.jsonl"
	@echo "    make diag-planifier  la répète toutes les 6 h ; make diag-deplanifier la retire"
	@echo
	@echo "  Planification"
	@echo "    make planifier       installe la tâche de 7h30"
	@echo "    make deplanifier     la retire"
	@echo "    make etat            état du dépôt, de la tâche, du jour"
	@echo
	@echo "  Sécurité"
	@echo "    make stop            kill-switch, arrête tout"
	@echo "    make reprendre       lève le kill-switch"
	@echo
	@echo "  Envoi réel : make candidater-pour-de-vrai"

# ---------------------------------------------------------------- mise en service

install:
	bash scripts/setup.sh

login:
	$(PY) scripts/apply.py --login

test:
	bash scripts/verifier.sh

# Relève le DOM réel du parcours de candidature (EPIC-8) dans tests/pages/freework/,
# sans jamais cliquer sur « Je postule », puis rejoue les tests de sélecteurs sur
# ces instantanés : s'ils échouent, le site a changé, on le sait avant un envoi raté.
# Écrit sur le compte : dépose le CV de simulation s'il manque, bascule le CV
# partagé puis remet le CV de repos.
sonde:
	$(PY) scripts/sonde_freework.py
	bash scripts/verifier.sh

# ---------------------------------------------------------------- exploitation

veille:
	$(PY) scripts/collect.py --source freework --limit 200 --delay 0.8

simu:
	scripts/matin.sh

candidater-pour-de-vrai:
	@echo "Envoi RÉEL de candidatures sur Free-Work."
	@echo "Plafond : $${MAX:-3} candidature(s). CV : $${CV:-FR_ARCHITECTE_IA_GENAI.pdf}"
	@read -p "Taper OUI pour confirmer : " r; [ "$$r" = "OUI" ] || { echo "annulé"; exit 1; }
	scripts/matin.sh --envoyer

rapport:
	@$(PY) -m src.report.digest $(JOUR) >/dev/null
	@cat data/output/$(JOUR)/rapport-matin.md

attente:
	@f=data/output/$(JOUR)/file_attente.json; \
	if [ -s "$$f" ]; then $(PY) -m json.tool "$$f"; \
	else echo "aucune candidature en attente pour le $(JOUR)"; fi

catalogue:
	$(PY) scripts/catalogue.py
	@echo "rapport : data/catalogue.md — aucune modification du catalogue, décision humaine"

# ---------------------------------------------------------------- mesure de durée (EPIC-12)

# Une visite d'une page de connecté, une ligne dans data/diag-session.jsonl :
# présence, longueur et expiration de jwt_s, jwt_hp, refresh_token. Jamais une valeur.
diag-session:
	$(PY) scripts/diag_session.py --visiter

# Agent launchd TEMPORAIRE : une visite toutes les 6 h, verrou du matin partagé.
# À retirer (make diag-deplanifier) une fois la mesure lue.
DIAG_LABEL := fr.kiras.jobautopilot.diag-session
DIAG_PLIST := $$HOME/Library/LaunchAgents/$(DIAG_LABEL).plist

diag-planifier:
	@d="$$HOME/Library/LaunchAgents"; mkdir -p "$$d" data/logs; \
	py="$(abspath $(PY))"; \
	[ -x "$$py" ] || py="$$(command -v python3)"; \
	sed -e "s#@RACINE@#$$PWD#g" -e "s#@PYTHON@#$$py#g" \
	  scripts/launchd/diag-session.plist > "$(DIAG_PLIST)"; \
	plutil -lint "$(DIAG_PLIST)" >/dev/null || { echo "plist invalide"; exit 1; }; \
	launchctl unload "$(DIAG_PLIST)" 2>/dev/null || true; \
	launchctl load "$(DIAG_PLIST)"; \
	echo "mesure lancée : un relevé maintenant, puis toutes les 6 h"; \
	echo "lecture : data/diag-session.jsonl — arrêt : make diag-deplanifier"

diag-deplanifier:
	@launchctl unload "$(DIAG_PLIST)" 2>/dev/null \
	  && echo "mesure arrêtée" || echo "aucune mesure chargée"; \
	rm -f "$(DIAG_PLIST)"

# ---------------------------------------------------------------- planification

planifier:
	@d="$$HOME/Library/LaunchAgents"; mkdir -p "$$d"; \
	sed "s#REMPLACER_PAR_LE_CHEMIN/job-autopilot#$$PWD#g" \
	  scripts/fr.kiras.jobautopilot.plist > "$$d/fr.kiras.jobautopilot.plist"; \
	launchctl unload "$$d/fr.kiras.jobautopilot.plist" 2>/dev/null || true; \
	launchctl load "$$d/fr.kiras.jobautopilot.plist"; \
	echo "tâche installée, déclenchement à 7h30"; \
	echo "pour un essai immédiat : launchctl start fr.kiras.jobautopilot"

deplanifier:
	@launchctl unload "$$HOME/Library/LaunchAgents/fr.kiras.jobautopilot.plist" 2>/dev/null \
	  && echo "tâche retirée" || echo "aucune tâche chargée"

etat:
	@echo "dépôt    : $$(git log --oneline -1 2>/dev/null || echo 'pas de dépôt')"
	@echo "modifié  : $$(git status --short 2>/dev/null | wc -l | tr -d ' ') fichier(s)"
	@echo "tâche    : $$(launchctl list 2>/dev/null | grep -c 'fr.kiras.jobautopilot$$' | tr -d ' ') chargée(s)"
	@echo "mesure   : $$(launchctl list 2>/dev/null | grep -q 'jobautopilot.diag-session' && echo 'EN COURS (make diag-deplanifier)' || echo inactive)"
	@echo "session  : $$([ -d $$HOME/.job-autopilot/browser-profile ] && echo présente || echo ABSENTE)"
	@echo "stop     : $$([ -e $$HOME/.job-autopilot/STOP ] && echo ACTIF || echo inactif)"
	@echo "retenues : $$([ -s data/output/$(JOUR)/retenues.json ] && \
	   $(PY) -c "import json;print(len(json.load(open('data/output/$(JOUR)/retenues.json'))))" || echo 0) le $(JOUR)"

# ---------------------------------------------------------------- sécurité

stop:
	@mkdir -p $$HOME/.job-autopilot && touch $$HOME/.job-autopilot/STOP
	@echo "kill-switch ACTIF — rien ne partira"

reprendre:
	@rm -f $$HOME/.job-autopilot/STOP && echo "kill-switch levé"

propre:
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "caches Python supprimés"

# Modèle local (EPIC-14, docs/llm-local.md) : Ollama, MCP docx, bout en bout sur une copie de CV.
verifier-llm:
	$(PY) scripts/verifier_llm_local.py
