#!/usr/bin/python
import json
import pathlib
import requests
import dataclasses

# global config
repo_url = r"https://raw.githubusercontent.com/Woctor-Dho/woctors-mod-manager"
branch = r"main_rewrite"
version = r"1.18"

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
        for item in self.json(local):
            func(item, *args, **kwargs)


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
            # remove any existing
            for p in pathlib.Path(output_dir).glob(mod["name"] + "*"):
                print(f"\tremoving {p}")
                p.unlink()
            
            with open(output_file, "wb") as out:
                out.write(result.content)

        else:
            print("download failed, skipping mod")
def main():
    local = True
    cwd = pathlib.Path.cwd()
    branch = "master"

    # remove any old files
    #rm_patterns = JsonSource("woctors_modpack\rm_patterns.json", f"{repo_url}/{branch}/versions/{version}/rm_patterns.json")
    #rm_patterns.do_for_each(rm_pattern, local, cwd)

    # update mods
    mods = JsonSource(f"woctors-mod-manager/versions/{version}/woctors_modlist.json", f"{repo_url}/{branch}/versions/{version}/woctors_modlist.json")
    mods.do_for_each(update_mod, local, cwd)

    # update config files
    #config = JsonSource("woctors_modpack\woctors_configlist.json", f"{repo_url}/{branch}/versions/{version}/woctors_configlist.json")
    #config.do_for_each(update_config, local, cwd, branch)

if __name__ == "__main__":
    main()