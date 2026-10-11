# Whiteboard — the named meaning session, declared before the port.
#
# A whiteboard is the client's own naming layer over the session's self-directed state: a board
# holds PINS, and a board has a FOCUS.  This pack declares that vocabulary, and the shape of the
# pins Set, BEFORE the whiteboard port mints it.
#
# Two namespaces meet here and are not the same thing:
#   · `wb:`         — the Workbench (a research bench on the shared world).  The board's pins Set
#                     lives under it: `set:wb:whiteboard:<board>:pins`.
#   · `whiteboard:` — this vocabulary, and the op family (`whiteboard.*`, renamed from `wb.*` so
#                     the ops are not spelled like the bench namespace they are not).

def "whiteboard" "Whiteboard — a NAMED bundle of a client's self-directed state: its pins and its focus. It is the client's own layer, world-ignorable and never able to widen an IAM grant; naming it is what lets a client keep several and switch between them."
al whiteboard whiteboard
set.add name="whiteboard:vocabulary" id="whiteboard"

def "whiteboard:board" "A board — one named whiteboard. Its pins are the members of `set:wb:whiteboard:<board>:pins`; the Set IS the board, so there is no second place a board's contents are kept."
al whiteboard:board board
ln whiteboard:board whiteboard sys:is_a
set.add name="whiteboard:vocabulary" id="whiteboard:board"

def "whiteboard:pin" "A pin — a MEMBERSHIP in the board's pins Set, taken at the bench clock. Pinning adds a membership and unpinning ends it; neither rewrites the board, so what a board held at a given moment stays readable."
al whiteboard:pin pin
ln whiteboard:pin whiteboard sys:is_a
set.add name="whiteboard:vocabulary" id="whiteboard:pin"

def "whiteboard:focus" "The focus — the coordinate a board is currently looking from. It is a coordinate, not a pin: the focus moves, the pins stay, and recreating or switching a board never erases either."
al whiteboard:focus focus_board
ln whiteboard:focus whiteboard sys:is_a
set.add name="whiteboard:vocabulary" id="whiteboard:focus"

def "whiteboard:pins_set" "The board's pins Set — `set:wb:whiteboard:<board>:pins`, one per board. Declared here, populated by the whiteboard port at run time; it holds the pinned coordinates, so a read of one never answers with this vocabulary."
set.add name="whiteboard:vocabulary" id="whiteboard:pins_set"

def "whiteboard:op_rename" "The op family is `whiteboard.*` (`whiteboard.pin` / `.focus` / `.ls` / …), renamed from `wb.*`: `wb:` is the WORKBENCH namespace, and an op family spelled like a namespace it does not belong to invites both to be read as one. The pins Set keeps its `wb:` prefix because it is stored on the bench; only the ops are renamed."
set.add name="whiteboard:vocabulary" id="whiteboard:op_rename"
