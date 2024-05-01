import itertools

import axis_and_allies.game_state as game_state


NT_purchase = "purchase"

class EventTree:
    id_iter = itertools.count()

    def __init__(self) -> None:
        self.root = self.build_basic_node()

    def build_basic_node(self):
        new_node = {"children":[], "id":next(EventTree.id_iter), "game_state":game_state.GameState()}
        return new_node
    

    def __repr__(self) -> str:
        return "len(root):  {}  root.keys():  {}".format(
            len(self.root), self.root.keys()
        )
    
    def __str__(self) -> str:
        return self.__repr__()