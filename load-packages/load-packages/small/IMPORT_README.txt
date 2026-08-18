RELATIVITY IMPORT INSTRUCTIONS
====================================

This package contains:
  natives/         — native files (.eml, .docx, .xlsx, .pptx, .pdf, .rsmf)
  load-file.dat    — Relativity Concordance load file (metadata + native paths)
  load-file.opt    — image load file placeholder (native-only import)

STEP 1 — Copy the package to your Relativity file server
  Place this entire folder on the server at a path Relativity can access.
  Example: \\fileserver\LoadFiles\MDL2804-small\

STEP 2 — Create a Relativity Processing Set (OR use Import)
  Option A (Processing): Use Relativity Processing to create workspace fields
    that match the columns in load-file.dat (see field list below).
  Option B (Import): Use the Relativity Import module:
    Workspace → Import → Relativity Load File → select load-file.dat

STEP 3 — Field mapping
  The .dat file uses Concordance delimiters:
    Column separator: þ (ASCII 254)
    Text qualifier:   ÿ (ASCII 255)
    Newline in field: ® (ASCII 174)

  Map these .dat columns to Relativity fields:
    BegDoc#              → Control Number
    Custodian            → Custodian
    Custodian Org        → Custodian Org (custom text field)
    Responsive           → Responsiveness (single choice)
    Privileged           → Privilege (single choice)
    Hot Doc              → Hot Doc (yes/no)
    Issue Tags           → Issue Tags (multi-choice or long text)
    Narrative Phase      → Narrative Phase (number)
    Narrative Phase Name → Narrative Phase Name (text)
    TAR Score            → TAR Score (decimal)
    NativeFilePath       → (mapped to native file upload)

STEP 4 — Set the native file path base
  When prompted for the native file path, set the base path to the
  location of this package on the file server. The NativeFilePath
  column contains relative paths like: natives\DOC-0000001.eml

VERIFYING THE IMPORT
  After import, run this search in Relativity to find the scripted hot docs:
    Control Number StartsWith "HOT-"

  These 8–13 documents are the key evidentiary moments in the MDL 2804 story.
  See mock-data/DEMO_GUIDE.md for a full walkthrough.

QUESTIONS
  See CONTRIBUTING.md or open a GitHub issue at:
  https://github.com/nickmanoogian/oioda-registry
