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

MUST_HAVES = {
    "mod": [
        "sodium",
        "reese's sodium options",
        "lithium",
        "entity culling",
        "ferritecore",
        "more culling",
        "iris",
        "zoomify",
        "appleskin",
        "3d skin layers",
        "mouse tweaks",
        "model gap fix",
        "fabric language kotlin",
        "lamb dynamic lights",
        "modmenu",
    ],
    "resourcepack": [
        "fresh animations",
        "fresh moves",
        "motschen's better leaves",
        "low fire",
        "bee's fancy crops",
        "enhanced boss bars",
        "even better enchants",
    ],
    "shader": ["complementary shaders - reimagined", "miniature", "pastel"],
}
