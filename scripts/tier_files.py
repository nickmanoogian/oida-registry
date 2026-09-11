#!/usr/bin/env python3
"""
tier_files.py — What a tier consists of, declared once

`entities.json` shipped in Rule 20 and reached none of the four places that hand a
tier to somebody: no `.dvc` pointer, no `make mock-*` target, no release asset, and
the load package did not copy it. The list of files a tier consists of existed in
three places and agreed in none of them, so adding a fourth file to the generator
updated exactly one.

This is that list, in one place, with no dependencies beyond the standard library so
anything can import it. `write_dvc_pointers` builds the pointers from it, the load
package copies the ground truth from it, and `check_tier_config` asserts the make
targets pull all of it.
"""

# The workspace itself.
WORKSPACE_FILES = ("documents.csv", "custodians.json", "email-families.json",
                   "batches.json")

# The manifests for content seeded on purpose. Without these the seeded PI, the
# second language, the planted findings and the entity population sit in the data
# with nothing to score them against.
GROUND_TRUTH_FILES = ("pi-ground-truth.csv", "language-mix.json", "findings.json",
                      "entities.json")

PRODUCED_FILES = WORKSPACE_FILES + GROUND_TRUTH_FILES

# Above the medium tier the two big files are published gzipped, which is why the
# published names differ per tier rather than the naming being inconsistent.
GZIPPED_ABOVE_MEDIUM = ("documents.csv", "email-families.json")

# Tiers published as release artifacts. `small` lives in git.
PUBLISHED_TIERS = ("medium", "large", "xlarge")


def published_names(tier):
    """The file names as published for a tier, gzipped where that applies."""
    gz = tier != "medium"
    return [f"{n}.gz" if (gz and n in GZIPPED_ABOVE_MEDIUM) else n
            for n in PRODUCED_FILES]


TIER_FILES = {tier: published_names(tier) for tier in PUBLISHED_TIERS}
