import json
from json import JSONEncoder
from types import MappingProxyType


class CarsDataEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def save_data(data, name):
    cars_json_data = json.dumps(data, cls=CarsDataEncoder, indent=2)

    with open(f"{name}.json", "w") as f:
        f.write(cars_json_data)

