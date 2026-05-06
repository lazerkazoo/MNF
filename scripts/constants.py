from json import dump, load
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

MUSTHAVES = "must-haves.json"
DEF_MUSTHAVES = {
    "mod": [
        "fabric-api",
        "lithium",
        "modmenu",
        "sodium",
        "sodium-extra",
        "fabric-language-kotlin",
    ],
    "resourcepack": ["better-leaves", "qraftys-capitalized-font"],
    "shader": [],
}


if not exists(MUSTHAVES):
    dump(DEF_MUSTHAVES, open(MUSTHAVES, "w"))
with open(MUSTHAVES, "r") as f:
    must_haves = load(f)
