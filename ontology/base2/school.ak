# Akasha ontology — schooling: institutions, faculty, supplies, events, exams.
# Children attend kindergarten/school. Built on place:school/kindergarten,
# social:teacher_of/student_of, occupation:teacher/principal. Base pack.

def "school" "An educational institution."
def "school_stage:preschool" "before compulsory school"
def "school_stage:primary" "elementary"
def "school_stage:secondary" "middle/high"
def "school_stage:higher" "tertiary"
def "school_stage:supplementary" "cram/extra"

# ── school types → stage ──
def "school:nursery" "Nursery (保育園)."
ln school:nursery school_stage:preschool school:stage
ln school:nursery place:school thesaurus:related
def "school:kindergarten" "Kindergarten (幼稚園)."
ln school:kindergarten school_stage:preschool school:stage
ln school:kindergarten place:school thesaurus:related
def "school:elementary_school" "Elementary school (小学校)."
ln school:elementary_school school_stage:primary school:stage
ln school:elementary_school place:school thesaurus:related
def "school:junior_high_school" "Junior high school (中学校)."
ln school:junior_high_school school_stage:secondary school:stage
ln school:junior_high_school place:school thesaurus:related
def "school:high_school" "High school (高校)."
ln school:high_school school_stage:secondary school:stage
ln school:high_school place:school thesaurus:related
def "school:university" "University (大学)."
ln school:university school_stage:higher school:stage
ln school:university place:school thesaurus:related
def "school:vocational_school" "Vocational school (専門学校)."
ln school:vocational_school school_stage:higher school:stage
ln school:vocational_school place:school thesaurus:related
def "school:cram_school" "Cram school (塾)."
ln school:cram_school school_stage:supplementary school:stage
ln school:cram_school place:school thesaurus:related

# ── faculty & students ──
def "school:teacher" "Teacher — school role."
ln school:teacher place:school civic:role_at
ln school:teacher occupation:teacher thesaurus:related
ln school:teacher social:teacher_of thesaurus:related
def "school:homeroom_teacher" "Homeroom teacher (担任) — school role."
ln school:homeroom_teacher place:school civic:role_at
ln school:homeroom_teacher occupation:teacher thesaurus:related
def "school:principal" "Principal — school role."
ln school:principal place:school civic:role_at
ln school:principal occupation:principal thesaurus:related
def "school:vice_principal" "Vice principal (教頭) — school role."
ln school:vice_principal place:school civic:role_at
def "school:school_counselor" "School counselor (スクールカウンセラー) — school role."
ln school:school_counselor place:school civic:role_at
ln school:school_counselor social:mentor_of thesaurus:related
def "school:school_nurse" "School nurse (養護教諭) — school role."
ln school:school_nurse place:school civic:role_at
ln school:school_nurse social:caregiver_of thesaurus:related
def "school:school_staff" "School staff — school role."
ln school:school_staff place:school civic:role_at
def "school:janitor" "Janitor — school role."
ln school:janitor place:school civic:role_at
def "school:student" "Student — school role."
ln school:student place:school civic:role_at
ln school:student social:student_of thesaurus:related
def "school:pupil" "Pupil — school role."
ln school:pupil place:school civic:role_at
ln school:pupil social:student_of thesaurus:related

# ── school supplies ──
def "school:textbook" "Textbook (教科書)."
ln school:textbook school thesaurus:related
ln school:textbook verb:act:carry verb:acts_on
ln school:textbook obj:durable obj_durability
def "school:workbook" "Workbook."
ln school:workbook school thesaurus:related
ln school:workbook verb:act:carry verb:acts_on
ln school:workbook obj:consumable obj_durability
def "school:tablet" "Tablet (タブレット)."
ln school:tablet school thesaurus:related
ln school:tablet verb:act:carry verb:acts_on
ln school:tablet obj:durable obj_durability
def "school:randoseru" "Randoseru (ランドセル)."
ln school:randoseru school thesaurus:related
ln school:randoseru verb:act:carry verb:acts_on
ln school:randoseru obj:durable obj_durability
def "school:pencil_case" "Pencil case."
ln school:pencil_case school thesaurus:related
ln school:pencil_case verb:act:carry verb:acts_on
ln school:pencil_case obj:durable obj_durability
def "school:school_bag" "School bag."
ln school:school_bag school thesaurus:related
ln school:school_bag verb:act:carry verb:acts_on
ln school:school_bag obj:durable obj_durability
ln school:textbook stationery:notebook thesaurus:related
ln school:student school:textbook verb:act:carry
ln clothing:uniform school thesaurus:related

# ── school events ──
def "event_type:school_event" "a school ceremony or event."
def "event:entrance_ceremony" "Entrance ceremony (入学式) — start of school life."
ln event:entrance_ceremony event_type:school_event thesaurus:related
ln event:entrance_ceremony place:school civic:held_at
def "event:graduation_ceremony" "Graduation ceremony (卒業式) — end of a school stage."
ln event:graduation_ceremony event_type:school_event thesaurus:related
ln event:graduation_ceremony place:school civic:held_at
def "event:sports_day" "Sports day (運動会) — athletic meet."
ln event:sports_day event_type:school_event thesaurus:related
ln event:sports_day place:school civic:held_at
def "event:school_festival" "School festival (文化祭) — cultural festival."
ln event:school_festival event_type:school_event thesaurus:related
ln event:school_festival place:school civic:held_at
def "event:field_trip" "Field trip (遠足) — outing."
ln event:field_trip event_type:school_event thesaurus:related
ln event:field_trip place:school civic:held_at
ln event:entrance_ceremony school_stage:primary thesaurus:related
ln event:graduation_ceremony school_stage:secondary thesaurus:related

# ── exams & assessment ──
def "school:assessment" "Testing and grading of students."
def "school:exam" "Exam (試験) — a formal test."
ln school:exam school:assessment thesaurus:related
ln school:exam place:school thesaurus:related
def "school:test" "Test — a test."
ln school:test school:assessment thesaurus:related
ln school:test place:school thesaurus:related
def "school:quiz" "Quiz — a short test."
ln school:quiz school:assessment thesaurus:related
ln school:quiz place:school thesaurus:related
def "school:entrance_exam" "Entrance exam (入学試験) — admission test."
ln school:entrance_exam school:assessment thesaurus:related
ln school:entrance_exam place:school thesaurus:related
def "school:midterm_exam" "Midterm exam — mid-term."
ln school:midterm_exam school:assessment thesaurus:related
ln school:midterm_exam place:school thesaurus:related
def "school:final_exam" "Final exam — end-of-term."
ln school:final_exam school:assessment thesaurus:related
ln school:final_exam place:school thesaurus:related
def "school:report_card" "Report card (通知表) — grade report."
ln school:report_card school:assessment thesaurus:related
ln school:report_card place:school thesaurus:related
def "school:grade" "Grade — a mark."
ln school:grade school:assessment thesaurus:related
ln school:grade place:school thesaurus:related
ln school:student school:exam school:sits   # a student sits an exam
ln school:entrance_exam school thesaurus:related
