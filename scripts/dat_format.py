#!/usr/bin/env python3
"""
dat_format.py — The Concordance delimiters, declared once

These three characters lived in four scripts (`build_load_package`,
`build_real_load_package`, `build_broken_load_files`, `validate_load_package`).
They agreed with each other, which is why nothing caught that all four were
*wrong*: the column separator and the text qualifier were one character off from
the Concordance standard, so every `.dat` this repo produced needed a delimiter
combination no other tool uses.

It surfaced the only way it could, in Relativity's own import: the load file was
read as a single 59-field-wide column, because ASCII 254 is the qualifier
everywhere else and the importer was looking for ASCII 20 between fields.

The standard, which is what these are now:

    Column separator  ASCII 20   the field delimiter
    Text qualifier    ASCII 254  wraps each value
    Newline in field  ASCII 174  stands in for a newline inside a value

Stdlib-only and dependency-free on purpose, the same reason `tier_files.py` is,
so the validator can import it without pulling in the native-writing libraries.
"""

DAT_FIELD_SEP = chr(20)    # the column delimiter
DAT_QUOTE     = chr(254)   # þ, the text qualifier
DAT_NEWLINE   = chr(174)   # ®, a newline inside a field value

# What to tell a human in an import README.
DELIMITER_NOTE = (f"Column separator: ASCII {ord(DAT_FIELD_SEP)}\n"
                  f"    Text qualifier:   {DAT_QUOTE} (ASCII {ord(DAT_QUOTE)})\n"
                  f"    Newline in field: {DAT_NEWLINE} (ASCII {ord(DAT_NEWLINE)})")
