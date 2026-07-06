"""
Akasha DNA Sequence
Encodes innate primal logic, spatiotemporal axes, fuzzy logic operations, 
and both primary & compound emotion dimensions.

[MULTIDIMENSIONAL SCOPE INTEGRATION]
During Cortex initialization, these sequences are automatically extracted 
and anchored permanently into the `scope:sys:universal` space. They serve 
as the absolute baseline ontology for all users and cognitive processes.

[FUTURE ROADMAP: MULTIPLE PERSPECTIVE FRAMES]
Designed to be easily expanded with alternative cognitive lenses (e.g., 
Dialectics, Cybernetics, Eastern Dependent Origination) to allow the AI 
to analyze graphs from completely different philosophical viewpoints.
"""

def get_primal_sequence() -> dict:
    """
    Returns the foundational cognitive framework of the system.
    This dict represents the state of the brain immediately after 'birth'.
    """
    
    dna = {}

    # --- 1. System & Topology (The Architecture of Space) ---
    topology = {
        "sys:is_a": "Class/Subclass hierarchy relation. (e.g., Dog is_a Animal)",
        "sys:part_of": "Meronymic system-component relation. (e.g., Engine part_of Car)",
        "sys:associated_with": "Broad associative semantic link.",
        "sys:mapped_to": "Forward topological mapping (transform).",
        "sys:mapped_from": "Inverse topological mapping (transform).",
        "sys:requires": "Dependency relation. (e.g., Fire requires Oxygen)",
        "sys:causes": "Causality relation. (e.g., Rain causes Wetness)"
    }
    dna.update(topology)

    # --- 2. Fuzzy Formal Logic (The Engine of Reason) ---
    logic = {
        "log:not": "Fuzzy Negation (NOT P). Expresses the probability of mutual exclusivity.",
        "log:and": "Logical Conjunction (P AND Q). Degree of necessity for both conditions.",
        "log:or": "Logical Disjunction (P OR Q). Degree of sufficiency for either condition.",
        "log:implies": "Fuzzy Implication (If P then Q). Expresses confidence level (w).",
        "log:iff": "Fuzzy Equivalence (P IFF Q). Probability that two concepts are semantically identical."
    }
    dna.update(logic)

    # --- 3. Spatiotemporal Axes (The Coordinates of Reality) ---
    spacetime = {
        "geo:at": "Spatial Link: Pins an atom to a coordinate [lat, lng].",
        "geo:ref": "Affine Reference: Used to calibrate historical vs modern maps.",
        "chrono:period": "Temporal Link: Pins an atom to a historical era.",
        "nar:perspective": "Narrative Filter: Defines the POV for a specific cognitive layer."
    }
    dna.update(spacetime)

    # --- 4. Primary Emotions (The 8 Dimensions of Feeling - Plutchik/Keltner basis) ---
    primary_emotions = {
        "emo:joy": "Primary Emotion: Happiness, expansion, and presence.",
        "emo:sadness": "Primary Emotion: Melancholy, contraction, and memory.",
        "emo:fear": "Primary Emotion: Caution, avoidance, and survival focus.",
        "emo:anger": "Primary Emotion: Hostility, friction, and boundary defense.",
        "emo:trust": "Primary Emotion: Acceptance, openness, and vulnerability.",
        "emo:disgust": "Primary Emotion: Rejection, aversion, and boundary protection.",
        "emo:surprise": "Primary Emotion: Unexpectedness, interruption, and attention reset.",
        "emo:anticipation": "Primary Emotion: Forward-looking, expectation, and readiness."
    }
    dna.update(primary_emotions)

    # --- 5. Compound Emotions (Early Childhood Self-Organization) ---
    compound_emotions = {
        "emo:awe": "Compound: Fear + Surprise + Joy. The feeling of being in the presence of something vast.",
        "emo:nostalgia": "Compound: Joy + Sadness. Sentimental longing for the past.",
        "emo:love": "Compound: Joy + Trust. Deep affection and attachment.",
        "emo:guilt": "Compound: Fear + Sadness + Disgust(self). Remorse for past actions.",
        "emo:curiosity": "Compound: Anticipation + Surprise. Desire to explore the unknown.",
        "emo:despair": "Compound: Sadness + Fear (absence of Anticipation). Complete loss of hope.",
        "emo:contempt": "Compound: Anger + Disgust. Feeling that someone/something is beneath consideration."
    }
    dna.update(compound_emotions)

    # --- 6. Epistemological Frames (Cognitive Lenses for Future Expansion) ---
    # Placeholder for alternative worldview frames (e.g., Dialectics, Systems Theory)
    frames = {
        "frame:dialectics:thesis": "The initial proposition or concept.",
        "frame:dialectics:antithesis": "The negation or contradiction of the thesis.",
        "frame:dialectics:synthesis": "The resolution combining truths from both thesis and antithesis.",
        "frame:systems:feedback_loop": "A circular causality where an output loops back to influence the input."
    }
    dna.update(frames)

    # --- 7. Set-Theoretic Primitives ---
    # The logical foundation of Akasha's collection layer.
    # Set operations are the extension of propositional logic over domains:
    #   set_op:union        ↔ log:or  (member of A OR B)
    #   set_op:intersection ↔ log:and (member of A AND B)
    #   set_op:complement   ↔ log:not (NOT a member of A)
    # This equivalence is what makes set queries composable as logical expressions.
    set_ops = {
        "set_op:union":        "Set union (∪): the collection of all elements belonging to A or B or both.",
        "set_op:intersection": "Set intersection (∩): elements common to both A and B.",
        "set_op:difference":   "Set difference (A∖B): elements in A that are not in B.",
        "set_op:complement":   "Set complement (¬A): all elements in the domain that do not belong to A.",
        "set_op:membership":   "Set membership (∈): the relation of an element belonging to a set.",
        "set_op:subset":       "Set subset (A⊆B): every element of A is also an element of B.",
        "set_op:empty":        "Empty set (∅): the unique set containing no elements; identity for union.",
        "set_op:universal":    "Universal set (Ω): the set of all elements under consideration; identity for intersection.",
    }
    dna.update(set_ops)

    return dna
