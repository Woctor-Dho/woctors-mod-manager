#!/usr/bin/python3
import requests
import enum
import json
import pathlib
import argparse
import jsbeautifier
from pprint import pprint
from datetime import datetime

# curseforge global config
with open("curseforge_api_key.txt", "r") as f:
    CURSE_API_KEY = f.read().strip()
CURSE_BASE_URL = r"https://api.curseforge.com"
# 306612
curse_headers = {
    'Accept': 'application/json',
    'x-api-key': CURSE_API_KEY
}

# modrinth global config
MODRINTH_BASE_URL = r"https://api.modrinth.com/"

# general global config
MAX_ENTRIES = 8

class Source(enum.Enum):
    CURSEFORGE = 1
    MODRINTH = 2

SOURCE_TEMPLATE = [
    {
        "name": "fabric_api",
        "source": Source.CURSEFORGE,
        "mod_id": 306612,
        "output_dir": "mods",
    },
    {
        "name": "cloth_config",
        "source": Source.CURSEFORGE,
        "mod_id": 319057,
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
    {
        "name": "better_taskbar",
        "source": Source.MODRINTH,
        "mod_id": "gPEcet33",
        "output_dir": "mods",
    },
    {
        "name": "dark_loading_screen",
        "source": Source.CURSEFORGE,
        "mod_id": 365727,
        "output_dir": "mods",
    },
    {
        "name": "falling_leaves",
        "source": Source.MODRINTH,
        "mod_id": "WhbRG4iK",
        "output_dir": "mods",
    },
    {
        "name": "ferrite_core",
        "source": Source.MODRINTH,
        "mod_id": "uXXizFIs",
        "output_dir": "mods",
    },
    {
        "name": "Iris",
        "source": Source.MODRINTH,
        "mod_id": "YL57xq9U",
        "output_dir": "mods",
    },
    {
        "name": "item_scroller",
        "source": Source.CURSEFORGE,
        "mod_id": 242064,
        "output_dir": "mods",
    },
    {
        "name": "krypton",
        "source": Source.MODRINTH,
        "mod_id": "fQEb0iXm",
        "output_dir": "mods",
    },
    {
        "name": "lazy_dfu",
        "source": Source.MODRINTH,
        "mod_id": "hvFnDODi",
        "output_dir": "mods",
    },
    {
        "name": "lazy_language_loader",
        "source": Source.MODRINTH,
        "mod_id": "Nz0RSWrF",
        "output_dir": "mods",
    },
    {
        "name": "malilib",
        "source": Source.CURSEFORGE,
        "mod_id": 303119,
        "output_dir": "mods",
    },
    {
        "name": "mod_menu",
        "source": Source.MODRINTH,
        "mod_id": "mOgUt4GM",
        "output_dir": "mods",
    },
    {
        "name": "ok_zoomer",
        "source": Source.MODRINTH,
        "mod_id": "aXf2OSFU",
        "output_dir": "mods",
    },
    {
        "name": "rebind_narrator",
        "source": Source.MODRINTH,
        "mod_id": "qw2Ls89j",
        "output_dir": "mods",
    },
    {
        "name": "sodium",
        "source": Source.MODRINTH,
        "mod_id": "AANobbMI",
        "output_dir": "mods",
    },
    {
        "name": "sodium-extra",
        "source": Source.MODRINTH,
        "mod_id": "PtjYWJkn",
        "output_dir": "mods",
    },
    {
        "name": "starlight_fabric",
        "source": Source.MODRINTH,
        "mod_id": "H8CaAYZC",
        "output_dir": "mods",
    },
    {
        "name": "tweakeroo",
        "source": Source.CURSEFORGE,
        "mod_id": 297344,
        "output_dir": "mods",
    },
    {
        "name": "litematica",
        "source": Source.CURSEFORGE,
        "mod_id": 308892,
        "output_dir": "mods",
    },
    {
        "name": "fast_chest",
        "source": Source.CURSEFORGE,
        "mod_id": 436038,
        "output_dir": "mods",
    },
#    {
#        "name": "mini_hud",
#        "source": Source.CURSEFORGE,
#        "mod_id": 244260,
#        "output_dir": "mods",
#    },
    {
        "name": "minimal_menu",
        "source": Source.MODRINTH,
        "mod_id": "BYtiUf2Z",
        "output_dir": "mods",
    },
]

def get_input_num():
    while True:
        choice = input(" > ")
        try:
            ret = int(choice)
            break
        except ValueError:
            print("Try again")
    return ret

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

    default_curse_file = None

    data = r.json()["data"]
    data.sort(reverse=True, key=lambda item : item["fileDate"])
    print(f"\nChoose an option for {entry['name']} (CURSEFORGE):")
    for i, curse_file in enumerate(data[0:min(MAX_ENTRIES, len(data))]):
        is_curr_string = ""
        curr_file = pathlib.Path(entry["output_dir"], f"[{entry['name']}]{curse_file['fileName']}")
        if curr_file.exists():
            is_curr_string = "  CURRENT"
            # save a ref so can be used as defualt if needed
            default_curse_file = curse_file
        print(f"\t{i}: {curse_file['displayName']}  ({curse_file['downloadCount']} downloads){is_curr_string}")

    if default_curse_file is data[0]:
        curse_file = default_curse_file
    else:
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

def update_modrinth(game_version: str, entry: dict):
    r = requests.get(f"{MODRINTH_BASE_URL}api/v1/mod/{entry['mod_id']}/version")
    #pprint(r.json())

    def get_filename(modrinth_file):
        return modrinth_file['files'][0]["filename"]

    data = r.json()
    data.sort(reverse=True, key=lambda item : item["name"])

    default_modrinth_file = None

    print(f"\nChoose an option for {entry['name']} (MODRINTH):")
    for i, modrinth_file in enumerate(data[0:min(MAX_ENTRIES, len(data))]):
        is_curr_string = ""

        # hotifx
        if len(modrinth_file['files']) <= 0:
            continue

        curr_file = pathlib.Path(entry["output_dir"], f"[{entry['name']}]{get_filename(modrinth_file)}")
        if curr_file.exists():
            is_curr_string = "  CURRENT"
            # save a ref so can be used as defualt if needed
            default_modrinth_file = modrinth_file
        print(f"\t{i}: {modrinth_file['name']}  ({modrinth_file['downloads']} downloads){is_curr_string}")

    if default_modrinth_file is data[0]:
        modrinth_file = default_modrinth_file
    else:
        # get choice
        choice = get_input_num()
        
        # save off needed data
        if choice is None:
            modrinth_file = default_modrinth_file
        else:
            modrinth_file = data[choice]
    
    #pprint(curse_file)
    entry['file_name'] = get_filename(modrinth_file)
    entry['download_url'] =  modrinth_file['files'][0]["url"]

    return entry

def generate_modlist(modlist_file: str):
    game_version = "1.18"
    # name is just for ease of reading 

    output = list()

    for entry in SOURCE_TEMPLATE:
        result = None
        if entry["source"] == Source.CURSEFORGE:
            result = update_curse(game_version, entry)
        elif entry["source"] == Source.MODRINTH:
            result = update_modrinth(game_version, entry)

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
        generate_modlist(r"woctors-mod-manager\versions\1.18\modlist.json")

if __name__ == "__main__":
    main()
