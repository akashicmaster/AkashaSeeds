# Akasha ontology — work: the human experience of working.
# org:* has the management theory and biz:* the abstract terms, but how a
# PERSON works — the workplace, the day, pay, career moves, relationships and
# how it feels — was missing. Built on social: (boss/colleague), occupation:,
# status: (rank ladder), org: (theory), place:. Base pack.

def "work" "The activity and experience of holding a job."
# ── workplace ──
def "place_type:workplace" "workplaces"
ln place_type:workplace place_type thesaurus:related
def "place:office" "Office (オフィス) — オフィス — white-collar workplace."
ln place:office place_type:workplace civic:function
def "place:factory" "Factory (工場) — 工場 — manufacturing workplace."
ln place:factory place_type:workplace civic:function
def "place:workplace" "Workplace — A place of work (generic)."
ln place:workplace place_type:workplace civic:function
def "place:home_office" "Home office (在宅勤務) — 在宅勤務 — working from home."
ln place:home_office place_type:workplace civic:function
def "place:coworking_space" "Coworking space — Shared work space."
ln place:coworking_space place_type:workplace civic:function
ln place:home_office home:study thesaurus:related

# ── org units ──
def "work:department" "Department (部署)."
ln work:department work thesaurus:related
ln work:department social:member_of work:belong_via
ln work:department biz:team thesaurus:related
def "work:team" "Team."
ln work:team work thesaurus:related
ln work:team social:member_of work:belong_via
ln work:team biz:team thesaurus:related
def "work:division" "Division."
ln work:division work thesaurus:related
ln work:division social:member_of work:belong_via
def "work:project" "Project."
ln work:project work thesaurus:related
ln work:project social:member_of work:belong_via
def "work:section" "Section."
ln work:section work thesaurus:related
ln work:section social:member_of work:belong_via

# ── employment terms ──
def "work:employment_type" "The basis of employment."
def "work:employ:full_time" "Full time employment."
ln work:employ:full_time work:employment_type thesaurus:related
def "work:employ:part_time" "Part time employment."
ln work:employ:part_time work:employment_type thesaurus:related
def "work:employ:contract" "Contract employment."
ln work:employ:contract work:employment_type thesaurus:related
def "work:employ:temp" "Temp employment."
ln work:employ:temp work:employment_type thesaurus:related
def "work:employ:dispatch" "Dispatch employment."
ln work:employ:dispatch work:employment_type thesaurus:related
def "work:employ:freelance" "Freelance employment."
ln work:employ:freelance work:employment_type thesaurus:related
def "work:salary" "Salary (給料) — monthly pay."
ln work:salary work thesaurus:related
def "work:wage" "Wage — hourly pay."
ln work:wage work thesaurus:related
def "work:bonus" "Bonus (ボーナス) — periodic bonus."
ln work:bonus work thesaurus:related
def "work:payday" "Payday (給料日) — pay date."
ln work:payday work thesaurus:related
def "work:paycheck" "Paycheck (給与明細) — pay statement."
ln work:paycheck work thesaurus:related
def "work:working_hours" "Working hours — hours worked."
ln work:working_hours work thesaurus:related
def "work:overtime" "Overtime (残業) — work beyond hours."
ln work:overtime work thesaurus:related
def "work:paid_leave" "Paid leave (有給休暇) — paid time off."
ln work:paid_leave work thesaurus:related
def "work:sick_leave" "Sick leave — leave for illness."
ln work:sick_leave work thesaurus:related
def "work:commute_allowance" "Commute allowance — travel subsidy."
ln work:commute_allowance work thesaurus:related
def "work:minimum_wage" "Minimum wage — legal pay floor."
ln work:minimum_wage work thesaurus:related
ln work:overtime work:working_hours thesaurus:related
ln work:salary occupation thesaurus:related
ln work:minimum_wage gov:function:taxation gov:regulated_by

# ── daily work events ──
def "work:commute" "Commute (通勤)."
ln work:commute work thesaurus:related
ln work:commute emo:anticipation calc:associated_with
def "work:meeting" "Meeting (会議)."
ln work:meeting work thesaurus:related
ln work:meeting emo:anticipation calc:associated_with
ln work:meeting emo:interest calc:associated_with
def "work:presentation" "Presentation."
ln work:presentation work thesaurus:related
ln work:presentation emo:anxiety calc:associated_with
ln work:presentation emo:anticipation calc:associated_with
def "work:task" "Task."
ln work:task work thesaurus:related
def "work:deadline" "Deadline."
ln work:deadline work thesaurus:related
ln work:deadline emo:anxiety calc:associated_with
def "work:business_trip" "Business trip (出張)."
ln work:business_trip work thesaurus:related
ln work:business_trip emo:anticipation calc:associated_with
def "work:overtime" "Overtime (残業)."
ln work:overtime work thesaurus:related
ln work:overtime emo:anxiety calc:associated_with
def "work:lunch_break" "Lunch break."
ln work:lunch_break work thesaurus:related
ln work:lunch_break emo:satisfaction calc:associated_with
def "work:morning_assembly" "Morning assembly (朝礼)."
ln work:morning_assembly work thesaurus:related
def "work:report" "Report."
ln work:report work thesaurus:related
def "work:nomikai" "Nomikai (飲み会)."
ln work:nomikai work thesaurus:related
ln work:nomikai emo:joy calc:associated_with
ln work:nomikai emo:trust calc:associated_with
def "work:telework" "Telework (在宅勤務)."
ln work:telework work thesaurus:related
ln work:telework emo:satisfaction calc:associated_with
ln work:meeting biz:meeting thesaurus:related
ln work:deadline biz:deadline thesaurus:related
ln work:telework teb:telework thesaurus:related
ln work:meeting social:colleague_of thesaurus:related
ln work:nomikai social:colleague_of thesaurus:related
ln work:commute transport thesaurus:related

# ── career events ──
def "work:hiring" "Hiring (採用)."
ln work:hiring work thesaurus:related
def "work:promotion" "Promotion (昇進)."
ln work:promotion work thesaurus:related
ln work:promotion emo:satisfaction calc:associated_with
ln work:promotion emo:admiration calc:associated_with
def "work:demotion" "Demotion."
ln work:demotion work thesaurus:related
ln work:demotion emo:anxiety calc:associated_with
def "work:transfer" "Transfer (異動)."
ln work:transfer work thesaurus:related
ln work:transfer emo:anticipation calc:associated_with
ln work:transfer emo:anxiety calc:associated_with
def "work:performance_review" "Performance review (人事評価)."
ln work:performance_review work thesaurus:related
ln work:performance_review emo:anxiety calc:associated_with
ln work:performance_review emo:anticipation calc:associated_with
def "work:raise" "Raise (昇給)."
ln work:raise work thesaurus:related
ln work:raise emo:satisfaction calc:associated_with
def "work:resignation" "Resignation (退職)."
ln work:resignation work thesaurus:related
ln work:resignation emo:anticipation calc:associated_with
def "work:retirement" "Retirement (定年)."
ln work:retirement work thesaurus:related
ln work:retirement emo:nostalgia calc:associated_with
ln work:retirement emo:satisfaction calc:associated_with
def "work:layoff" "Layoff (リストラ)."
ln work:layoff work thesaurus:related
ln work:layoff emo:anxiety calc:associated_with
def "work:job_change" "Job change (転職)."
ln work:job_change work thesaurus:related
ln work:job_change emo:anticipation calc:associated_with
ln work:job_change emo:anxiety calc:associated_with
# promotions climb the status ladder; reviews decide rank
ln work:promotion status:outranks thesaurus:related
ln work:promotion status thesaurus:related
ln work:performance_review status thesaurus:related
ln work:performance_review org:role_clarity thesaurus:related
ln work:hiring org:onboarding thesaurus:related
ln work:retirement gov:benefit:pension thesaurus:related

# ── work experience & wellbeing ──
def "work:workload" "Workload."
ln work:workload work thesaurus:related
ln work:workload emo:anxiety calc:associated_with
def "work:deadline_pressure" "Deadline pressure."
ln work:deadline_pressure work thesaurus:related
ln work:deadline_pressure emo:anxiety calc:associated_with
def "work:job_satisfaction" "Job satisfaction (仕事の満足)."
ln work:job_satisfaction work thesaurus:related
ln work:job_satisfaction emo:satisfaction calc:associated_with
ln work:job_satisfaction emo:joy calc:associated_with
ln work:job_satisfaction org:engagement thesaurus:related
def "work:work_stress" "Work stress (仕事のストレス)."
ln work:work_stress work thesaurus:related
ln work:work_stress emo:anxiety calc:associated_with
ln work:work_stress org:burnout thesaurus:related
def "work:work_life_balance" "Work life balance (ワークライフバランス)."
ln work:work_life_balance work thesaurus:related
ln work:work_life_balance emo:satisfaction calc:associated_with
ln work:work_life_balance org:autonomy thesaurus:related
def "work:teamwork" "Teamwork."
ln work:teamwork work thesaurus:related
ln work:teamwork emo:trust calc:associated_with
ln work:teamwork org:collaboration thesaurus:related
def "work:overwork" "Overwork (過労)."
ln work:overwork work thesaurus:related
ln work:overwork emo:anxiety calc:associated_with
ln work:overwork org:burnout thesaurus:related
def "work:power_harassment" "Power harassment (パワハラ)."
ln work:power_harassment work thesaurus:related
ln work:power_harassment emo:anger calc:associated_with
ln work:power_harassment emo:anxiety calc:associated_with
ln work:power_harassment org:psychological_safety thesaurus:related
def "work:job_security" "Job security."
ln work:job_security work thesaurus:related
ln work:job_security emo:trust calc:associated_with
def "work:motivation" "Motivation."
ln work:motivation work thesaurus:related
ln work:motivation emo:anticipation calc:associated_with
ln work:motivation org:intrinsic_motivation thesaurus:related
ln work:power_harassment social:boss_of thesaurus:related
ln work:teamwork social:colleague_of thesaurus:related
ln work:overwork work:overtime thesaurus:related
