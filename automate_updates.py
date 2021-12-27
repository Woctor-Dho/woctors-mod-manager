#!/usr/bin/python3
import requests
import enum
import json
import pathlib
import argparse
import jsbeautifier
from pprint import pprint
from datetime import datetime

with open("curseforge_api_key.txt", "r") as f:
    API_KEY = f.read().strip()
CURSE_BASE_URL = "https://api.curseforge.com"
# 306612
curse_headers = {
    'Accept': 'application/json',
    'x-api-key': API_KEY
}

def get_input_num():
    choice = input(" > ")
    try:
        return int(choice)
    except ValueError:
        return None

def mod_exists(dir:str, name:str):
    return pathlib.Path(dir).glob(f"{name}--*")

def get_version_id(version: str):
    version = f"Minecraft {version}"
    minecraft_game_id = 432
    r = requests.get(f'{CURSE_BASE_URL}/v1/games/{minecraft_game_id}/version-types', headers=curse_headers)
    for item in r.json()["data"]:
        if item["name"] == version:
            return item["id"]
    return None

def update_curse(game_version: str, entry: dict):
    game_version = get_version_id(game_version)
    params = {
        "gameVersionTypeId": game_version,
        "pageSize": 50
    }

    r = requests.get(f"{CURSE_BASE_URL}/v1/mods/{entry['mod_id']}/files", headers=curse_headers, params=params)

    data = r.json()["data"]
    data.sort(reverse=True, key=lambda item : item["fileDate"])
    print("Choose an option:")
    for i, curse_file in enumerate(data[0:min(8, len(data))]):
        is_curr_string = ""
        curr_file = pathlib.Path(entry["output_dir"], f"[{entry['name']}]{curse_file['fileName']}")
        if curr_file.exists():
            is_curr_string = " current"
            # save a ref so can be used as defualt if needed
            default_curse_file = curse_file
        print(f"\t{i}: {curse_file['displayName']}  ({curse_file['downloadCount']} downloads){is_curr_string}")

    # get choice
    choice = get_input_num()
    
    # save off needed data
    if choice is None:
        curse_file = default_curse_file
    else:
        curse_file = data[choice]
    #pprint(curse_file)
    entry['file_name'] = curse_file['fileName']
    entry['download_url'] = curse_file['downloadUrl']

    return entry

class Source(enum.Enum):
    CURSEFORGE = 1

def generate_modlist(modlist_file: str):
    game_version = "1.18"
    # name is just for ease of reading 
    source_template = [
        {
            "name": "fabric_api",
            "source": Source.CURSEFORGE,
            "mod_id": 306612,
            "output_dir": "mods",
        },
        {
            "name": "ding",
            "source": Source.CURSEFORGE,
            "mod_id": 231275,
            "output_dir": "mods",
        },
        {
            "name": "bears_armour_hud",
            "source": Source.CURSEFORGE,
            "mod_id": 420155,
            "output_dir": "mods",
        },
    ]

    output = list()

    for entry in source_template:
        result = None
        if entry["source"] == Source.CURSEFORGE:
            result = update_curse(game_version, entry)

        # save result
        if entry is None:
            raise Exception(f"No result for {entry['name']}")
        else:
            entry.pop("source", None) # remove uneeded items
            output.append(result)
    
    with open(pathlib.Path(modlist_file).resolve(), "w") as f:
        opts = jsbeautifier.default_options()
        opts.indent_size = 4
        f.write(jsbeautifier.beautify(json.dumps(output), opts))
    
    return output

def main():
    # parse args
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--update-list', default=False, action='store_true', help='Menu driven list updater. Must have a curseforge api key.')
    args = parser.parse_args()

    if args.update_list:
        generate_modlist(r"woctors-mod-manager\versions\1.18\woctors_modlist.json")

if __name__ == "__main__":
    main()