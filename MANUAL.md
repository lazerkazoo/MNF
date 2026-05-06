# MNF User Manual

## When Choosing
- It should look something like this:
```sh
[1] option1
[2] option2
[3] option3
```
- In this example u can choose between option 1 to 3 by typing the respective number. Note that you can also choose by typing the name of the option.
- You can also exit the program by typing "0"

## Must-Haves

Configure default mods, resource packs, and shaders to automatically download when creating new modpacks.

**Features:**
- Automatically installs specified content when creating your own modpacks
- Prompts for optional downloads when installing third-party modpacks
- Manage must-haves through the "Edit Must-Haves" option at startup

---

## Search Modrinth

Browse and download content directly from Modrinth, including mods, modpacks, resource packs, and shader packs.

**Process:**
- Choose between downloading mods, modpacks, resource packs, or shader packs
- **For Modpacks:** Select a Minecraft version (1.21, 1.20.1, etc.), or the system will suggest compatible versions
- **For Other Content:** Select the target modpack, and the system automatically uses that modpack's Minecraft version
- Search for specific content (e.g., Sodium, WorldEdit, etc.)

---

## Edit Must-Haves

Manage your must-have content by adding or removing items.

**Features:**
- Add or remove must-haves interactively
- Choose content type: mods, resource packs, or shader packs
- Add system works similarly to Modrinth search (without requiring modpack selection)
- Remove system allows you to specify items to delete

---

## Modpack Management

### Create Custom Modpack

Create an empty modpack from scratch with your chosen Minecraft version.

**Process:**
1. Enter a name for your modpack
2. Select a Minecraft version
3. System automatically downloads all compatible must-haves

### Update Modpack Mods

Update all mods in an existing modpack to their latest versions.

**Process:**
- Select the target modpack
- Automatically updates the Fabric loader version
- Updates all included mods to compatible versions

### Change Modpack Version

Update a modpack to a different Minecraft version.

**Process:**
1. Select the target modpack
2. Choose the new Minecraft version
3. System updates the version and removes incompatible mods

### Add Must-Haves to Modpack

Retroactively add must-haves to an existing modpack.

**Process:**
1. Select the target modpack
2. System installs all must-haves compatible with that modpack

### Remove Modpack

Delete a modpack and all its contents.

**Process:**
1. Select the modpack to remove
2. Confirm deletion

---

## Remove Mod from Modpack

Remove a specific mod from one of your modpacks.

**Process:**
1. Select the target modpack
2. Choose the mod to delete

---

## Download Modpack from File

Install a modpack from a `.mrpack` file.

**Process:**
1. Select a `.mrpack` file from your Downloads folder
2. System installs the modpack with all contents

---

## Export Modpack

Export a modpack as a `.mrpack` file for sharing with others.

**Process:**
1. Select the modpack to export
2. File is saved to your Downloads folder

---

## Open Manual

Opens this file in the default web browser.
