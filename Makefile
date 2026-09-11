REGISTRY := https://github.com/nickmanoogian/oida-registry
OUT       := ./data
MOCK_OUT  := ./mock-data
ECI_OUT   := /tmp/oida-large

.PHONY: help setup deps check lint typecheck imports tiers list get-small get-all manifest verify \
        mock-small mock-medium mock-large mock-xlarge mock-validate \
        mock-regen-small mock-regen-medium mock-regen-large mock-regen-xlarge mock-small-edge \
        load-small load-small-synthetic load-small-errors load-broken load-medium load-large load-xlarge load-validate \
        load-release \
        export-insys

help:
	@echo ""
	@echo "  ── Setup ─────────────────────────────────────────────────────"
	@echo "  make setup           Create .venv and install requirements-dev.txt"
	@echo ""
	@echo "  ── Quality gate ──────────────────────────────────────────────"
	@echo "  make check           Everything a branch must pass before a PR"
	@echo "  make deps            Check the gate's own dependencies are installed"
	@echo "  make lint            Ruff only"
	@echo "  make typecheck       Mypy only"
	@echo "  make imports         Import cycle check only"
	@echo "  make tiers           Tier configuration check only (no generation)"
	@echo ""
	@echo "  ── Raw OIDA data ─────────────────────────────────────────────"
	@echo "  make list            List all available OIDA datasets with sizes"
	@echo "  make get-small       Download OIDA files under 100 MB (fast, CI-friendly)"
	@echo "  make get-all         Download all structured datasets from data-products/"
	@echo "  make manifest        Regenerate the full archive manifest (manifest.tsv.gz)"
	@echo "  make verify          Check all S3 URLs are still reachable"
	@echo ""
	@echo "  ── Relativity mock data (MDL 2804 narrative) ─────────────────"
	@echo "  make mock-small      Pull pre-built small tier (~1,430 docs) into $(MOCK_OUT)/small/"
	@echo "  make mock-medium     Pull pre-built medium tier (~9,900 docs) into $(MOCK_OUT)/medium/"
	@echo "  make mock-large      Pull pre-built large tier (~148K docs) into $(MOCK_OUT)/large/"
	@echo "  make mock-xlarge     Pull pre-built extra large tier (~275K docs) into $(MOCK_OUT)/xlarge/"
	@echo "  make mock-validate   Validate the small tier against RULES.md"
	@echo "  make mock-small-edge Generate a small tier with edge cases (starved documents)"
	@echo "  make mock-regen-small   Regenerate small tier from the generator script"
	@echo "  make mock-regen-medium  Regenerate medium tier"
	@echo "  make mock-regen-large   Regenerate large tier"
	@echo "  make mock-regen-xlarge  Regenerate the extra large tier locally (~2 min)"
	@echo ""
	@echo "  ── Native file load packages (Relativity import) ─────────────"
	@echo "  make load-small          Build small tier: native files + .dat load file"
	@echo "  make load-small-synthetic  Same, synthetic content (no S3, faster)"
	@echo "  make load-medium         Build medium tier load package"
	@echo "  make load-small-errors   Build small tier with natives that genuinely fail processing"
	@echo "                           (separate package: load-packages/small-errors/)"
	@echo "  make load-broken         Build load files that fail at IMPORT (opt in, .dat only)"
	@echo "  make load-large          Build large tier load package"
	@echo "  make load-xlarge         Build extra large tier load package (~270K natives)"
	@echo "  make load-validate       Check a built package against RULES.md Rule 11"
	@echo "  make load-release        Build, validate and zip both release assets"
	@echo ""
	@echo "  ── ECI real-data export (real OIDA processing fields) ────────"
	@echo "  make export-insys    Export ALL real Insys docs + custodians.json -> $(ECI_OUT)/"
	@echo "                       (real metadata only; needs pip install -r requirements.txt)"
	@echo ""
	@echo "  OUT=$(OUT)       — raw OIDA download dir"
	@echo "  MOCK_OUT=$(MOCK_OUT)  — mock data dir"
	@echo ""

# ── Quality gate ───────────────────────────────────────────────────────────
# The single command a branch must pass before a PR goes up, modelled on eci-ui's
# `npm run check:circular-deps` (lint + typecheck + cycles + tests in one). Ordered
# cheapest first so a typo fails in seconds rather than after a two minute build.

# The gate used to resolve ruff and mypy against .venv but run everything else
# through a bare `python3`, so it could lint with one interpreter and generate with
# another. `make setup` populates .venv, so .venv wins when it exists and the whole
# gate agrees on which Python it is testing.
VENV := .venv
PY   := $(if $(wildcard $(VENV)/bin/python3),$(VENV)/bin/python3,python3)
RUFF := $(if $(wildcard $(VENV)/bin/ruff),$(VENV)/bin/ruff,$(shell command -v ruff 2>/dev/null || echo ruff))
MYPY := $(if $(wildcard $(VENV)/bin/mypy),$(VENV)/bin/mypy,$(shell command -v mypy 2>/dev/null || echo mypy))

setup:
	@python3 -m venv $(VENV)
	@$(VENV)/bin/python3 -m pip install --quiet --upgrade pip
	@$(VENV)/bin/python3 -m pip install --quiet -r requirements-dev.txt
	@echo "  $(VENV) ready — run 'make check'"

deps:
	@$(PY) scripts/check_deps.py

lint:
	@$(RUFF) check . || (echo "  lint failed — run '$(RUFF) check . --fix'" && exit 1)

typecheck:
	@$(MYPY) scripts/ --ignore-missing-imports

imports:
	@$(PY) scripts/check_imports.py

tiers:
	@$(PY) scripts/check_tier_config.py

check: deps lint typecheck imports tiers
	@echo "\n── Rules ──"
	@$(PY) scripts/validate_mock_data.py --tier small
	@echo "\n── Edge case tier ──"
	@$(PY) scripts/generate_mock_metadata.py --tier small --edge-cases --out /tmp/oida-gate-edge >/dev/null
	@$(PY) scripts/validate_mock_data.py --tier small --dir /tmp/oida-gate-edge
	@echo "\n── Error scenarios ──"
	@$(PY) scripts/test_error_scenarios.py
	@echo "\n── Determinism ──"
	@$(PY) scripts/generate_mock_metadata.py --tier small >/dev/null
	@git diff --quiet mock-data/small/ || (echo "  FAIL regenerating the small tier changed it — commit the regenerated files" && exit 1)
	@echo "  small tier regenerates byte-identical"
	@echo "\n  All gate checks passed. Safe to raise a PR.\n"

# ── Raw OIDA data ──────────────────────────────────────────────────────────

list:
	python3 scripts/download.py --list

get-small:
	@mkdir -p $(OUT)
	dvc get $(REGISTRY) data-products/prescribers.csv             --out $(OUT)/prescribers.csv
	dvc get $(REGISTRY) data-products/mnk_customer_orders.csv     --out $(OUT)/mnk_customer_orders.csv
	dvc get $(REGISTRY) data-products/mnk_customer_orders.csv.zip --out $(OUT)/mnk_customer_orders.csv.zip
	dvc get $(REGISTRY) data-products/oida-image-collection-metadata-version-1.csv.gz --out $(OUT)/oida-image-collection-metadata-version-1.csv.gz
	dvc get $(REGISTRY) data-products/duexis_bydates.csv          --out $(OUT)/duexis_bydates.csv
	dvc get $(REGISTRY) data-products/sumavel_bydates.csv         --out $(OUT)/sumavel_bydates.csv
	dvc get $(REGISTRY) samples/oida-bulk-download-sample.zip     --out $(OUT)/oida-bulk-download-sample.zip

get-all:
	@mkdir -p $(OUT)
	dvc pull --with-deps

manifest:
	python3 scripts/fetch_manifest.py --out manifest.tsv.gz
	@echo "Written to manifest.tsv.gz"

verify:
	@python3 scripts/verify_urls.py

# ── Relativity mock data ───────────────────────────────────────────────────

mock-small:
	@mkdir -p $(MOCK_OUT)/small
	dvc get $(REGISTRY) mock-data/small/documents.csv      --out $(MOCK_OUT)/small/documents.csv
	dvc get $(REGISTRY) mock-data/small/custodians.json    --out $(MOCK_OUT)/small/custodians.json
	dvc get $(REGISTRY) mock-data/small/email-families.json --out $(MOCK_OUT)/small/email-families.json
	dvc get $(REGISTRY) mock-data/small/batches.json       --out $(MOCK_OUT)/small/batches.json
	@echo "Small tier ready at $(MOCK_OUT)/small/"

# The ground truth files are part of a tier, not extras: without them the seeded
# PI, the second language and the planted findings are in the data with nothing
# to score them against.
mock-medium:
	@mkdir -p $(MOCK_OUT)/medium
	dvc get $(REGISTRY) mock-data/medium/documents.csv        --out $(MOCK_OUT)/medium/documents.csv
	dvc get $(REGISTRY) mock-data/medium/custodians.json      --out $(MOCK_OUT)/medium/custodians.json
	dvc get $(REGISTRY) mock-data/medium/email-families.json  --out $(MOCK_OUT)/medium/email-families.json
	dvc get $(REGISTRY) mock-data/medium/batches.json         --out $(MOCK_OUT)/medium/batches.json
	dvc get $(REGISTRY) mock-data/medium/pi-ground-truth.csv  --out $(MOCK_OUT)/medium/pi-ground-truth.csv
	dvc get $(REGISTRY) mock-data/medium/language-mix.json    --out $(MOCK_OUT)/medium/language-mix.json
	dvc get $(REGISTRY) mock-data/medium/findings.json        --out $(MOCK_OUT)/medium/findings.json
	dvc get $(REGISTRY) mock-data/medium/entities.json        --out $(MOCK_OUT)/medium/entities.json
	dvc get $(REGISTRY) mock-data/medium/data-sources.json    --out $(MOCK_OUT)/medium/data-sources.json
	@echo "Medium tier ready at $(MOCK_OUT)/medium/"

mock-large:
	@mkdir -p $(MOCK_OUT)/large
	dvc get $(REGISTRY) mock-data/large/documents.csv.gz      --out $(MOCK_OUT)/large/documents.csv.gz
	dvc get $(REGISTRY) mock-data/large/custodians.json        --out $(MOCK_OUT)/large/custodians.json
	dvc get $(REGISTRY) mock-data/large/email-families.json.gz --out $(MOCK_OUT)/large/email-families.json.gz
	dvc get $(REGISTRY) mock-data/large/batches.json           --out $(MOCK_OUT)/large/batches.json
	dvc get $(REGISTRY) mock-data/large/pi-ground-truth.csv    --out $(MOCK_OUT)/large/pi-ground-truth.csv
	dvc get $(REGISTRY) mock-data/large/language-mix.json      --out $(MOCK_OUT)/large/language-mix.json
	dvc get $(REGISTRY) mock-data/large/findings.json          --out $(MOCK_OUT)/large/findings.json
	dvc get $(REGISTRY) mock-data/large/entities.json          --out $(MOCK_OUT)/large/entities.json
	dvc get $(REGISTRY) mock-data/large/data-sources.json      --out $(MOCK_OUT)/large/data-sources.json
	gunzip -f $(MOCK_OUT)/large/documents.csv.gz
	gunzip -f $(MOCK_OUT)/large/email-families.json.gz
	@echo "Large tier ready at $(MOCK_OUT)/large/"

mock-xlarge:
	@mkdir -p $(MOCK_OUT)/xlarge
	dvc get $(REGISTRY) mock-data/xlarge/documents.csv.gz      --out $(MOCK_OUT)/xlarge/documents.csv.gz
	dvc get $(REGISTRY) mock-data/xlarge/custodians.json        --out $(MOCK_OUT)/xlarge/custodians.json
	dvc get $(REGISTRY) mock-data/xlarge/email-families.json.gz --out $(MOCK_OUT)/xlarge/email-families.json.gz
	dvc get $(REGISTRY) mock-data/xlarge/batches.json           --out $(MOCK_OUT)/xlarge/batches.json
	dvc get $(REGISTRY) mock-data/xlarge/pi-ground-truth.csv    --out $(MOCK_OUT)/xlarge/pi-ground-truth.csv
	dvc get $(REGISTRY) mock-data/xlarge/language-mix.json      --out $(MOCK_OUT)/xlarge/language-mix.json
	dvc get $(REGISTRY) mock-data/xlarge/findings.json          --out $(MOCK_OUT)/xlarge/findings.json
	dvc get $(REGISTRY) mock-data/xlarge/entities.json          --out $(MOCK_OUT)/xlarge/entities.json
	dvc get $(REGISTRY) mock-data/xlarge/data-sources.json      --out $(MOCK_OUT)/xlarge/data-sources.json
	gunzip -f $(MOCK_OUT)/xlarge/documents.csv.gz
	gunzip -f $(MOCK_OUT)/xlarge/email-families.json.gz
	@echo "Extra large tier ready at $(MOCK_OUT)/xlarge/"

mock-validate:
	python3 scripts/validate_mock_data.py --tier small

mock-small-edge:
	python3 scripts/generate_mock_metadata.py --tier small --edge-cases --out mock-data/small-edge
	python3 scripts/validate_mock_data.py --tier small --dir mock-data/small-edge

# ── ECI real-data export ────────────────────────────────────────────────────

export-insys:
	@mkdir -p $(ECI_OUT)
	python3 scripts/export_insys_documents.py --out $(ECI_OUT)
	@echo "Real Insys export ready at $(ECI_OUT)/ (documents.csv.gz + custodians.json)"

mock-regen-small:
	python3 scripts/generate_mock_metadata.py --tier small
	python3 scripts/validate_mock_data.py --tier small

mock-regen-medium:
	python3 scripts/generate_mock_metadata.py --tier medium
	python3 scripts/validate_mock_data.py --tier medium

mock-regen-large:
	python3 scripts/generate_mock_metadata.py --tier large
	python3 scripts/validate_mock_data.py --tier large

# Published as a release artifact like the other tiers. Regenerate it locally only
# if you are changing the generator, or you want a different seed.
mock-regen-xlarge:
	python3 scripts/generate_mock_metadata.py --tier xlarge
	python3 scripts/validate_mock_data.py --tier xlarge

# ── Native file load packages ──────────────────────────────────────────────

load-small:
	python3 scripts/build_load_package.py --tier small
	@echo "Package ready at load-packages/small/"

load-small-synthetic:
	python3 scripts/build_load_package.py --tier small --no-oida
	@echo "Package ready at load-packages/small/"

load-small-errors: mock-small-edge
	python3 scripts/build_load_package.py --tier small --dir mock-data/small-edge --with-errors --out load-packages/small-errors
	@echo "Package ready at load-packages/small-errors/ (see EXPECTED_ERRORS.csv)"

load-broken:
	python3 scripts/build_broken_load_files.py
	python3 scripts/build_broken_load_files.py --verify

load-medium:
	python3 scripts/build_load_package.py --tier medium
	@echo "Package ready at load-packages/medium/"

load-large:
	python3 scripts/build_load_package.py --tier large
	@echo "Package ready at load-packages/large/"

load-xlarge:
	python3 scripts/build_load_package.py --tier xlarge
	@echo "Package ready at load-packages/xlarge/"

load-validate:
	python3 scripts/validate_load_package.py load-packages/small
	@test ! -d load-packages/small-errors || python3 scripts/validate_load_package.py load-packages/small-errors

# The release assets. Zipped from the repo root so the archive holds
# load-packages/{small,small-errors}/, which is the shape every published
# version has had. Validate before zipping: a package that fails the gate is
# not a release candidate.
load-release: load-small load-small-errors load-validate
	@rm -f load-packages/small-load-package.zip load-packages/small-errors-load-package.zip
	cd $(CURDIR) && zip -qr load-packages/small-load-package.zip load-packages/small
	cd $(CURDIR) && zip -qr load-packages/small-errors-load-package.zip load-packages/small-errors
	@ls -la load-packages/*.zip
