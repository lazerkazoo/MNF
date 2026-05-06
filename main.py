import webbrowser
from os import listdir, makedirs, remove, rename
from os.path import exists
from shutil import copy, copytree, make_archive, rmtree
from time import time

import requests
from termcolor import colored

from scripts.constants import DOWNLOADS, INST_DIR, MC_DIR
from scripts.helper import (
    choose,
    confirm,
    create_params,
    download_from_modrinth,
    download_musthaves,
    extract,
    get_hits,
    get_latest_fabric,
    get_mcversion,
    get_modpacks,
    get_modrinth_index,
    get_mrpack,
    get_versions,
    init_data,
    install_modpack,
    load_json,
    remove_temps,
    save_json,
    update_mod,
)

session = requests.session()


def edit_musthaves(todo=None, to_edit=None):
    file = load_json("data/must-haves.json")
    if todo is None:
        todo = choose(["add", "remove"])
    if to_edit is None:
        to_edit = choose(["mod", "resourcepack", "shader"])
    stuff = file[to_edit]

    if todo == "add":
        query = input("what u want to add -> ")
        params = create_params(to_edit, query=query)
        hits = get_hits(params)

        hit_titles = []
        for h in hits:
            hit_titles.append(h["title"])
        choice = hits[hit_titles.index(choose(hit_titles))]

        stuff.append(choice["slug"])
    else:
        choice = choose(list(stuff), to_edit)
        if confirm(f"remove {choice}"):
            stuff.remove(choice)

    stuff = list(set(stuff))
    stuff.sort()
    file[to_edit] = stuff
    save_json("data/must-haves.json", file)
    if confirm("another"):
        edit_musthaves(todo, to_edit)


def change_modpack_ver(skip=False):
    pack = choose(get_modpacks(), "modpack")
    index_data = get_modrinth_index(get_mrpack(pack))
    version = input("choose version -> ") if not skip else get_mcversion(index_data)

    index_data["dependencies"]["minecraft"] = version
    index_data["dependencies"]["fabric-loader"] = get_latest_fabric(version)

    save_json(f"{get_mrpack(pack)}/modrinth.index.json", index_data)
    copytree(f"{get_mrpack(pack)}", "/tmp/modpack")
    rmtree(f"{MC_DIR}/versions/{index_data['name']}")
    rmtree(f"{INST_DIR}/{index_data['name']}")
    remove_modpack(pack)

    install_modpack()
    download_from_modrinth("mod", pack, get_versions("fabric-api", version))
    update_modpack_mods(pack)


def custom_modpack():
    name = input("name -> ")
    version = input("minecraft version -> ")

    index_data = {
        "formatVersion": 1,
        "game": "minecraft",
        "name": name,
        "versionId": "1.0",
        "files": [],
        "dependencies": {
            "fabric-loader": get_latest_fabric(version),
            "minecraft": version,
        },
    }
    makedirs("/tmp/modpack/overrides/config")
    save_json("/tmp/modpack/modrinth.index.json", index_data)

    install_modpack()

    download_musthaves(name)


def update_modpack_mods(pack=None):
    st = time()

    if pack is None:
        pack = choose(get_modpacks(), "modpacks")
    pack_index = get_modrinth_index(get_mrpack(pack))

    new_files = []
    for num, file_entry in enumerate(pack_index["files"]):
        print(colored(f"[{num + 1}/{len(pack_index['files'])}]", "yellow"))
        update_mod(file_entry, new_files, pack)

    print(colored(f"finished updating in {round(time() - st, 1)}s!", "green"))

    pack_index["files"] = new_files
    save_json(f"{get_mrpack(pack)}/modrinth.index.json", pack_index)


def download_modpack():
    file = choose(list(listdir(DOWNLOADS)), "modpacks downloaded")
    extract(f"{DOWNLOADS}/{file}", "modpack")

    install_modpack()


def export_modpack():
    pack = choose(get_modpacks(), "modpack")
    if confirm("copy resource/shader packs"):
        try:
            copytree(
                f"{INST_DIR}/{pack}/resourcepacks",
                "/tmp/modpack/overrides/resourcepacks",
                dirs_exist_ok=True,
            )
        except Exception:
            pass
        try:
            copytree(
                f"{INST_DIR}/{pack}/shaderpacks",
                "/tmp/modpack/overrides/shaderpacks",
                dirs_exist_ok=True,
            )
        except Exception:
            pass
    copy(f"{get_mrpack(pack)}/modrinth.index.json", "/tmp/modpack")
    make_archive(
        f"{DOWNLOADS}/{pack}",  # where the zip will be created
        "zip",
        root_dir="/tmp/modpack",  # what 2 zip
    )
    rename(f"{DOWNLOADS}/{pack}.zip", f"{DOWNLOADS}/{pack}.mrpack")


def remove_mod(pack=None):
    if pack is None:
        pack = choose(get_modpacks(), "modpack")
    pack_index = get_modrinth_index(get_mrpack(pack))
    mods_dir = f"{INST_DIR}/{pack}/mods"
    mods = []

    for m in listdir(mods_dir):
        mods.append(m)

    mods.sort()
    mod = choose(mods, "mod", True)

    remove(f"{mods_dir}/{mod}")

    pack_index["files"] = [
        f for f in pack_index["files"] if not f["path"].lower().endswith(mod.lower())
    ]
    save_json(f"{get_mrpack(pack)}/modrinth.index.json", pack_index)

    if confirm("another"):
        remove_mod(pack)


def remove_modpack(pack=None):
    if pack is None:
        pack = choose(get_modpacks(), "modpack", True)
    profiles_file = f"{MC_DIR}/launcher_profiles.json"

    launcher_data = load_json(profiles_file)

    profiles = launcher_data.get("profiles", {})

    for i in list(profiles.keys()):
        if profiles[i]["name"] == pack:
            profiles.pop(i)

    launcher_data["profiles"] = profiles

    save_json(profiles_file, launcher_data)
    for path in [
        f"{INST_DIR}/{pack}",
        f"{MC_DIR}/versions/{pack}",
    ]:
        if exists(path):
            rmtree(path)


def search_modrinth(type=None, version=None, modpack=None):
    remove_temps()

    data = init_data(type, version, modpack)
    hits = get_hits(create_params(data["type"], data["version"]))
    save_json("stuff.json", hits)

    if not hits:
        print(colored(f"no {data['type']}s found", "red"))
        return search_modrinth(data["type"], data["version"])

    hit_titles = []
    for h in hits:
        hit_titles.append(h["title"])

    choice = hits[hit_titles.index(choose(hit_titles, data["type"]))]

    if not data["version"]:
        data["version"] = choose(choice["versions"])
    versions = get_versions(
        choice["slug"], data["version"], data["type"] in ["mod", "modpack"]
    )

    download_from_modrinth(data["type"], data["modpack"], versions)
    if data["type"] != "modpack" and confirm("another"):
        search_modrinth(data["type"], data["version"], data["modpack"])
    return None


def main():
    remove_temps()
    if MC_DIR == "":
        print(colored("minecraft is not installed", "red"))
        exit()

    options = {
        "search modrinth": search_modrinth,
        "edit must-haves": edit_musthaves,
        "modpack (expands)": {
            "create custom modpack": custom_modpack,
            "update modpack mods": lambda: change_modpack_ver(True),
            "change version of modpack": change_modpack_ver,
            "add must-haves to modpack": download_musthaves,
            "remove modpack": remove_modpack,
        },
        "remove mod from modpack": remove_mod,
        "download modpack from file": download_modpack,
        "export modpack": export_modpack,
        "open manual": lambda: webbrowser.open(
            "https://github.com/lazerkazoo/MNF/blob/master/MANUAL.md"
        ),
    }

    choice = choose(list(options.keys()))
    if isinstance(options[choice], dict):
        options[choice][choose(list(options[choice].keys()))]()
    else:
        options[choice]()

    if confirm("do other stuff") or choice == "open manual":
        main()


main()
