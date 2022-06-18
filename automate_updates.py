#!/usr/bin/python3
import requests
import json
import pathlib
import argparse
import jsbeautifier
import copy
import sys
import dataclasses
from pprint import pprint

# TODO add this mod
#    {
#        "name": "mini_hud",
#        "source": "curseforge",
#        "mod_id": 244260,
#        "output_dir": "mods",
#    },

def get_input_num():
    while True:
        choice = input(" > ")
        try:
            ret = int(choice)
            break
        except ValueError:
            print("Try again")
    return ret

@dataclasses.dataclass(frozen=True)
class mod_source():
    base_url: str
    api_path_fmt_str: str
    to_filename:callable # takes a single list entry, and returns the filename
    to_download_url:callable # takes a single list entry, and returns the download url
    to_data:callable = lambda x:x # assume the api just returns a list, if it doesnt, provide your own lambda that fetches the list from the api's respose's json
    to_downloads:callable = None # optional, get the number of downloads, used by the user prompt
    headers:dict = None
    params:dict = None
    sort_kwargs:dict = None # a dict that is splated (**)
    filter:callable = None

    @property
    def api_fmt_str(self):
        return '/'.join((self.base_url, self.api_path_fmt_str))
    
    @staticmethod
    def get_current_version(minecraft_dir:pathlib.Path, mod_name:str, verbose=False):
        current_version = None
        if minecraft_dir:
            for file in minecraft_dir.glob("mods/**/*.jar"):
                file = str(file)
                if f"[{mod_name}]" in file:
                    current_version = file.rsplit(']', 1)[1]
                    break
        if verbose:
            print(f"{current_version=}")
        return current_version

    
    def entry_fill(self, entry:dict, data_item:dict):
        entry['file_name'] = self.to_filename(data_item)
        entry['download_url'] =  self.to_download_url(data_item)
        return entry

    def update_entry(self, entry:dict, version:str, verbose=False, minecraft_dir=None, max_entries=24):
        entry = copy.deepcopy(entry) # guarantees we don't modify the original

        # fetch api data
        url = self.api_fmt_str.format_map(entry)
        r = requests.get(url, headers=self.headers, params=self.params)

        if r.status_code != 200:
            raise TypeError(f"got {r.status_code=} for {url=}")

        data = self.to_data(r.json())

        # sort if enabled
        if self.sort_kwargs:
            data.sort(**self.sort_kwargs)

        # TODO remove the below, this is tmp

        # filter if enabled
        if self.filter:
            def filter_helper(iterable):
                return self.filter(iterable, version)
            data = list(filter(filter_helper, data))
        if len(data) <= 0:
            print(f"mod {entry['name']} unsupported for version {version}, skipping".format_map(entry))
            return None

        # get current filename
        #print(f"looking for {entry['name']=}")
        current_version = self.get_current_version(minecraft_dir, entry['name'], verbose=verbose)

        # if we already have the top item in the list, we can quick return without prompting the user
        if current_version == self.to_filename(data[0]):
            return self.entry_fill(entry, data[0])

        # loop through each item, and prompt the user
        print("\nChoose an option for {name} ({source}):".format_map(entry))
        selection = None
        for i, item in enumerate(data[0:min(max_entries, len(data))]): # for each item in data (up to max_entries)
            # if no filename, skip
            try:
                if len(self.to_filename(item)) <= 0:
                    continue
            except (IndexError):
                # skip the entry, modrinth causes this issue sometimes, I dont know why
                continue

            # build prompt string for the current item in the list
            prompt_str = [f"\t{i}: {self.to_filename(item)}"]

            if self.to_downloads: # optional
                downloads = self.to_downloads(item)
                prompt_str.append(f"({downloads} downloads)")

            if self.to_filename(item) == current_version:
                prompt_str.append(" CURRENT")
            
            # print user prompt
            print(' '.join(prompt_str))

        # get the user's response or autoselect if only one option
        if len(data) == 1:
            print("\t\t...auto selecting only choice.")
            choice = 0
        else:
            choice = get_input_num()
        if choice >= len(data):
            raise ValueError(f"Your selection of {choice} is out of range")

        # apply the user's choice, and return the resultant entry
        return self.entry_fill(entry, data[choice])

def generate_modlist(args:argparse.ArgumentParser, curseforge_api_key_file="curseforge_api_key.txt"):
    """Processes each entry in mod_templates.json and outputs to modlist_file."""

    infile = pathlib.Path(f"versions\\{args.version}\source_template.json")
    outfile = pathlib.Path(f"versions\\{args.version}\modlist.json")

    # read in curseforge api key
    with open(curseforge_api_key_file, "r") as f:
        CURSE_API_KEY = f.read().strip()
    
    def get_version_id(version: str): # TODO rewrite this completly
        version = f"Minecraft {version}"
        minecraft_game_id = 432

        headers = {
                    'Accept': 'application/json',
                    'x-api-key': CURSE_API_KEY
        }

        r = requests.get(f'https://api.curseforge.com/v1/games/{minecraft_game_id}/version-types', headers=headers)
        for item in r.json()["data"]:
            if item["name"] == version:
                return item["id"]
        return None
    
    def modrinth_filter(item, game_version):
        # must have files
        if not len(item['files']):
            return False
        # anti forge
        pprint(item)
        if "forge" in item['files'][0]["filename"]:
            return False
        # major version match
        for curr_ver in item["game_versions"]:
            if game_version in curr_ver:
                return True
        return False

    def cursefoge_filter(item, game_version):
        # anti forge
        if "forge" in item["fileName"]:
            return False
        if not args.version in item['gameVersions']:
            return False
        return True
    
    # define sources
    sources = {
        "curseforge": mod_source(r"https://api.curseforge.com", "v1/mods/{mod_id}/files",
            lambda x:x['fileName'],
            lambda x:x['downloadUrl'],
            to_data = lambda x:x["data"],
            to_downloads=lambda x:x['downloadCount'],
            headers = {
                'Accept': 'application/json',
                'x-api-key': CURSE_API_KEY
            },
            params = {
                "gameVersionTypeId": get_version_id(args.version),
                "pageSize": 50
            },
            sort_kwargs = {
                "reverse":True,
                "key":lambda x:x["fileDate"]
            },
            filter=cursefoge_filter,
        ),

        "modrinth": mod_source(r"https://api.modrinth.com", "api/v1/mod/{mod_id}/version",
            lambda x:x['files'][0]["filename"],
            lambda x:x['files'][0]["url"],
            sort_kwargs= {
                "reverse":True,
                "key":lambda item:item["date_published"],
            },
            filter = modrinth_filter,
        )
    }

    # load the mod template for the selected version
    source_template = list()
    with open(infile.resolve(), "r") as f:
        source_template = json.load(f)
        source_template.sort(key=lambda x:x['name'].lower())
    
    # process each entry, append each result to results
    results = list()
    for entry in source_template:
        result = sources[entry["source"]].update_entry(entry, args.version, verbose=args.verbose, minecraft_dir=args.minecraft_dir)

        # save result after error checking
        if result is None:
            print("No result for {name}, mod_id={mod_id}".format_map(entry))
        elif not result['download_url']: # and result['name'] != 'effective': # TODO need a better way to do this
            pprint(result)
            raise("result had no download_url, suggest switching to modrinth")
        else:
            results.append(result)
    
    # write results to outfile
    with open(outfile.resolve(), "w") as f:
        opts = jsbeautifier.default_options()
        opts.indent_size = 4
        
        f.write(jsbeautifier.beautify(json.dumps(results), opts))

def main():
    # argparse helper functions
    def dir_path(string):
        path = pathlib.Path(string)
        if path.is_dir():
            return path
        else:
            raise NotADirectoryError(f"\"{string}\" does not exist, or is not a directory")

    def minecraft_version(string):
        # TODO make this ignore minecraft sub-versions
        path = pathlib.Path("./versions/", string)
        if path.is_dir():
            return string
        else:
            raise TypeError(f"version \"{string}\", is not a supported minecraft version")

    # parse args
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--verbose', default=False, action='store_true', help="Enable verbose output.")
    #parser.add_argument('--update-list', default=False, action='store_true', help='Menu driven list updater. Must have a curseforge api key.')
    parser.add_argument('-v', '--version', type=minecraft_version, required=True, help="the minecraft version")
    parser.add_argument('--minecraft-dir', type=dir_path, required=True, help="the minecraft output directory (where all the mod jars, config, etc end up). If provided, this will allow this script to automatically skip over mods that are already current.")
    try:
        args = parser.parse_args()
    except Exception as e:
        print(e)
        sys.exit(1)

    #if args.update_list:
    generate_modlist(args)
    #try:
    #except Exception as e:
    #    print(f"Error: {e}")
    #    if args.verbose:
    #        raise e

if __name__ == "__main__":
    main()
