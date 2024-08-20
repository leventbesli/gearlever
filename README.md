# Gear Lever


<p align="center">
  <img width="150" src="data/icons/hicolor/scalable/apps/it.mijorus.gearlever.svg">
</p>

<p align="center"><a href="https://flatstat.mijorus.it/app/it.mijorus.gearlever"  align="center"><img width="150" src="https://img.shields.io/endpoint?url=https://flathub-stats-backend.vercel.app/badges/it.mijorus.gearlever/shields.io.json"></a></p>

##  Support me
<p align="left">
  <img width="600" src="https://github.com/user-attachments/assets/448c0d18-7024-4ca9-aee8-0a11604b0909">
</p>

Do you agree? Here is a link 🍺: <br>
<a href="https://ko-fi.com/mijorus" align="center">
  <img width="250" src="https://mijorus.it/kofi-support.png">
</a>


## Features
- Integrate AppImages into your app menu with **just one click**
- **Drag and drop** files directly from your file manager
- Keep all the AppImages organized in a custom folder
- Open new AppImages directly with Gear lever
- **Manage updates**: keep older versions installed or replace them with the latest release
- Save CLI apps with their executable name automatically
- Modern and Fresh UI

## Download
<a href="https://flathub.org/apps/details/it.mijorus.gearlever" align="center">
  <img width="200" src="https://flathub.org/assets/badges/flathub-badge-i-en.png">
</a>

___

Get the [bundle from github](https://github.com/mijorus/gearlever/releases) (no auto-updates)
```sh
# From your Downloads folder
flatpak install --bundle --user gearlever.flatpak
```

## Changelog
[Open changelog](https://gearlever.mijorus.it/changelog)

## Permissions

- `--talk-name=org.freedesktop.Flatpak`: This permission is required in order to open apps and refresh the system menu when a new app is installed; if the user disables this permission manually (eg. with Flatseal), Gear lever should countinue to work normally, except you would not be able to open apps directly.

## Preview
<p align="center">
  <img width="850" src="https://raw.githubusercontent.com/mijorus/gearlever/master/docs/gearlever3.png">
</p>

## Building and running
- Option #1 (suggested)

  **Open this project with Gnome Builder and press RUN (the play icon on top)**

- Option #2
  ```sh
  # Run the app
  flatpak-builder build/ it.mijorus.gearlever.json --user --force-clean
  flatpak-builder --run build/ it.mijorus.gearlever.json gearlever

  # Install the app
  flatpak-builder build/ it.mijorus.gearlever.json --user --install --force-clean
  ```

## ... And AppImageHub / AppImage Store?
At the moment there are no plans to integrate any type of Hub/Store/Repository into Gear Lever.
Why? Because the existing ones have a very poor selection of apps, and most of these apps are just unofficial ports


