#!/usr/bin/env python3
"""
check_tier_config.py — Every declared tier is fully declared, and in band

Generating a tier takes seconds for small and two minutes for xlarge, so CI only
generates the small one. That leaves the bigger tiers' configuration unguarded: a
tier can be added without an entry in the PI table or the language mix, and a file
count can be edited until a share leaves the band Rule 1 sets, and nothing notices
until somebody spends two minutes finding out.

This runs in milliseconds against the declarations alone. It does not generate
anything.

Usage:
  python scripts/check_tier_config.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import entity_population
import generate_mock_metadata as gen
import language_mix
import pi_layer
import validate_mock_data as val

PASS = "\033[32mok  \033[0m"
FAIL = "\033[31mFAIL\033[0m"

failures: list[str] = []


def check(label, ok, detail=""):
    print(f"  [{PASS if ok else FAIL}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label)


def main():
    tiers = list(gen.TIER_FILE_COUNTS)
    print(f"\n  Tier configuration: {', '.join(tiers)}\n")

    # 1. Every tier-keyed table covers every tier. A tier borrowing another's
    #    narrative is exempt from the narrative tables and only those.
    narrative_only = {"CUSTODIANS": gen.CUSTODIANS, "PHASE_WEIGHTS": gen.PHASE_WEIGHTS}
    own = {"WORKFLOW": gen.WORKFLOW, "DATE_RANGES": gen.DATE_RANGES,
           "LANGUAGE_MIX": language_mix.LANGUAGE_MIX,
           "ROSTER_SIZE": entity_population.ROSTER_SIZE,
           "ALIAS_COUNT": entity_population.ALIAS_COUNT}
    for name, table in own.items():
        missing = [t for t in tiers if t not in table]
        check(f"{name} covers every tier", not missing,
              f"missing: {missing}" if missing else f"{len(tiers)} tiers")
    for name, table in narrative_only.items():
        missing = [t for t in tiers
                   if gen.narrative_tier(t) not in table]
        check(f"{name} covers every tier or its narrative parent", not missing,
              f"missing: {missing}" if missing else f"{len(tiers)} tiers")

    for scenario, per_tier in pi_layer.SCENARIOS.items():
        missing = [t for t in tiers if t not in per_tier]
        check(f"PI scenario {scenario} covers every tier", not missing,
              f"missing: {missing}" if missing else "")

    # 2. A narrative parent has to be a tier that exists.
    orphan = {t: p for t, p in gen.NARRATIVE_PARENT.items() if p not in tiers}
    check("every narrative parent is a real tier", not orphan,
          f"{orphan}" if orphan else ", ".join(f"{t} -> {p}" for t, p
                                               in gen.NARRATIVE_PARENT.items()))

    # 3. Every file type share sits inside the band the validator will check.
    for tier in tiers:
        counts = gen.TIER_FILE_COUNTS[tier]
        total  = sum(counts.values())
        out_of_band = []
        for family, band in val.FAMILY_SHARE.items():
            lo, hi = val.FAMILY_SHARE_BY_TIER.get(family, {}).get(tier, band)
            share = sum(n for cat, n in counts.items()
                        if val.in_family(cat, family)) / total
            if not lo <= share <= hi:
                out_of_band.append(f"{family} {share:.1%} outside {lo:.1%}-{hi:.1%}")
        check(f"{tier}: every family share is in band", not out_of_band,
              "; ".join(out_of_band) if out_of_band
              else f"{total:,} documents across {len(counts)} types")

        enough = len(counts) >= val.MIN_FILE_TYPES.get(tier, 20)
        check(f"{tier}: enough distinct file types", enough,
              f"{len(counts)} declared, {val.MIN_FILE_TYPES.get(tier, 20)} required")

    print()
    if failures:
        print(f"  {len(failures)} check(s) failed\n")
        sys.exit(1)
    print("  Tier configuration is complete and in band\n")


if __name__ == "__main__":
    main()
