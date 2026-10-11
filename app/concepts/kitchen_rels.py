"""The three canonical product·component·method relations (application-side constants).

The law is the application's: `app/ontology/kitchen_index/canon.json` declares it and
`app/scripts/gen_canonical.py` writes it into each pack at build time. The kitchen concept models
(meal / drink / producer) only READ these relations, so they name them here — nothing is imported
from the platform.
"""
MADE_FROM = "sys:made_from"     # product → component
METHOD_OF = "sys:method_of"     # method  → product
MADE_BY = "sys:made_by"         # product → producer
