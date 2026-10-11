# Akasha ontology — kinship ROLES by defining axes (built on kin.ak relations).
# The kin: relations (parent_of/child_of/…) and the WordNet kinship words
# (mother/father/…) already exist; what was missing is the axes that DISTINGUISH
# the roles. Tag each role by gender × generation × line (lineal/collateral/
# affinal) and its precise relation, so 'mother vs father' = gender, 'mother vs
# grandmother' = generation, 'mother vs aunt' = lineal vs collateral all fall
# out of the graph. Also adds the precise relations the crude bridges lacked.
# Base pack.

def "kin:gender" "Gender axis of a kinship role."
def "kin:gender:male" "male-gendered role (father, son, uncle…)"
ln kin:gender:male kin:gender thesaurus:related
def "kin:gender:female" "female-gendered role (mother, daughter, aunt…)"
ln kin:gender:female kin:gender thesaurus:related
def "kin:gender:neutral" "gender-neutral role (parent, child, cousin…)"
ln kin:gender:neutral kin:gender thesaurus:related
def "kin:generation" "Generational offset from ego."
def "kin:gen:g2" "+2 — grandparent generation"
ln kin:gen:g2 kin:generation thesaurus:related
def "kin:gen:g1" "+1 — parent generation"
ln kin:gen:g1 kin:generation thesaurus:related
def "kin:gen:g0" "0 — ego / sibling / spouse generation"
ln kin:gen:g0 kin:generation thesaurus:related
def "kin:gen:gm1" "-1 — child generation"
ln kin:gen:gm1 kin:generation thesaurus:related
def "kin:gen:gm2" "-2 — grandchild generation"
ln kin:gen:gm2 kin:generation thesaurus:related
def "kin:line" "Line of descent: lineal (direct), collateral (side), affinal (by marriage)."
def "kin:line:lineal" "direct line — ancestors and descendants"
ln kin:line:lineal kin:line thesaurus:related
def "kin:line:collateral" "side line — siblings, aunts/uncles, cousins, niblings"
ln kin:line:collateral kin:line thesaurus:related
def "kin:line:affinal" "related by marriage"
ln kin:line:affinal kin:line thesaurus:related

def "kin:grandparent_of" "The relation of being a parent of someone's parent."
ln kin:grandparent_of kin:grandchild_of sys:antonym
ln kin:grandparent_of kin:ancestor_of thesaurus:related
def "kin:grandchild_of" "The relation of being a child of someone's child."
ln kin:grandchild_of kin:grandparent_of sys:antonym
ln kin:grandchild_of kin:descendant_of thesaurus:related
def "kin:auncle_of" "Aunt-or-uncle relation — a sibling of one's parent."
ln kin:auncle_of kin:nibling_of sys:antonym
ln kin:auncle_of kin:sibling_of thesaurus:related
def "kin:nibling_of" "Niece-or-nephew relation — a child of one's sibling."
ln kin:nibling_of kin:auncle_of sys:antonym
def "kin:cousin_of" "Collateral relative of the same generation (parent's sibling's child)."
ln kin:cousin_of kin:cousin_of sys:synonym   # symmetric
def "lineage:begat" "Bloodline relation parent→child (the family-tree axis; cf. lineage_demo)."
ln lineage:begat kin:parent_of thesaurus:related

# ── kinship roles tagged by axis + precise relation ──
ln mother kin:gender:female kin:gender
ln mother kin:gen:g1 kin:generation
ln mother kin:line:lineal kin:line
ln mother kin:parent_of kin:role_of
ln father kin:gender:male kin:gender
ln father kin:gen:g1 kin:generation
ln father kin:line:lineal kin:line
ln father kin:parent_of kin:role_of
ln parent kin:gender:neutral kin:gender
ln parent kin:gen:g1 kin:generation
ln parent kin:line:lineal kin:line
ln parent kin:parent_of kin:role_of
ln son kin:gender:male kin:gender
ln son kin:gen:gm1 kin:generation
ln son kin:line:lineal kin:line
ln son kin:child_of kin:role_of
ln daughter kin:gender:female kin:gender
ln daughter kin:gen:gm1 kin:generation
ln daughter kin:line:lineal kin:line
ln daughter kin:child_of kin:role_of
ln child kin:gender:neutral kin:gender
ln child kin:gen:gm1 kin:generation
ln child kin:line:lineal kin:line
ln child kin:child_of kin:role_of
ln brother kin:gender:male kin:gender
ln brother kin:gen:g0 kin:generation
ln brother kin:line:collateral kin:line
ln brother kin:sibling_of kin:role_of
ln sister kin:gender:female kin:gender
ln sister kin:gen:g0 kin:generation
ln sister kin:line:collateral kin:line
ln sister kin:sibling_of kin:role_of
ln sibling kin:gender:neutral kin:gender
ln sibling kin:gen:g0 kin:generation
ln sibling kin:line:collateral kin:line
ln sibling kin:sibling_of kin:role_of
ln grandmother kin:gender:female kin:gender
ln grandmother kin:gen:g2 kin:generation
ln grandmother kin:line:lineal kin:line
ln grandmother kin:grandparent_of kin:role_of
ln grandfather kin:gender:male kin:gender
ln grandfather kin:gen:g2 kin:generation
ln grandfather kin:line:lineal kin:line
ln grandfather kin:grandparent_of kin:role_of
ln grandson kin:gender:male kin:gender
ln grandson kin:gen:gm2 kin:generation
ln grandson kin:line:lineal kin:line
ln grandson kin:grandchild_of kin:role_of
ln granddaughter kin:gender:female kin:gender
ln granddaughter kin:gen:gm2 kin:generation
ln granddaughter kin:line:lineal kin:line
ln granddaughter kin:grandchild_of kin:role_of
ln grandchild kin:gender:neutral kin:gender
ln grandchild kin:gen:gm2 kin:generation
ln grandchild kin:line:lineal kin:line
ln grandchild kin:grandchild_of kin:role_of
ln uncle kin:gender:male kin:gender
ln uncle kin:gen:g1 kin:generation
ln uncle kin:line:collateral kin:line
ln uncle kin:auncle_of kin:role_of
ln aunt kin:gender:female kin:gender
ln aunt kin:gen:g1 kin:generation
ln aunt kin:line:collateral kin:line
ln aunt kin:auncle_of kin:role_of
ln nephew kin:gender:male kin:gender
ln nephew kin:gen:gm1 kin:generation
ln nephew kin:line:collateral kin:line
ln nephew kin:nibling_of kin:role_of
ln niece kin:gender:female kin:gender
ln niece kin:gen:gm1 kin:generation
ln niece kin:line:collateral kin:line
ln niece kin:nibling_of kin:role_of
ln cousin kin:gender:neutral kin:gender
ln cousin kin:gen:g0 kin:generation
ln cousin kin:line:collateral kin:line
ln cousin kin:cousin_of kin:role_of
ln husband kin:gender:male kin:gender
ln husband kin:gen:g0 kin:generation
ln husband kin:line:affinal kin:line
ln husband kin:partner_of kin:role_of
ln wife kin:gender:female kin:gender
ln wife kin:gen:g0 kin:generation
ln wife kin:line:affinal kin:line
ln wife kin:partner_of kin:role_of
ln spouse kin:gender:neutral kin:gender
ln spouse kin:gen:g0 kin:generation
ln spouse kin:line:affinal kin:line
ln spouse kin:partner_of kin:role_of
