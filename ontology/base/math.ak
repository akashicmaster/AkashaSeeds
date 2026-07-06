# Akasha ontology — namespace: math
# atoms: 4

def "math:concept:algorithm" "A finite sequence of rigorous instructions, typically used to solve a class of specific problems or to perform a computation."

def "math:concept:hindu_arabic_numerals" "The set of 10 symbols (0-9) that represent numbers in the decimal number system, originating in India."
ln math:concept:hindu_arabic_numerals sci:history:house_of_wisdom @adopted_by
ln math:concept:hindu_arabic_numerals sci:history:liber_abaci @popularized_by

def "math:concept:zero" "A numerical digit used to represent that number in numerals, and plays a central role in mathematics as the additive identity of the integers."
ln math:concept:zero math:concept:hindu_arabic_numerals @foundational_for

def "math:discipline:algebra" "The study of mathematical symbols and the rules for manipulating these symbols; a unifying thread of almost all of mathematics."
ln math:discipline:algebra sci:history:translation_movement @transmitted_via
ln math:discipline:algebra math:concept:algorithm @utilizes
ln math:discipline:algebra astro:law:keplers_first_law @enables
