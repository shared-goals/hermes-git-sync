.PHONY: help git-sync git-sync-dry skills-sync patch install update check-update dashboard

SHELL := /bin/bash

HERMES_DIR        := $(HOME)/my-hermes
GIT_SYNC_SCRIPTS  := $(HOME)/.hermes/skills/devops/hermes-git-sync/scripts
UPDATE_SCRIPTS    := $(HOME)/.hermes/skills/devops/hermes-update-workflow/scripts

# ── Hermes ────────────────────────────────────────────────────────────────────

help: ## Show this help
	@awk 'BEGIN {FS=":.*##"; printf "\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  make %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

git-sync: ## Sync Hermes config, memories and skills to git
	@MY_HERMES_REPO=$(HERMES_DIR) bash $(GIT_SYNC_SCRIPTS)/hermes-git-sync.sh

skills-sync: ## Sync my-skills snapshot only (no commit) — use to see changes in IDE
	@MY_HERMES_REPO=$(HERMES_DIR) bash $(GIT_SYNC_SCRIPTS)/hermes-git-sync.sh --sync-only

git-sync-dry: ## Show what would be committed (no commit)
	@MY_HERMES_REPO=$(HERMES_DIR) bash $(GIT_SYNC_SCRIPTS)/hermes-git-sync.sh --dry-run

patch: ## Re-apply patches after hermes update
	@MY_HERMES_REPO=$(HERMES_DIR) bash $(UPDATE_SCRIPTS)/apply-patches.sh

update: ## Safe update — check releases, PR statuses, confirm, update, re-apply patches
	@MY_HERMES_REPO=$(HERMES_DIR) bash $(UPDATE_SCRIPTS)/hermes-update.sh

check-update: ## Check for new releases and patch PR statuses (no changes)
	@MY_HERMES_REPO=$(HERMES_DIR) bash $(UPDATE_SCRIPTS)/hermes-update.sh --check

install: ## Bootstrap my-hermes on a new machine (symlinks, cron)
	@bash $(GIT_SYNC_SCRIPTS)/setup-my-hermes.sh $(HERMES_DIR)

dashboard: ## Start Hermes dashboard on default port 9119 (checks for conflicts first)
	@PID=$$(lsof -nP -iTCP:9119 -sTCP:LISTEN 2>/dev/null | awk 'NR==2{print $$2}'); \
	if [ -n "$$PID" ]; then \
		echo "⚠️  Port 9119 is in use by PID $$PID:"; \
		ps -p $$PID -o pid,command 2>/dev/null | tail -1; \
		echo "Kill it first: kill $$PID"; \
		exit 1; \
	fi
	hermes dashboard --host 0.0.0.0 --insecure --no-open
