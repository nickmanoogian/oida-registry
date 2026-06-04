REGISTRY := https://github.com/nickmanoogian/oioda-registry
OUT       := ./data
MOCK_OUT  := ./mock-data

.PHONY: help list get-small get-all manifest verify \
        mock-small mock-medium mock-large mock-validate \
        mock-regen-small mock-regen-medium mock-regen-large \
        load-small load-small-synthetic load-medium load-large

help:
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
	@echo "  make mock-validate   Validate the small tier against RULES.md"
	@echo "  make mock-regen-small   Regenerate small tier from the generator script"
	@echo "  make mock-regen-medium  Regenerate medium tier"
	@echo "  make mock-regen-large   Regenerate large tier"
	@echo ""
	@echo "  ── Native file load packages (Relativity import) ─────────────"
	@echo "  make load-small          Build small tier: native files + .dat load file"
	@echo "  make load-small-synthetic  Same, synthetic content (no S3, faster)"
	@echo "  make load-medium         Build medium tier load package"
	@echo "  make load-large          Build large tier load package"
	@echo ""
	@echo "  OUT=$(OUT)       — raw OIDA download dir"
	@echo "  MOCK_OUT=$(MOCK_OUT)  — mock data dir"
	@echo ""

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
	@python3 -c " \
	import os, urllib.request, sys; \
	ok = 0; fail = 0; \
	[setattr(sys.modules[__name__], '_', None) or \
	 (print(f'  PASS  {f}') or setattr(sys.modules[__name__], 'ok', ok+1)) \
	  if (lambda r: r == 200)(urllib.request.urlopen(urllib.request.Request( \
	    [l.strip().split('path: ',1)[1] for l in open('data-products/'+f) if 'path: https://' in l][0], \
	    method='HEAD', headers={'User-Agent':'oioda'}), timeout=10).status) \
	  else (print(f'  FAIL  {f}') or setattr(sys.modules[__name__], 'fail', fail+1)) \
	  for f in sorted(os.listdir('data-products')) if f.endswith('.dvc')] ; \
	print(f'  {ok} OK, {fail} failed'); sys.exit(fail)"

# ── Relativity mock data ───────────────────────────────────────────────────

mock-small:
	@mkdir -p $(MOCK_OUT)/small
	dvc get $(REGISTRY) mock-data/small/documents.csv      --out $(MOCK_OUT)/small/documents.csv
	dvc get $(REGISTRY) mock-data/small/custodians.json    --out $(MOCK_OUT)/small/custodians.json
	dvc get $(REGISTRY) mock-data/small/email-families.json --out $(MOCK_OUT)/small/email-families.json
	dvc get $(REGISTRY) mock-data/small/batches.json       --out $(MOCK_OUT)/small/batches.json
	@echo "Small tier ready at $(MOCK_OUT)/small/"

mock-medium:
	@mkdir -p $(MOCK_OUT)/medium
	dvc get $(REGISTRY) mock-data/medium/documents.csv      --out $(MOCK_OUT)/medium/documents.csv
	dvc get $(REGISTRY) mock-data/medium/custodians.json    --out $(MOCK_OUT)/medium/custodians.json
	dvc get $(REGISTRY) mock-data/medium/email-families.json --out $(MOCK_OUT)/medium/email-families.json
	dvc get $(REGISTRY) mock-data/medium/batches.json       --out $(MOCK_OUT)/medium/batches.json
	@echo "Medium tier ready at $(MOCK_OUT)/medium/"

mock-large:
	@mkdir -p $(MOCK_OUT)/large
	dvc get $(REGISTRY) mock-data/large/documents.csv.gz      --out $(MOCK_OUT)/large/documents.csv.gz
	dvc get $(REGISTRY) mock-data/large/custodians.json        --out $(MOCK_OUT)/large/custodians.json
	dvc get $(REGISTRY) mock-data/large/email-families.json.gz --out $(MOCK_OUT)/large/email-families.json.gz
	dvc get $(REGISTRY) mock-data/large/batches.json           --out $(MOCK_OUT)/large/batches.json
	gunzip -f $(MOCK_OUT)/large/documents.csv.gz
	gunzip -f $(MOCK_OUT)/large/email-families.json.gz
	@echo "Large tier ready at $(MOCK_OUT)/large/"

mock-validate:
	python3 scripts/validate_mock_data.py --tier small

mock-regen-small:
	python3 scripts/generate_mock_metadata.py --tier small
	python3 scripts/validate_mock_data.py --tier small

mock-regen-medium:
	python3 scripts/generate_mock_metadata.py --tier medium
	python3 scripts/validate_mock_data.py --tier medium

mock-regen-large:
	python3 scripts/generate_mock_metadata.py --tier large
	python3 scripts/validate_mock_data.py --tier large

# ── Native file load packages ──────────────────────────────────────────────

load-small:
	python3 scripts/build_load_package.py --tier small
	@echo "Package ready at load-packages/small/"

load-small-synthetic:
	python3 scripts/build_load_package.py --tier small --no-oida
	@echo "Package ready at load-packages/small/"

load-medium:
	python3 scripts/build_load_package.py --tier medium
	@echo "Package ready at load-packages/medium/"

load-large:
	python3 scripts/build_load_package.py --tier large
	@echo "Package ready at load-packages/large/"
