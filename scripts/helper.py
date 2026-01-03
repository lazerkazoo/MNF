import json
from datetime import datetime
from os import listdir, makedirs, rename
from os.path import abspath, dirname, exists
from shutil import copy, copytree, rmtree
from subprocess import run
from threading import Thread
from time import sleep, time
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
    threads = []

    if pack is None:
        pack = choose(get_modpacks(), "modpack")
    st = time()

    for i in must_haves:
        for j in must_haves[i]:
            threads.append(
                Thread(target=download_first_from_modrinth, args=(pack, j, i))
            )

    for thread in threads:
        print(
            colored(
                f"[{thread._args[2]}] starting download for {thread._args[1]}...",
                "yellow",
            )
        )
        thread.start()
        sleep(0.2)

    print(colored(f"downloaded must-haves in {round(time() - st, 2)}s", "green"))


def download_first_from_modrinth(pack: str, query: str, type: str, strict=False):
    index = get_modrinth_index(get_mrpack(pack))
    depends = index["dependencies"]
    version = depends["minecraft"]

    params = create_params(type, version, query)
    hits = get_hits(params)

    if not hits:
        return
    if strict and hits[0]["slug"] != query:
        return

    project_id = hits[0]["project_id"]

    versions = get_versions(project_id)

    download_from_modrinth(type, version, pack, versions, False)


def extract(file: str, extr_dir: str):
    remove_temps()
    with ZipFile(file, "r") as z:
        z.extractall(f"/tmp/{extr_dir}")


def remove_temps():
    rmtree("/tmp/mod", ignore_errors=True)
    rmtree("/tmp/modpack", ignore_errors=True)
    rmtree("/tmp/worlds", ignore_errors=True)


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


def download_depends(file: str, pack: str):
    with ZipFile(file, "r") as z:
        data = json.loads(z.read("fabric.mod.json"))

    depends = data["depends"]
    for dep in ["minecraft", "java", "sodium"]:
        if dep in depends:
            depends.pop(dep)

    for i in list(depends):
        if i.startswith("fabric"):
            depends.pop(i)

    if not depends:
        return

    print(colored("downloading dependencies...", "yellow"))

    for dep in depends:
        download_first_from_modrinth(pack, dep, "mod", True)


def install_fabric(mc: str, loader: str = ""):
    print("installing fabric...")
    if not exists("/tmp/fabric-installer.jar"):
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


def install_modpack(ask_install_musthaves=False):
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

    threads = []
    for num, url in enumerate(downloads):
        threads.append(Thread(target=download_file, args=(url, downloads[url])))

    for num, thread in enumerate(threads):
        if num % 10 == 0 and num > 0:
            threads[num - 5].join()
        print(
            colored(
                f"[{num + 1}/{len(downloads)}] downloading {thread._args[0].split('/')[-1]}",
                "yellow",
            )
        )
        thread.start()
        sleep(0.02)

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

    if ask_install_musthaves:
        if confirm("download must-haves"):
            download_musthaves(name)


def init_data(type=None, version=None, modpack=None):
    if type is None:
        types = ["mod", "modpack", "resourcepack", "shader"]
        type = choose(types)

        if type != "modpack":
            modpack = choose(get_modpacks(), "modpack")
            index_file = f"{get_mrpack(modpack)}/modrinth.index.json"
            version = json.load(open(index_file))["dependencies"]["minecraft"]

    if version is None:
        version = input("mc version [just press enter to search all versions] -> ")

    return (type, version, modpack)


def create_params(type, version, query=None):
    if query is None:
        query = input("search modrinth -> ")

    base_facets = [[f"project_type:{type}"]]

    if type not in ["resourcepack", "shader"]:
        base_facets.append(["categories:fabric"])

    if version not in ("", None) and type not in ["resourcepack", "shader"]:
        base_facets.append([f"versions:{version}"])

    return {"query": query, "facets": json.dumps(base_facets)}


def get_hits(params):
    response = session.get("https://api.modrinth.com/v2/search", params=params)
    return response.json().get("hits", [])


def get_versions(project_id):
    return session.get(
        f"https://api.modrinth.com/v2/project/{project_id}/version"
    ).json()


def double_check_version(versions, version):
    all_versions = list({v["game_versions"][0] for v in versions})
    all_versions.sort()
    all_versions.reverse()

    if version == "":
        version = choose(list(reversed(all_versions)), "version")

    return version


def download_from_modrinth(type, version, modpack, versions, print_downloading=True):
    version = double_check_version(versions, version)
    for v in versions:
        condition = (
            version in v["game_versions"] and "fabric" in v["loaders"]
            if type in ["mod", "modpack"]
            else True
        )
        if condition:
            file_info = v["files"][0]
            file_url = file_info["url"]
            file_name = file_info["filename"]

            if type != "modpack":
                type_dir = f"{INST_DIR}/{modpack}/{DIRS[type]}"
                makedirs(abspath(type_dir), exist_ok=True)
                target = f"{type_dir}/{file_name}"

                if print_downloading:
                    print(colored(f"downloading {file_name}...", "yellow"))
                download_file(file_url, target)

                generate_new_entry(
                    (type, get_modrinth_index(get_mrpack(modpack)), modpack),
                    (file_name, file_url),
                    v,
                )

                if type == "mod":
                    download_depends(target, modpack)
                break

            # MODPACK INSTALLATION
            tmp_path = f"/tmp/{file_name}"
            download_file(file_url, tmp_path)

            extract(tmp_path, "modpack")
            install_modpack(True)
            break


def generate_new_entry(data, file_data, v):
    new_entry = {
        "path": f"{DIRS[data[0]]}/{file_data[0]}",
        "hashes": {
            "sha1": v["files"][0]["hashes"]["sha1"],
            "sha512": v["files"][0]["hashes"].get("sha512", ""),
        },
        "downloads": [file_data[1]],
        "fileSize": v["files"][0]["size"],
    }
    data[1]["files"] = [
        f for f in data[1]["files"] if f["path"].lower() != new_entry["path"].lower()
    ]

    data[1]["files"].append(new_entry)

    save_json(
        f"{get_mrpack(data[2])}/modrinth.index.json",
        data[1],
    )
