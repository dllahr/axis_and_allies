import json
import itertools

UNIT_TYPE_NAVAL = "naval"
UNIT_TYPE_LAND = "land"
UNIT_TYPE_AIR = "air"

ARTILLERY = "artillery"
INFANTRY = "infantry"
CRUISER = "cruiser"
BATTLESHIP = "battleship"

CAN_BOMBARD_NAMES = {CRUISER, BATTLESHIP}

class Unit:
    id_iter = itertools.count()

    def __init__(self, name=None, ipc=None, attack=None, defense=None, unit_type=None, move=None, max_hit_points=None) -> None:
        self.id = next(Unit.id_iter)

        self.name = name
        self.ipc = ipc

        self.attack = attack
        self.temp_attack = attack

        self.defense = defense

        self.unit_type = unit_type
        self.move = move
        self.max_hit_points = max_hit_points
        self.cur_hit_points = max_hit_points
    
    def __str__(self) -> str:
        return """name:  {}
id:  {}
ipc:  {}
attack:  {}
temp_attack:  {}
defense:  {}
unit_type:  {}
move:  {}
max_hit_points:  {}
cur_hit_points:  {}
""".format(self.name, self.id, self.ipc, self.attack, self.temp_attack, self.defense, self.unit_type, self.move,
           self.max_hit_points, self.cur_hit_points)

    def __repr__(self) -> str:
        return self.__str__()

    def copy(self):
        my_copy = Unit(name=self.name, ipc=self.ipc, attack=self.attack, defense=self.defense, unit_type=self.unit_type,
                       move=self.move, max_hit_points=self.max_hit_points)
        my_copy.id = self.id
        return my_copy
    
def load_from_json(json_str):
    input_dict = json.loads(json_str)

    unit_dict = {}
    for name, cur_dict in input_dict.items():
        new_unit = Unit(
            name=name,
            ipc=cur_dict["ipc"],
            attack=cur_dict["attack"],
            defense=cur_dict["defense"],
            unit_type=cur_dict["unit_type"],
            move=cur_dict["move"],
            max_hit_points=cur_dict["max_hit_points"]
        )
        unit_dict[name] = new_unit

    return unit_dict
