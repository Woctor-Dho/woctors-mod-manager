# Woctor's Modpack

## How to use with automatic updates

1) Install [Multi MC](https://multimc.org/) and [python](https://www.python.org/downloads/windows/).
2) MultiMC requires a specific java version. See [this guide](https://github.com/MultiMC/Launcher/wiki/Using-the-right-Java) for install instructions. 
3) Using MultiMC, create a new Instance, and install Fabric.
4) Put [`mod_updater.py`](https://raw.githubusercontent.com/Woctor-Dho/woctors-mod-manager/main/mod_updater.py) in the instance's `.minecraft` folder.
5) Got to your `Edit Instance > Settings > Custom commands`:
     - Enable "Custom Commands"
     - Paste `python "$INST_MC_DIR\mod_updater.py -v 1.18"` in to your "Pre-Launch command".
6) stonkz (Minecraft will now auto-update mods when launching)
7) Optional: if you want to use optifine (instead of sodium), you'll have to [manually download it](https://optifine.net/downloads) and drop it in your mods folder because the optifine website is dumb. 

## How to use with manual updates

1) Install [python](https://www.python.org/downloads/windows/).
2) Put [`mod_updater.py`](https://raw.githubusercontent.com/Woctor-Dho/woctors-mod-manager/main/mod_updater.py) in the instance's `.minecraft` folder.
3) Run `python mod_updater.py` in a terminal, or double click the `mod_updater.py` each time you want to manually update mods. 
4) Optional: if you want to use optifine (instead of sodium), you'll have to [manually download it](https://optifine.net/downloads) and drop it in your mods folder because the optifine website is dumb.
