import axis_and_allies.unit as unit


test_unit_json = """
{
    "always_hit":{
        "ipc":1001,
        "attack":7,
        "defense":7,
        "unit_type":"land",
        "max_hit_points":1,
        "move":1
    },
    "always_miss":{
        "ipc":1003,
        "attack":0,
        "defense":0,
        "unit_type":"land",
        "max_hit_points":1,
        "move":1
    }
}
""".strip()


def load_units(unit_file="../unit_data.json", do_add_test_units=False):
    with open(unit_file) as file:
        json_str = file.read().strip()
    my_unit_dict = unit.load_from_json(json_str)

    if do_add_test_units:
        my_unit_dict.update(
            unit.load_from_json(test_unit_json)
        )
        
        t = my_unit_dict["always_miss"].copy()
        t.unit_type = unit.UNIT_TYPE_NAVAL
        t.name = "always_miss_naval"
        my_unit_dict[t.name] = t

        u = my_unit_dict["always_hit"].copy()
        u.unit_type = unit.UNIT_TYPE_NAVAL
        u.name = "always_hit_naval"
        my_unit_dict[u.name] = u
    
    return my_unit_dict


def build_units(unit_dict):
    units = [unit_dict[name].copy() for name in sorted(unit_dict.keys())]
    return units