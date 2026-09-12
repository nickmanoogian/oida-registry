"""The Document fields a stock Relativity workspace does not have.

A default workspace template carries 472 Document fields, and 34 of the load
file's 59 columns auto-map to one by exact name. The other 25 do not, and only
one of those is a naming problem: ExtractedTextFilePath, which is handled by the
import profile because the "Text File" setting cannot be expressed in a column
name at all.

The remaining 24 are not junk columns and should not be deleted from the load
file. They carry the parts of this corpus a stock template has nowhere to put:
Rule 21's data source dimension, which Collection Coverage is measured against;
the RSMF chat layer, whose 40,882 messages reach the workspace through these
columns and no other route, because the package ships no .rsmf natives for
processing to read; and the scripted review state DEMO_GUIDE walks through.

Relativity's Import/Export ignores an unmatched column, so shipping them costs
bytes and nothing else. Create these fields once per workspace and all 24 land.

Every type here was derived by measuring the extra large tier, not guessed:
cardinality decided choice-vs-text, and the longest observed value set each
length. See `scripts/create_workspace_fields.py` to apply them.
"""

# FieldType values are Relativity's own, as returned by
# GET /Relativity.Rest/API/relativity-object-model/v1/workspaces/{id}/fields/{id}
FIXED_LENGTH    = "FixedLength"
LONG_TEXT       = "LongText"
SINGLE_CHOICE   = "SingleChoice"
MULTIPLE_CHOICE = "MultipleChoice"
WHOLE_NUMBER    = "WholeNumber"
DECIMAL         = "Decimal"
YES_NO          = "YesNo"

# name, type, length (FixedLength only), why it exists.
# "distinct" is the value count measured on the extra large tier, 275,273 rows.
WORKSPACE_FIELDS = [
    ("Data Source",           SINGLE_CHOICE,   0,   "Rule 21. 10 sources. Collection Coverage is measured against this."),
    ("Custodian Org",         SINGLE_CHOICE,   0,   "4 orgs. The defendant split Key Relationships groups by."),
    ("Custodian Email",       FIXED_LENGTH,    100, "40 addresses, one per custodian. Joins custodians to entities."),
    ("Conversation Topic",    FIXED_LENGTH,    255, "905 thread subjects. The readable half of email threading."),
    ("Page Count",            WHOLE_NUMBER,    0,   "30 distinct. Document length without opening the native."),

    ("Workflow Stage",        SINGLE_CHOICE,   0,   "6 stages, from ECA: Excluded through Review: Reviewed."),
    ("Privileged",            YES_NO,          0,   "The flag. The reason it asserts goes to the stock Privilege field."),
    ("Hot Doc",               YES_NO,          0,   "The scripted hot documents."),
    ("Redacted",              YES_NO,          0,   "Redaction state."),
    ("Production Set",        SINGLE_CHOICE,   0,   "6 volumes, VOL001 to VOL006."),
    ("TAR Score",             DECIMAL,         0,   "Relevance score on the 24.7% sent to review."),
    ("AL Predicted Relevant", YES_NO,          0,   "Active learning prediction."),
    # Not "Batch Name"/"Batch Status": the latter is reserved, because Relativity's
    # Batch application already owns Batch, Batch::Status and Batch::Assigned To,
    # and the create is refused with "the field name you've entered is either
    # reserved by the system". These simulate review batching rather than being
    # that application, so both take the Review prefix and stay a matched pair.
    ("Review Batch Name",     FIXED_LENGTH,    50,  "97 review batches."),
    ("Review Batch Status",   SINGLE_CHOICE,   0,   "Not Started / In Progress / Completed."),
    ("Reviewer",              SINGLE_CHOICE,   0,   "19 reviewers. Makes review workload pivotable."),
    ("Narrative Phase",       WHOLE_NUMBER,    0,   "1 to 4. The phase ordering."),
    ("Narrative Phase Name",  SINGLE_CHOICE,   0,   "Growth / Pressure / Crisis / Litigation."),
    ("Dedup Method",          SINGLE_CHOICE,   0,   "MD5 / SHA256 / EventCollectionId / N/A."),
    ("OCR Flag",              YES_NO,          0,   "Whether text came from OCR."),

    # No stock field carries any of this. There is no RSMF, short message or chat
    # field in the template, and no .rsmf native ships for processing to parse,
    # so these three columns are the only route for the chat layer.
    ("Rsmf Application",      SINGLE_CHOICE,   0,   "Teams / Slack / SMS / Google Chat / WhatsApp."),
    ("Rsmf Participants",     MULTIPLE_CHOICE, 0,   "40 participants, semicolon-delimited like Issues."),
    ("Rsmf Message Count",    WHOLE_NUMBER,    0,   "Messages inside each RSMF document."),

    ("Processing Status",     SINGLE_CHOICE,   0,   "Complete / Error."),
    ("Processing Error Type", SINGLE_CHOICE,   0,   "8 error types. The Rule 6 documents that fail on purpose."),
]

# Load file columns that map to a stock field only after this module's fields
# exist. Kept as a set so the README generator and the validator agree.
NEEDS_FIELD_CREATED = {name for name, _t, _l, _why in WORKSPACE_FIELDS}


ROUTE = {
    FIXED_LENGTH:    "fixed-length",
    LONG_TEXT:       "long-text",
    SINGLE_CHOICE:   "single-choice",
    MULTIPLE_CHOICE: "multiple-choice",
    WHOLE_NUMBER:    "whole-number",
    DECIMAL:         "decimal",
    YES_NO:          "yes-no",
}


def field_request(name, field_type, length=0):
    """The body Relativity's object model expects to create one Document field.

    POST /Relativity.Rest/API/relativity-object-model/v1/workspaces/{ws}/fields/{ROUTE[type]}
    with {"fieldRequest": <this>}.

    The per-type keys below are copied from real fields in a stock workspace
    (Issues for multiple choice, Responsive for single, Email Has Attachments for
    Yes/No, Author for fixed length), read back off the same API. AutoAddChoices
    is what lets the import create the choice values instead of erroring on one
    it has never seen, which is how Issues already behaves.
    """
    req = {
        "Name": name,
        # Document, and it has to be nested under "Value". A bare
        # {"ArtifactTypeID": 10}, or an ArtifactID, is rejected with "the object
        # type property is required", which reads like the key is missing rather
        # than wrongly shaped. Found by probing, not guessed.
        "ObjectType": {"Value": {"ArtifactTypeID": 10}},
        "IsRequired": False,
        "OpenToAssociations": False,
        "AvailableInFieldTree": True,
        "AllowSortTally": True,
        "Wrapping": True,
    }

    if field_type in (SINGLE_CHOICE, MULTIPLE_CHOICE):
        req.update({
            "HasUnicode": True,
            "AutoAddChoices": True,
            "AllowGroupBy": True,
            "AllowPivot": True,
            "OverlayBehavior": "ReplaceValues",
            "FilterType": "MultiList" if field_type == MULTIPLE_CHOICE else "List",
        })
    elif field_type == YES_NO:
        req.update({
            "DisplayValueTrue": "Yes",
            "DisplayValueFalse": "No",
            "AllowGroupBy": True,
            "AllowPivot": True,
            "FilterType": "Boolean",
        })
    elif field_type in (WHOLE_NUMBER, DECIMAL):
        req.update({"AllowGroupBy": False, "AllowPivot": False, "FilterType": "TextBox"})
    elif field_type == FIXED_LENGTH:
        req.update({
            "Length": length or 255,
            "HasUnicode": True,
            "IncludeInTextIndex": False,
            "AllowGroupBy": False,
            "AllowPivot": False,
            "FilterType": "TextBox",
        })
    elif field_type == LONG_TEXT:
        req.update({
            "HasUnicode": True,
            "IncludeInTextIndex": False,
            "AllowHtml": False,
            "EnableDataGrid": False,
            "FilterType": "TextBox",
        })
    return req
