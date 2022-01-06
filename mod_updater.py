#!/usr/bin/python
import sys
import json
import pathlib
import requests
import dataclasses
import argparse
from pprint import pprint

# global config
REPO_URL = r"https://raw.githubusercontent.com/Woctor-Dho/woctors-mod-manager"

@dataclasses.dataclass(frozen=True)
class JsonSource:
    __slots__ = "local", "remote"
    local: str
    remote: str

    def _get_local(self):
        with open(self.local) as file:
            return json.load(file)
    
    def _get_remote(self):
        result = requests.get(self.remote)
        if result.status_code == 200:
            return result.json()
        else:
            raise Exception(f"could not fetch {self.remote}")
    
    def json(self, local:bool):
        if local:
            return self._get_local()
        else:
            return self._get_remote()
    
    def do_for_each(self, func:callable, local:bool, *args, **kwargs):
        ret = list()
        for item in self.json(local):
            ret.append(
                func(item, *args, **kwargs)
            )
        return ret

def update_mod(mod:dict, install_dir:str):
    modname_formatstr:str = r"[{name}]{file_name}"
    output_dir = pathlib.Path(install_dir, mod["output_dir"])
    output_file = pathlib.Path(output_dir,  modname_formatstr.format_map(mod))

    # create output directory if doesnt exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # if file does not exit
    if not output_file.is_file():
        print("Updating {name}...".format_map(mod))

        # download new mod
        print("\tdownloading {download_url}".format_map(mod))
        result = requests.get(mod["download_url"])
        if result.status_code == 200:
            
            with open(output_file, "wb") as out:
                out.write(result.content)

        else:
            print("download failed, skipping mod")
    
    return output_file

def update_config(config:dict, install_dir:str, branch:str, version:str):
    """Updates non-mod files."""
    base=f"{REPO_URL}/{branch}/versions/{version}/resources/"
    resource = requests.get(base + config["name"])
    if resource.status_code == 200:
        output_dir = pathlib.Path(install_dir, config["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = pathlib.Path(output_dir, config["name"])
        with open(output_file, "wb") as out:
            out.write(resource.content)
    else:
        print(f"could not download resouce {config['name']}!")
        sys.exit(1)

def remove_unused_mods(minecraft_dir:pathlib.Path, created_files:pathlib.Path):
   # remove extra files in mod dir
    mods_dir = pathlib.Path(minecraft_dir, "./mods/")
    all = list(mods_dir.glob('**/*'))
    diff = list(set(all) - set(created_files))
    diff = sorted(diff, reverse=True)

    # if files to remove
    for file in diff:
        if file.is_dir():
            if not any(file.iterdir()):
                print(f"removing empty directory {file}")
                file.rmdir()
        else:
            print(f"removing file {file}")
            file.unlink(missing_ok=True)

def do_mod_updates(args):
    # update mods
    mods = JsonSource(f"versions/{args.version}/modlist.json", f"{REPO_URL}/{args.branch}/versions/{args.version}/modlist.json")
    created_files = mods.do_for_each(update_mod, args.local, args.minecraft_dir)
    remove_unused_mods(args.minecraft_dir, created_files) # remove old mods

    # update config files
    #config = JsonSource(f"versions/{args.version}/configlist.json", f"{REPO_URL}/{args.branch}/versions/{args.version}/configlist.json")
    #config.do_for_each(update_config, args.local, args.minecraft_dir, args.branch, args.version)

def main():
    # argparse helper functions
    def dir_path(string):
        path = pathlib.Path(string)
        if path.is_dir():
            return path
        else:
            raise NotADirectoryError(f"\"{string}\" does not exist, or is not a directory")
    
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--verbose', default=False, action='store_true', help="Enable verbose output.")
    parser.add_argument('--local', default=False, action='store_true', help="Dont reach out to github, just look locally for json files. (FOR DEVELOPMENT ONLY)")
    parser.add_argument('--branch', type=str, default="master", help="which branch in the repo to pull the config from. default is master. (FOR DEVELOPMENT ONLY)")
    parser.add_argument('-v', '--version', type=str, required=True, help="the minecraft version")
    parser.add_argument('--minecraft-dir', type=dir_path, required=True, help="the minecraft output directory (where all the mod jars, config, etc end up).")

    try:
        args = parser.parse_args()
    except Exception as e:
        print(e)
        sys.exit(1)
    
    do_mod_updates(args)

if __name__ == "__main__":
    main()
