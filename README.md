# Steam Archive Manager

Steam Archive Manager is a Python desktop application designed to help manage installed Steam games and archived game folders.

The program scans the Steam installation folder, lists installed games, displays useful information such as the game ID, installed version, latest available version, compression state, and update status, then allows selected games to be archived or extracted with 7-Zip.

## Features

- Scan installed Steam games from the Steam `steamapps` folder.
- Display game headers when available from Steam's library cache.
- Show the installed build version and latest available build version.
- Detect whether a game folder is archived or extracted.
- Archive selected games with 7-Zip using Ultra compression.
- Extract archived games when needed.
- Launch Steam validation/update for selected games.
- Automatically extract, update, and re-archive games while preserving their original state.
- Right-click a game row to archive, extract, or open its installation folder.
- Save configuration such as window size, Steam path, and language.
- Support English and French interface languages.

## Requirements

- Windows
- Python 3
- Steam installed locally
- 7-Zip installed for archive and extraction features
- Python dependencies listed in `requirements.txt`

## Installation

On Windows, run the setup script once:

```text
Setup Python and Dependencies.cmd
```

The script checks for Python and Pillow, installs the dependencies from `requirements.txt`, and can try to install Python with `winget` if Python is missing.

You can also install the required Python dependencies manually:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python main.py
```

## First Launch

On first launch, the application creates a local configuration file and asks for the Steam installation path.

The Steam path can also be changed later from the menu:

```text
File > Steam path...
```

The interface language can be changed from:

```text
Configuration > Language
```

## Notes

The application uses Steam local files to detect installed games and available build versions. Update operations are launched through Steam, so Steam remains responsible for validating and downloading game updates.

Archived games are detected when their installation folder contains a single archive file with a supported extension such as `.7z`, `.rar`, or `.zip`.

## Project Background

I created this program to keep my Steam library up to date while compressing games I am not currently using to save disk space. The goal is to keep a local physical copy of my games and avoid having to fully download them again later.

This project was created with the help of AI, as I have almost no programming knowledge. It was mainly built for my personal use and will probably not receive updates.

## Warning

This project modifies game installation folders when archiving or extracting games. Make sure you understand what the program does before using it on important data.
