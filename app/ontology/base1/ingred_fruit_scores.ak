# Akasha ontology — fruit sensory scores
# Numeric sweetness, acidity, and color attributes for the 5 base-pack fruits.
# These rec: links enable lens.scan to discover and project these attributes
# into a rec table or quadrant scatter plot without any manual data entry.
# atoms: 14  (10 numeric + 4 color text atoms)

# ── Shared numeric value atoms ────────────────────────────────────────────────
def "score:0.05"  "0.05"
def "score:0.08"  "0.08"
def "score:0.25"  "0.25"
def "score:0.38"  "0.38"
def "score:0.52"  "0.52"
def "score:0.68"  "0.68"
def "score:0.78"  "0.78"
def "score:0.85"  "0.85"
def "score:0.90"  "0.90"
def "score:0.95"  "0.95"

# ── Shared color text atoms ───────────────────────────────────────────────────
def "score:color:red"    "red"
def "score:color:yellow" "yellow"
def "score:color:orange" "orange"
def "score:color:green"  "green"

# ── Apple  (sweet, low-acid, red) ────────────────────────────────────────────
ln ingred:fruit:apple score:0.85        rec:sweetness
ln ingred:fruit:apple score:0.25        rec:acidity
ln ingred:fruit:apple score:color:red   rec:color

# ── Banana  (very sweet, very low-acid, yellow) ──────────────────────────────
ln ingred:fruit:banana score:0.90        rec:sweetness
ln ingred:fruit:banana score:0.08        rec:acidity
ln ingred:fruit:banana score:color:yellow rec:color

# ── Orange  (moderately sweet, medium-acid, orange) ──────────────────────────
ln ingred:fruit:orange score:0.68        rec:sweetness
ln ingred:fruit:orange score:0.52        rec:acidity
ln ingred:fruit:orange score:color:orange rec:color

# ── Lemon  (barely sweet, very high-acid, yellow) ────────────────────────────
ln ingred:fruit:lemon score:0.05        rec:sweetness
ln ingred:fruit:lemon score:0.95        rec:acidity
ln ingred:fruit:lemon score:color:yellow rec:color

# ── Grape  (moderately sweet, medium-low-acid, green) ────────────────────────
ln ingred:fruit:grape score:0.78        rec:sweetness
ln ingred:fruit:grape score:0.38        rec:acidity
ln ingred:fruit:grape score:color:green  rec:color
