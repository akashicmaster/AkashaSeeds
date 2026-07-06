# Akasha ontology — namespace: tech
# atoms: 19

def "tech:aviation:airplane" "A powered, fixed-wing aircraft propelled forward by thrust from a jet engine, propeller, or rocket engine."
ln tech:aviation:airplane phys:aero:lift @generates
ln tech:aviation:airplane phys:aero:thrust @requires
ln tech:aviation:airplane tech:aviation:internal_combustion_engine @utilizes

def "tech:aviation:glider" "A heavier-than-air aircraft supported in flight by aerodynamic lift, whose free flight does not depend on an engine."
ln tech:aviation:glider tech:aviation:airplane @precedes

def "tech:aviation:hot_air_balloon" "A lighter-than-air aircraft consisting of a bag (envelope) that contains heated air."
ln tech:aviation:hot_air_balloon tech:aviation:glider @precedes

def "tech:aviation:internal_combustion_engine" "A heat engine in which the combustion of a fuel occurs with an oxidizer in a combustion chamber."

def "tech:aviation:jet_engine" "A reaction engine discharging a fast-moving jet that generates thrust by jet propulsion."
ln tech:aviation:jet_engine phys:law:newtons_third_law @utilizes
ln tech:aviation:jet_engine phys:aero:thrust @generates_efficiently
ln tech:aviation:jet_engine sci:history:jet_age @triggers
ln tech:aviation:jet_engine mat:class:metal @relies_on_advanced

def "tech:concept:gunpowder" "The earliest known chemical explosive, consisting of a mixture of sulfur, charcoal, and potassium nitrate."
ln tech:concept:gunpowder tech:weapon:fire_lance @utilized_in
ln tech:concept:gunpowder tech:weapon:cannon @enables
ln tech:concept:gunpowder tech:weapon:matchlock @enables

def "tech:concept:incandescent_light_bulb" "An electric light with a wire filament heated until it glows, revolutionizing indoor illumination and extending the workday."
ln tech:concept:incandescent_light_bulb sci:history:electrification @drives_demand_for

def "tech:concept:movable_type" "The system and technology of printing and typography that uses movable components (letters/characters) to reproduce a document."
ln tech:concept:movable_type tech:material:paper @requires
ln tech:concept:movable_type tech:concept:printing_press @influences_conceptually

def "tech:concept:power_grid" "An interconnected network for delivering electricity from producers to consumers."
ln tech:concept:power_grid sci:history:electrification @enables

def "tech:concept:printing_press" "A mechanical device for applying pressure to an inked surface resting upon a print medium (such as paper or cloth), thereby transferring the ink."
ln tech:concept:printing_press tech:concept:movable_type @mechanizes
ln tech:concept:printing_press mat:class:metal @utilizes
ln tech:concept:printing_press sci:history:printing_revolution @triggers

def "tech:concept:woodblock_printing" "A technique for printing text, images or patterns used widely throughout East Asia and originating in China as a method of printing on textiles and later paper."
ln tech:concept:woodblock_printing tech:material:paper @requires
ln tech:concept:woodblock_printing tech:concept:printing_press @precedes

def "tech:material:paper" "A thin sheet material produced by mechanically or chemically processing cellulose fibres, originating in ancient China."
ln tech:material:paper tech:concept:printing_press @enables

def "tech:power:alternating_current" "An electric current which periodically reverses direction and changes its magnitude continuously with time (championed by Tesla/Westinghouse)."
ln tech:power:alternating_current tech:concept:power_grid @enables_long_distance

def "tech:power:battery" "A device consisting of one or more electrochemical cells with external connections for powering electrical devices (e.g., Voltaic pile)."
ln tech:power:battery phys:em:electric_current @provides_continuous

def "tech:power:direct_current" "The unidirectional flow or movement of electric charge carriers (championed by Edison)."
ln tech:power:direct_current tech:concept:power_grid @limits_distance

def "tech:power:electrical_generator" "A machine that converts motive power (mechanical energy) into electrical power for use in an external circuit."
ln tech:power:electrical_generator phys:energy:kinetic_energy @consumes
ln tech:power:electrical_generator phys:em:electric_current @produces
ln tech:power:electrical_generator phys:law:faradays_law @utilizes

def "tech:weapon:cannon" "A type of large, tubular firearm that uses gunpowder to launch a projectile over long distances, revolutionizing siege warfare."
ln tech:weapon:cannon sci:history:military_revolution @triggers

def "tech:weapon:fire_lance" "A very early gunpowder weapon originating in 10th-century China, consisting of a tube filled with gunpowder attached to the end of a spear."

def "tech:weapon:matchlock" "An early type of firearm, introduced to Japan by the Portuguese in 1543, which drastically changed the nature of warfare in the Sengoku period."
ln tech:weapon:matchlock mat:class:metal @utilizes
