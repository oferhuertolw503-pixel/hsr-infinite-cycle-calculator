"""Character data loader."""

import json


def load_character(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_team(paths):
    return [load_character(p) for p in paths]
