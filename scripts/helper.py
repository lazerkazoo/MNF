import json
from datetime import datetime
from os import listdir, makedirs, remove, rename
from os.path import dirname, exists
from shutil import copy, copytree, rmtree
from subprocess import check_output, run
from sys import exit
from threading import Thread
from time import sleep, time
from uuid import uuid4
from zipfile import ZipFile

import requests
from fuzzywuzzy import fuzz
from termcolor import colored

from scripts.constants import DIRS, INST_DIR, MC_DIR, must_haves

session = requests.session()


def save_json(file: str, js):
    with open(file, "w") as f:
        json.dump(js, f, indent=2)


def load_json(file: str):
    with open(file, "r") as f:
        return json.load(f)


def download_file(url: str, dest: str):
    makedirs(dirname(dest), exist_ok=True)
    run(["curl", url, "-o", dest, "-s"])


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


def get_mrpack(pack: str):
    return f"{INST_DIR}/{pack}/mrpack"


def get_modrinth_index(folder="/tmp/modpack"):
    return load_json(f"{folder}/modrinth.index.json")


def get_mcversion(index: str | dict):
    if isinstance(index, str):
        index = get_modrinth_index(get_mrpack(index))
    return index["dependencies"]["minecraft"]


def confirm(txt="r u sure", strict=False):
    inp = input(f"{txt} [y/n] -> ").lower()
    return inp in ["y"] if strict else inp in ["y", ""]


def choose(lst: list, stuff="stuff", check=False):
    print()
    final = ""
    if len(lst) <= 0:
        print(colored(f"no {stuff}s installed!", "yellow"))
        exit()
    for n, i in enumerate(lst):
        print(f"[{n + 1}] {i}")
    print()

    choice = input("choose [can enter name] -> ")
    try:
        choice = int(choice) - 1
        if choice > len(lst) - 1 or choice < 0:
            print(colored("that is not an option try again", "red"))
            return choose(lst, stuff, check)
        final = lst[choice]
    except Exception:
        current = 0
        for i in lst:
            ratio = fuzz.ratio(i, choice)
            if ratio > current:
                current = ratio
                final = i
    if check and not confirm(final):
        return choose(lst, stuff, check)
    return final


def create_params(type, version=None, query=None):
    if query is None:
        query = input("search modrinth -> ")

    base_facets = [[f"project_type:{type}"]]

    if type not in ["resourcepack", "shader"]:
        base_facets.append(["categories:fabric"])

    if (
        version not in ("", None)
        and type not in ["resourcepack", "shader"]
        and version is not None
    ):
        base_facets.append([f"versions:{version}"])

    return {"query": query, "facets": json.dumps(base_facets)}


def get_hits(params):
    response = session.get("https://api.modrinth.com/v2/search", params=params)
    return response.json().get("hits", [])


def get_versions(slug, mc=None, mod=True):
    url = f"https://api.modrinth.com/v2/project/{slug}/version"
    if mod:
        url = f"https://api.modrinth.com/v2/project/{slug}/version?game_versions=%5B%22{mc}%22%5D&loaders=%5B%22fabric%22%5D"
    return json.loads(check_output(["curl", "-X", "GET", "-s", url]))


def double_check_version(versions, version):
    all_versions = list({v["game_versions"][0] for v in versions})
    all_versions.sort()
    all_versions.reverse()

    if version == "":
        version = choose(list(reversed(all_versions)), "version")

    return version


def init_data(type=None, version=None, modpack=None):
    if type is None:
        types = ["mod", "modpack", "resourcepack", "shader"]
        type = choose(types)

        if type != "modpack":
            modpack = choose(get_modpacks(), "modpack")
            version = get_mcversion(modpack)

    if version is None:
        version = input("mc version [just press enter to search all versions] -> ")

    return {"type": type, "version": version, "modpack": modpack}


def download_from_modrinth(type, modpack, versions, print_downloading=True):
    if len(versions) <= 0:
        return
    v = versions[0]

    # setup file data
    file_info = v["files"][0]
    file_url = file_info["url"]
    file_name = file_info["filename"]

    # modpack stuff
    if type == "modpack":
        tmp_path = f"/tmp/{file_name}"
        download_file(file_url, tmp_path)

        extract(tmp_path, "modpack")
        install_modpack(True)
        return

    # setup target path
    type_dir = f"{INST_DIR}/{modpack}/{DIRS[type]}"
    target = f"{type_dir}/{file_name}"
    if exists(target):
        return

    # download
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


def get_depends(id) -> list:
    data = session.get(f"https://api.modrinth.com/v2/project/{id}/dependencies").json()
    return data.get("projects", [])


def download_depends(file: str, pack: str):
    with ZipFile(file, "r") as z:
        try:
            data: dict = json.loads(z.read("fabric.mod.json"))
            depends = get_depends(data["id"])
        except Exception:
            return
    if len(depends) == 0:
        return

    print(colored("downloading dependencies...", "yellow"))
    for dep in depends:
        if dep["client_side"] != "required":
            continue
        download_from_modrinth(
            "mod", pack, get_versions(dep["slug"], get_mcversion(pack)), False
        )


def download_musthaves(pack=None):
    if pack is None:
        pack = choose(get_modpacks(), "modpack")
    mc = get_mcversion(pack)
    st = time()

    for type in must_haves:
        for slug in must_haves[type]:
            download_from_modrinth(type, pack, get_versions(slug, mc, type == "mod"))

    print(colored(f"downloaded must-haves in {round(time() - st, 2)}s", "green"))


def update_mod(file_entry: dict, new_files: list, pack: str):
    new_files.append(file_entry)
    url = file_entry["downloads"][0]
    pack_index = get_modrinth_index(get_mrpack(pack))
    mc = get_mcversion(pack_index)
    index = pack_index["files"].index(file_entry)
    old_path = pack_index["files"][index]["path"]

    slug = url.split("/data/")[1].split("/")[0]
    versions = get_versions(slug, mc)
    latest_version = None

    for v in versions:
        condition = (
            mc in v["game_versions"] and "fabric" in v["loaders"]
            if url.split(".")[-1] == "jar"
            else True
        )
        if condition:
            latest_version = v
            break
    if latest_version is None:
        return

    files = latest_version["files"][0]
    hashes = files["hashes"]
    latest_sha1 = ["sha1"]
    latest_sha512 = hashes["sha512"]
    latest_path = f"{file_entry['path'].split('/')[0]}/{files['filename']}"
    latest_url = files["url"]

    if latest_url == url:
        print(colored("already up-to-date, skipping", "magenta"))
        return
    print(colored(f"downloading {latest_path}...", "cyan"))

    download_file(latest_url, f"{INST_DIR}/{pack}/{latest_path}")
    download_depends(f"{INST_DIR}/{pack}/{latest_path}", pack)
    try:
        remove(f"{INST_DIR}/{pack}/{old_path}")
    except Exception:
        print(colored("failed to remove old file!", "red"))

    new_files.remove(file_entry)

    file_entry = {
        "path": latest_path,
        "downloads": [latest_url],
        "hashes": {
            "sha1": latest_sha1,
            "sha512": latest_sha512,
        },
    }
    new_files.append(file_entry)


def get_latest_fabric(mc):
    print(colored(f"getting latest fabric version for mc {mc}", "yellow"))
    return session.get(f"https://meta.fabricmc.net/v2/versions/loader/{mc}").json()[0][
        "loader"
    ]["version"]


def install_fabric(mc: str, loader: str = ""):
    print("installing fabric...")
    if not exists("/tmp/fabric-installer.jar"):
        download_file(
            "https://maven.fabricmc.net/net/fabricmc/fabric-installer/1.1.1/fabric-installer-1.1.1.jar",
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


def setup_fabric(mc, fabric, name):
    install_fabric(mc, fabric)
    copytree(
        f"{MC_DIR}/versions/fabric-loader-{fabric}-{mc}",
        f"{MC_DIR}/versions/{name}",
        dirs_exist_ok=True,
    )
    rename(
        f"{MC_DIR}/versions/{name}/fabric-loader-{fabric}-{mc}.json",
        f"{MC_DIR}/versions/{name}/{name}.json",
    )

    copy(
        f"{MC_DIR}/libraries/net/fabricmc/fabric-loader/{fabric}/fabric-loader-{fabric}.jar",
        f"{MC_DIR}/versions/{name}/{name}.jar",
    )


def install_modpack(ask_install_musthaves=False):
    st = time()
    data = get_modrinth_index()
    fabric = data["dependencies"]["fabric-loader"]
    mc = get_mcversion(data)
    name = data["name"]
    files = data["files"]
    dir = f"{INST_DIR}/{name}"
    copytree("/tmp/modpack/overrides/", f"{INST_DIR}/{name}/", dirs_exist_ok=True)
    makedirs(f"{dir}/mods", exist_ok=True)

    setup_fabric(mc, fabric, name)

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
        if num % 20 == 0 and num > 0:
            threads[num - 20].join()
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

    profile_id = uuid4().hex
    timestamp = datetime.now().isoformat() + "Z"

    profiles[profile_id] = {
        "created": timestamp,
        "lastUsed": timestamp,
        "icon": "Grass",
        "name": name,
        "type": "modded",
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

    if ask_install_musthaves and confirm("download must-haves"):
        download_musthaves(name)
