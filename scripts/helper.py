import json
from datetime import datetime
from os import listdir, makedirs, rename
from os.path import dirname, exists
from shutil import copy, copytree, rmtree
from subprocess import run
from time import time
from uuid import uuid4
from zipfile import ZipFile

import requests
from termcolor import colored

from scripts.constants import DIRS, INST_DIR, MC_DIR, must_haves

session = requests.session()


def download_file(url: str, dest: str):
    makedirs(dirname(dest), exist_ok=True)
    with session.get(url, stream=True) as r:
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1024 * 1024 * 8):
                f.write(chunk)


def download_musthaves(pack=None):
    if pack is None:
        pack = choose(get_modpacks(), "modpack")
    if confirm("download must-haves"):
        st = time()
        for i in must_haves:
            for num, j in enumerate(must_haves[i]):
                try:
                    print(
                        colored(
                            f"[{i}] [{num + 1}/{len(must_haves[i])}] downloading {j}",
                            "yellow",
                        )
                    )
                    file_name = download_first_from_modrinth(pack, j, i)["file"]
                    file_path = f"{INST_DIR}/{pack}/{DIRS[i]}/{file_name}"
                    if file_path.endswith(".jar"):
                        download_depends(
                            file_path,
                            get_modrinth_index(get_mrpack(pack))["dependencies"][
                                "minecraft"
                            ],
                            pack,
                        )
                except Exception:
                    print(colored("something went wrong!", "red"))
        print(colored(f"downloaded must-haves in {round(time() - st, 2)}s", "green"))


def download_first_from_modrinth(pack: str, query: str, type: str):
    index = get_modrinth_index(get_mrpack(pack))
    depends = index["dependencies"]
    version = depends["minecraft"]
    facets = [
        [f"project_type:{type}"],
    ]
    if type == "mod":
        facets.append(["categories:fabric"])
    if type not in ["resourcepack", "shader"]:
        facets.append([f"versions:{version}"])
    params = {
        "query": query,
        "facets": json.dumps(facets),
    }
    response = session.get("https://api.modrinth.com/v2/search", params=params)
    hits = response.json().get("hits", [])

    if not hits:
        return

    project_id = hits[0]["project_id"]

    versions = session.get(
        f"https://api.modrinth.com/v2/project/{project_id}/version"
    ).json()

    if type != "mod":
        for v in versions:
            file_url = v["files"][0]["url"]
            file_name = v["files"][0]["filename"]
            new_entry = {
                "path": f"{DIRS[type]}/{file_name}",
                "hashes": {
                    "sha1": v["files"][0]["hashes"]["sha1"],
                    "sha512": v["files"][0]["hashes"].get("sha512", ""),
                },
                "downloads": [file_url],
                "fileSize": v["files"][0]["size"],
            }
            index["files"] = [
                f
                for f in index["files"]
                if f["path"].lower() != new_entry["path"].lower()
            ]

            index["files"].append(new_entry)

            save_json(
                f"{get_mrpack(pack)}/modrinth.index.json",
                index,
            )
            download_file(file_url, f"{INST_DIR}/{pack}/{DIRS[type]}/{file_name}")
            return {"file": file_name, "url": file_url}

    for v in versions:
        if version in v["game_versions"] and "fabric" in v["loaders"]:
            file_url = v["files"][0]["url"]
            file_name = v["files"][0]["filename"]
            new_entry = {
                "path": f"{DIRS[type]}/{file_name}",
                "hashes": {
                    "sha1": v["files"][0]["hashes"]["sha1"],
                    "sha512": v["files"][0]["hashes"].get("sha512", ""),
                },
                "downloads": [file_url],
                "fileSize": v["files"][0]["size"],
            }
            index["files"] = [
                f
                for f in index["files"]
                if f["path"].lower() != new_entry["path"].lower()
            ]

            index["files"].append(new_entry)

            save_json(
                f"{get_mrpack(pack)}/modrinth.index.json",
                index,
            )
            download_file(file_url, f"{INST_DIR}/{pack}/{DIRS[type]}/{file_name}")
            return {"file": file_name, "url": file_url}


def extract(file: str, extr_dir: str):
    if exists(f"/tmp/{extr_dir}"):
        rmtree(f"/tmp/{extr_dir}")
    with ZipFile(file, "r") as z:
        z.extractall(f"/tmp/{extr_dir}")


def remove_temps():
    if exists("/tmp/mod"):
        rmtree("/tmp/mod")
    if exists("/tmp/modpack"):
        rmtree("/tmp/modpack")
    if exists("/tmp/worlds"):
        rmtree("/tmp/worlds")


def get_modpacks():
    if exists(f"{INST_DIR}"):
        return listdir(f"{INST_DIR}")
    return []


def confirm(txt="r u sure"):
    return input(f"{txt} [y/n] -> ") in ["Y", "y", ""]


def choose(lst: list, stuff: str = "stuff"):
    if len(lst) <= 0:
        print(colored(f"no {stuff}s installed!", "yellow"))
        exit()
    for num, i in enumerate(lst):
        print(f"[{num + 1}] {i}")

    choice = int(input("choose -> ")) - 1
    if choice > len(lst) - 1 or choice < 0:
        print(colored("that is not an option try again", "red"))
        return choose(lst, stuff)

    return lst[choice]


def save_json(file: str, js):
    with open(file, "w") as f:
        json.dump(js, f, indent=2)


def load_json(file: str):
    with open(file, "r") as f:
        return json.load(f)


def get_mrpack(pack: str):
    return f"{INST_DIR}/{pack}/mrpack"


def get_modrinth_index(folder="/tmp/modpack"):
    return load_json(f"{folder}/modrinth.index.json")


def download_depends(file: str, version: str, pack: str):
    extract(file, "mod")

    data = load_json("/tmp/mod/fabric.mod.json")

    depends = data["depends"]
    if "minecraft" in depends:
        depends.pop("minecraft")
    if "java" in depends:
        depends.pop("java")
    if "sodium" in depends:
        depends.pop("sodium")

    for i in list(depends):
        if i.startswith("fabric"):
            depends.pop(i)

    if len(depends) <= 0:
        return
    print(colored("downloading dependencies...", "yellow"))

    for dep in depends:
        params = {
            "query": dep,
            "facets": f'[["project_type:mod"], ["categories:fabric"], ["versions:{version}"]]',
        }
        response = session.get("https://api.modrinth.com/v2/search", params=params)
        r_data = response.json()
        hits = r_data["hits"]
        if hits[0]["slug"] != dep:
            continue
        project_id = hits[0]["project_id"]
        versions = session.get(
            f"https://api.modrinth.com/v2/project/{project_id}/version"
        ).json()
        for v in versions:
            if version in v["game_versions"] and "fabric" in v["loaders"]:
                file_url = v["files"][0]["url"]
                file_name = v["files"][0]["filename"]
                if file_name in listdir(f"{INST_DIR}/{pack}/mods"):
                    continue
                mods_dir = f"{INST_DIR}/{pack}/mods"
                download_file(file_url, f"{mods_dir}/{file_name}")


def install_fabric(mc: str, loader: str = ""):
    print("installing fabric...")
    download_file(
        "https://maven.fabricmc.net/net/fabricmc/fabric-installer/1.1.0/fabric-installer-1.1.0.jar",
        "/tmp/fabric-installer.jar",
    )

    cmd = [
        "java",
        "-jar",
        "/tmp/fabric-installer.jar",
        "client",
        "-mcversion",
        mc,
        "-dir",
        MC_DIR,
        "-noprofile",
    ]

    if loader != "":
        cmd.extend(["-loader", loader])

    run(cmd)


def install_modpack():
    st = time()
    data = get_modrinth_index()
    depends = data["dependencies"]
    name = data["name"]
    files = data["files"]
    dir = f"{INST_DIR}/{name}"
    copytree("/tmp/modpack/overrides/", f"{INST_DIR}/{name}/", dirs_exist_ok=True)
    makedirs(f"{dir}/mods", exist_ok=True)

    install_fabric(depends["minecraft"], depends["fabric-loader"])
    copytree(
        f"{MC_DIR}/versions/fabric-loader-{depends['fabric-loader']}-{depends['minecraft']}",
        f"{MC_DIR}/versions/{name}",
        dirs_exist_ok=True,
    )
    rename(
        f"{MC_DIR}/versions/{name}/fabric-loader-{depends['fabric-loader']}-{depends['minecraft']}.json",
        f"{MC_DIR}/versions/{name}/{name}.json",
    )

    copy(
        f"{MC_DIR}/libraries/net/fabricmc/intermediary/{depends['minecraft']}/intermediary-{depends['minecraft']}.jar",
        f"{MC_DIR}/versions/{name}/{name}.jar",
    )

    with open(f"{MC_DIR}/versions/{name}/{name}.json", "r") as f:
        version_data = json.load(f)
    version_data["id"] = name
    with open(f"{MC_DIR}/versions/{name}/{name}.json", "w") as f:
        json.dump(version_data, f, indent=2)

    downloads = {i["downloads"][0]: f"{dir}/{i['path']}" for i in files}

    for num, url in enumerate(downloads):
        print(
            colored(
                f"[{num + 1}/{len(downloads)}] downloading {url.split('/')[-1]}",
                "yellow",
            )
        )
        download_file(url, downloads[url])

    launcher_data = load_json(f"{MC_DIR}/launcher_profiles.json")

    profiles = launcher_data.setdefault("profiles", {})

    profile_id = uuid4().hex  # UUID as json-safe string
    timestamp = datetime.utcnow().isoformat() + "Z"

    profiles[profile_id] = {
        "created": timestamp,
        "lastUsed": timestamp,
        "icon": "Grass",
        "name": name,
        "type": "custom",
        "lastVersionId": name,
        "gameDir": f"{INST_DIR}/{name}",
    }

    save_json(f"{MC_DIR}/launcher_profiles.json", launcher_data)

    print(
        colored(
            f"created launcher profile '{name}' in {round(time() - st, 2)}s", "green"
        )
    )
    copytree("/tmp/modpack", f"{dir}/mrpack", dirs_exist_ok=True)
