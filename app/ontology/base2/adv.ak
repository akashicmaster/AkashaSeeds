# Akasha ontology — namespace: adv
# atoms: 27

def "adv:ab_testing" "Experiment comparing variations of an advertisement."
ln adv:ab_testing advertising.performance sys:is_a
set.add name="ontology.advertising" id="adv:ab_testing"

def "adv:art_direction" "Guiding the visual style and aesthetic of an advertisement."
ln adv:art_direction advertising.creative sys:is_a
set.add name="ontology.advertising" id="adv:art_direction"

def "adv:benefit_statement" "Copy emphasizing the value or advantage of a product."
ln adv:benefit_statement advertising.copywriting sys:is_a
set.add name="ontology.advertising" id="adv:benefit_statement"

def "adv:brand_lift" "Increase in brand perception or awareness due to advertising."
ln adv:brand_lift advertising.performance sys:is_a
set.add name="ontology.advertising" id="adv:brand_lift"

def "adv:call_to_action" "Instruction prompting the audience to take a specific action."
ln adv:call_to_action advertising.copywriting sys:is_a
set.add name="ontology.advertising" id="adv:call_to_action"

def "adv:concept" "The central creative idea behind an advertisement."
ln adv:concept advertising.creative sys:is_a
ln adv:concept adv:creative_brief @supports
set.add name="ontology.advertising" id="adv:concept"

def "adv:conversion" "Completion of a desired action after exposure to an ad."
ln adv:conversion advertising.performance sys:is_a
set.add name="ontology.advertising" id="adv:conversion"

def "adv:creative_brief" "Document outlining objectives, audience, and key messages for a campaign."
ln adv:creative_brief advertising.strategy sys:is_a
set.add name="ontology.advertising" id="adv:creative_brief"

def "adv:ctr" "Click-through rate — percentage of viewers who clicked an ad."
ln adv:ctr advertising.performance sys:is_a
set.add name="ontology.advertising" id="adv:ctr"

def "adv:digital_ad" "Online advertisement delivered through digital platforms."
ln adv:digital_ad advertising.media sys:is_a
ln adv:digital_ad adv:ctr @related_to
set.add name="ontology.advertising" id="adv:digital_ad"

def "adv:emotional_appeal" "Copy designed to evoke emotional responses."
ln adv:emotional_appeal advertising.copywriting sys:is_a
ln adv:emotional_appeal adv:storytelling_copy @enhances
set.add name="ontology.advertising" id="adv:emotional_appeal"

def "adv:headline" "The primary attention-grabbing line in an advertisement."
ln adv:headline advertising.copywriting sys:is_a
ln adv:headline adv:call_to_action @supports
set.add name="ontology.advertising" id="adv:headline"

def "adv:impressions" "Number of times an advertisement is displayed."
ln adv:impressions advertising.performance sys:is_a
set.add name="ontology.advertising" id="adv:impressions"

def "adv:media_mix" "Combination of media channels used in a campaign."
ln adv:media_mix advertising.strategy sys:is_a
set.add name="ontology.advertising" id="adv:media_mix"

def "adv:native_ad" "Advertisement designed to match the form and function of the platform."
ln adv:native_ad advertising.media sys:is_a
ln adv:native_ad adv:storytelling_copy @supports
set.add name="ontology.advertising" id="adv:native_ad"

def "adv:ooh_ad" "Out-of-home advertisement such as billboards or transit ads."
ln adv:ooh_ad advertising.media sys:is_a
set.add name="ontology.advertising" id="adv:ooh_ad"

def "adv:positioning" "Crafting the intended perception of a brand or product."
ln adv:positioning advertising.strategy sys:is_a
set.add name="ontology.advertising" id="adv:positioning"

def "adv:print_ad" "Newspaper or magazine advertisement."
ln adv:print_ad advertising.media sys:is_a
set.add name="ontology.advertising" id="adv:print_ad"

def "adv:problem_solution" "Copy structure presenting a problem and offering a solution."
ln adv:problem_solution advertising.copywriting sys:is_a
set.add name="ontology.advertising" id="adv:problem_solution"

def "adv:radio_ad" "Radio or audio-based advertisement."
ln adv:radio_ad advertising.media sys:is_a
set.add name="ontology.advertising" id="adv:radio_ad"

def "adv:roas" "Return on Advertising Spend — revenue generated per unit of ad spend."
ln adv:roas advertising.performance sys:is_a
ln adv:roas adv:conversion @supports
set.add name="ontology.advertising" id="adv:roas"

def "adv:social_ad" "Advertisement delivered through social media platforms."
ln adv:social_ad advertising.media sys:is_a
set.add name="ontology.advertising" id="adv:social_ad"

def "adv:storyboard" "Visual sequence outlining the structure of an advertisement."
ln adv:storyboard advertising.creative sys:is_a
set.add name="ontology.advertising" id="adv:storyboard"

def "adv:storytelling_copy" "Narrative-driven copy that engages and persuades."
ln adv:storytelling_copy advertising.copywriting sys:is_a
set.add name="ontology.advertising" id="adv:storytelling_copy"

def "adv:targeting" "Selecting specific audience segments for advertising."
ln adv:targeting advertising.strategy sys:is_a
set.add name="ontology.advertising" id="adv:targeting"

def "adv:tv_ad" "Television advertisement."
ln adv:tv_ad advertising.media sys:is_a
set.add name="ontology.advertising" id="adv:tv_ad"

def "adv:visual_design" "Creation of imagery, layout, and graphic elements."
ln adv:visual_design advertising.creative sys:is_a
set.add name="ontology.advertising" id="adv:visual_design"
