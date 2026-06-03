REGISTRY := https://github.com/nickmanoogian/oioda-registry
OUT       := ./data

.PHONY: help list get-small get-all manifest verify

help:
	@echo ""
	@echo "  make list          List all available datasets with sizes"
	@echo "  make get-small     Download datasets under 100 MB (fast, good for CI/testing)"
	@echo "  make get-all       Download all structured datasets (~80 GB)"
	@echo "  make manifest      Generate the full archive manifest (manifest.tsv.gz)"
	@echo "  make verify        Check that all S3 URLs are still reachable"
	@echo ""
	@echo "  OUT=$(OUT)  — override output dir:  make get-small OUT=./mydata"
	@echo "  REGISTRY=$(REGISTRY)"
	@echo ""

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
	failures = []; \
	[failures.append((f, 'FAIL')) or print('FAIL', f) \
	  for f in sorted(os.listdir('data-products')) if f.endswith('.dvc') \
	  for line in open('data-products/'+f) if 'path: https://' in line \
	  for url in [line.strip().split('path: ',1)[1]] \
	  if (lambda r: r != 200)(urllib.request.urlopen(urllib.request.Request(url, method='HEAD', headers={'User-Agent':'oioda'}), timeout=10).status) \
	] or print('All', len(os.listdir('data-products')), 'URLs OK'); \
	sys.exit(len(failures))"
