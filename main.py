from statemachine import StateChart, State
from frozendict import frozendict

# TODO Alphabet could be it's own class,
#  with transliterated and Arabic script variants


rows = [[]]

# TODO what other transcription systems are there??
df = pd.DataFrame(rows, columns=["arabic", "ipa", "romanization"])

alphabet = frozendict(
    {
        "b": "b",
        "d": "d",
        "l": "l",
        # "pharyngals": [],
        # "sibilants": [],
        # "uvulars": [],
        # "nasals": [],
        # "emphatics": [],
    }
)


"""
encode Arabic phonotactics as conditions
"""


# The boolean function acting as a guard
def r3_not_same_as_r2(self) -> bool:
    return self.stock_count > 0


# TODO Maybe using a state machine is overthinking it?
class NaiveTriliteralMachine(StateChart):
    r_0 = State("r_0", initial=True)

    # TODO states should be the alphabet
    # for a in alphabet:

    # Or could have like this and change value per run??:
    # r_1 = State('r_1', value="b", initial=True)  # Eek, this seems not good.

    r_1 = State("r_1")
    r_2 = State("r_2")
    r_3 = State("r_3", final=True)

    def __init__(self, alphabet=alphabet):
        super().__init__()
        self.alphabet = alphabet

    """
    | on_enter_<state>() | Every time <state> is entered |
    | on_exit_<state>() | Every time <state> is exited |
    | before_<event>() | Before any transition for <event> |
    | on_<event>() | During the transition for <event> |
    | after_<event>() | After the transition for <event> |
    """

    def on_enter_r_1(self, source: State, target: State):
        print(target.name)

    def on_enter_r_2(self, source: State, target: State):
        print(target.name)

    def on_enter_r_3(self, source: State, target: State):
        print(target.name)

    # Define the transitions
    emit_literal_r1 = r_0.to(r_1)  # AKA ":start"
    emit_literal_r2 = r_1.to(r_2)
    emit_literal_r3 = r_2.to(r_3)


root = NaiveTriliteralMachine(alphabet=alphabet)

"""
"Use `send()` when the event name is dynamic 
 (e.g., comes from user input or a message queue)."
"""
root.send("emit_literal_r1")  # AKA root.emit_literal_r1()
# print(root.r_1.is_active)

root.send("emit_literal_r2")
# print(root.r_2.is_active)

root.send("emit_literal_r3")
# print(root.r_3.is_active)
