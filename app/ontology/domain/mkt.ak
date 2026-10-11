# Akasha ontology — namespace: mkt
# atoms: 29

def "mkt:advertising" "Paid promotion to influence awareness or behavior."
ln mkt:advertising marketing.communication sys:is_a
set.add name="ontology.marketing" id="mkt:advertising"

def "mkt:analytics" "Measurement and analysis of marketing performance."
ln mkt:analytics marketing.digital sys:is_a
set.add name="ontology.marketing" id="mkt:analytics"

def "mkt:brand_strategy" "Long-term plan for building and managing brand perception."
ln mkt:brand_strategy marketing.strategy sys:is_a
set.add name="ontology.marketing" id="mkt:brand_strategy"

def "mkt:cac" "Customer Acquisition Cost — cost to acquire one customer."
ln mkt:cac marketing.metrics sys:is_a
set.add name="ontology.marketing" id="mkt:cac"

def "mkt:churn" "Percentage of customers who stop using a product."
ln mkt:churn marketing.metrics sys:is_a
ln mkt:churn mkt:retention @contrasts_with
set.add name="ontology.marketing" id="mkt:churn"

def "mkt:content_marketing" "Creating valuable content to attract and engage audiences."
ln mkt:content_marketing marketing.communication sys:is_a
set.add name="ontology.marketing" id="mkt:content_marketing"

def "mkt:conversion" "Turning prospects into customers through desired actions."
ln mkt:conversion marketing.digital sys:is_a
ln mkt:conversion mkt:marketing_funnel @related_to
set.add name="ontology.marketing" id="mkt:conversion"

def "mkt:customer_journey" "End-to-end experience a customer has with a product or brand."
ln mkt:customer_journey marketing.research sys:is_a
set.add name="ontology.marketing" id="mkt:customer_journey"

def "mkt:engagement" "Level of user activity and involvement."
ln mkt:engagement marketing.metrics sys:is_a
set.add name="ontology.marketing" id="mkt:engagement"

def "mkt:feature_strategy" "Deciding which features to build and prioritize."
ln mkt:feature_strategy marketing.product sys:is_a
set.add name="ontology.marketing" id="mkt:feature_strategy"

def "mkt:ltv" "Lifetime Value — total value a customer generates over time."
ln mkt:ltv marketing.metrics sys:is_a
ln mkt:ltv mkt:retention @related_to
set.add name="ontology.marketing" id="mkt:ltv"

def "mkt:marketing_funnel" "Stages from awareness to conversion."
ln mkt:marketing_funnel marketing.digital sys:is_a
set.add name="ontology.marketing" id="mkt:marketing_funnel"

def "mkt:messaging" "Core messages that communicate value to the audience."
ln mkt:messaging marketing.communication sys:is_a
ln mkt:messaging mkt:storytelling @related_to
set.add name="ontology.marketing" id="mkt:messaging"

def "mkt:packaging" "Design and presentation of a product's physical or digital container."
ln mkt:packaging marketing.product sys:is_a
set.add name="ontology.marketing" id="mkt:packaging"

def "mkt:persona" "Archetypal representation of a customer segment."
ln mkt:persona marketing.research sys:is_a
ln mkt:persona mkt:customer_journey @supports
set.add name="ontology.marketing" id="mkt:persona"

def "mkt:positioning" "Crafting the desired perception of a product in the customer's mind."
ln mkt:positioning marketing.strategy sys:is_a
ln mkt:positioning mkt:brand_strategy @supports
set.add name="ontology.marketing" id="mkt:positioning"

def "mkt:pricing" "Setting the value exchange for a product or service."
ln mkt:pricing marketing.product sys:is_a
set.add name="ontology.marketing" id="mkt:pricing"

def "mkt:product_market_fit" "Degree to which a product satisfies strong market demand."
ln mkt:product_market_fit marketing.product sys:is_a
ln mkt:product_market_fit mkt:value_proposition @supports
set.add name="ontology.marketing" id="mkt:product_market_fit"

def "mkt:public_relations" "Managing relationships with media and the public."
ln mkt:public_relations marketing.communication sys:is_a
set.add name="ontology.marketing" id="mkt:public_relations"

def "mkt:qualitative_research" "Research focused on understanding motivations and behaviors."
ln mkt:qualitative_research marketing.research sys:is_a
set.add name="ontology.marketing" id="mkt:qualitative_research"

def "mkt:quantitative_research" "Research using numerical data to validate hypotheses."
ln mkt:quantitative_research marketing.research sys:is_a
set.add name="ontology.marketing" id="mkt:quantitative_research"

def "mkt:retention" "Percentage of customers who continue using a product."
ln mkt:retention marketing.metrics sys:is_a
set.add name="ontology.marketing" id="mkt:retention"

def "mkt:segmentation" "Dividing a market into distinct groups with shared characteristics."
ln mkt:segmentation marketing.strategy sys:is_a
set.add name="ontology.marketing" id="mkt:segmentation"

def "mkt:sem" "Search Engine Marketing — paid search advertising."
ln mkt:sem marketing.digital sys:is_a
set.add name="ontology.marketing" id="mkt:sem"

def "mkt:seo" "Search Engine Optimization — improving organic visibility."
ln mkt:seo marketing.digital sys:is_a
ln mkt:seo mkt:marketing_funnel @supports
set.add name="ontology.marketing" id="mkt:seo"

def "mkt:storytelling" "Using narrative techniques to communicate brand meaning."
ln mkt:storytelling marketing.communication sys:is_a
set.add name="ontology.marketing" id="mkt:storytelling"

def "mkt:stp" "Segmentation, Targeting, Positioning — core marketing strategy model."
ln mkt:stp marketing.strategy sys:is_a
ln mkt:stp mkt:segmentation @supports
set.add name="ontology.marketing" id="mkt:stp"

def "mkt:targeting" "Selecting the most attractive segments to serve."
ln mkt:targeting marketing.strategy sys:is_a
set.add name="ontology.marketing" id="mkt:targeting"

def "mkt:value_proposition" "Statement of the unique value a product delivers to customers."
ln mkt:value_proposition marketing.strategy sys:is_a
set.add name="ontology.marketing" id="mkt:value_proposition"
