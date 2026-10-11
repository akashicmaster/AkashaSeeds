# Akasha ontology — namespace: mystic
# atoms: 16

def "mystic:concept:astrology" "A range of divinatory practices that claim to discern information about human affairs and terrestrial events by studying the movements and relative positions of celestial objects."
ln mystic:concept:astrology astro:body:celestial_body @observes
ln mystic:concept:astrology astro:theory:geocentrism @historically_relies_on

def "mystic:concept:horoscope" "An astrological chart representing the positions of the Sun, Moon, and planets at the time of an event, such as the moment of a person's birth."

def "mystic:concept:macrocosm_microcosm" "An ancient philosophical worldview seeing a structural similarity and correspondence between the universe (macrocosm) and the human body (microcosm)."
ln mystic:concept:macrocosm_microcosm mystic:concept:astrology @underpins
ln mystic:concept:macrocosm_microcosm sci:history:alchemy @underpins
ln mystic:concept:macrocosm_microcosm sci:history:humorism @underpins

def "mystic:concept:zodiac" "A belt of the heavens within about 8 degrees either side of the ecliptic, divided into twelve equal divisions or signs."

def "mystic:sign:aquarius" "The Water-Bearer (Jan 20 - Feb 18)."
ln mystic:sign:aquarius mystic:concept:zodiac sys:is_a
ln mystic:sign:aquarius astro:constellation:aquarius @namesake_of

def "mystic:sign:aries" "The Ram (Mar 21 - Apr 19)."
ln mystic:sign:aries mystic:concept:zodiac sys:is_a
ln mystic:sign:aries astro:constellation:aries @namesake_of

def "mystic:sign:cancer" "The Crab (Jun 21 - Jul 22)."
ln mystic:sign:cancer mystic:concept:zodiac sys:is_a
ln mystic:sign:cancer astro:constellation:cancer @namesake_of

def "mystic:sign:capricorn" "The Sea-Goat (Dec 22 - Jan 19)."
ln mystic:sign:capricorn mystic:concept:zodiac sys:is_a
ln mystic:sign:capricorn astro:constellation:capricornus @namesake_of

def "mystic:sign:gemini" "The Twins (May 21 - Jun 20)."
ln mystic:sign:gemini mystic:concept:zodiac sys:is_a
ln mystic:sign:gemini astro:constellation:gemini @namesake_of

def "mystic:sign:leo" "The Lion (Jul 23 - Aug 22)."
ln mystic:sign:leo mystic:concept:zodiac sys:is_a
ln mystic:sign:leo astro:constellation:leo @namesake_of

def "mystic:sign:libra" "The Scales (Sep 23 - Oct 22)."
ln mystic:sign:libra mystic:concept:zodiac sys:is_a
ln mystic:sign:libra astro:constellation:libra @namesake_of

def "mystic:sign:pisces" "The Fishes (Feb 19 - Mar 20)."
ln mystic:sign:pisces mystic:concept:zodiac sys:is_a
ln mystic:sign:pisces astro:constellation:pisces @namesake_of

def "mystic:sign:sagittarius" "The Archer (Nov 22 - Dec 21)."
ln mystic:sign:sagittarius mystic:concept:zodiac sys:is_a
ln mystic:sign:sagittarius astro:constellation:sagittarius @namesake_of

def "mystic:sign:scorpio" "The Scorpion (Oct 23 - Nov 21)."
ln mystic:sign:scorpio mystic:concept:zodiac sys:is_a
ln mystic:sign:scorpio astro:constellation:scorpius @namesake_of

def "mystic:sign:taurus" "The Bull (Apr 20 - May 20)."
ln mystic:sign:taurus mystic:concept:zodiac sys:is_a
ln mystic:sign:taurus astro:constellation:taurus @namesake_of

def "mystic:sign:virgo" "The Maiden (Aug 23 - Sep 22)."
ln mystic:sign:virgo mystic:concept:zodiac sys:is_a
ln mystic:sign:virgo astro:constellation:virgo @namesake_of
