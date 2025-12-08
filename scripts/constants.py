from json import load
from os.path import exists, expanduser

HOME = expanduser("~")
MC_DIR = (
    f"{HOME}/.var/app/com.mojang.Minecraft/.minecraft"
    if exists(f"{HOME}/.var/app/com.mojang.Minecraft/.minecraft")
    else f"{HOME}/.minecraft"
    if exists(f"{HOME}/.minecraft")
    else ""
)
INST_DIR = f"{MC_DIR}/instances"
DOWNLOADS = f"{HOME}/Downloads"
DIRS = {
    "mod": "mods",
    "resourcepack": "resourcepacks",
    "shader": "shaderpacks",
}

with open("data/must-haves.json", "r") as f:
    must_haves = load(f)
