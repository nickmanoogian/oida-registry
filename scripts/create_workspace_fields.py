#!/usr/bin/env python3
"""Create the Document fields a stock workspace lacks, so the load file fully maps.

Without these, Import/Export's Auto Map Fields matches 34 of the load file's 59
columns and the other 25 sit inert: Relativity ignores an unmatched column, so
they import as nothing at all. With them, 58 of 59 map by exact name. The last
one is ExtractedTextFilePath, which cannot be fixed by naming at any price and
is handled by the import profile instead. See workspace_fields.py for why.

    export RELATIVITY_URL=https://yourinstance.relativity.one
    export RELATIVITY_TOKEN=...            # or RELATIVITY_USER + RELATIVITY_PASSWORD
    python3 scripts/create_workspace_fields.py --workspace 1234567

Idempotent: a field that already exists is reported and skipped, so re-running
after a partial failure is safe. Pass --dry-run to print what it would create.

Each create alters the Document table schema, so do not run this underneath an
import job that may be hours into extracting text.

IF AN ANALYSIS OVER THIS DATA FAILS, DO NOT START WITH THE LOAD FILE. An Early
Insights run on our 9,980 document workspace failed twice, about 7 minutes in
each time, at the step named RunningStructuredAnalytics, producing no report and
no partial results. Both times the service's own readiness endpoint reported
ready with no missing dependencies, before and after, so readiness passing is
not evidence that a run will complete.

What made the corpus an unlikely cause: no workspace anywhere on that instance
had ever completed an Early Insights report, including one that predates this
data entirely. A failure shared by a workspace that never held our documents is
not about our documents.

The useful check before blaming the data is therefore: has any workspace on this
instance ever completed one? If none has, the problem is upstream of whatever
you just imported.
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from workspace_fields import ROUTE, WORKSPACE_FIELDS, field_request  # noqa: E402

OBJECT_MODEL = "/Relativity.Rest/API/relativity-object-model/v1/workspaces/{ws}/fields/{route}"
QUERY = "/Relativity.REST/api/Relativity.Objects/workspace/{ws}/object/queryslim"


def _auth_header():
    token = os.environ.get("RELATIVITY_TOKEN")
    if token:
        return "Bearer " + token
    user, pw = os.environ.get("RELATIVITY_USER"), os.environ.get("RELATIVITY_PASSWORD")
    if user and pw:
        return "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()
    sys.exit("Set RELATIVITY_TOKEN, or RELATIVITY_USER and RELATIVITY_PASSWORD.")


def _post(base, path, payload, auth):
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "X-CSRF-Header": "-",
            "Authorization": auth,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def existing_document_fields(base, ws, auth):
    """Every Document field name in the workspace, lowercased."""
    names, start = set(), 0
    while True:
        status, body = _post(base, QUERY.format(ws=ws), {
            "request": {
                "objectType": {"artifactTypeID": 14},
                "fields": [{"name": "Name"}],
                "condition": "'Object Type' == 'Document'",
            },
            "start": start, "length": 500,
        }, auth)
        if status != 200:
            sys.exit(f"Could not read existing fields ({status}): {body[:300]}")
        page = json.loads(body)
        objects = page.get("Objects") or []
        if not objects:
            break
        names.update(o["Values"][0].lower() for o in objects)
        start += len(objects)
        if start >= page.get("TotalCount", 0):
            break
    return names


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", type=int, required=True, help="workspace artifact ID")
    ap.add_argument("--url", default=os.environ.get("RELATIVITY_URL"),
                    help="instance URL (default: $RELATIVITY_URL)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.url:
        sys.exit("Set RELATIVITY_URL or pass --url.")

    # A dry run should describe the plan without needing credentials or a
    # reachable instance, so it stays useful in CI and on a plane.
    if args.dry_run:
        auth, have = None, set()
        print(f"workspace {args.workspace}: dry run, not contacting {args.url}\n")
    else:
        auth = _auth_header()
        have = existing_document_fields(args.url, args.workspace, auth)
        print(f"workspace {args.workspace}: {len(have)} Document fields already present\n")

    created = skipped = failed = 0
    for name, ftype, length, why in WORKSPACE_FIELDS:
        if name.lower() in have:
            print(f"  = {name}  (exists)")
            skipped += 1
            continue
        if args.dry_run:
            print(f"  + {name}  [{ftype}]  {why}")
            created += 1
            continue
        status, body = _post(args.url, OBJECT_MODEL.format(ws=args.workspace, route=ROUTE[ftype]),
                             {"fieldRequest": field_request(name, ftype, length)}, auth)
        if status == 200:
            print(f"  + {name}  [{ftype}]  artifactID {body.strip()}")
            created += 1
        else:
            print(f"  ! {name}  ({status}) {body[:200]}")
            failed += 1

    verb = "would create" if args.dry_run else "created"
    print(f"\n{verb} {created}, skipped {skipped}, failed {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
