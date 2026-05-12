SKILL_DIR := $(shell python3 -c "import subprocess,json; skills=json.loads(subprocess.check_output(['hermes','skills','--json']).decode()); s=[x for x in skills if x['name']=='hermes-git-sync']; print(s[0]['path'] if s else '')")
SCRIPTS    := $(SKILL_DIR)/scripts

# ── Sync skills + commit + push ───────────────────────────────────────────────
.PHONY: git-sync git-sync-dry skills-sync
git-sync:
	MY_HERMES_REPO=$(CURDIR) bash $(SCRIPTS)/hermes-git-sync.sh

git-sync-dry: ## Show what would be committed (no commit)
	MY_HERMES_REPO=$(CURDIR) bash $(SCRIPTS)/hermes-git-sync.sh --dry-run

skills-sync: ## Sync my-skills snapshot only (no commit) — inspect changes in IDE
	MY_HERMES_REPO=$(CURDIR) bash $(SCRIPTS)/hermes-git-sync.sh --sync-only

# ── Re-apply patches after hermes update ─────────────────────────────────────
.PHONY: patch
patch:
	bash $(SCRIPTS)/apply-patches.sh

# ── Show patch + PR status ────────────────────────────────────────────────────
.PHONY: check-update
check-update:
	hermes --version
	@echo ""
	@echo "Patch registry:"
	@cat patches/registry.yaml | grep -E 'file:|status:|pr:' | paste - - -

# ── Safe hermes update ────────────────────────────────────────────────────────
.PHONY: update
update: check-update
	@echo ""
	@read -p "Proceed with hermes update? [y/N] " ans && [ "$$ans" = "y" ] && hermes update || echo "Aborted."
