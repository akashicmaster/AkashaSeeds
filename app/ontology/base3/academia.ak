# Akasha ontology — academia I: career, institutions, methodology, teaching, admin.
# Researchers/scholars are a core Akasha audience. Built on occupation:researcher/
# professor, school:university, person:field:*, work:, social:mentor_of/student_of,
# status:. Base pack.

def "academia" "The world of research and scholarship."
# ── academic career ladder ──
def "acad:outranks" "Senior academic position to."
def "acad:emeritus_professor" "Emeritus professor — academic position."
ln acad:emeritus_professor academia thesaurus:related
ln acad:emeritus_professor acad:professor acad:outranks
def "acad:professor" "Professor (教授) — academic position."
ln acad:professor academia thesaurus:related
ln acad:professor acad:associate_professor acad:outranks
def "acad:associate_professor" "Associate professor (准教授) — academic position."
ln acad:associate_professor academia thesaurus:related
ln acad:associate_professor acad:assistant_professor acad:outranks
def "acad:assistant_professor" "Assistant professor (助教) — academic position."
ln acad:assistant_professor academia thesaurus:related
ln acad:assistant_professor acad:lecturer acad:outranks
def "acad:lecturer" "Lecturer (講師) — academic position."
ln acad:lecturer academia thesaurus:related
ln acad:lecturer acad:postdoc acad:outranks
def "acad:postdoc" "Postdoc (ポスドク) — academic position."
ln acad:postdoc academia thesaurus:related
ln acad:postdoc acad:phd_candidate acad:outranks
def "acad:phd_candidate" "Phd candidate (博士課程) — academic position."
ln acad:phd_candidate academia thesaurus:related
ln acad:phd_candidate acad:graduate_student acad:outranks
def "acad:graduate_student" "Graduate student (大学院生) — academic position."
ln acad:graduate_student academia thesaurus:related
ln acad:graduate_student acad:undergraduate acad:outranks
def "acad:undergraduate" "Undergraduate — academic position."
ln acad:undergraduate academia thesaurus:related
ln acad:professor occupation:professor thesaurus:related
ln acad:postdoc occupation:researcher thesaurus:related
ln acad:graduate_student social:student_of thesaurus:related
ln acad:outranks status:outranks thesaurus:related
def "acad:principal_investigator" "Principal investigator (研究代表者(PI)) — academic role."
ln acad:principal_investigator academia thesaurus:related
ln acad:principal_investigator occupation:researcher thesaurus:related
def "acad:advisor" "Advisor (指導教員) — academic role."
ln acad:advisor academia thesaurus:related
ln acad:advisor social:mentor_of thesaurus:related
def "acad:dean" "Dean (学部長) — academic role."
ln acad:dean academia thesaurus:related
def "acad:department_chair" "Department chair — academic role."
ln acad:department_chair academia thesaurus:related
def "acad:research_assistant" "Research assistant — academic role."
ln acad:research_assistant academia thesaurus:related
ln acad:research_assistant occupation:researcher thesaurus:related
def "acad:supervisor" "Supervisor — academic role."
ln acad:supervisor academia thesaurus:related
ln acad:supervisor social:mentor_of thesaurus:related

# ── academic institutions ──
def "place:research_institute" "Research institute (研究所) — academic place."
ln place:research_institute place_type:education civic:function
def "place:laboratory" "Laboratory (研究室) — academic place."
ln place:laboratory place_type:education civic:function
def "place:graduate_school" "Graduate school (大学院) — academic place."
ln place:graduate_school place_type:education civic:function
def "place:faculty" "Faculty — academic place."
ln place:faculty place_type:education civic:function
def "place:academic_department" "Academic department — academic place."
ln place:academic_department place_type:education civic:function
def "place:campus" "Campus — academic place."
ln place:campus place_type:education civic:function
def "place:think_tank" "Think tank — academic place."
ln place:think_tank place_type:civic civic:function
ln place:laboratory school:university thesaurus:related
ln place:graduate_school school:university thesaurus:related

# ── research methodology ──
def "research" "The systematic pursuit of knowledge."
# process
def "research:research_question" "Research question (研究課題)."
ln research:research_question research thesaurus:related
ln research:research_question research:literature_review chrono:before
def "research:literature_review" "Literature review (文献レビュー)."
ln research:literature_review research thesaurus:related
ln research:literature_review research:hypothesis chrono:before
def "research:hypothesis" "Hypothesis (仮説)."
ln research:hypothesis research thesaurus:related
ln research:hypothesis research:methodology chrono:before
def "research:methodology" "Methodology (方法論)."
ln research:methodology research thesaurus:related
ln research:methodology research:data_collection chrono:before
def "research:data_collection" "Data collection."
ln research:data_collection research thesaurus:related
ln research:data_collection research:analysis chrono:before
def "research:analysis" "Analysis."
ln research:analysis research thesaurus:related
ln research:analysis research:findings chrono:before
def "research:findings" "Findings."
ln research:findings research thesaurus:related
ln research:findings research:conclusion chrono:before
def "research:conclusion" "Conclusion."
ln research:conclusion research thesaurus:related
# method types & concepts
def "research:method:qualitative" "Qualitative research."
ln research:method:qualitative research:methodology thesaurus:related
def "research:method:quantitative" "Quantitative research."
ln research:method:quantitative research:methodology thesaurus:related
def "research:method:experimental" "Experimental research."
ln research:method:experimental research:methodology thesaurus:related
def "research:method:theoretical" "Theoretical research."
ln research:method:theoretical research:methodology thesaurus:related
def "research:method:empirical" "Empirical research."
ln research:method:empirical research:methodology thesaurus:related
def "research:method:computational" "Computational research."
ln research:method:computational research:methodology thesaurus:related
def "research:method:observational" "Observational research."
ln research:method:observational research:methodology thesaurus:related
def "research:method:mixed_methods" "Mixed methods research."
ln research:method:mixed_methods research:methodology thesaurus:related
def "research:experiment" "Experiment (実験) — a controlled test."
ln research:experiment research thesaurus:related
def "research:observation" "Observation — systematic watching."
ln research:observation research thesaurus:related
def "research:survey" "Survey — structured questioning."
ln research:survey research thesaurus:related
def "research:fieldwork" "Fieldwork (フィールドワーク) — 研究のための現地調査."
ln research:fieldwork research thesaurus:related
def "research:sampling" "Sampling — selecting a subset."
ln research:sampling research thesaurus:related
def "research:variable" "Variable — a measured factor."
ln research:variable research thesaurus:related
def "research:control_group" "Control group — baseline comparison group."
ln research:control_group research thesaurus:related
def "research:reproducibility" "Reproducibility (再現性) — 再現性 — repeatable results."
ln research:reproducibility research thesaurus:related
def "research:validity" "Validity — soundness of inference."
ln research:validity research thesaurus:related
def "research:reliability" "Reliability — consistency of measure."
ln research:reliability research thesaurus:related
def "research:research_ethics" "Research ethics — ethical conduct of research."
ln research:research_ethics research thesaurus:related
def "research:dataset" "Dataset — a body of data."
ln research:dataset research thesaurus:related
def "research:model" "Model — a formal representation."
ln research:model research thesaurus:related
def "research:theory" "Theory — an explanatory framework."
ln research:theory research thesaurus:related
def "research:evidence" "Evidence — supporting data."
ln research:evidence research thesaurus:related
def "research:induction" "帰納 — building concepts up from observations."
def "research:deduction" "演繹 — deriving instances from a defined concept."
ln research:induction research thesaurus:related
ln research:deduction research thesaurus:related
ln research:induction research:deduction sys:antonym

# ── teaching & lectures ──
def "teaching:lecture" "Lecture (講義)."
ln teaching:lecture academia thesaurus:related
ln teaching:lecture social:teacher_of thesaurus:related
def "teaching:seminar" "Seminar (ゼミ)."
ln teaching:seminar academia thesaurus:related
ln teaching:seminar social:teacher_of thesaurus:related
def "teaching:tutorial" "Tutorial."
ln teaching:tutorial academia thesaurus:related
ln teaching:tutorial social:teacher_of thesaurus:related
def "teaching:course" "Course."
ln teaching:course academia thesaurus:related
ln teaching:course social:teacher_of thesaurus:related
def "teaching:syllabus" "Syllabus (シラバス)."
ln teaching:syllabus academia thesaurus:related
ln teaching:syllabus social:teacher_of thesaurus:related
def "teaching:curriculum" "Curriculum."
ln teaching:curriculum academia thesaurus:related
ln teaching:curriculum social:teacher_of thesaurus:related
def "teaching:lecture_notes" "Lecture notes."
ln teaching:lecture_notes academia thesaurus:related
ln teaching:lecture_notes social:teacher_of thesaurus:related
def "teaching:grading" "Grading."
ln teaching:grading academia thesaurus:related
ln teaching:grading social:teacher_of thesaurus:related
def "teaching:office_hours" "Office hours (オフィスアワー)."
ln teaching:office_hours academia thesaurus:related
ln teaching:office_hours social:teacher_of thesaurus:related
def "teaching:thesis_supervision" "Thesis supervision (論文指導)."
ln teaching:thesis_supervision academia thesaurus:related
ln teaching:thesis_supervision social:teacher_of thesaurus:related
def "teaching:teaching_assistant" "Teaching assistant."
ln teaching:teaching_assistant academia thesaurus:related
ln teaching:teaching_assistant social:teacher_of thesaurus:related
def "teaching:assignment" "Assignment."
ln teaching:assignment academia thesaurus:related
ln teaching:assignment social:teacher_of thesaurus:related
ln teaching:lecture place:university thesaurus:related
ln teaching:thesis_supervision acad:advisor thesaurus:related

# ── research administration & grants ──
def "acad_admin:research_grant" "Research grant (研究助成) — 研究助成金."
ln acad_admin:research_grant academia thesaurus:related
def "acad_admin:funding_agency" "Funding agency — a body that funds research."
ln acad_admin:funding_agency academia thesaurus:related
def "acad_admin:grant_application" "Grant application (申請) — 申請書."
ln acad_admin:grant_application academia thesaurus:related
def "acad_admin:research_proposal" "Research proposal (研究計画) — 研究計画書."
ln acad_admin:research_proposal academia thesaurus:related
def "acad_admin:research_budget" "Research budget — grant budget."
ln acad_admin:research_budget academia thesaurus:related
def "acad_admin:scholarship" "Scholarship — student funding."
ln acad_admin:scholarship academia thesaurus:related
def "acad_admin:fellowship" "Fellowship — research funding."
ln acad_admin:fellowship academia thesaurus:related
def "acad_admin:tenure" "Tenure (テニュア) — permanent academic post."
ln acad_admin:tenure academia thesaurus:related
def "acad_admin:tenure_track" "Tenure track — path to tenure."
ln acad_admin:tenure_track academia thesaurus:related
def "acad_admin:sabbatical" "Sabbatical (サバティカル) — 研究休暇."
ln acad_admin:sabbatical academia thesaurus:related
def "acad_admin:ethics_approval" "Ethics approval (倫理審査) — 倫理審査承認."
ln acad_admin:ethics_approval academia thesaurus:related
def "acad_admin:academic_cv" "Academic cv — academic curriculum vitae."
ln acad_admin:academic_cv academia thesaurus:related
def "acad_admin:publication_record" "Publication record — list of one's papers."
ln acad_admin:publication_record academia thesaurus:related
def "acad_admin:research_report" "Research report — a report to a funder."
ln acad_admin:research_report academia thesaurus:related
ln acad_admin:research_grant work thesaurus:related
ln acad_admin:grant_application acad_admin:research_grant thesaurus:related
ln acad_admin:tenure status thesaurus:related
