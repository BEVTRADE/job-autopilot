# Points d'entrée du radar. Chaque cible correspond à une spécification.
#
#   make            liste les cibles
#   make install    installe l'environnement
#   make test       tests hors ligne
#   make simu       exécution du matin, sans envoi
#
# La cible d'envoi réel est délibérément verbeuse : elle ne doit pas être
# tapée par réflexe.

SHELL := /bin/bash
PY := $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
JOUR := $(shell date +%F)

.DEFAULT_GOAL := aide
.PHONY: aide install login test veille simu candidater-pour-de-vrai rapport \
        attente catalogue planifier deplanifier etat stop reprendre propre

aide:
	@echo "Radar de missions — cibles disponibles"
	@echo
	@echo "  Mise en service        spécification : docs/autonomie.md"
	@echo "    make install         environnement, Playwright, Chromium"
	@echo "    make login           connexion Free-Work, manuelle, une fois"
	@echo "    make test            tests hors ligne, sans réseau ni navigateur"
	@echo
	@echo "  Exploitation           spécification : docs/autonomie.md"
	@echo "    make veille          collecte seule, aucune candidature"
	@echo "    make simu            chaîne complète, arrêt avant envoi"
	@echo "    make rapport         rapport du jour"
	@echo "    make attente         candidatures à reprendre à la main"
	@echo "    make catalogue       écart vocabulaire CV / missions, data/catalogue.md"
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
	@echo "tâche    : $$(launchctl list 2>/dev/null | grep -c jobautopilot | tr -d ' ') chargée(s)"
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
