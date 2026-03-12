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
    download_first_from_modrinth,
    download_from_modrinth,
    download_musthaves,
    extract,
    get_hits,
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

        for num, hit in enumerate(hits):
            print(f"[{num + 1}] {hit['title']}")
        choice = hits[int(input("choose -> ")) - 1]

        file[to_edit][choice["slug"]] = choice["project_id"]
    else:
        choice = choose(list(file[to_edit].keys()), to_edit)
        if confirm(f"remove {choice}"):
            file[to_edit].pop(choice)

    file[to_edit] = stuff
    save_json("data/must-haves.json", file)
    if confirm("another"):
        edit_musthaves(todo, to_edit)


def change_modpack_ver():
    pack = choose(get_modpacks(), "modpack")
    version = input("choose version -> ")
    index_data = get_modrinth_index(get_mrpack(pack))

    index_data["dependencies"]["minecraft"] = version

    save_json(f"{get_mrpack(pack)}/modrinth.index.json", index_data)
    copytree(f"{get_mrpack(pack)}", "/tmp/modpack")
    rmtree(f"{MC_DIR}/versions/{index_data['name']}")
    rmtree(f"{INST_DIR}/{index_data['name']}")
    remove_modpack(pack)

    install_modpack()
    download_first_from_modrinth(pack, "fabric api", "mod")
    update_modpack_mods(pack)


def custom_modpack():
    name = input("name -> ")
    version = input("minecraft version -> ")

    print(colored(f"gettings latest fabric version for mc {version}", "yellow"))
    url = f"https://meta.fabricmc.net/v2/versions/loader/{version}"
    response = session.get(url)

    if response.status_code != 200:
        print(colored("error fetching Fabric data.", "red"))
        return

    data = response.json()

    if not data:
        print(colored("no Fabric loader found for that version.", "red"))
        return

    latest_loader = data[0]["loader"]["version"]

    index_data = {
        "formatVersion": 1,
        "game": "minecraft",
        "name": name,
        "versionId": "1.0",
        "files": [],
        "dependencies": {"fabric-loader": latest_loader, "minecraft": version},
    }
    makedirs("/tmp/modpack/overrides/config")
    save_json("/tmp/modpack/modrinth.index.json", index_data)

    install_modpack()

    download_first_from_modrinth(name, "fabric api", "mod")

    download_musthaves(name)


def update_modpack_mods(pack=None):
    st = time()

    if pack is None:
        pack = choose(get_modpacks(), "modpacks")
    pack_index = get_modrinth_index(get_mrpack(pack))
    mc_version = pack_index["dependencies"]["minecraft"]

    new_files = []
    for num, file_entry in enumerate(pack_index["files"]):
        print(colored(f"[{num + 1}/{len(pack_index['files'])}]", "yellow"))
        update_mod(file_entry, mc_version, new_files, pack, pack_index)

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
    pack_index = get_modrinth_index(f"{get_mrpack(pack)}")
    mods_dir = f"{INST_DIR}/{pack}/mods"
    mods = []

    for m in listdir(mods_dir):
        mods.append(m)

    mods.sort()
    mod = choose(mods, "mod")

    if confirm(f"remove {mod}"):
        remove(f"{mods_dir}/{mod}")

        pack_index["files"] = [
            f
            for f in pack_index["files"]
            if not f["path"].lower().endswith(mod.lower())
        ]
        save_json(f"{get_mrpack(pack)}/modrinth.index.json", pack_index)

    if confirm("another"):
        remove_mod(pack)


def remove_modpack(pack=None):
    if pack is None:
        pack = choose(get_modpacks(), "modpack")
    profiles_file = f"{MC_DIR}/launcher_profiles.json"

    launcher_data = load_json(profiles_file)

    profiles: dict = launcher_data["profiles"]

    profiles = launcher_data.get("profiles", {})

    for i in list(profiles.keys()):
        if profiles[i]["name"] == pack:
            profiles.pop(i)

    launcher_data["profiles"] = profiles

    if confirm("r u sure"):
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
    hits = get_hits(create_params(data[0], data[1]))

    if not hits:
        print(colored(f"no {data[0]}s found", "red"))
        return search_modrinth(data[0], data[1])

    hit_titles = []
    for h in hits:
        hit_titles.append(h["title"])

    choice = hits[hit_titles.index(choose(hit_titles, data[0]))]

    versions = get_versions(choice["project_id"])

    download_from_modrinth(data[0], data[1], data[2], versions)
    if data[0] != "modpack":
        if confirm("another"):
            search_modrinth(data[0], data[1], data[2])


def main():
    remove_temps()
    if MC_DIR == "":
        print(colored("minecraft is not installed", "red"))
        exit()

    options = {
        "search modrinth": search_modrinth,
        "edit must-haves": edit_musthaves,
        "modpack": {
            "create custom modpack": custom_modpack,
            "update modpack mods [beta]": update_modpack_mods,
            "change version of modpack [uses update modpack mods]": change_modpack_ver,
            "add must-haves to modpack": download_musthaves,
            "remove modpack": remove_modpack,
        },
        "remove mod from modpack": remove_mod,
        "download modpack from file": download_modpack,
        "export modpack": export_modpack,
    }

    choice = choose(list(options.keys()))
    if isinstance(options[choice], dict):
        options[choice][choose(list(options[choice].keys()))]()
    else:
        options[choice]()

    if confirm("do other stuff"):
        main()


main()
