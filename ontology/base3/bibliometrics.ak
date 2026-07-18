# Akasha ontology — bibliometrics & research evaluation.
# Metrics over the citation/coauthor graphs (cite:*/collab:*), plus the
# assessment frameworks and their critiques. Base pack.

def "bib" "Bibliometrics / research evaluation."
# ── author & article metrics ──
def "bib:h_index" "H index (h指数) — productivity+impact index."
ln bib:h_index bib thesaurus:related
def "bib:g_index" "G index — weights highly-cited papers."
ln bib:g_index bib thesaurus:related
def "bib:i10_index" "I10 index — papers with ≥10 citations."
ln bib:i10_index bib thesaurus:related
def "bib:citation_count" "Citation count (被引用数) — total citations received."
ln bib:citation_count bib thesaurus:related
def "bib:citation_percentile" "Citation percentile (被引用パーセンタイル) — rank among peers."
ln bib:citation_percentile bib thesaurus:related
def "bib:field_weighted_citation_impact" "Field weighted citation impact (分野正規化被引用インパクト) — citations vs field average."
ln bib:field_weighted_citation_impact bib thesaurus:related
def "bib:times_cited" "Times cited — count of citing works."
ln bib:times_cited bib thesaurus:related
# ── journal & venue metrics ──
def "bib:impact_factor" "Impact factor (インパクトファクター) — mean citations per article."
ln bib:impact_factor bib thesaurus:related
def "bib:eigenfactor" "Eigenfactor — influence-weighted citations."
ln bib:eigenfactor bib thesaurus:related
def "bib:sjr" "Sjr — SCImago Journal Rank."
ln bib:sjr bib thesaurus:related
def "bib:snip" "Snip — source-normalized impact."
ln bib:snip bib thesaurus:related
def "bib:cite_score" "Cite score — Scopus citation metric."
ln bib:cite_score bib thesaurus:related
def "bib:journal_ranking" "Journal ranking (雑誌ランキング) — ranking of journals."
ln bib:journal_ranking bib thesaurus:related
def "bib:quartile" "Quartile — journal quartile (Q1–Q4)."
ln bib:quartile bib thesaurus:related
# ── altmetrics ──
def "bib:altmetrics" "Altmetrics (オルトメトリクス) — attention beyond citations."
def "bib:alt:downloads" "Downloads as an attention signal."
ln bib:alt:downloads bib:altmetrics sys:part_of
def "bib:alt:views" "Views as an attention signal."
ln bib:alt:views bib:altmetrics sys:part_of
def "bib:alt:social_mentions" "Social mentions as an attention signal."
ln bib:alt:social_mentions bib:altmetrics sys:part_of
def "bib:alt:news_mentions" "News mentions as an attention signal."
ln bib:alt:news_mentions bib:altmetrics sys:part_of
def "bib:alt:saves" "Saves as an attention signal."
ln bib:alt:saves bib:altmetrics sys:part_of
# ── methods & science mapping ──
def "bib:bibliometrics" "Bibliometrics — quantitative study of publications."
ln bib:bibliometrics bib thesaurus:related
def "bib:scientometrics" "Scientometrics — metrics of science."
ln bib:scientometrics bib thesaurus:related
def "bib:informetrics" "Informetrics — metrics of information."
ln bib:informetrics bib thesaurus:related
def "bib:citation_analysis" "Citation analysis — analysing citation patterns."
ln bib:citation_analysis bib thesaurus:related
def "bib:co_citation_analysis" "Co citation analysis — clustering by shared citation."
ln bib:co_citation_analysis bib thesaurus:related
def "bib:science_mapping" "Science mapping — mapping a field's structure."
ln bib:science_mapping bib thesaurus:related
def "bib:research_front" "Research front — the active edge of a field."
ln bib:research_front bib thesaurus:related
def "bib:benchmarking" "Benchmarking — comparing against peers."
ln bib:benchmarking bib thesaurus:related
# ── assessment frameworks & critique ──
def "bib:research_assessment" "Research assessment (研究評価) — evaluating research quality."
ln bib:research_assessment bib thesaurus:related
def "bib:university_ranking" "University ranking (大学ランキング) — ranking of universities."
ln bib:university_ranking bib thesaurus:related
def "bib:peer_review" "Peer review — expert judgement of quality."
ln bib:peer_review bib thesaurus:related
def "bib:societal_impact" "Societal impact — impact beyond academia."
ln bib:societal_impact bib thesaurus:related
def "bib:responsible_metrics" "Responsible metrics (責任ある指標) — metrics used responsibly."
ln bib:responsible_metrics bib thesaurus:related
def "bib:dora" "Dora — San Francisco Declaration on Research Assessment."
ln bib:dora bib thesaurus:related
def "bib:leiden_manifesto" "Leiden manifesto — principles for metrics use."
ln bib:leiden_manifesto bib thesaurus:related
def "bib:goodharts_law" "Goodharts law — when a measure becomes a target it fails."
ln bib:goodharts_law bib thesaurus:related
# ── bridges to the graphs & careers ──
ln bib:h_index pub:metric:h_index thesaurus:related
ln bib:impact_factor pub:metric:impact_factor thesaurus:related
ln bib:citation_count cite:citation_count thesaurus:related
ln bib:citation_analysis cite:citation_analysis thesaurus:related
ln bib:co_citation_analysis cite:co_citation thesaurus:related
ln bib:science_mapping cite:citation_network thesaurus:related
ln bib:peer_review research:peer_review thesaurus:related
ln bib:research_assessment work:performance_review thesaurus:related
ln bib:research_assessment acad_admin:tenure thesaurus:related
ln bib:altmetrics collab:coauthorship_network thesaurus:related
ln bib:responsible_metrics bib:dora thesaurus:related
