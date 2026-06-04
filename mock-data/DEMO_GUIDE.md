# Demo Guide — Walking Through the MDL 2804 Dataset

This guide is for anyone presenting the mock dataset in a Relativity demo, UX walkthrough,
or feature review. It explains the story, the key documents to surface, and how to frame
the narrative for an audience.

---

## The case in one paragraph

The National Prescription Opiate Litigation (MDL 2804) was a massive federal multi-district
litigation consolidating thousands of cases against opioid manufacturers, distributors, and
consultants. Three defendants are represented in this dataset: **Mallinckrodt** (manufactured
generic oxycodone and failed to report suspicious orders to the DEA), **Insys Therapeutics**
(bribed doctors through a fraudulent speaker bureau and defrauded insurers — CEO convicted under
RICO), and **McKinsey & Co** (consulted on opioid sales maximization strategies — settled for
$600M). The workspace represents a single law firm's review of documents produced across all
three defendants into the same MDL.

---

## The four acts

Use the `Narrative Phase` field to filter documents by act. Each act has a distinct character:

| Phase | Filter | Character |
|-------|--------|-----------|
| **1 — Growth** (2010–2012) | `Narrative Phase = 1` | Routine business. Sales reports, McKinsey strategy decks, speaker bureau KOL recruitment. Most docs are non-responsive. |
| **2 — Pressure** (2013–2014) | `Narrative Phase = 2` | Where the conduct happens. SOM override memos, Cardinal Health anomaly alerts, speaker payment approvals, IRC call scripts. 40% responsive. |
| **3 — Crisis** (2015–2016) | `Narrative Phase = 3` | Everything unravels. Legal hold notices, whistleblower emails, SOM deletion logs, AG subpoenas. 55% responsive. |
| **4 — Litigation** (2017–2018) | `Narrative Phase = 4` | Settlement and production. MDL discovery orders, privilege logs, clawback notices. High privilege rate. |

---

## The 13 hot documents — your demo anchors

Filter `Hot Doc = Yes` and `Control Number LIKE 'HOT-%'` to get the scripted story documents.
These are the most impactful documents to surface in a demo.

| Control # | What it is | Why it matters |
|-----------|-----------|----------------|
| `HOT-0000001` | SOM Override Memo | The email explicitly authorizing release of a flagged suspicious order. The word "override" in the subject is what every state AG searched for. |
| `HOT-0000002` | McKinsey Turbocharge Deck | The PowerPoint that became the centerpiece of McKinsey's $600M settlement. "Growth Acceleration Strategy v3.2" — the title alone tells the story. |
| `HOT-0000003` | DEA Meeting Forward | Mallinckrodt received a letter from the DEA noting SOM deficiencies — and continued shipping. This forward establishes they knew. |
| `HOT-0000004` | Speaker Payment Approval | Dr. Alan Foster's Q3 2013 payment approval. Foster was later indicted. |
| `HOT-0000005` | IRC Call Guide v4 | The script telling Insys agents how to misrepresent patient diagnoses to get prior authorizations. Exhibit in the RICO trial. |
| `HOT-0000006` | Whistleblower Email | The compliance officer forwarded a tip to outside counsel instead of HR — establishing company knowledge. Privileged. |
| `HOT-0000007` | Legal Hold Notice | Issued 2015-09-14. SOM records were deleted 8 days later. |
| `HOT-0000008` | SOM Deletion Log | `SOM_Flag_Archive_Cleanup_September2015.xlsx` — dated 9/22/2015. The spoliation document. |
| `HOT-0000009` | AG Subpoena Draft | Redline edits in this draft altered facts from an earlier version. Version comparison revealed strategic omissions. |
| `HOT-0000010` | RICO Indictment Response | Harrington's internal email on the day of the RICO indictment. Privileged. |
| `HOT-0000011` | McKinsey Settlement Memo | McKinsey's internal discussion of their $600M exposure. Work product. |
| `HOT-0000012` | Cardinal Health Alert | The escalation email from Sandra Nguyen that triggered the SOM override chain. |
| `HOT-0000013` | Quota Spreadsheet | FY2013 incentive compensation tied directly to oxycodone volume with no compliance carve-outs. |

---

## The 5 email threads — showing the decision chain

Filter by `Email Thread ID LIKE 'STHR-%'` to pull the scripted threads. These show how
decisions were made inside each organization.

| Thread | What it shows |
|--------|--------------|
| `STHR-0001` | The SOM override decision chain — Nguyen escalates → Ashton consults → Ashton approves (HOT-0000001). 3 emails. |
| `STHR-0002` | McKinsey engagement — Whitfield hires McKinsey → Tevelow delivers the turbocharge deck (HOT-0000002). 3 emails. |
| `STHR-0003` | Insys speaker bureau — Harrington launches → Rosen processes payments → Harrington approves Foster (HOT-0000004). 3 emails. |
| `STHR-0004` | Whistleblower and hold — Bradley escalates tip (HOT-0000006) → legal hold issued (HOT-0000007). 2 emails. |
| `STHR-0005` | DEA response strategy — Kowalski forwards DEA letter (HOT-0000003) → Whitfield directs outside counsel → Bradley objects. 3 emails. |

---

## Demo flow: a suggested walkthrough

### 1 — Set the scene (2 min)
Open the workspace. Show the document count and the `Custodian Org` breakdown. Point out that
this is a real litigation — three real companies, real events, 2010–2018.

### 2 — Show the shape of the matter (2 min)
Filter by `Narrative Phase` and show the document count per phase. Show the responsiveness
rate climbing from Phase 1 to Phase 3. This is where you demonstrate analytics features —
TAR score distribution, phase-based culling, ECA exclusions.

### 3 — Find the crime (3 min)
Filter to `Issue Tags CONTAINS 'SOM Override'`. Show that these documents cluster in Phase 2
and Phase 3. Pull up `HOT-0000012` (the Cardinal Health alert) → `STHR-0001` thread →
`HOT-0000001` (the override memo). This is the decision chain.

### 4 — Show the cover-up (2 min)
Filter to `Issue Tags CONTAINS 'Legal Hold'`. Show `HOT-0000007` (hold issued 9/14/2015) next
to `HOT-0000008` (SOM deletion log dated 9/22/2015). Eight days apart. This is where you
demonstrate date filtering and near-duplicate detection.

### 5 — Show privilege (2 min)
Filter to `Privilege = Privileged`. Show that privilege spikes in Phase 3 and Phase 4 —
that's when outside counsel got involved. Pull up `HOT-0000006` (whistleblower — privileged)
and `HOT-0000009` (AG subpoena draft — work product).

### 6 — Show production (1 min)
Filter to `Bates Begin IS NOT EMPTY`. Show the org-specific prefixes: MNK, INSYS, MCK.
Show a redacted document. Demonstrate the production log.

---

## Filtering cheat sheet

```python
import pandas as pd
docs = pd.read_csv("mock-data/small/documents.csv")

# By phase
phase2 = docs[docs["Narrative Phase"] == 2]

# By org
insys  = docs[docs["Custodian Org"] == "Insys"]

# Hot documents (all)
hot    = docs[docs["Hot Doc"] == "Yes"]

# Scripted hot documents specifically
scripted_hot = docs[docs["Control Number"].str.startswith("HOT-")]

# Scripted email threads
threads = docs[docs["Email Thread ID"].str.startswith("STHR-", na=False)]

# Responsive, unprivileged, produced
produced = docs[(docs["Responsiveness"] == "Responsive") &
                (docs["Privilege"] != "Privileged") &
                (docs["Bates Begin"] != "")]

# SOM Override issue cluster
som = docs[docs["Issue Tags"].str.contains("SOM Override", na=False)]

# Phase 3 — the crisis
crisis = docs[docs["Narrative Phase Name"] == "Crisis"]

# High TAR score docs
high_tar = docs[pd.to_numeric(docs["TAR Score"], errors="coerce") > 75]

# The legal hold and the deletion — 8 days apart
hold_date = docs[docs["Control Number"] == "HOT-0000007"]["Primary Date"].iloc[0]
deletion  = docs[docs["Control Number"] == "HOT-0000008"]
```

---

## Key people at a glance

| Name | Org | Role in the story |
|------|-----|-------------------|
| James Whitfield | Mallinckrodt | CEO — ultimate SOM override authority |
| Robert Ashton | Mallinckrodt | VP Sales — approved the Cardinal Health override |
| Thomas Bradley | Mallinckrodt | CCO — raised concerns, issued legal hold, forwarded whistleblower tip |
| Sandra Nguyen | Mallinckrodt | Regional Director — sent the original anomaly alert |
| Gregory Nash | Mallinckrodt | SOM Director — wrote override justification memos; authored deletion log |
| Dr. Alec Harrington | Insys | VP Sales — speaker bureau architect; RICO defendant |
| Natalie Rosen | Insys | Reimbursement Mgr — ran the prior auth fraud calls |
| Bradley Tevelow | McKinsey | Engagement Manager — delivered the turbocharge deck; Outstanding hold |
| Richard Galveston | Outside Counsel | Litigation partner — DEA response, AG subpoena, settlement |
