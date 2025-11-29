from os.path import exists, expanduser

HOME = expanduser("~")
MC_DIR = (
    f"{HOME}/.minecraft"
    if exists(f"{HOME}/.minecraft")
    else "/home/lazerkazoo/.var/app/com.mojang.Minecraft/.minecraft"
    if exists("/home/lazerkazoo/.var/app/com.mojang.Minecraft/.minecraft")
    else ""
)
DOWNLOADS = f"{HOME}/Downloads"
