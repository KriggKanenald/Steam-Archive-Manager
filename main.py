import math
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from bisect import bisect_right
from dataclasses import dataclass
from pathlib import Path


def restart_with_portable_python() -> None:
    if __name__ != "__main__":
        return

    script_path = Path(__file__).resolve()
    portable_python_dir = script_path.with_name("portable-python")
    if not portable_python_dir.is_dir():
        return

    current_executable = Path(sys.executable).resolve()
    portable_executables = [
        portable_python_dir / "python.exe",
        portable_python_dir / "pythonw.exe",
    ]
    resolved_portable_executables = {
        executable.resolve()
        for executable in portable_executables
        if executable.is_file()
    }
    if current_executable in resolved_portable_executables:
        return

    portable_python = portable_python_dir / "pythonw.exe"
    if not portable_python.is_file():
        portable_python = portable_python_dir / "python.exe"
    if not portable_python.is_file():
        return

    try:
        subprocess.Popen(
            [str(portable_python), str(script_path), *sys.argv[1:]],
            cwd=script_path.parent,
        )
    except OSError:
        return

    sys.exit(0)


restart_with_portable_python()

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


APP_TITLE = "Steam Archive Manager"
CONFIG_FILE = Path(__file__).with_name("config.json")
COMPRESSION_IGNORE_FILE = Path(__file__).with_name("compression_ignored_entries.txt")
HEADER_IMAGE_SIZE = (184, 86)
GAME_ROW_HEIGHT = HEADER_IMAGE_SIZE[1]
SECTION_ROW_HEIGHT = 28
VIRTUAL_SCROLL_UNIT_PIXELS = 42
VIRTUAL_RENDER_BUFFER_PIXELS = GAME_ROW_HEIGHT * 2
MOUSEWHEEL_DELTA_UNIT = 120
TOUCHPAD_SCROLL_MULTIPLIER = 1
AUTOSCROLL_INTERVAL_MS = 16
AUTOSCROLL_DEAD_ZONE_PIXELS = 12
AUTOSCROLL_SPEED_DIVISOR = 8
AUTOSCROLL_MAX_PIXELS_PER_TICK = 48
PROGRESS_WINDOW_WIDTH = 540
HEADER_IMAGE_CACHE_LIMIT = 1000
DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = {"en", "fr"}
LANGUAGE_LABELS = {
    "en": "English",
    "fr": "Français",
}
STEAM_UPDATE_POLL_INTERVAL_SECONDS = 5
STEAM_UPDATE_TIMEOUT_SECONDS = 6 * 60 * 60
STEAM_UPDATE_STABLE_POLLS = 2
STEAM_STATE_UPDATE_REQUIRED = 2
COLUMN_SEPARATOR_COLOR = "#dddddd"
TABLE_CELL_PAD_X = 6
TABLE_FLEX_COLUMN = 4
TABLE_FIXED_COLUMNS = (0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
TABLE_DEFAULT_FIXED_COLUMNS_WIDTH = 869
TK_IMAGE_EXTENSIONS = {".gif", ".pgm", ".png", ".ppm"}
HEADER_IMAGE_EXTENSIONS = {".gif", ".jpg", ".jpeg", ".png", ".webp"}
COMPRESSED_GAME_EXTENSIONS = {".7", ".7z", ".rar", ".zip"}
COMPRESSED_STATE = "compressed"
UNCOMPRESSED_STATE = "uncompressed"
UNKNOWN_STATE = "unknown"
UNKNOWN_VERSION = "unknown"
UNAVAILABLE_VERSION = "unavailable"
ACF_VALUE_PATTERN = re.compile(r'^\s*"([^"]+)"\s+"([^"]*)"\s*$')
ACF_OBJECT_KEY_PATTERN = re.compile(r'^\s*"([^"]+)"\s*$')
APPINFO_MAGIC_V41 = 0x07564429
APPINFO_HEADER_SIZE = 16
APPINFO_ENTRY_METADATA_SIZE = 60
BINARY_VDF_OBJECT = 0x00
BINARY_VDF_STRING = 0x01
BINARY_VDF_INT32 = 0x02
BINARY_VDF_FLOAT32 = 0x03
BINARY_VDF_POINTER = 0x04
BINARY_VDF_WSTRING = 0x05
BINARY_VDF_COLOR = 0x06
BINARY_VDF_UINT64 = 0x07
BINARY_VDF_END = 0x08
BINARY_VDF_INT64 = 0x0A
DEFAULT_CONFIG = {
    "window": {
        "width": 900,
        "height": 600,
    },
    "steam_path": "",
    "language": DEFAULT_LANGUAGE,
}

TEXTS = {
    "en": {
        "config_read_error": "The configuration file is unreadable. A default configuration will be used.",
        "menu_file": "File",
        "menu_steam_path": "Steam path...",
        "menu_quit": "Quit",
        "menu_filtering": "Filtering",
        "filter_up_to_date": "Up to date",
        "filter_not_up_to_date": "Not up to date",
        "filter_compressed": "Compressed",
        "filter_uncompressed": "Uncompressed",
        "menu_configuration": "Configuration",
        "menu_language": "Language",
        "button_refresh": "Refresh list",
        "button_compression": "Compress",
        "button_decompression": "Extract",
        "button_update": "Update",
        "button_update_all": "Update all",
        "status_steam_path_missing": "Steam path: not set",
        "status_steam_path": "Steam path: {steam_path}",
        "status_scan_running": "Scanning Steam library: {steam_path}",
        "message_no_steam_path": "No Steam path set.",
        "message_read_steam_error": "Unable to read the Steam folder: {error}",
        "message_scanning_games": "Scanning Steam library...",
        "message_no_games": "No game found in steamapps/common.",
        "message_no_games_after_filter": "No game matches the active filters.",
        "column_header": "Header",
        "column_game_name": "Game name",
        "column_game_id": "Game ID",
        "column_state": "State",
        "column_installed_version": "Installed version",
        "column_latest_version": "Latest available version",
        "column_up_to_date": "Up to date",
        "section_tools": "Tools",
        "state_compressed": "Compressed",
        "state_uncompressed": "Uncompressed",
        "state_unknown": "Unknown",
        "version_unknown": "Unknown",
        "version_unavailable": "Unavailable",
        "message_operation_running": "An operation is already in progress.",
        "message_language_operation_running": "The language cannot be changed while an operation is in progress.",
        "message_no_updates_found": "No game requiring an update was found.",
        "message_select_update": "Select at least one game to update.",
        "message_latest_unknown": (
            "The latest available version is unknown for at least one game. "
            "The program cannot know when Steam has finished.\n\n"
            "Affected game: {game_name}"
        ),
        "message_games_already_up_to_date": "The selected games are already up to date.",
        "message_state_unknown": (
            "The compression state is unknown for at least one game. "
            "The automatic update cannot guarantee its final state.\n\n"
            "Affected game: {game_name}"
        ),
        "action_update": "Update",
        "confirm_update": (
            "Update {game_count} game(s)?\n\n"
            "The program will ask Steam to validate the files and wait for the new version."
        ),
        "confirm_update_compressed": (
            "\n\n{game_count} compressed game(s) will be extracted before the "
            "update, then recompressed afterwards."
        ),
        "confirm_update_uncompressed": (
            "\n\n{game_count} uncompressed game(s) will remain uncompressed."
        ),
        "confirm_update_skipped": "\n\n{game_count} game(s) already up to date will be skipped.",
        "action_compression": "Compression",
        "action_decompression": "Extraction",
        "verb_compress": "compress",
        "verb_decompress": "extract",
        "message_compression_invalid_state": "Compression can only be started on uncompressed games.",
        "message_decompression_invalid_state": "Extraction can only be started on compressed games.",
        "confirm_compression": "Original files will be deleted after the archive has been verified.",
        "confirm_decompression": "The original archive will be deleted after verification and extraction.",
        "message_select_action": "Select at least one game to {action_verb}.",
        "message_mixed_states": "Cannot start {action_name} with games in different states.",
        "confirm_selected_action": "{action_name} of {game_count} selected game(s)?\n\n{details}",
        "status_operation_running": "{action_name} in progress...",
        "context_open_location": "Open location",
        "message_game_folder_missing": "The installation folder cannot be found:\n{folder}",
        "message_open_location_error": "Unable to open the location: {error}",
        "message_action_cancelled": "{action_name} cancelled.",
        "message_games_processed": "{game_count} game(s) processed.",
        "message_games_updated": "{game_count} game(s) updated.",
        "progress_title": "{action_name} in progress",
        "progress_preparation": "0/{game_count} - Preparation",
        "button_cancel": "Cancel",
        "progress_cancel_requested": "Cancellation requested...",
        "seven_zip_help": "Check the 7-Zip window for more information.",
        "seven_zip_background_help": "7-Zip verification running in the background.",
        "steam_wait_help": (
            "Update launched in Steam. Follow the progress in the Steam window. "
            "The program will wait until the installed version is updated."
        ),
        "message_7zip_required": "7-Zip is required for this compressed game.",
        "progress_decompression": "Extraction",
        "progress_game_uncompressed": "Uncompressed game",
        "message_unknown_state_during_update": "Unknown compression state during update: {game_name}",
        "progress_launch_steam": "Launching Steam",
        "progress_wait_steam": "Waiting for Steam",
        "progress_recompression": "Recompression",
        "progress_uncompressed_preserved": "Uncompressed state preserved",
        "message_update_cancelled": (
            "Update cancelled. If Steam has already started an update, it may continue in Steam."
        ),
        "message_steam_protocol_windows_only": "The Steam protocol can only be launched from Windows for now.",
        "message_steam_launch_error": "Unable to launch the Steam update for {game_name}: {error}",
        "message_steam_timeout": (
            "Steam did not finish updating {game_name} before the timeout. "
            "The game is left extracted to avoid recompressing an incomplete installation."
        ),
        "version_current_unknown": "unknown version",
        "message_folder_empty": "The folder for {game_name} is empty.",
        "progress_compression": "Compression",
        "progress_verify_archive": "Archive verification",
        "message_compression_failed": "Compression failed for {game_name}.",
        "message_archive_verify_failed": "Archive verification failed for {game_name}.",
        "message_decompression_failed": "Extraction failed for {game_name}.",
        "message_read_folder_error": "Unable to read folder {folder}: {error}",
        "message_single_archive_required": "The folder for {folder_name} does not contain a single archive.",
        "message_delete_cancelled": "Deletion cancelled: {path} is not inside the game folder.",
        "message_delete_failed": "Unable to delete {path}: {error}",
        "missing_items_separator": " and ",
        "message_7zip_missing": (
            "Cannot start {action_name}: {missing_text} cannot be found.\n\n"
            "Install 7-Zip or add its executables to PATH.\n\n"
            "Checked locations:\n"
            "- PATH: 7z, 7za, 7zG\n"
            "- Folder next to the 7-Zip executable found in PATH\n"
            "- C:\\Program Files\\7-Zip\\7z.exe and 7zG.exe\n"
            "- C:\\Program Files (x86)\\7-Zip\\7z.exe and 7zG.exe"
        ),
        "placeholder_header_missing": "Header\nmissing",
        "placeholder_image_unreadable": "Image\nunreadable",
        "placeholder_pillow_missing": "Pillow\nmissing",
        "message_steam_folder_missing": "The Steam folder cannot be found.",
        "message_steamapps_missing": "The steamapps folder cannot be found.",
        "message_common_missing": "The steamapps/common folder cannot be found.",
        "dialog_steam_path_title": "Steam path",
        "dialog_steam_path_prompt": "Select the Steam installation folder.",
        "dialog_no_path": "No path set",
        "dialog_select_steam_folder": "Select Steam folder",
        "button_select_path": "Select path",
        "button_ask_later": "Set later",
        "message_quit_operation_running": "An operation is in progress. Wait for it to finish before quitting.",
    },
    "fr": {
        "config_read_error": "Le fichier de configuration est illisible. Une configuration par défaut va être utilisée.",
        "menu_file": "Fichier",
        "menu_steam_path": "Chemin d'accès Steam...",
        "menu_quit": "Quitter",
        "menu_filtering": "Filtrage",
        "filter_up_to_date": "À jour",
        "filter_not_up_to_date": "Pas à jour",
        "filter_compressed": "Compressé",
        "filter_uncompressed": "Non compressé",
        "menu_configuration": "Configuration",
        "menu_language": "Langue",
        "button_refresh": "Rafraîchir la liste",
        "button_compression": "Compression",
        "button_decompression": "Extraire",
        "button_update": "Mettre à jour",
        "button_update_all": "Tout mettre à jour",
        "status_steam_path_missing": "Chemin d'accès Steam : non renseigné",
        "status_steam_path": "Chemin d'accès Steam : {steam_path}",
        "status_scan_running": "Analyse de la bibliothèque Steam : {steam_path}",
        "message_no_steam_path": "Aucun chemin d'accès Steam renseigné.",
        "message_read_steam_error": "Impossible de lire le dossier Steam : {error}",
        "message_scanning_games": "Analyse de la bibliothèque Steam...",
        "message_no_games": "Aucun jeu trouvé dans steamapps/common.",
        "message_no_games_after_filter": "Aucun jeu ne correspond aux filtres actifs.",
        "column_header": "Bannière",
        "column_game_name": "Nom du jeu",
        "column_game_id": "ID du jeu",
        "column_state": "État",
        "column_installed_version": "Version installée",
        "column_latest_version": "Dernière version disponible",
        "column_up_to_date": "À jour",
        "section_tools": "Outils",
        "state_compressed": "Compressé",
        "state_uncompressed": "Non compressé",
        "state_unknown": "Inconnu",
        "version_unknown": "Inconnue",
        "version_unavailable": "Indisponible",
        "message_operation_running": "Une opération est déjà en cours.",
        "message_language_operation_running": "La langue ne peut pas être changée pendant une opération.",
        "message_no_updates_found": "Aucun jeu à mettre à jour n'a été trouvé.",
        "message_select_update": "Sélectionnez au moins un jeu à mettre à jour.",
        "message_latest_unknown": (
            "La dernière version disponible est inconnue pour au moins un jeu. "
            "Le programme ne peut pas savoir quand Steam a terminé.\n\n"
            "Jeu concerné : {game_name}"
        ),
        "message_games_already_up_to_date": "Les jeux sélectionnés sont déjà à jour.",
        "message_state_unknown": (
            "L'état de compression est inconnu pour au moins un jeu. "
            "La mise à jour automatique ne peut pas garantir son état final.\n\n"
            "Jeu concerné : {game_name}"
        ),
        "action_update": "Mise à jour",
        "confirm_update": (
            "Mise à jour de {game_count} jeu(x) ?\n\n"
            "Le programme va demander à Steam de valider les fichiers et attendre la nouvelle version."
        ),
        "confirm_update_compressed": (
            "\n\n{game_count} jeu(x) compressé(s) seront extrait(s) "
            "avant la mise à jour, puis recompressé(s) ensuite."
        ),
        "confirm_update_uncompressed": (
            "\n\n{game_count} jeu(x) non compressé(s) resteront non compressé(s)."
        ),
        "confirm_update_skipped": "\n\n{game_count} jeu(x) déjà à jour seront ignoré(s).",
        "action_compression": "Compression",
        "action_decompression": "Extraction",
        "verb_compress": "compresser",
        "verb_decompress": "extraire",
        "message_compression_invalid_state": "La compression ne peut être lancée que sur des jeux non compressés.",
        "message_decompression_invalid_state": "L'extraction ne peut être lancée que sur des jeux compressés.",
        "confirm_compression": "Les fichiers d'origine seront supprimés après vérification de l'archive.",
        "confirm_decompression": "L'archive d'origine sera supprimée après vérification et extraction.",
        "message_select_action": "Sélectionnez au moins un jeu à {action_verb}.",
        "message_mixed_states": "Impossible de lancer l'action {action_name} avec des jeux dans des états différents.",
        "confirm_selected_action": "{action_name} de {game_count} jeu(x) sélectionné(s) ?\n\n{details}",
        "status_operation_running": "{action_name} en cours...",
        "context_open_location": "Ouvrir l'emplacement",
        "message_game_folder_missing": "Le dossier d'installation est introuvable :\n{folder}",
        "message_open_location_error": "Impossible d'ouvrir l'emplacement : {error}",
        "message_action_cancelled": "{action_name} annulée.",
        "message_games_processed": "{game_count} jeu(x) traité(s).",
        "message_games_updated": "{game_count} jeu(x) mis à jour.",
        "progress_title": "{action_name} en cours",
        "progress_preparation": "0/{game_count} - Préparation",
        "button_cancel": "Annuler",
        "progress_cancel_requested": "Annulation demandée...",
        "seven_zip_help": "Consultez la fenêtre 7-Zip pour plus d'informations.",
        "seven_zip_background_help": "Vérification 7-Zip en cours en arrière-plan.",
        "steam_wait_help": (
            "Mise à jour lancée dans Steam. Suivez la progression dans la fenêtre Steam. "
            "Le programme attendra que la version installée soit mise à jour."
        ),
        "message_7zip_required": "7-Zip est requis pour ce jeu compressé.",
        "progress_decompression": "Extraction",
        "progress_game_uncompressed": "Jeu non compressé",
        "message_unknown_state_during_update": "État de compression inconnu pendant la mise à jour : {game_name}",
        "progress_launch_steam": "Lancement Steam",
        "progress_wait_steam": "Attente de Steam",
        "progress_recompression": "Recompression",
        "progress_uncompressed_preserved": "État non compressé conservé",
        "message_update_cancelled": (
            "Mise à jour annulée. Si Steam a déjà commencé une mise à jour, elle peut continuer dans Steam."
        ),
        "message_steam_protocol_windows_only": "Le protocole Steam ne peut être lancé que depuis Windows pour le moment.",
        "message_steam_launch_error": "Impossible de lancer la mise à jour Steam pour {game_name} : {error}",
        "message_steam_timeout": (
            "Steam n'a pas terminé la mise à jour de {game_name} avant le délai maximal. "
            "Le jeu reste extrait pour éviter de recompresser une installation incomplète."
        ),
        "version_current_unknown": "version inconnue",
        "message_folder_empty": "Le dossier de {game_name} est vide.",
        "progress_compression": "Compression",
        "progress_verify_archive": "Vérification de l'archive",
        "message_compression_failed": "Échec de la compression de {game_name}.",
        "message_archive_verify_failed": "La vérification de l'archive de {game_name} a échoué.",
        "message_decompression_failed": "Échec de l'extraction de {game_name}.",
        "message_read_folder_error": "Impossible de lire le dossier {folder} : {error}",
        "message_single_archive_required": "Le dossier de {folder_name} ne contient pas une seule archive.",
        "message_delete_cancelled": "Suppression annulée : {path} n'est pas dans le dossier du jeu.",
        "message_delete_failed": "Impossible de supprimer {path} : {error}",
        "missing_items_separator": " et ",
        "message_7zip_missing": (
            "{action_name} impossible : {missing_text} introuvable.\n\n"
            "Installez 7-Zip ou ajoutez ses exécutables au PATH.\n\n"
            "Emplacements vérifiés :\n"
            "- PATH : 7z, 7za, 7zG\n"
            "- Dossier voisin de l'exécutable 7-Zip trouvé dans le PATH\n"
            "- C:\\Program Files\\7-Zip\\7z.exe et 7zG.exe\n"
            "- C:\\Program Files (x86)\\7-Zip\\7z.exe et 7zG.exe"
        ),
        "placeholder_header_missing": "Bannière\nabsente",
        "placeholder_image_unreadable": "Image\nillisible",
        "placeholder_pillow_missing": "Pillow requis\npour l'image",
        "message_steam_folder_missing": "Le dossier Steam est introuvable.",
        "message_steamapps_missing": "Le dossier steamapps est introuvable.",
        "message_common_missing": "Le dossier steamapps/common est introuvable.",
        "dialog_steam_path_title": "Chemin d'accès Steam",
        "dialog_steam_path_prompt": "Sélectionnez le dossier d'installation de Steam.",
        "dialog_no_path": "Aucun chemin renseigné",
        "dialog_select_steam_folder": "Sélectionner le dossier Steam",
        "button_select_path": "Sélectionner le chemin",
        "button_ask_later": "Renseigner plus tard",
        "message_quit_operation_running": "Une opération est en cours. Attendez la fin avant de quitter.",
    },
}


def normalize_language(language: str | None) -> str:
    if language in SUPPORTED_LANGUAGES:
        return language

    return DEFAULT_LANGUAGE


def get_text(language: str | None, key: str, **values) -> str:
    normalized_language = normalize_language(language)
    text = TEXTS[normalized_language].get(key, TEXTS[DEFAULT_LANGUAGE][key])
    if values:
        return text.format(**values)

    return text


@dataclass
class SteamGame:
    folder: Path
    app_id: str
    app_type: str
    compression_state: str
    name: str
    version: str
    latest_version: str
    steam_update_required: bool
    header_path: Path | None


@dataclass
class SevenZipExecutables:
    cli_path: str
    gui_path: str


class OperationCancelled(Exception):
    pass


class ConfigManager:
    def __init__(self, path: Path):
        self.path = path
        self.steam_path_was_missing = False
        self.data = self.load_or_create()

    def load_or_create(self) -> dict:
        if not self.path.exists():
            self.steam_path_was_missing = True
            data = self.default_config()
            self.save(data)
            return data

        try:
            with self.path.open("r", encoding="utf-8") as config_file:
                data = json.load(config_file)
        except (OSError, json.JSONDecodeError):
            messagebox.showwarning(
                APP_TITLE,
                get_text(DEFAULT_LANGUAGE, "config_read_error"),
            )
            self.steam_path_was_missing = True
            data = self.default_config()
            self.save(data)
            return data

        self.steam_path_was_missing = "steam_path" not in data
        merged = self.merge_defaults(data)
        if self.steam_path_was_missing or merged != data:
            self.save(merged)
        return merged

    def default_config(self) -> dict:
        return {
            "window": DEFAULT_CONFIG["window"].copy(),
            "steam_path": DEFAULT_CONFIG["steam_path"],
            "language": DEFAULT_CONFIG["language"],
        }

    def merge_defaults(self, data: dict) -> dict:
        merged = self.default_config()
        merged["window"] = {
            **DEFAULT_CONFIG["window"],
            **data.get("window", {}),
        }
        merged["steam_path"] = data.get("steam_path", DEFAULT_CONFIG["steam_path"])
        merged["language"] = normalize_language(
            data.get("language", DEFAULT_CONFIG["language"])
        )
        return merged

    def save(self, data: dict | None = None) -> None:
        if data is not None:
            self.data = data

        with self.path.open("w", encoding="utf-8") as config_file:
            json.dump(self.data, config_file, indent=4)

    def save_window_size(self, width: int, height: int) -> None:
        self.data.setdefault("window", {})
        self.data["window"]["width"] = width
        self.data["window"]["height"] = height
        self.save()

    def save_steam_path(self, steam_path: str) -> None:
        self.data["steam_path"] = steam_path
        self.save()

    def save_language(self, language: str) -> None:
        self.data["language"] = normalize_language(language)
        self.save()


class SteamManagerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.config = ConfigManager(CONFIG_FILE)
        self.language = normalize_language(self.config.data.get("language"))
        self.language_var = tk.StringVar(value=self.language)
        self.game_selection = {}
        self.games_by_path = {}
        self.header_images = []
        self.header_image_cache = {}
        self.scanned_games = []
        self.display_items = []
        self.display_item_offsets = []
        self.total_content_height = 0
        self.virtual_scroll_y = 0
        self.table_message = ""
        self.table_body_width = 1
        self.table_fixed_columns_width = TABLE_DEFAULT_FIXED_COLUMNS_WIDTH
        self.table_column_widths = {
            column: 1
            for column in TABLE_FIXED_COLUMNS
        }
        self.visible_row_slots = []
        self.rendered_item_range = None
        self.autoscroll_active = False
        self.autoscroll_anchor_y = 0
        self.autoscroll_current_y = 0
        self.autoscroll_after_id = None
        self.autoscroll_previous_cursor = ""
        self.mousewheel_pixel_remainder = 0.0
        self.refresh_request_id = 0
        self.is_refreshing = False
        self.pending_render_after_id = None
        self.appinfo_cache_lock = threading.Lock()
        self.appinfo_cache_key = None
        self.appinfo_metadata_cache = {}
        self.appinfo_metadata_cached_app_ids = set()
        self.is_operation_running = False
        self.operation_cancel_event = threading.Event()
        self.current_7zip_process = None
        self.process_lock = threading.Lock()
        self.progress_window = None
        self.progress_frame = None
        self.progress_bar = None
        self.progress_percent_label = None
        self.progress_help_label = None
        self.progress_title_var = tk.StringVar(value="")
        self.progress_detail_var = tk.StringVar(value="")
        self.progress_help_var = tk.StringVar(value="")
        self.progress_percent_var = tk.StringVar(value="0%")
        self.progress_value_var = tk.DoubleVar(value=0)
        self.select_all_var = tk.BooleanVar(value=False)
        self.filter_up_to_date_var = tk.BooleanVar(value=True)
        self.filter_not_up_to_date_var = tk.BooleanVar(value=True)
        self.filter_compressed_var = tk.BooleanVar(value=True)
        self.filter_uncompressed_var = tk.BooleanVar(value=True)

        self.root.title(APP_TITLE)
        self.apply_saved_window_size()
        self.create_menu()
        self.create_main_content()
        self.refresh_game_list()

        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)
        if self.config.steam_path_was_missing:
            self.root.after(100, self.show_steam_path_dialog)

    def t(self, key: str, **values) -> str:
        return get_text(self.language, key, **values)

    def change_language(self, language: str) -> None:
        language = normalize_language(language)
        if language == self.language:
            self.language_var.set(language)
            return

        if self.is_operation_running:
            self.language_var.set(self.language)
            messagebox.showwarning(
                APP_TITLE,
                self.t("message_language_operation_running"),
            )
            return

        self.language = language
        self.language_var.set(language)
        self.config.save_language(language)
        self.create_menu()
        self.update_button_texts()
        self.refresh_game_list()

    def apply_saved_window_size(self) -> None:
        window_config = self.config.data.get("window", {})
        width = int(window_config.get("width", DEFAULT_CONFIG["window"]["width"]))
        height = int(window_config.get("height", DEFAULT_CONFIG["window"]["height"]))
        self.root.geometry(f"{width}x{height}")

    def create_menu(self) -> None:
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(
            label=self.t("menu_steam_path"),
            command=self.show_steam_path_dialog,
        )
        file_menu.add_separator()
        file_menu.add_command(label=self.t("menu_quit"), command=self.quit_application)

        filtering_menu = tk.Menu(menu_bar, tearoff=0)
        filtering_menu.add_checkbutton(
            label=self.t("filter_up_to_date"),
            variable=self.filter_up_to_date_var,
            command=self.apply_game_filters,
        )
        filtering_menu.add_checkbutton(
            label=self.t("filter_not_up_to_date"),
            variable=self.filter_not_up_to_date_var,
            command=self.apply_game_filters,
        )
        filtering_menu.add_separator()
        filtering_menu.add_checkbutton(
            label=self.t("filter_compressed"),
            variable=self.filter_compressed_var,
            command=self.apply_game_filters,
        )
        filtering_menu.add_checkbutton(
            label=self.t("filter_uncompressed"),
            variable=self.filter_uncompressed_var,
            command=self.apply_game_filters,
        )

        configuration_menu = tk.Menu(menu_bar, tearoff=0)
        language_menu = tk.Menu(configuration_menu, tearoff=0)
        for language_code in ("en", "fr"):
            language_menu.add_radiobutton(
                label=LANGUAGE_LABELS[language_code],
                variable=self.language_var,
                value=language_code,
                command=lambda selected_language=language_code: self.change_language(
                    selected_language
                ),
            )
        configuration_menu.add_cascade(
            label=self.t("menu_language"),
            menu=language_menu,
        )

        menu_bar.add_cascade(label=self.t("menu_file"), menu=file_menu)
        menu_bar.add_cascade(label=self.t("menu_filtering"), menu=filtering_menu)
        menu_bar.add_cascade(
            label=self.t("menu_configuration"),
            menu=configuration_menu,
        )
        self.root.config(menu=menu_bar)

    def create_main_content(self) -> None:
        self.main_frame = tk.Frame(self.root, padx=12, pady=12)
        self.main_frame.pack(fill="both", expand=True)

        top_bar = tk.Frame(self.main_frame)
        top_bar.pack(fill="x", pady=(0, 8))
        top_bar.columnconfigure(5, weight=1)

        self.refresh_button = tk.Button(
            top_bar,
            text=self.t("button_refresh"),
            command=self.refresh_game_list,
        )
        self.refresh_button.grid(row=0, column=0, sticky="w")

        self.compression_button = tk.Button(
            top_bar,
            text=self.t("button_compression"),
            command=self.compress_selected_games,
        )
        self.compression_button.grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.decompression_button = tk.Button(
            top_bar,
            text=self.t("button_decompression"),
            command=self.decompress_selected_games,
        )
        self.decompression_button.grid(row=0, column=2, sticky="w", padx=(8, 0))

        self.update_button = tk.Button(
            top_bar,
            text=self.t("button_update"),
            command=self.update_selected_games,
        )
        self.update_button.grid(row=0, column=3, sticky="w", padx=(8, 0))

        self.update_all_button = tk.Button(
            top_bar,
            text=self.t("button_update_all"),
            command=self.update_all_games,
        )
        self.update_all_button.grid(row=0, column=4, sticky="w", padx=(8, 0))

        self.path_status_label = tk.Label(top_bar, text="", anchor="e")
        self.path_status_label.grid(row=0, column=5, sticky="e")

        self.table_frame = tk.Frame(self.main_frame, bd=1, relief="solid")
        self.table_frame.pack(fill="both", expand=True)

        header_container = tk.Frame(self.table_frame)
        header_container.pack(fill="x")

        self.header_frame = tk.Frame(header_container)
        self.header_frame.pack(side="left", fill="x", expand=True)
        self.configure_table_columns(self.header_frame)
        self.header_scrollbar_spacer = tk.Frame(
            header_container,
            width=17,
            bg="#eeeeee",
        )
        self.header_scrollbar_spacer.pack(side="right", fill="y")

        body_frame = tk.Frame(self.table_frame)
        body_frame.pack(fill="both", expand=True)

        self.game_canvas = tk.Canvas(body_frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(
            body_frame,
            orient="vertical",
            command=self.on_vertical_scroll,
        )
        self.vertical_scrollbar = scrollbar
        self.header_scrollbar_spacer.configure(width=scrollbar.winfo_reqwidth())

        scrollbar.pack(side="right", fill="y")
        self.game_canvas.pack(side="left", fill="both", expand=True)

        self.rows_frame = tk.Frame(self.game_canvas)
        self.rows_frame.columnconfigure(0, weight=1)
        self.rows_window = self.game_canvas.create_window(
            (0, 0),
            window=self.rows_frame,
            anchor="nw",
        )

        self.game_canvas.bind(
            "<Configure>",
            self.on_canvas_configure,
        )
        self.root.bind_all("<MouseWheel>", self.on_mousewheel, add="+")
        self.root.bind_all("<Button-4>", self.on_mousewheel, add="+")
        self.root.bind_all("<Button-5>", self.on_mousewheel, add="+")
        self.root.bind_all("<Button-2>", self.on_middle_click, add="+")
        self.root.bind_all("<Motion>", self.on_autoscroll_motion, add="+")
        self.root.bind_all("<Escape>", self.cancel_autoscroll, add="+")

    def update_button_texts(self) -> None:
        self.refresh_button.config(text=self.t("button_refresh"))
        self.compression_button.config(text=self.t("button_compression"))
        self.decompression_button.config(text=self.t("button_decompression"))
        self.update_button.config(text=self.t("button_update"))
        self.update_all_button.config(text=self.t("button_update_all"))

    def on_mousewheel(self, event: tk.Event) -> str | None:
        if not self.display_items or not self.is_event_inside_game_canvas(event):
            return None

        scroll_delta = self.get_mousewheel_scroll_delta(event)
        if scroll_delta == 0:
            return None

        self.mousewheel_pixel_remainder += scroll_delta

        pixel_delta = int(self.mousewheel_pixel_remainder)
        if pixel_delta:
            self.mousewheel_pixel_remainder -= pixel_delta
            self.scroll_virtual_pixels(pixel_delta)

        return "break"

    def get_mousewheel_scroll_delta(self, event: tk.Event) -> float:
        event_number = getattr(event, "num", None)
        if event_number == 4:
            return -VIRTUAL_SCROLL_UNIT_PIXELS
        if event_number == 5:
            return VIRTUAL_SCROLL_UNIT_PIXELS

        raw_delta = getattr(event, "delta", 0)
        if raw_delta == 0:
            return 0

        if abs(raw_delta) < MOUSEWHEEL_DELTA_UNIT:
            return -raw_delta * TOUCHPAD_SCROLL_MULTIPLIER

        return -raw_delta / MOUSEWHEEL_DELTA_UNIT * VIRTUAL_SCROLL_UNIT_PIXELS

    def on_middle_click(self, event: tk.Event) -> str | None:
        if self.autoscroll_active:
            self.stop_autoscroll()
            return "break"

        if not self.is_event_inside_game_canvas(event):
            return None

        self.start_autoscroll(event.y_root)
        return "break"

    def on_autoscroll_motion(self, event: tk.Event) -> None:
        if self.autoscroll_active:
            self.autoscroll_current_y = event.y_root

    def cancel_autoscroll(self, event: tk.Event | None = None) -> str | None:
        if not self.autoscroll_active:
            return None

        self.stop_autoscroll()
        return "break"

    def is_event_inside_game_canvas(self, event: tk.Event) -> bool:
        if not hasattr(self, "game_canvas"):
            return False

        canvas_x = self.game_canvas.winfo_rootx()
        canvas_y = self.game_canvas.winfo_rooty()
        canvas_width = self.game_canvas.winfo_width()
        canvas_height = self.game_canvas.winfo_height()
        return (
            canvas_x <= event.x_root < canvas_x + canvas_width
            and canvas_y <= event.y_root < canvas_y + canvas_height
        )

    def start_autoscroll(self, anchor_y: int) -> None:
        if not self.display_items:
            return

        self.autoscroll_active = True
        self.autoscroll_anchor_y = anchor_y
        self.autoscroll_current_y = anchor_y
        self.autoscroll_previous_cursor = self.root.cget("cursor")
        try:
            self.root.configure(cursor="sb_v_double_arrow")
        except tk.TclError:
            pass
        self.run_autoscroll()

    def stop_autoscroll(self) -> None:
        if self.autoscroll_after_id is not None:
            try:
                self.root.after_cancel(self.autoscroll_after_id)
            except tk.TclError:
                pass
            self.autoscroll_after_id = None

        self.autoscroll_active = False
        try:
            self.root.configure(cursor=self.autoscroll_previous_cursor)
        except tk.TclError:
            pass

    def run_autoscroll(self) -> None:
        if not self.autoscroll_active:
            return

        offset = self.autoscroll_current_y - self.autoscroll_anchor_y
        if abs(offset) > AUTOSCROLL_DEAD_ZONE_PIXELS:
            speed = int(offset / AUTOSCROLL_SPEED_DIVISOR)
            if speed == 0:
                speed = 1 if offset > 0 else -1
            speed = max(
                -AUTOSCROLL_MAX_PIXELS_PER_TICK,
                min(AUTOSCROLL_MAX_PIXELS_PER_TICK, speed),
            )
            self.scroll_virtual_pixels(speed)

        self.autoscroll_after_id = self.root.after(
            AUTOSCROLL_INTERVAL_MS,
            self.run_autoscroll,
        )

    def on_canvas_configure(self, event: tk.Event) -> None:
        self.table_body_width = max(1, event.width)
        self.game_canvas.itemconfigure(self.rows_window, width=self.table_body_width)
        self.rows_frame.configure(width=self.table_body_width)
        self.rows_frame.columnconfigure(0, minsize=self.table_body_width)
        self.header_frame.configure(width=self.table_body_width)
        self.configure_table_columns(self.header_frame)
        for slot in self.visible_row_slots:
            slot["frame"].configure(width=self.table_body_width)
            self.configure_table_columns(slot["frame"])
        self.clamp_virtual_scroll()
        self.render_visible_game_rows()
        self.update_virtual_scrollbar()

    def on_vertical_scroll(self, *args) -> None:
        if not args:
            return

        if args[0] == "moveto" and len(args) >= 2:
            try:
                fraction = float(args[1])
            except ValueError:
                return
            max_scroll = self.get_max_virtual_scroll()
            self.virtual_scroll_y = int(max_scroll * fraction)
        elif args[0] == "scroll" and len(args) >= 3:
            try:
                amount = int(args[1])
            except ValueError:
                return
            if args[2] == "pages":
                self.scroll_virtual_pixels(
                    amount * max(1, self.game_canvas.winfo_height() - GAME_ROW_HEIGHT)
                )
                return
            self.scroll_virtual_pixels(amount * VIRTUAL_SCROLL_UNIT_PIXELS)
            return

        self.clamp_virtual_scroll()
        self.render_visible_game_rows()
        self.update_virtual_scrollbar()

    def scroll_virtual_pixels(self, pixel_delta: int) -> None:
        self.virtual_scroll_y += pixel_delta
        self.clamp_virtual_scroll()
        self.render_visible_game_rows()
        self.update_virtual_scrollbar()

    def clamp_virtual_scroll(self) -> None:
        self.virtual_scroll_y = max(
            0,
            min(self.virtual_scroll_y, self.get_max_virtual_scroll()),
        )

    def get_max_virtual_scroll(self) -> int:
        return max(0, self.total_content_height - self.game_canvas.winfo_height())

    def update_virtual_scrollbar(self) -> None:
        if not hasattr(self, "vertical_scrollbar"):
            return

        canvas_height = max(1, self.game_canvas.winfo_height())
        if self.total_content_height <= canvas_height:
            self.vertical_scrollbar.set(0, 1)
            return

        first = self.virtual_scroll_y / self.total_content_height
        last = (self.virtual_scroll_y + canvas_height) / self.total_content_height
        self.vertical_scrollbar.set(
            max(0, min(1, first)),
            max(0, min(1, last)),
        )

    def refresh_game_list(self, preserve_scroll: bool = False) -> None:
        self.refresh_request_id += 1
        refresh_request_id = self.refresh_request_id
        preserved_scroll_y = self.virtual_scroll_y if preserve_scroll else 0
        self.cancel_pending_game_render()

        steam_path_value = self.config.data.get("steam_path", "")
        if not steam_path_value:
            self.scanned_games = []
            self.clear_game_table()
            self.add_table_header()
            self.path_status_label.config(text=self.t("status_steam_path_missing"))
            self.show_game_message(self.t("message_no_steam_path"))
            self.complete_game_refresh(refresh_request_id)
            return

        steam_path = Path(steam_path_value)
        self.is_refreshing = True
        self.set_operation_controls_enabled(False)
        self.path_status_label.config(
            text=self.t("status_scan_running", steam_path=steam_path)
        )
        if not self.rows_frame.winfo_children():
            self.show_loading_game_message()

        scan_thread = threading.Thread(
            target=self.run_game_scan_worker,
            args=(refresh_request_id, steam_path, preserved_scroll_y),
            daemon=True,
        )
        scan_thread.start()

    def run_game_scan_worker(
        self,
        refresh_request_id: int,
        steam_path: Path,
        preserved_scroll_y: int,
    ) -> None:
        try:
            games = self.find_installed_games(steam_path)
            error_message = ""
        except FileNotFoundError as error:
            games = []
            error_message = str(error)
        except OSError as error:
            games = []
            error_message = self.t("message_read_steam_error", error=error)

        self.schedule_main_thread_callback(
            lambda: self.finish_game_scan(
                refresh_request_id,
                games,
                error_message,
                preserved_scroll_y,
            )
        )

    def schedule_main_thread_callback(self, callback) -> None:
        try:
            self.root.after(0, callback)
        except tk.TclError:
            pass

    def finish_game_scan(
        self,
        refresh_request_id: int,
        games: list[SteamGame],
        error_message: str,
        preserved_scroll_y: int = 0,
    ) -> None:
        if refresh_request_id != self.refresh_request_id:
            return

        self.scanned_games = games
        self.clear_game_table()
        self.add_table_header()

        if error_message:
            self.show_game_message(error_message)
            self.complete_game_refresh(refresh_request_id)
            return

        if not games:
            self.show_game_message(self.t("message_no_games"))
            self.complete_game_refresh(refresh_request_id)
            return

        display_items = self.get_game_display_items(games)
        if not display_items:
            self.show_game_message(self.t("message_no_games_after_filter"))
            self.complete_game_refresh(refresh_request_id)
            return

        self.set_virtual_display_items(display_items, preserved_scroll_y)
        self.complete_game_refresh(refresh_request_id)

    def clear_game_table(self) -> None:
        self.stop_autoscroll()
        for widget in self.rows_frame.winfo_children():
            widget.destroy()

        self.visible_row_slots = []
        self.rendered_item_range = None
        self.display_items = []
        self.display_item_offsets = []
        self.total_content_height = 0
        self.virtual_scroll_y = 0
        self.table_message = ""
        self.game_selection.clear()
        self.games_by_path.clear()
        self.header_images.clear()
        self.select_all_var.set(False)
        self.game_canvas.coords(self.rows_window, 0, 0)
        self.update_virtual_scrollbar()

    def get_game_display_items(self, games: list[SteamGame]) -> list[tuple[str, object]]:
        filtered_games = [
            game
            for game in games
            if self.game_matches_active_filters(game)
        ]
        games_only = [game for game in filtered_games if not self.is_tool(game)]
        tools = [game for game in filtered_games if self.is_tool(game)]
        display_items: list[tuple[str, object]] = [
            ("game", game) for game in games_only
        ]
        if tools:
            display_items.append(("section", self.t("section_tools")))
            display_items.extend(("game", tool) for tool in tools)

        return display_items

    def apply_game_filters(self) -> None:
        if not self.scanned_games:
            return

        self.clear_game_table()
        display_items = self.get_game_display_items(self.scanned_games)
        if not display_items:
            self.show_game_message(self.t("message_no_games_after_filter"))
            return

        self.set_virtual_display_items(display_items)

    def game_matches_active_filters(self, game: SteamGame) -> bool:
        is_up_to_date = self.is_game_up_to_date(game)
        if is_up_to_date and not self.filter_up_to_date_var.get():
            return False
        if not is_up_to_date and not self.filter_not_up_to_date_var.get():
            return False

        compression_state = game.compression_state.strip().casefold()
        if compression_state == COMPRESSED_STATE:
            return self.filter_compressed_var.get()
        if compression_state == UNCOMPRESSED_STATE:
            return self.filter_uncompressed_var.get()

        return (
            self.filter_compressed_var.get()
            and self.filter_uncompressed_var.get()
        )

    def set_virtual_display_items(
        self,
        display_items: list[tuple[str, object]],
        scroll_y: int = 0,
    ) -> None:
        self.display_items = display_items
        self.display_item_offsets = []
        self.total_content_height = 0
        self.virtual_scroll_y = max(0, scroll_y)
        self.table_message = ""

        for item in self.display_items:
            self.display_item_offsets.append(self.total_content_height)
            self.total_content_height += self.get_display_item_height(item)

            item_type, item_value = item
            if item_type == "game":
                game = item_value
                game_path = str(game.folder)
                self.games_by_path[game_path] = game
                self.game_selection[game_path] = tk.BooleanVar(value=False)

        self.clamp_virtual_scroll()
        self.render_visible_game_rows()
        self.update_select_all_state()
        self.update_virtual_scrollbar()

    def get_display_item_height(self, display_item: tuple[str, object]) -> int:
        item_type, _ = display_item
        if item_type == "section":
            return SECTION_ROW_HEIGHT

        return GAME_ROW_HEIGHT

    def render_visible_game_rows(self) -> None:
        if not hasattr(self, "rows_frame"):
            return

        if not self.display_items:
            self.game_canvas.coords(self.rows_window, 0, 0)
            if self.rendered_item_range is not None:
                self.hide_unused_row_slots(0)
                self.rendered_item_range = None
            if self.table_message:
                for widget in self.rows_frame.winfo_children():
                    widget.destroy()
                self.visible_row_slots = []
                self.add_game_message_label(self.table_message)
            return

        if self.table_message:
            for widget in self.rows_frame.winfo_children():
                widget.destroy()
            self.visible_row_slots = []
            self.rendered_item_range = None
            self.table_message = ""

        canvas_height = max(1, self.game_canvas.winfo_height())
        render_top = max(0, self.virtual_scroll_y - VIRTUAL_RENDER_BUFFER_PIXELS)
        render_bottom = min(
            self.total_content_height,
            self.virtual_scroll_y + canvas_height + VIRTUAL_RENDER_BUFFER_PIXELS,
        )
        start_index = max(
            0,
            bisect_right(self.display_item_offsets, render_top) - 1,
        )
        start_y = self.display_item_offsets[start_index] - self.virtual_scroll_y

        end_index = start_index
        while (
            end_index < len(self.display_items)
            and self.display_item_offsets[end_index] < render_bottom
        ):
            end_index += 1
        if end_index < len(self.display_items):
            end_index += 1

        item_range = (start_index, end_index)
        if item_range == self.rendered_item_range:
            self.game_canvas.coords(self.rows_window, 0, start_y)
            return

        required_slots = end_index - start_index
        self.ensure_row_slot_count(required_slots)
        self.hide_unused_row_slots(required_slots)

        for row_index, item_index in enumerate(range(start_index, end_index)):
            item_type, item_value = self.display_items[item_index]
            if item_type == "section":
                self.show_section_row_slot(
                    self.visible_row_slots[row_index],
                    str(item_value),
                    row_index,
                )
            else:
                self.show_game_row_slot(
                    self.visible_row_slots[row_index],
                    item_value,
                    row_index,
                    item_index,
                )

        self.rendered_item_range = item_range
        self.game_canvas.coords(self.rows_window, 0, start_y)

    def update_table_fixed_columns_width_from_header(self) -> None:
        if not hasattr(self, "header_frame"):
            return

        column_widths = {}
        for widget in self.header_frame.grid_slaves(row=0):
            grid_info = widget.grid_info()
            try:
                column = int(grid_info.get("column", -1))
                columnspan = int(grid_info.get("columnspan", 1))
            except (TypeError, ValueError):
                continue

            if columnspan != 1 or column not in TABLE_FIXED_COLUMNS:
                continue

            column_widths[column] = max(
                column_widths.get(column, 0),
                widget.winfo_reqwidth(),
            )

        column_widths[2] = max(column_widths.get(2, 0), HEADER_IMAGE_SIZE[0])
        fixed_columns_width = sum(column_widths.values())
        if fixed_columns_width > 0:
            self.table_column_widths.update(column_widths)
            self.table_fixed_columns_width = fixed_columns_width

    def get_table_flex_column_width(self) -> int:
        return max(1, self.table_body_width - self.table_fixed_columns_width)

    def configure_table_columns(self, frame: tk.Widget) -> None:
        for column in TABLE_FIXED_COLUMNS:
            frame.columnconfigure(
                column,
                minsize=self.table_column_widths.get(column, 1),
                weight=0,
            )
        frame.columnconfigure(
            TABLE_FLEX_COLUMN,
            minsize=self.get_table_flex_column_width(),
            weight=0,
        )

    def ensure_row_slot_count(self, required_slots: int) -> None:
        while len(self.visible_row_slots) < required_slots:
            self.visible_row_slots.append(
                self.create_row_slot(len(self.visible_row_slots))
            )

    def create_row_slot(self, row_index: int) -> dict:
        slot = {
            "game": None,
            "photo": None,
            "type": None,
        }

        row_frame = tk.Frame(
            self.rows_frame,
            width=self.table_body_width,
            height=GAME_ROW_HEIGHT,
        )
        row_frame.grid(
            row=row_index,
            column=0,
            sticky="ew",
            padx=0,
            pady=0,
        )
        row_frame.grid_propagate(False)
        row_frame.rowconfigure(0, weight=1)
        self.configure_table_columns(row_frame)
        row_frame.bind(
            "<Button-1>",
            lambda event, row_slot=slot: self.toggle_row_slot_selection(row_slot),
        )
        row_frame.bind(
            "<Button-3>",
            lambda event, row_slot=slot: self.show_row_slot_context_menu(
                row_slot,
                event,
            ),
        )

        slot["frame"] = row_frame

        checkbox = tk.Checkbutton(
            row_frame,
            command=self.update_select_all_state,
            padx=TABLE_CELL_PAD_X,
        )
        checkbox.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        checkbox.bind(
            "<Button-3>",
            lambda event, row_slot=slot: self.show_row_slot_context_menu(
                row_slot,
                event,
            ),
        )
        slot["checkbox"] = checkbox

        slot["separator_1"] = self.create_slot_separator(row_frame, 1, slot)

        image_cell = tk.Frame(
            row_frame,
            width=HEADER_IMAGE_SIZE[0],
            height=HEADER_IMAGE_SIZE[1],
        )
        image_cell.grid(row=0, column=2, sticky="nsw", padx=0, pady=0)
        image_cell.grid_propagate(False)
        self.bind_row_slot_widget(image_cell, slot)
        slot["image_cell"] = image_cell

        image_label = tk.Label(image_cell)
        self.bind_row_slot_widget(image_label, slot)
        slot["image_label"] = image_label

        placeholder_label = tk.Label(
            image_cell,
            justify="center",
            bg="#eeeeee",
            fg="#777777",
        )
        self.bind_row_slot_widget(placeholder_label, slot)
        slot["placeholder_label"] = placeholder_label

        slot["separator_3"] = self.create_slot_separator(row_frame, 3, slot)
        slot["name_label"] = self.create_slot_label(
            row_frame,
            4,
            slot,
            width=1,
            sticky="nsew",
        )
        slot["separator_5"] = self.create_slot_separator(row_frame, 5, slot)
        slot["app_id_label"] = self.create_slot_label(row_frame, 6, slot, width=12)
        slot["separator_7"] = self.create_slot_separator(row_frame, 7, slot)
        slot["state_label"] = self.create_slot_label(row_frame, 8, slot, width=14)
        slot["separator_9"] = self.create_slot_separator(row_frame, 9, slot)
        slot["version_label"] = self.create_slot_label(row_frame, 10, slot, width=18)
        slot["separator_11"] = self.create_slot_separator(row_frame, 11, slot)
        slot["latest_label"] = self.create_slot_label(row_frame, 12, slot, width=28)
        slot["separator_13"] = self.create_slot_separator(row_frame, 13, slot)
        slot["update_label"] = self.create_slot_label(
            row_frame,
            14,
            slot,
            width=8,
            sticky="nsew",
            anchor="center",
            font=("Arial", 14, "bold"),
        )

        section_frame = tk.Frame(row_frame, bg="#dddddd", padx=8, pady=6)
        section_frame.grid(row=0, column=0, columnspan=15, sticky="nsew")
        section_frame.columnconfigure(0, weight=1)
        section_frame.columnconfigure(2, weight=1)
        tk.Frame(section_frame, height=1, bg="#bdbdbd").grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 8),
        )
        section_label = tk.Label(
            section_frame,
            bg="#dddddd",
            fg="#444444",
        )
        section_label.grid(row=0, column=1)
        tk.Frame(section_frame, height=1, bg="#bdbdbd").grid(
            row=0,
            column=2,
            sticky="ew",
            padx=(8, 0),
        )
        section_frame.grid_remove()
        slot["section_frame"] = section_frame
        slot["section_label"] = section_label

        return slot

    def create_slot_separator(
        self,
        parent: tk.Widget,
        column: int,
        slot: dict,
    ) -> tk.Frame:
        separator = tk.Frame(parent, width=1, bg=COLUMN_SEPARATOR_COLOR)
        separator.grid(row=0, column=column, sticky="ns", padx=0, pady=0)
        self.bind_row_slot_widget(separator, slot)
        return separator

    def create_slot_label(
        self,
        parent: tk.Widget,
        column: int,
        slot: dict,
        width: int | None = None,
        sticky: str = "nsw",
        anchor: str = "w",
        font=None,
    ) -> tk.Label:
        label_options = {
            "anchor": anchor,
            "padx": TABLE_CELL_PAD_X,
        }
        if width is not None:
            label_options["width"] = width
        if font is not None:
            label_options["font"] = font

        label = tk.Label(parent, **label_options)
        label.grid(row=0, column=column, sticky=sticky, padx=0, pady=0)
        self.bind_row_slot_widget(label, slot)
        return label

    def bind_row_slot_widget(self, widget: tk.Widget, slot: dict) -> None:
        widget.bind(
            "<Button-1>",
            lambda event, row_slot=slot: self.toggle_row_slot_selection(row_slot),
        )
        widget.bind(
            "<Button-3>",
            lambda event, row_slot=slot: self.show_row_slot_context_menu(
                row_slot,
                event,
            ),
        )

    def hide_unused_row_slots(self, used_slots: int) -> None:
        for slot in self.visible_row_slots[used_slots:]:
            slot["frame"].grid_remove()
            slot["game"] = None
            slot["photo"] = None
            slot["type"] = None

    def show_section_row_slot(
        self,
        slot: dict,
        title: str,
        row_index: int,
    ) -> None:
        slot["game"] = None
        slot["photo"] = None
        slot["type"] = "section"

        row_frame = slot["frame"]
        self.configure_table_columns(row_frame)
        row_frame.configure(
            width=self.table_body_width,
            height=SECTION_ROW_HEIGHT,
            bg="#dddddd",
        )
        row_frame.grid(row=row_index, column=0, sticky="ew", padx=0, pady=0)
        slot["section_label"].configure(text=title)
        slot["section_frame"].grid()

        for widget_name in self.get_game_slot_widget_names():
            slot[widget_name].grid_remove()
        slot["image_label"].place_forget()
        slot["placeholder_label"].place_forget()

    def show_game_row_slot(
        self,
        slot: dict,
        game: SteamGame,
        row_index: int,
        visual_index: int,
    ) -> None:
        row_background = "#ffffff" if visual_index % 2 == 0 else "#f7f7f7"
        game_path = str(game.folder)
        selected = self.game_selection.get(game_path)
        if selected is None:
            selected = tk.BooleanVar(value=False)
            self.game_selection[game_path] = selected
        self.games_by_path[game_path] = game

        slot["game"] = game
        slot["type"] = "game"
        slot["section_frame"].grid_remove()

        row_frame = slot["frame"]
        self.configure_table_columns(row_frame)
        row_frame.configure(
            width=self.table_body_width,
            height=GAME_ROW_HEIGHT,
            bg=row_background,
        )
        row_frame.grid(row=row_index, column=0, sticky="ew", padx=0, pady=0)

        game_slot_widget_names = self.get_game_slot_widget_names()
        for widget_name in game_slot_widget_names:
            slot[widget_name].grid()

        slot["checkbox"].configure(
            variable=selected,
            command=self.update_select_all_state,
            bg=row_background,
            activebackground=row_background,
        )
        slot["image_cell"].configure(bg=row_background)
        slot["image_label"].configure(bg=row_background)

        photo = self.load_header_image(game.header_path)
        slot["photo"] = photo
        if photo is not None:
            slot["image_label"].configure(image=photo)
            slot["image_label"].place(relx=0.5, rely=0.5, anchor="center")
            slot["placeholder_label"].place_forget()
        else:
            slot["image_label"].place_forget()
            slot["image_label"].configure(image="")
            placeholder_text = self.t("placeholder_header_missing")
            if game.header_path is not None:
                if self.header_image_requires_pillow(game.header_path):
                    placeholder_text = self.t("placeholder_pillow_missing")
                else:
                    placeholder_text = self.t("placeholder_image_unreadable")
            slot["placeholder_label"].configure(text=placeholder_text)
            slot["placeholder_label"].place(
                relx=0.5,
                rely=0.5,
                relwidth=1,
                relheight=1,
                anchor="center",
            )

        slot["name_label"].configure(text=game.name)
        slot["app_id_label"].configure(text=game.app_id)
        slot["state_label"].configure(
            text=self.get_compression_state_display(game.compression_state)
        )
        slot["version_label"].configure(text=self.get_version_display(game.version))
        slot["latest_label"].configure(
            text=self.get_version_display(game.latest_version)
        )

        update_symbol, update_color = self.get_update_status_display(game)
        slot["update_label"].configure(text=update_symbol, fg=update_color)

        for widget_name in (
            "name_label",
            "app_id_label",
            "state_label",
            "version_label",
            "latest_label",
            "update_label",
        ):
            slot[widget_name].configure(bg=row_background)

    def get_game_slot_widget_names(self) -> tuple[str, ...]:
        return (
            "checkbox",
            "separator_1",
            "image_cell",
            "separator_3",
            "name_label",
            "separator_5",
            "app_id_label",
            "separator_7",
            "state_label",
            "separator_9",
            "version_label",
            "separator_11",
            "latest_label",
            "separator_13",
            "update_label",
        )

    def toggle_row_slot_selection(self, slot: dict) -> str:
        game = slot.get("game")
        if game is None:
            return "break"

        game_path = str(game.folder)
        selected = self.game_selection.get(game_path)
        if selected is None:
            selected = tk.BooleanVar(value=False)
            self.game_selection[game_path] = selected

        selected.set(not selected.get())
        self.update_select_all_state()
        return "break"

    def show_row_slot_context_menu(self, slot: dict, event: tk.Event) -> str:
        game = slot.get("game")
        if game is None:
            return "break"

        return self.show_game_context_menu(event, game)

    def cancel_pending_game_render(self) -> None:
        if self.pending_render_after_id is None:
            return

        try:
            self.root.after_cancel(self.pending_render_after_id)
        except tk.TclError:
            pass
        self.pending_render_after_id = None

    def complete_game_refresh(self, refresh_request_id: int) -> None:
        if refresh_request_id != self.refresh_request_id:
            return

        self.is_refreshing = False
        steam_path_value = self.config.data.get("steam_path", "")
        if steam_path_value:
            self.path_status_label.config(
                text=self.t("status_steam_path", steam_path=Path(steam_path_value))
            )
        else:
            self.path_status_label.config(text=self.t("status_steam_path_missing"))

        if not self.is_operation_running:
            self.set_operation_controls_enabled(True)

    def show_loading_game_message(self) -> None:
        self.clear_game_table()
        self.add_table_header()
        self.show_game_message(self.t("message_scanning_games"))

    def add_table_header(self) -> None:
        for widget in self.header_frame.winfo_children():
            widget.destroy()

        header_background = "#eeeeee"
        row_index = 0

        tk.Checkbutton(
            self.header_frame,
            variable=self.select_all_var,
            command=self.toggle_all_games,
            bg=header_background,
            activebackground=header_background,
            padx=TABLE_CELL_PAD_X,
        ).grid(
            row=row_index,
            column=0,
            sticky="nsew",
            padx=0,
            pady=0,
        )
        self.add_column_separator(self.header_frame, row_index, 1)
        self.add_cell_label(
            self.header_frame,
            row_index,
            2,
            self.t("column_header"),
            header_background,
            width=24,
        )
        self.add_column_separator(self.header_frame, row_index, 3)
        self.add_cell_label(
            self.header_frame,
            row_index,
            4,
            self.t("column_game_name"),
            header_background,
            width=1,
            sticky="nsew",
        )
        self.add_column_separator(self.header_frame, row_index, 5)
        self.add_cell_label(
            self.header_frame,
            row_index,
            6,
            self.t("column_game_id"),
            header_background,
            width=12,
        )
        self.add_column_separator(self.header_frame, row_index, 7)
        self.add_cell_label(
            self.header_frame,
            row_index,
            8,
            self.t("column_state"),
            header_background,
            width=14,
        )
        self.add_column_separator(self.header_frame, row_index, 9)
        self.add_cell_label(
            self.header_frame,
            row_index,
            10,
            self.t("column_installed_version"),
            header_background,
            width=18,
        )
        self.add_column_separator(self.header_frame, row_index, 11)
        self.add_cell_label(
            self.header_frame,
            row_index,
            12,
            self.t("column_latest_version"),
            header_background,
            width=28,
        )
        self.add_column_separator(self.header_frame, row_index, 13)
        self.add_cell_label(
            self.header_frame,
            row_index,
            14,
            self.t("column_up_to_date"),
            header_background,
            width=8,
            anchor="center",
        )
        self.update_table_fixed_columns_width_from_header()
        self.configure_table_columns(self.header_frame)

    def is_tool(self, game: SteamGame) -> bool:
        return game.app_type.casefold() == "tool"

    def add_section_separator(self, title: str, row_index: int) -> None:
        separator = tk.Frame(self.rows_frame, bg="#dddddd", padx=8, pady=6)
        separator.grid(row=row_index, column=0, columnspan=15, sticky="ew")
        separator.columnconfigure(0, weight=1)
        separator.columnconfigure(2, weight=1)

        tk.Frame(separator, height=1, bg="#bdbdbd").grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 8),
        )
        tk.Label(
            separator,
            text=title,
            bg="#dddddd",
            fg="#444444",
        ).grid(row=0, column=1)
        tk.Frame(separator, height=1, bg="#bdbdbd").grid(
            row=0,
            column=2,
            sticky="ew",
            padx=(8, 0),
        )

    def toggle_all_games(self) -> None:
        select_all = self.select_all_var.get()
        for selected in self.game_selection.values():
            selected.set(select_all)

    def update_select_all_state(self) -> None:
        if not self.game_selection:
            self.select_all_var.set(False)
            return

        self.select_all_var.set(
            all(selected.get() for selected in self.game_selection.values())
        )

    def compress_selected_games(self) -> None:
        self.start_selected_operation("compression", self.get_selected_games())

    def decompress_selected_games(self) -> None:
        self.start_selected_operation("decompression", self.get_selected_games())

    def update_selected_games(self) -> None:
        self.start_update_operation(self.get_selected_games(), automatic_detection=False)

    def update_all_games(self) -> None:
        steam_path = self.get_valid_steam_path()
        if steam_path is None:
            return

        games = [
            game
            for game in (self.scanned_games or self.games_by_path.values())
            if not self.is_tool(game)
        ]
        self.refresh_games_metadata(games, steam_path)
        games_to_update = [
            game
            for game in games
            if game.compression_state in {COMPRESSED_STATE, UNCOMPRESSED_STATE}
            and self.has_known_latest_version(game)
            and not self.is_game_up_to_date(game)
        ]

        self.start_update_operation(
            games_to_update,
            automatic_detection=True,
            steam_path=steam_path,
        )

    def start_update_operation(
        self,
        selected_games: list[SteamGame],
        automatic_detection: bool,
        steam_path: Path | None = None,
    ) -> None:
        if self.is_operation_running:
            messagebox.showwarning(
                APP_TITLE,
                self.t("message_operation_running"),
            )
            return

        if steam_path is None:
            steam_path = self.get_valid_steam_path()
            if steam_path is None:
                return

        if not selected_games:
            if automatic_detection:
                messagebox.showinfo(
                    APP_TITLE,
                    self.t("message_no_updates_found"),
                )
            else:
                messagebox.showwarning(
                    APP_TITLE,
                    self.t("message_select_update"),
                )
            return

        self.refresh_games_metadata(selected_games, steam_path)

        unknown_latest_games = [
            game.name
            for game in selected_games
            if not self.has_known_latest_version(game)
        ]
        if unknown_latest_games:
            messagebox.showerror(
                APP_TITLE,
                self.t("message_latest_unknown", game_name=unknown_latest_games[0]),
            )
            return

        games_to_update = [
            game
            for game in selected_games
            if not self.is_game_up_to_date(game)
        ]
        skipped_count = len(selected_games) - len(games_to_update)
        if not games_to_update:
            messagebox.showinfo(
                APP_TITLE,
                self.t("message_games_already_up_to_date"),
            )
            return

        unsupported_state_games = [
            game.name
            for game in games_to_update
            if game.compression_state not in {COMPRESSED_STATE, UNCOMPRESSED_STATE}
        ]
        if unsupported_state_games:
            messagebox.showerror(
                APP_TITLE,
                self.t("message_state_unknown", game_name=unsupported_state_games[0]),
            )
            return

        initial_compression_states = {
            str(game.folder): game.compression_state
            for game in games_to_update
        }
        compressed_count = sum(
            1
            for state in initial_compression_states.values()
            if state == COMPRESSED_STATE
        )
        uncompressed_count = len(games_to_update) - compressed_count
        seven_zip_executables = None
        if compressed_count:
            try:
                seven_zip_executables = self.find_7zip_executables(
                    self.t("action_update")
                )
            except FileNotFoundError as error:
                messagebox.showerror(APP_TITLE, str(error))
                return

        confirm_message = self.t(
            "confirm_update",
            game_count=len(games_to_update),
        )
        if compressed_count:
            confirm_message += self.t(
                "confirm_update_compressed",
                game_count=compressed_count,
            )
        if uncompressed_count:
            confirm_message += self.t(
                "confirm_update_uncompressed",
                game_count=uncompressed_count,
            )
        if skipped_count:
            confirm_message += self.t(
                "confirm_update_skipped",
                game_count=skipped_count,
            )

        confirm = messagebox.askyesno(APP_TITLE, confirm_message)
        if not confirm:
            return

        self.start_steam_update_operation(
            games_to_update,
            steam_path,
            seven_zip_executables,
            initial_compression_states,
        )

    def start_selected_operation(
        self,
        operation: str,
        selected_games: list[SteamGame],
    ) -> None:
        if self.is_operation_running:
            messagebox.showwarning(
                APP_TITLE,
                self.t("message_operation_running"),
            )
            return

        if operation == "compression":
            action_title = self.t("action_compression")
            action_verb = self.t("verb_compress")
            required_state = UNCOMPRESSED_STATE
            invalid_state_message = self.t("message_compression_invalid_state")
            confirm_message = self.t("confirm_compression")
        else:
            action_title = self.t("action_decompression")
            action_verb = self.t("verb_decompress")
            required_state = COMPRESSED_STATE
            invalid_state_message = self.t("message_decompression_invalid_state")
            confirm_message = self.t("confirm_decompression")

        if not selected_games:
            messagebox.showwarning(
                APP_TITLE,
                self.t("message_select_action", action_verb=action_verb),
            )
            return

        for game in selected_games:
            game.compression_state = self.get_compression_state(
                game.folder,
                game.app_id,
            )

        selected_states = {game.compression_state for game in selected_games}
        if len(selected_states) > 1:
            messagebox.showerror(
                APP_TITLE,
                self.t(
                    "message_mixed_states",
                    action_name=action_title.casefold(),
                ),
            )
            return

        selected_state = next(iter(selected_states))
        if selected_state != required_state:
            messagebox.showerror(
                APP_TITLE,
                invalid_state_message,
            )
            return

        try:
            seven_zip_executables = self.find_7zip_executables(action_title)
        except FileNotFoundError as error:
            messagebox.showerror(APP_TITLE, str(error))
            return

        game_count = len(selected_games)
        confirm = messagebox.askyesno(
            APP_TITLE,
            self.t(
                "confirm_selected_action",
                action_name=action_title,
                game_count=game_count,
                details=confirm_message,
            ),
        )
        if not confirm:
            return

        self.start_file_operation(
            operation,
            action_title,
            selected_games,
            seven_zip_executables,
        )

    def start_file_operation(
        self,
        operation: str,
        action_title: str,
        selected_games: list[SteamGame],
        seven_zip_executables: SevenZipExecutables,
    ) -> None:
        self.operation_cancel_event.clear()
        self.set_operation_controls_enabled(False)
        self.is_operation_running = True
        self.path_status_label.config(
            text=self.t("status_operation_running", action_name=action_title)
        )
        self.show_progress_window(action_title, len(selected_games))

        operation_thread = threading.Thread(
            target=self.run_file_operation_worker,
            args=(operation, action_title, selected_games, seven_zip_executables),
            daemon=True,
        )
        operation_thread.start()

    def start_steam_update_operation(
        self,
        selected_games: list[SteamGame],
        steam_path: Path,
        seven_zip_executables: SevenZipExecutables | None,
        initial_compression_states: dict[str, str],
    ) -> None:
        action_title = self.t("action_update")
        self.operation_cancel_event.clear()
        self.set_operation_controls_enabled(False)
        self.is_operation_running = True
        self.path_status_label.config(
            text=self.t("status_operation_running", action_name=action_title)
        )
        self.show_progress_window(action_title, len(selected_games))

        operation_thread = threading.Thread(
            target=self.run_steam_update_worker,
            args=(
                selected_games,
                steam_path,
                seven_zip_executables,
                initial_compression_states,
            ),
            daemon=True,
        )
        operation_thread.start()

    def get_selected_games(self) -> list[SteamGame]:
        return [
            self.games_by_path[game_path]
            for game_path, selected in self.game_selection.items()
            if selected.get() and game_path in self.games_by_path
        ]

    def get_valid_steam_path(self) -> Path | None:
        steam_path_value = self.config.data.get("steam_path", "")
        if not steam_path_value:
            messagebox.showwarning(
                APP_TITLE,
                self.t("message_no_steam_path"),
            )
            return None

        steam_path = Path(steam_path_value)
        if not steam_path.is_dir():
            messagebox.showerror(
                APP_TITLE,
                f"{self.t('message_steam_folder_missing')}\n{steam_path}",
            )
            return None

        if not (steam_path / "steamapps").is_dir():
            messagebox.showerror(
                APP_TITLE,
                f"{self.t('message_steamapps_missing')}\n{steam_path / 'steamapps'}",
            )
            return None

        return steam_path

    def set_operation_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.refresh_button.config(state=state)
        self.compression_button.config(state=state)
        self.decompression_button.config(state=state)
        self.update_button.config(state=state)
        self.update_all_button.config(state=state)

    def show_game_context_menu(self, event: tk.Event, game: SteamGame) -> str:
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label=game.name, state="disabled")
        context_menu.add_separator()
        context_menu.add_command(
            label=self.t("button_compression"),
            command=lambda: self.start_selected_operation("compression", [game]),
        )
        context_menu.add_command(
            label=self.t("button_decompression"),
            command=lambda: self.start_selected_operation("decompression", [game]),
        )
        context_menu.add_separator()
        context_menu.add_command(
            label=self.t("context_open_location"),
            command=lambda: self.open_game_location(game),
        )

        context_menu.tk_popup(event.x_root, event.y_root)
        context_menu.grab_release()
        return "break"

    def open_game_location(self, game: SteamGame) -> None:
        if not game.folder.is_dir():
            messagebox.showerror(
                APP_TITLE,
                self.t("message_game_folder_missing", folder=game.folder),
            )
            return

        try:
            subprocess.Popen(["explorer", str(game.folder)])
        except OSError as error:
            messagebox.showerror(
                APP_TITLE,
                self.t("message_open_location_error", error=error),
            )

    def run_file_operation_worker(
        self,
        operation: str,
        action_title: str,
        selected_games: list[SteamGame],
        seven_zip_executables: SevenZipExecutables,
    ) -> None:
        try:
            for index, game in enumerate(selected_games, start=1):
                self.raise_if_operation_cancelled()
                self.root.after(
                    0,
                    lambda current=index, total=len(selected_games), current_game=game: (
                        self.update_progress_window(
                            action_title,
                            f"{current}/{total} - {current_game.name}",
                        )
                    ),
                )

                progress_context = f"{index}/{len(selected_games)} - {game.name}"
                if operation == "compression":
                    self.compress_game(game, seven_zip_executables, progress_context)
                else:
                    self.decompress_game(game, seven_zip_executables, progress_context)
        except OperationCancelled:
            self.root.after(
                0,
                lambda: self.finish_file_operation(
                    False,
                    self.t("message_action_cancelled", action_name=action_title),
                    was_cancelled=True,
                ),
            )
            return
        except Exception as error:
            self.root.after(
                0,
                lambda message=str(error): self.finish_file_operation(False, message),
            )
            return

        self.root.after(
            0,
            lambda: self.finish_file_operation(
                True,
                self.t("message_games_processed", game_count=len(selected_games)),
            ),
        )

    def run_steam_update_worker(
        self,
        selected_games: list[SteamGame],
        steam_path: Path,
        seven_zip_executables: SevenZipExecutables | None,
        initial_compression_states: dict[str, str],
    ) -> None:
        action_title = self.t("action_update")
        try:
            for index, game in enumerate(selected_games, start=1):
                initial_state = initial_compression_states.get(
                    str(game.folder),
                    game.compression_state,
                )
                self.raise_if_operation_cancelled()
                if initial_state == COMPRESSED_STATE:
                    if seven_zip_executables is None:
                        raise RuntimeError(self.t("message_7zip_required"))

                    self.root.after(
                        0,
                        lambda current=index, total=len(selected_games), current_game=game: (
                            self.update_progress_window(
                                action_title,
                                f"{current}/{total} - {self.t('progress_decompression')} - {current_game.name}",
                            )
                        ),
                    )
                    self.decompress_game(
                        game,
                        seven_zip_executables,
                        f"{index}/{len(selected_games)} - {self.t('progress_decompression')} - {game.name}",
                    )
                elif initial_state == UNCOMPRESSED_STATE:
                    self.root.after(
                        0,
                        lambda current=index, total=len(selected_games), current_game=game: (
                            self.update_progress_window(
                                action_title,
                                f"{current}/{total} - {self.t('progress_game_uncompressed')} - {current_game.name}",
                            )
                        ),
                    )
                else:
                    raise RuntimeError(
                        (
                            self.t(
                                "message_unknown_state_during_update",
                                game_name=game.name,
                            )
                        )
                    )

                self.raise_if_operation_cancelled()
                self.root.after(
                    0,
                    lambda current=index, total=len(selected_games), current_game=game: (
                        self.update_progress_window(
                            action_title,
                            f"{current}/{total} - {self.t('progress_launch_steam')} - {current_game.name}",
                        )
                    ),
                )
                self.launch_steam_validation(game)

                self.root.after(
                    0,
                    lambda current=index, total=len(selected_games), current_game=game: (
                        self.update_progress_window(
                            action_title,
                            f"{current}/{total} - {self.t('progress_wait_steam')} - {current_game.name}",
                        )
                    ),
                )
                self.root.after(0, self.show_steam_wait_progress_mode)
                self.wait_for_steam_update(game, steam_path, index, len(selected_games))

                self.raise_if_operation_cancelled()
                if initial_state == COMPRESSED_STATE:
                    if seven_zip_executables is None:
                        raise RuntimeError(self.t("message_7zip_required"))

                    self.root.after(
                        0,
                        lambda current=index, total=len(selected_games), current_game=game: (
                            self.update_progress_window(
                                action_title,
                                f"{current}/{total} - {self.t('progress_recompression')} - {current_game.name}",
                            )
                        ),
                    )
                    self.compress_game(
                        game,
                        seven_zip_executables,
                        f"{index}/{len(selected_games)} - {self.t('progress_recompression')} - {game.name}",
                    )
                else:
                    self.root.after(
                        0,
                        lambda current=index, total=len(selected_games), current_game=game: (
                            self.update_progress_window(
                                action_title,
                                f"{current}/{total} - {self.t('progress_uncompressed_preserved')} - {current_game.name}",
                            )
                        ),
                    )
        except OperationCancelled:
            self.root.after(
                0,
                lambda: self.finish_file_operation(
                    False,
                    self.t("message_update_cancelled"),
                    was_cancelled=True,
                ),
            )
            return
        except Exception as error:
            self.root.after(
                0,
                lambda message=str(error): self.finish_file_operation(False, message),
            )
            return

        self.root.after(
            0,
            lambda: self.finish_file_operation(
                True,
                self.t("message_games_updated", game_count=len(selected_games)),
            ),
        )

    def finish_file_operation(
        self,
        success: bool,
        message: str,
        was_cancelled: bool = False,
    ) -> None:
        self.is_operation_running = False
        self.operation_cancel_event.clear()
        self.clear_current_7zip_process()
        self.destroy_progress_window()
        self.set_operation_controls_enabled(True)
        self.refresh_game_list(preserve_scroll=True)

        if success:
            messagebox.showinfo(APP_TITLE, message)
        elif was_cancelled:
            messagebox.showinfo(APP_TITLE, message)
        else:
            messagebox.showerror(APP_TITLE, message)

    def show_progress_window(self, action_title: str, game_count: int) -> None:
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title(action_title)
        self.progress_window.transient(self.root)
        self.progress_window.grab_set()
        self.progress_window.resizable(False, False)

        content = tk.Frame(self.progress_window, padx=16, pady=16)
        content.pack(fill="both", expand=True)

        self.progress_title_var.set(
            self.t("progress_title", action_name=action_title)
        )
        self.progress_detail_var.set(
            self.t("progress_preparation", game_count=game_count)
        )
        self.progress_help_var.set("")
        self.progress_percent_var.set("0%")
        self.progress_value_var.set(0)

        tk.Label(
            content,
            textvariable=self.progress_title_var,
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            content,
            textvariable=self.progress_detail_var,
            anchor="w",
            fg="#555555",
            wraplength=420,
        ).pack(fill="x", pady=(8, 12))

        self.progress_frame = tk.Frame(content)
        self.progress_frame.columnconfigure(1, weight=1)

        self.progress_percent_label = tk.Label(
            self.progress_frame,
            textvariable=self.progress_percent_var,
            width=5,
            anchor="e",
        )
        self.progress_percent_label.grid(row=0, column=0)
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode="determinate",
            maximum=100,
            variable=self.progress_value_var,
        )
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.progress_help_label = tk.Label(
            content,
            textvariable=self.progress_help_var,
            anchor="w",
            fg="#555555",
            justify="left",
            wraplength=500,
        )
        self.progress_help_label.pack(fill="x", pady=(0, 12))

        self.progress_cancel_button = tk.Button(
            content,
            text=self.t("button_cancel"),
            command=self.request_cancel_current_operation,
        )
        self.progress_cancel_button.pack(anchor="center")

        self.progress_window.protocol(
            "WM_DELETE_WINDOW",
            self.request_cancel_current_operation,
        )
        self.progress_window.update_idletasks()
        self.progress_window.geometry(
            f"{PROGRESS_WINDOW_WIDTH}x{self.progress_window.winfo_height()}"
        )
        self.center_dialog(self.progress_window)

    def show_7zip_progress_mode(self) -> None:
        if self.progress_bar is not None:
            self.progress_bar.stop()

        if self.progress_frame is not None and self.progress_frame.winfo_ismapped():
            self.progress_frame.pack_forget()

        self.progress_help_var.set(self.t("seven_zip_help"))
        self.refresh_progress_window_size()

    def show_7zip_background_progress_mode(self) -> None:
        if self.progress_bar is not None:
            self.progress_bar.stop()

        if self.progress_frame is not None and self.progress_frame.winfo_ismapped():
            self.progress_frame.pack_forget()

        self.progress_help_var.set(self.t("seven_zip_background_help"))
        self.refresh_progress_window_size()

    def show_steam_wait_progress_mode(self) -> None:
        if self.progress_bar is not None:
            self.progress_bar.stop()

        if self.progress_frame is not None and self.progress_frame.winfo_ismapped():
            self.progress_frame.pack_forget()

        self.progress_help_var.set(self.t("steam_wait_help"))
        self.refresh_progress_window_size()

    def refresh_progress_window_size(self) -> None:
        if self.progress_window is None:
            return

        self.progress_window.update_idletasks()
        self.progress_window.geometry(
            f"{PROGRESS_WINDOW_WIDTH}x{self.progress_window.winfo_reqheight()}"
        )

    def update_progress_window(self, title: str, detail: str) -> None:
        self.progress_title_var.set(self.t("progress_title", action_name=title))
        self.progress_detail_var.set(detail)
        self.update_progress_percent(0)

    def update_progress_percent(self, percent: int) -> None:
        bounded_percent = max(0, min(100, percent))
        if self.progress_bar is None:
            return

        self.progress_value_var.set(bounded_percent)
        self.progress_percent_var.set(f"{bounded_percent}%")

    def request_cancel_current_operation(self) -> None:
        if not self.is_operation_running:
            return

        self.operation_cancel_event.set()
        self.progress_detail_var.set(self.t("progress_cancel_requested"))
        if hasattr(self, "progress_cancel_button"):
            self.progress_cancel_button.config(state="disabled")

        with self.process_lock:
            process = self.current_7zip_process

        self.terminate_process(process)

    def destroy_progress_window(self) -> None:
        if self.progress_bar is not None:
            self.progress_bar.stop()
            self.progress_bar = None
        self.progress_frame = None
        self.progress_percent_label = None
        self.progress_help_label = None

        if self.progress_window is not None:
            try:
                self.progress_window.grab_release()
            except tk.TclError:
                pass
            self.progress_window.destroy()
            self.progress_window = None

    def raise_if_operation_cancelled(self) -> None:
        if self.operation_cancel_event.is_set():
            raise OperationCancelled

    def terminate_process(self, process: subprocess.Popen | None) -> None:
        if process is None or process.poll() is not None:
            return

        try:
            process.terminate()
        except OSError:
            return

    def launch_steam_validation(self, game: SteamGame) -> None:
        self.raise_if_operation_cancelled()
        steam_url = f"steam://validate/{game.app_id}"
        startfile = getattr(os, "startfile", None)
        if startfile is None:
            raise RuntimeError(self.t("message_steam_protocol_windows_only"))

        try:
            startfile(steam_url)
        except OSError as error:
            raise RuntimeError(
                self.t(
                    "message_steam_launch_error",
                    game_name=game.name,
                    error=error,
                )
            ) from error

    def wait_for_steam_update(
        self,
        game: SteamGame,
        steam_path: Path,
        game_index: int,
        game_count: int,
    ) -> None:
        target_version = game.latest_version.strip()
        manifest_path = self.get_appmanifest_path(steam_path, game.app_id)
        deadline = time.monotonic() + STEAM_UPDATE_TIMEOUT_SECONDS
        stable_match_count = 0

        while time.monotonic() < deadline:
            self.raise_if_operation_cancelled()
            manifest = self.parse_appmanifest(manifest_path)
            current_version = manifest.get("buildid", "").strip()
            manifest_target_version = self.get_manifest_target_version(manifest)
            if manifest_target_version:
                target_version = manifest_target_version
            steam_update_required = self.manifest_requires_steam_update(manifest)

            detail = (
                f"{game_index}/{game_count} - {self.t('progress_wait_steam')} - "
                f"{game.name} ({current_version or self.t('version_current_unknown')} / "
                f"{target_version})"
            )
            self.schedule_progress_detail(detail)

            if current_version == target_version and not steam_update_required:
                stable_match_count += 1
                if stable_match_count >= STEAM_UPDATE_STABLE_POLLS:
                    game.version = current_version
                    game.steam_update_required = False
                    return
            else:
                stable_match_count = 0

            next_poll = time.monotonic() + STEAM_UPDATE_POLL_INTERVAL_SECONDS
            while time.monotonic() < next_poll:
                self.raise_if_operation_cancelled()
                time.sleep(0.2)

        raise RuntimeError(self.t("message_steam_timeout", game_name=game.name))

    def get_steam_manifest_progress_percent(self, manifest: dict[str, str]) -> int | None:
        downloaded = self.parse_positive_int(manifest.get("bytesdownloaded", ""))
        download_total = self.parse_positive_int(manifest.get("bytestodownload", ""))
        if downloaded is not None and download_total:
            return max(0, min(100, int(downloaded * 100 / download_total)))

        staged = self.parse_positive_int(manifest.get("bytesstaged", ""))
        stage_total = self.parse_positive_int(manifest.get("bytestostage", ""))
        if staged is not None and stage_total:
            return max(0, min(100, int(staged * 100 / stage_total)))

        return None

    def parse_positive_int(self, value: str) -> int | None:
        try:
            parsed_value = int(value)
        except (TypeError, ValueError):
            return None

        if parsed_value < 0:
            return None

        return parsed_value

    def schedule_progress_detail(self, detail: str) -> None:
        if not hasattr(self, "root"):
            return

        self.root.after(0, lambda value=detail: self.progress_detail_var.set(value))

    def schedule_operation_step(
        self,
        progress_context: str | None,
        step_name: str,
    ) -> None:
        if progress_context is None:
            return

        self.schedule_progress_detail(f"{progress_context} - {step_name}")

    def compress_game(
        self,
        game: SteamGame,
        seven_zip_executables: SevenZipExecutables,
        progress_context: str | None = None,
    ) -> None:
        self.raise_if_operation_cancelled()
        source_entries = self.get_folder_entries(game.folder)
        if not source_entries:
            raise RuntimeError(self.t("message_folder_empty", game_name=game.name))

        archive_path = self.get_available_archive_path(game.folder)
        listfile_path = self.create_7zip_listfile(source_entries)

        try:
            self.schedule_operation_step(progress_context, self.t("progress_compression"))
            self.run_7zip_command(
                [
                    seven_zip_executables.gui_path,
                    "a",
                    str(archive_path),
                    f"@{listfile_path}",
                    "-scsUTF-8",
                    "-mx=9",
                    "-bb0",
                ],
                game.folder,
                self.t("message_compression_failed", game_name=game.name),
                show_gui=True,
            )
            self.raise_if_operation_cancelled()
            self.schedule_operation_step(
                progress_context,
                self.t("progress_verify_archive"),
            )
            self.run_7zip_command(
                [seven_zip_executables.cli_path, "t", str(archive_path), "-bb0"],
                game.folder,
                self.t("message_archive_verify_failed", game_name=game.name),
                show_gui=False,
            )
            self.raise_if_operation_cancelled()
        except Exception:
            self.delete_file_if_safe(archive_path, game.folder)
            raise
        finally:
            self.delete_temp_file(listfile_path)

        self.delete_original_entries(game.folder, source_entries, archive_path)

    def decompress_game(
        self,
        game: SteamGame,
        seven_zip_executables: SevenZipExecutables,
        progress_context: str | None = None,
    ) -> None:
        self.raise_if_operation_cancelled()
        archive_path = self.get_only_archive_path(game.folder, game.app_id)

        self.schedule_operation_step(progress_context, self.t("progress_verify_archive"))
        self.run_7zip_command(
            [seven_zip_executables.cli_path, "t", str(archive_path), "-bb0"],
            game.folder,
            self.t("message_archive_verify_failed", game_name=game.name),
            show_gui=False,
        )
        self.raise_if_operation_cancelled()

        try:
            self.schedule_operation_step(
                progress_context,
                self.t("progress_decompression"),
            )
            self.run_7zip_command(
                [
                    seven_zip_executables.gui_path,
                    "x",
                    str(archive_path),
                    f"-o{game.folder}",
                    "-aos",
                    "-y",
                    "-bb0",
                ],
                game.folder,
                self.t("message_decompression_failed", game_name=game.name),
                show_gui=True,
            )
            self.raise_if_operation_cancelled()
        except Exception:
            self.cleanup_decompression_output(
                game.folder,
                archive_path,
                game.app_id,
            )
            raise

        self.delete_file_if_safe(archive_path, game.folder)

    def run_7zip_command(
        self,
        command: list[str],
        working_directory: Path,
        error_message: str,
        show_gui: bool,
    ) -> None:
        self.raise_if_operation_cancelled()
        if show_gui:
            self.schedule_7zip_progress_mode()
        else:
            self.schedule_7zip_background_progress_mode()

        creation_flags = 0
        if not show_gui and hasattr(subprocess, "CREATE_NO_WINDOW"):
            creation_flags = subprocess.CREATE_NO_WINDOW

        try:
            process = subprocess.Popen(
                command,
                cwd=working_directory,
                stdout=None if show_gui else subprocess.PIPE,
                stderr=None if show_gui else subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creation_flags,
            )
        except OSError as error:
            raise RuntimeError(f"{error_message}\n\n{error}") from error

        with self.process_lock:
            self.current_7zip_process = process

        output_tail = ""
        output_thread = None

        def read_process_output() -> None:
            nonlocal output_tail
            if process.stdout is None:
                return

            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    break
                output_tail = (output_tail + chunk)[-4000:]

        if process.stdout is not None:
            output_thread = threading.Thread(target=read_process_output, daemon=True)
            output_thread.start()

        try:
            while process.poll() is None:
                if self.operation_cancel_event.is_set():
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
                    raise OperationCancelled

                time.sleep(0.1)

            if output_thread is not None:
                output_thread.join(timeout=5)
        finally:
            self.clear_current_7zip_process(process)

        if self.operation_cancel_event.is_set():
            raise OperationCancelled

        if process.returncode != 0:
            details = output_tail.strip()
            if details:
                raise RuntimeError(f"{error_message}\n\n{details[-1200:]}")

            raise RuntimeError(error_message)

    def clear_current_7zip_process(self, process: subprocess.Popen | None = None) -> None:
        with self.process_lock:
            if process is None or self.current_7zip_process is process:
                self.current_7zip_process = None

    def schedule_7zip_progress_mode(self) -> None:
        if not hasattr(self, "root"):
            return

        self.root.after(0, self.show_7zip_progress_mode)

    def schedule_7zip_background_progress_mode(self) -> None:
        if not hasattr(self, "root"):
            return

        self.root.after(0, self.show_7zip_background_progress_mode)

    def schedule_progress_percent(self, percent: int) -> None:
        if not hasattr(self, "root"):
            return

        self.root.after(0, lambda value=percent: self.update_progress_percent(value))

    def get_folder_entries(self, folder: Path) -> list[Path]:
        try:
            return list(folder.iterdir())
        except OSError as error:
            raise RuntimeError(
                self.t("message_read_folder_error", folder=folder, error=error)
            ) from error

    def create_7zip_listfile(self, entries: list[Path]) -> Path:
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                newline="\n",
                suffix=".txt",
                prefix="steam_archive_manager_",
                delete=False,
            ) as listfile:
                for entry in entries:
                    listfile.write(f"{entry.name}\n")
                return Path(listfile.name)
        except OSError as error:
            raise RuntimeError(str(error)) from error

    def delete_temp_file(self, file_path: Path) -> None:
        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            pass

    def get_available_archive_path(self, game_folder: Path) -> Path:
        archive_path = game_folder / f"{game_folder.name}.7z"
        if not archive_path.exists():
            return archive_path

        counter = 1
        while True:
            archive_path = game_folder / f"{game_folder.name}_{counter}.7z"
            if not archive_path.exists():
                return archive_path
            counter += 1

    def get_only_archive_path(self, game_folder: Path, app_id: str = "") -> Path:
        folder_content = self.get_compression_relevant_entries(game_folder, app_id)
        archives = [
            entry
            for entry in folder_content
            if entry.is_file()
            and entry.suffix.casefold() in COMPRESSED_GAME_EXTENSIONS
        ]

        if len(folder_content) != 1 or len(archives) != 1:
            raise RuntimeError(
                self.t(
                    "message_single_archive_required",
                    folder_name=game_folder.name,
                )
            )

        return archives[0]

    def cleanup_decompression_output(
        self,
        game_folder: Path,
        archive_path: Path,
        app_id: str = "",
    ) -> None:
        try:
            entries = list(game_folder.iterdir())
        except OSError:
            return

        resolved_archive_path = archive_path.resolve()
        ignored_entries = self.read_compression_ignored_entries()
        for entry in entries:
            if entry.resolve() == resolved_archive_path:
                continue
            if self.is_compression_ignored_entry(
                game_folder,
                entry,
                app_id,
                ignored_entries,
            ):
                continue
            self.delete_entry_if_safe(entry, game_folder)

    def delete_original_entries(
        self,
        game_folder: Path,
        source_entries: list[Path],
        archive_path: Path,
    ) -> None:
        resolved_game_folder = game_folder.resolve()
        resolved_archive_path = archive_path.resolve()

        for entry in source_entries:
            resolved_entry = entry.resolve()
            if resolved_entry == resolved_archive_path:
                continue

            if not self.is_path_inside(resolved_entry, resolved_game_folder):
                raise RuntimeError(
                    self.t("message_delete_cancelled", path=entry)
                )

            try:
                self.delete_entry_if_safe(entry, game_folder)
            except OSError as error:
                raise RuntimeError(
                    self.t("message_delete_failed", path=entry, error=error)
                ) from error

    def delete_file_if_safe(self, file_path: Path, parent_folder: Path) -> None:
        if not file_path.exists():
            return

        resolved_file_path = file_path.resolve()
        resolved_parent_folder = parent_folder.resolve()
        if not self.is_path_inside(resolved_file_path, resolved_parent_folder):
            raise RuntimeError(
                self.t("message_delete_cancelled", path=file_path)
            )

        try:
            if file_path.is_file() or file_path.is_symlink():
                file_path.unlink()
        except OSError as error:
            raise RuntimeError(
                self.t("message_delete_failed", path=file_path, error=error)
            ) from error

    def delete_entry_if_safe(self, entry: Path, parent_folder: Path) -> None:
        resolved_entry = entry.resolve()
        resolved_parent_folder = parent_folder.resolve()
        if not self.is_path_inside(resolved_entry, resolved_parent_folder):
            raise RuntimeError(
                self.t("message_delete_cancelled", path=entry)
            )

        if entry.is_symlink() or entry.is_file():
            entry.unlink()
        elif entry.is_dir():
            shutil.rmtree(entry)

    def is_path_inside(self, path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent)
        except ValueError:
            return False

        return True

    def find_7zip_executables(
        self,
        action_title: str | None = None,
    ) -> SevenZipExecutables:
        if action_title is None:
            action_title = self.t("action_compression")

        cli_path = self.find_7zip_cli_executable()
        gui_path = self.find_7zip_gui_executable(cli_path)
        if cli_path and gui_path:
            return SevenZipExecutables(cli_path=cli_path, gui_path=gui_path)

        missing_parts = []
        if not cli_path:
            missing_parts.append("7z.exe")
        if not gui_path:
            missing_parts.append("7zG.exe")

        missing_text = self.t("missing_items_separator").join(missing_parts)
        raise FileNotFoundError(
            self.t(
                "message_7zip_missing",
                action_name=action_title,
                missing_text=missing_text,
            )
        )

    def find_7zip_cli_executable(self) -> str | None:
        candidates = [
            shutil.which("7z"),
            shutil.which("7za"),
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
        ]

        return self.find_first_existing_file(candidates)

    def find_7zip_gui_executable(self, cli_path: str | None = None) -> str | None:
        command_line_7zip = shutil.which("7z") or shutil.which("7za")
        executable_for_sibling = cli_path or command_line_7zip
        path_sibling_gui = None
        if executable_for_sibling:
            path_sibling_gui = str(Path(executable_for_sibling).with_name("7zG.exe"))

        candidates = [
            shutil.which("7zG"),
            path_sibling_gui,
            r"C:\Program Files\7-Zip\7zG.exe",
            r"C:\Program Files (x86)\7-Zip\7zG.exe",
        ]

        return self.find_first_existing_file(candidates)

    def find_first_existing_file(self, candidates: list[str | None]) -> str | None:
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                return str(candidate)

        return None

    def show_game_message(self, message: str) -> None:
        self.table_message = message
        self.render_visible_game_rows()

    def add_game_message_label(self, message: str) -> None:
        tk.Label(
            self.rows_frame,
            text=message,
            anchor="center",
            fg="#555555",
            pady=24,
        ).grid(row=0, column=0, columnspan=15, sticky="ew")

    def add_cell_label(
        self,
        parent: tk.Widget,
        row: int,
        column: int,
        text: str,
        background: str,
        width: int | None = None,
        sticky: str = "nsw",
        anchor: str = "w",
        foreground: str | None = None,
        font=None,
        click_command=None,
    ) -> tk.Label:
        label_options = {
            "text": text,
            "anchor": anchor,
            "bg": background,
            "padx": TABLE_CELL_PAD_X,
        }
        if width is not None:
            label_options["width"] = width
        if foreground is not None:
            label_options["fg"] = foreground
        if font is not None:
            label_options["font"] = font

        label = tk.Label(parent, **label_options)
        label.grid(row=row, column=column, sticky=sticky, padx=0, pady=0)
        if click_command is not None:
            label.bind("<Button-1>", click_command)

        return label

    def add_column_separator(
        self,
        parent: tk.Widget,
        row: int,
        column: int,
        click_command=None,
    ) -> tk.Frame:
        separator = tk.Frame(parent, width=1, bg=COLUMN_SEPARATOR_COLOR)
        separator.grid(row=row, column=column, sticky="ns", padx=0, pady=0)
        if click_command is not None:
            separator.bind("<Button-1>", click_command)

        return separator

    def add_game_row(
        self,
        game: SteamGame,
        index: int,
        visual_index: int | None = None,
    ) -> None:
        background_index = index if visual_index is None else visual_index
        row_background = "#ffffff" if background_index % 2 == 0 else "#f7f7f7"

        game_path = str(game.folder)
        selected = self.game_selection.get(game_path)
        if selected is None:
            selected = tk.BooleanVar(value=False)
            self.game_selection[game_path] = selected
        self.games_by_path[str(game.folder)] = game

        def toggle_row_selection(event: tk.Event | None = None) -> str:
            selected.set(not selected.get())
            self.update_select_all_state()
            return "break"

        def show_context_menu(event: tk.Event) -> str:
            return self.show_game_context_menu(event, game)

        row_widgets = []

        checkbox = tk.Checkbutton(
            self.rows_frame,
            variable=selected,
            command=self.update_select_all_state,
            bg=row_background,
            activebackground=row_background,
            padx=TABLE_CELL_PAD_X,
        )
        checkbox.grid(row=index, column=0, sticky="nsew", padx=0, pady=0)
        row_widgets.append(checkbox)
        row_widgets.append(
            self.add_column_separator(
                self.rows_frame,
                index,
                1,
                toggle_row_selection,
            )
        )

        image_cell = tk.Frame(
            self.rows_frame,
            width=HEADER_IMAGE_SIZE[0],
            height=HEADER_IMAGE_SIZE[1],
            bg=row_background,
        )
        image_cell.grid(row=index, column=2, sticky="nsw", padx=0, pady=0)
        image_cell.grid_propagate(False)
        image_cell.bind("<Button-1>", toggle_row_selection)
        row_widgets.append(image_cell)

        photo = self.load_header_image(game.header_path)
        if photo is not None:
            self.header_images.append(photo)
            image_label = tk.Label(image_cell, image=photo, bg=row_background)
            image_label.place(
                relx=0.5,
                rely=0.5,
                anchor="center",
            )
            image_label.bind("<Button-1>", toggle_row_selection)
            row_widgets.append(image_label)
        else:
            placeholder_text = self.t("placeholder_header_missing")
            if game.header_path is not None:
                if self.header_image_requires_pillow(game.header_path):
                    placeholder_text = self.t("placeholder_pillow_missing")
                else:
                    placeholder_text = self.t("placeholder_image_unreadable")

            placeholder_label = tk.Label(
                image_cell,
                text=placeholder_text,
                justify="center",
                bg="#eeeeee",
                fg="#777777",
            )
            placeholder_label.place(
                relx=0.5,
                rely=0.5,
                relwidth=1,
                relheight=1,
                anchor="center",
            )
            placeholder_label.bind("<Button-1>", toggle_row_selection)
            row_widgets.append(placeholder_label)

        row_widgets.append(
            self.add_column_separator(
                self.rows_frame,
                index,
                3,
                toggle_row_selection,
            )
        )

        row_widgets.append(
            self.add_cell_label(
                self.rows_frame,
                index,
                4,
                game.name,
                row_background,
                sticky="nsew",
                click_command=toggle_row_selection,
            )
        )
        row_widgets.append(
            self.add_column_separator(
                self.rows_frame,
                index,
                5,
                toggle_row_selection,
            )
        )

        row_widgets.append(
            self.add_cell_label(
                self.rows_frame,
                index,
                6,
                game.app_id,
                row_background,
                width=12,
                click_command=toggle_row_selection,
            )
        )
        row_widgets.append(
            self.add_column_separator(
                self.rows_frame,
                index,
                7,
                toggle_row_selection,
            )
        )

        row_widgets.append(
            self.add_cell_label(
                self.rows_frame,
                index,
                8,
                self.get_compression_state_display(game.compression_state),
                row_background,
                width=14,
                click_command=toggle_row_selection,
            )
        )
        row_widgets.append(
            self.add_column_separator(
                self.rows_frame,
                index,
                9,
                toggle_row_selection,
            )
        )

        row_widgets.append(
            self.add_cell_label(
                self.rows_frame,
                index,
                10,
                self.get_version_display(game.version),
                row_background,
                width=18,
                click_command=toggle_row_selection,
            )
        )
        row_widgets.append(
            self.add_column_separator(
                self.rows_frame,
                index,
                11,
                toggle_row_selection,
            )
        )

        row_widgets.append(
            self.add_cell_label(
                self.rows_frame,
                index,
                12,
                self.get_version_display(game.latest_version),
                row_background,
                width=28,
                click_command=toggle_row_selection,
            )
        )
        row_widgets.append(
            self.add_column_separator(
                self.rows_frame,
                index,
                13,
                toggle_row_selection,
            )
        )

        update_symbol, update_color = self.get_update_status_display(game)
        row_widgets.append(
            self.add_cell_label(
                self.rows_frame,
                index,
                14,
                update_symbol,
                row_background,
                width=8,
                sticky="nsew",
                anchor="center",
                foreground=update_color,
                font=("Arial", 14, "bold"),
                click_command=toggle_row_selection,
            )
        )

        for widget in row_widgets:
            widget.bind("<Button-3>", show_context_menu)

    def get_update_status_display(self, game: SteamGame) -> tuple[str, str]:
        if self.is_game_up_to_date(game):
            return "✓", "#14833b"

        return "✕", "#b00020"

    def get_compression_state_display(self, state: str) -> str:
        normalized_state = state.strip().casefold()
        if normalized_state in {COMPRESSED_STATE, "compressé", "compresse"}:
            return self.t("state_compressed")
        if normalized_state in {UNCOMPRESSED_STATE, "non compressé", "non compresse"}:
            return self.t("state_uncompressed")

        return self.t("state_unknown")

    def get_version_display(self, version: str) -> str:
        normalized_version = version.strip().casefold()
        if normalized_version in {UNKNOWN_VERSION, "inconnue"}:
            return self.t("version_unknown")
        if normalized_version in {UNAVAILABLE_VERSION, "indisponible"}:
            return self.t("version_unavailable")

        return version

    def is_unknown_version_value(self, version: str) -> bool:
        return version.strip().casefold() in {
            "",
            UNKNOWN_VERSION,
            UNAVAILABLE_VERSION,
            "inconnue",
            "indisponible",
        }

    def is_game_up_to_date(self, game: SteamGame) -> bool:
        if game.steam_update_required:
            return False

        installed_version = game.version.strip()
        latest_version = game.latest_version.strip()
        return bool(
            installed_version
            and latest_version
            and not self.is_unknown_version_value(installed_version)
            and not self.is_unknown_version_value(latest_version)
            and installed_version == latest_version
        )

    def has_known_latest_version(self, game: SteamGame) -> bool:
        return not self.is_unknown_version_value(game.latest_version)

    def load_header_image(self, header_path: Path | None) -> tk.PhotoImage | None:
        if header_path is None:
            return None

        cache_key = self.get_header_image_cache_key(header_path)
        if cache_key is not None and cache_key in self.header_image_cache:
            return self.header_image_cache[cache_key]

        photo = None
        if Image is not None and ImageTk is not None:
            try:
                with Image.open(header_path) as source_image:
                    source_image.thumbnail(HEADER_IMAGE_SIZE)
                    if source_image.mode in {"RGB", "RGBA"}:
                        image = source_image.copy()
                    else:
                        image = source_image.convert("RGBA")
                    photo = ImageTk.PhotoImage(image)
            except OSError:
                return None
        else:
            if header_path.suffix.casefold() not in TK_IMAGE_EXTENSIONS:
                return None

            try:
                photo = tk.PhotoImage(file=str(header_path))
            except tk.TclError:
                return None

            scale = max(
                1,
                math.ceil(
                    max(
                        photo.width() / HEADER_IMAGE_SIZE[0],
                        photo.height() / HEADER_IMAGE_SIZE[1],
                    )
                ),
            )
            if scale > 1:
                photo = photo.subsample(scale, scale)

        if cache_key is not None and photo is not None:
            self.header_image_cache[cache_key] = photo
            self.trim_header_image_cache()

        return photo

    def header_image_requires_pillow(self, header_path: Path) -> bool:
        return (
            (Image is None or ImageTk is None)
            and header_path.suffix.casefold() not in TK_IMAGE_EXTENSIONS
        )

    def get_header_image_cache_key(
        self,
        header_path: Path,
    ) -> tuple[str, int, int] | None:
        try:
            file_stat = header_path.stat()
        except OSError:
            return None

        return (str(header_path), file_stat.st_mtime_ns, file_stat.st_size)

    def trim_header_image_cache(self) -> None:
        while len(self.header_image_cache) > HEADER_IMAGE_CACHE_LIMIT:
            oldest_key = next(iter(self.header_image_cache))
            del self.header_image_cache[oldest_key]

    def find_installed_games(self, steam_path: Path) -> list[SteamGame]:
        if not steam_path.is_dir():
            raise FileNotFoundError(self.t("message_steam_folder_missing"))

        steamapps_path = steam_path / "steamapps"
        common_path = steamapps_path / "common"
        if not steamapps_path.is_dir():
            raise FileNotFoundError(self.t("message_steamapps_missing"))
        if not common_path.is_dir():
            raise FileNotFoundError(self.t("message_common_missing"))

        installed_apps = []
        app_ids = set()
        for manifest_path in steamapps_path.glob("appmanifest_*.acf"):
            manifest = self.parse_appmanifest(manifest_path)
            app_id = manifest.get("appid", "").strip()
            install_dir = manifest.get("installdir", "")
            if not app_id or not install_dir:
                continue

            game_folder = common_path / install_dir
            if not game_folder.is_dir():
                continue

            installed_apps.append((game_folder, manifest))
            app_ids.add(app_id)

        app_metadata = self.read_appinfo_metadata(steam_path, app_ids)

        games = []
        installed_apps.sort(
            key=lambda app: (
                self.is_app_type_tool(
                    app_metadata.get(app[1].get("appid", ""), {}).get("type", "")
                ),
                (app[1].get("name") or app[0].name).casefold(),
            )
        )
        for game_folder, manifest in installed_apps:
            app_id = manifest.get("appid", "")
            metadata = app_metadata.get(app_id, {})
            app_type = metadata.get("type", "")
            games.append(
                SteamGame(
                    folder=game_folder,
                    app_id=app_id,
                    app_type=app_type,
                    compression_state=self.get_compression_state(
                        game_folder,
                        app_id,
                    ),
                    name=manifest.get("name") or game_folder.name,
                    version=manifest.get("buildid") or UNKNOWN_VERSION,
                    latest_version=self.get_latest_version_text(manifest, metadata),
                    steam_update_required=self.manifest_requires_steam_update(
                        manifest
                    ),
                    header_path=self.find_header_path(steam_path, app_id),
                )
            )

        return games

    def is_app_type_tool(self, app_type: str) -> bool:
        return app_type.casefold() == "tool"

    def get_compression_state(self, game_folder: Path, app_id: str = "") -> str:
        try:
            folder_content = self.get_compression_relevant_entries(
                game_folder,
                app_id,
            )
        except RuntimeError:
            return UNKNOWN_STATE

        if len(folder_content) != 1:
            return UNCOMPRESSED_STATE

        only_entry = folder_content[0]
        if (
            only_entry.is_file()
            and only_entry.suffix.casefold() in COMPRESSED_GAME_EXTENSIONS
        ):
            return COMPRESSED_STATE

        return UNCOMPRESSED_STATE

    def get_compression_relevant_entries(
        self,
        game_folder: Path,
        app_id: str = "",
    ) -> list[Path]:
        folder_content = self.get_folder_entries(game_folder)
        ignored_entries = self.read_compression_ignored_entries()

        return [
            entry
            for entry in folder_content
            if not self.is_compression_ignored_entry(
                game_folder,
                entry,
                app_id,
                ignored_entries,
            )
        ]

    def is_compression_ignored_entry(
        self,
        game_folder: Path,
        entry: Path,
        app_id: str,
        ignored_entries: dict[str, set[str]] | None = None,
    ) -> bool:
        if ignored_entries is None:
            ignored_entries = self.read_compression_ignored_entries()
        app_ignored_entries = ignored_entries.get(str(app_id).strip(), set())
        if not app_ignored_entries:
            return False

        try:
            relative_entry = entry.relative_to(game_folder)
        except ValueError:
            return False

        normalized_entry = self.normalize_compression_ignore_entry(relative_entry)
        if self.compression_ignore_path_matches(
            normalized_entry,
            app_ignored_entries,
        ):
            return True

        if entry.is_dir():
            return self.compression_directory_contains_only_ignored_entries(
                game_folder,
                entry,
                app_ignored_entries,
            )

        return False

    def compression_directory_contains_only_ignored_entries(
        self,
        game_folder: Path,
        directory: Path,
        app_ignored_entries: set[str],
    ) -> bool:
        try:
            children = list(directory.iterdir())
        except OSError:
            return False

        if not children:
            relative_directory = directory.relative_to(game_folder)
            normalized_directory = self.normalize_compression_ignore_entry(
                relative_directory
            )
            return any(
                ignored_entry.startswith(f"{normalized_directory}/")
                for ignored_entry in app_ignored_entries
            )

        for child in children:
            relative_child = child.relative_to(game_folder)
            normalized_child = self.normalize_compression_ignore_entry(relative_child)
            if self.compression_ignore_path_matches(
                normalized_child,
                app_ignored_entries,
            ):
                continue
            child_directory_is_ignored = (
                child.is_dir()
                and self.compression_directory_contains_only_ignored_entries(
                    game_folder,
                    child,
                    app_ignored_entries,
                )
            )
            if child_directory_is_ignored:
                continue
            return False

        return True

    def compression_ignore_path_matches(
        self,
        normalized_entry: str,
        app_ignored_entries: set[str],
    ) -> bool:
        return any(
            normalized_entry == ignored_entry
            or normalized_entry.startswith(f"{ignored_entry}/")
            for ignored_entry in app_ignored_entries
        )

    def read_compression_ignored_entries(self) -> dict[str, set[str]]:
        try:
            content = COMPRESSION_IGNORE_FILE.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except OSError:
            return {}

        ignored_entries = {}
        current_app_id = None
        for line in content.splitlines():
            entry = line.strip()
            if not entry or entry.startswith("#"):
                continue
            if set(entry) == {"-"}:
                continue

            app_id_match = re.search(r"\bID\s*:?\s*(\d+)\b", entry, re.IGNORECASE)
            if app_id_match:
                current_app_id = app_id_match.group(1)
                ignored_entries.setdefault(current_app_id, set())
                continue

            if current_app_id is None:
                continue

            normalized_entry = self.normalize_compression_ignore_entry(entry)
            if normalized_entry:
                ignored_entries[current_app_id].add(normalized_entry)

        return ignored_entries

    def normalize_compression_ignore_entry(self, entry: str | Path) -> str:
        normalized_entry = str(entry).replace("\\", "/").strip().strip("/")
        while normalized_entry.startswith("./"):
            normalized_entry = normalized_entry[2:]

        return normalized_entry.strip("/").casefold()

    def get_latest_version_text(
        self,
        manifest: dict[str, str],
        app_metadata: dict[str, str],
    ) -> str:
        installed_version = manifest.get("buildid", "").strip()
        latest_version = app_metadata.get("latest_version", "").strip()
        manifest_target_version = self.get_manifest_target_version(manifest)

        if self.manifest_requires_steam_update(manifest):
            if manifest_target_version:
                return manifest_target_version
            if latest_version:
                return latest_version
            if installed_version:
                return installed_version
            return UNAVAILABLE_VERSION

        if installed_version and self.installed_depot_manifests_are_current(
            manifest,
            app_metadata,
        ):
            return installed_version

        if manifest_target_version:
            return manifest_target_version

        if latest_version:
            return latest_version

        if installed_version:
            return installed_version

        return UNAVAILABLE_VERSION

    def installed_depot_manifests_are_current(
        self,
        manifest: dict[str, str],
        app_metadata: dict[str, str],
    ) -> bool:
        installed_depots = self.get_manifest_installed_depot_manifests(manifest)
        latest_depots = self.get_appinfo_latest_depot_manifests(app_metadata)
        if not installed_depots or not latest_depots:
            return False

        matching_depot_ids = set(installed_depots) & set(latest_depots)
        if not matching_depot_ids:
            return False

        return all(
            installed_depots[depot_id] == latest_depots[depot_id]
            for depot_id in matching_depot_ids
        )

    def get_manifest_installed_depot_manifests(
        self,
        manifest: dict[str, str],
    ) -> dict[str, str]:
        prefix = "installeddepot:"
        suffix = ":manifest"
        return {
            key.removeprefix(prefix).removesuffix(suffix): value
            for key, value in manifest.items()
            if key.startswith(prefix) and key.endswith(suffix) and value
        }

    def get_appinfo_latest_depot_manifests(
        self,
        app_metadata: dict[str, str],
    ) -> dict[str, str]:
        prefix = "appinfo_depot:"
        suffix = ":manifest"
        return {
            key.removeprefix(prefix).removesuffix(suffix): value
            for key, value in app_metadata.items()
            if key.startswith(prefix) and key.endswith(suffix) and value
        }

    def get_manifest_depot_manifest_key(self, depot_id: str) -> str:
        return f"installeddepot:{depot_id}:manifest"

    def get_appinfo_depot_manifest_key(self, depot_id: str) -> str:
        return f"appinfo_depot:{depot_id}:manifest"

    def get_manifest_target_version(self, manifest: dict[str, str]) -> str:
        target_version = manifest.get("targetbuildid", "").strip()
        if target_version and target_version != "0":
            return target_version

        return ""

    def manifest_requires_steam_update(self, manifest: dict[str, str]) -> bool:
        try:
            state_flags = int(manifest.get("stateflags", "0"))
        except (TypeError, ValueError):
            return False

        return bool(state_flags & STEAM_STATE_UPDATE_REQUIRED)

    def refresh_games_metadata(
        self,
        games: list[SteamGame],
        steam_path: Path,
    ) -> None:
        if not games:
            return

        app_ids = {game.app_id for game in games}
        app_metadata = self.read_appinfo_metadata(steam_path, app_ids)
        for game in games:
            manifest = self.parse_appmanifest(
                self.get_appmanifest_path(steam_path, game.app_id)
            )
            metadata = app_metadata.get(game.app_id, {})
            game.compression_state = self.get_compression_state(
                game.folder,
                game.app_id,
            )
            if manifest:
                game.version = manifest.get("buildid") or UNKNOWN_VERSION
                game.latest_version = self.get_latest_version_text(manifest, metadata)
                game.steam_update_required = self.manifest_requires_steam_update(
                    manifest
                )
                game.name = manifest.get("name") or game.name

    def get_appmanifest_path(self, steam_path: Path, app_id: str) -> Path:
        return steam_path / "steamapps" / f"appmanifest_{app_id}.acf"

    def read_appinfo_types(
        self,
        steam_path: Path,
        app_ids: set[str],
    ) -> dict[str, str]:
        return {
            app_id: metadata.get("type", "")
            for app_id, metadata in self.read_appinfo_metadata(
                steam_path,
                app_ids,
            ).items()
        }

    def read_appinfo_metadata(
        self,
        steam_path: Path,
        app_ids: set[str],
    ) -> dict[str, dict[str, str]]:
        if not app_ids:
            return {}

        wanted_app_ids = {str(app_id) for app_id in app_ids}
        appinfo_path = steam_path / "appcache" / "appinfo.vdf"
        cache_key = self.get_appinfo_cache_key(appinfo_path)
        if cache_key is None:
            return {}

        with self.appinfo_cache_lock:
            if self.appinfo_cache_key != cache_key:
                self.appinfo_cache_key = cache_key
                self.appinfo_metadata_cache = {}
                self.appinfo_metadata_cached_app_ids = set()
            elif wanted_app_ids.issubset(self.appinfo_metadata_cached_app_ids):
                return {
                    app_id: self.appinfo_metadata_cache[app_id]
                    for app_id in wanted_app_ids
                    if app_id in self.appinfo_metadata_cache
                }

        try:
            data = appinfo_path.read_bytes()
        except OSError:
            return {}

        if len(data) < APPINFO_HEADER_SIZE:
            return {}

        magic = self.read_uint32(data, 0)
        if magic != APPINFO_MAGIC_V41:
            return {}

        string_table_offset = self.read_uint64(data, 8)
        if string_table_offset >= len(data):
            return {}

        string_table = self.read_appinfo_string_table(data, string_table_offset)
        if not string_table:
            return {}

        app_metadata = {}
        position = APPINFO_HEADER_SIZE

        while position + 8 <= string_table_offset:
            app_id = self.read_uint32(data, position)
            if app_id == 0:
                break

            entry_size = self.read_uint32(data, position + 4)
            entry_start = position + 8
            entry_end = entry_start + entry_size
            if entry_size < APPINFO_ENTRY_METADATA_SIZE or entry_end > len(data):
                break

            app_id_text = str(app_id)
            if app_id_text in wanted_app_ids:
                binary_vdf_start = entry_start + APPINFO_ENTRY_METADATA_SIZE
                parsed_appinfo = self.parse_binary_vdf(
                    data[binary_vdf_start:entry_end],
                    string_table,
                )
                common = parsed_appinfo.get("appinfo", {}).get("common", {})
                depots = parsed_appinfo.get("appinfo", {}).get("depots", {})
                public_branch = depots.get("branches", {}).get("public", {})
                app_type = common.get("type")
                public_buildid = public_branch.get("buildid")
                public_depot_manifests = self.get_appinfo_public_depot_manifests(
                    depots
                )
                metadata = {}
                if isinstance(app_type, str):
                    metadata["type"] = app_type
                if public_buildid is not None:
                    metadata["latest_version"] = str(public_buildid)
                for depot_id, depot_manifest in public_depot_manifests.items():
                    metadata[
                        self.get_appinfo_depot_manifest_key(depot_id)
                    ] = depot_manifest
                app_metadata[app_id_text] = metadata

                if wanted_app_ids.issubset(app_metadata):
                    break

            position = entry_end

        with self.appinfo_cache_lock:
            if self.appinfo_cache_key == cache_key:
                self.appinfo_metadata_cache.update(app_metadata)
                self.appinfo_metadata_cached_app_ids.update(wanted_app_ids)

        return app_metadata

    def get_appinfo_public_depot_manifests(self, depots: dict) -> dict[str, str]:
        depot_manifests = {}
        if not isinstance(depots, dict):
            return depot_manifests

        for depot_id, depot_data in depots.items():
            if not str(depot_id).isdigit() or not isinstance(depot_data, dict):
                continue

            manifests = depot_data.get("manifests", {})
            if not isinstance(manifests, dict):
                continue

            public_manifest = manifests.get("public", {})
            if not isinstance(public_manifest, dict):
                continue

            manifest_gid = public_manifest.get("gid")
            if manifest_gid is not None:
                depot_manifests[str(depot_id)] = str(manifest_gid)

        return depot_manifests

    def get_appinfo_cache_key(self, appinfo_path: Path) -> tuple[str, int, int] | None:
        try:
            file_stat = appinfo_path.stat()
        except OSError:
            return None

        return (str(appinfo_path), file_stat.st_mtime_ns, file_stat.st_size)

    def read_appinfo_string_table(self, data: bytes, offset: int) -> list[str]:
        if offset + 4 > len(data):
            return []

        string_count = self.read_uint32(data, offset)
        position = offset + 4
        string_table = []

        for _ in range(string_count):
            end_position = data.find(b"\x00", position)
            if end_position == -1:
                return []

            string_table.append(
                data[position:end_position].decode("utf-8", errors="replace")
            )
            position = end_position + 1

        return string_table

    def parse_binary_vdf(
        self,
        data: bytes,
        string_table: list[str],
    ) -> dict:
        values, _ = self.parse_binary_vdf_object(data, 0, string_table)
        return values

    def parse_binary_vdf_object(
        self,
        data: bytes,
        position: int,
        string_table: list[str],
    ) -> tuple[dict, int]:
        values = {}

        while position < len(data):
            value_type = data[position]
            position += 1

            if value_type == BINARY_VDF_END:
                return values, position

            if position + 4 > len(data):
                return values, len(data)

            key_id = self.read_uint32(data, position)
            position += 4
            key = self.binary_vdf_key_name(key_id, string_table)

            if value_type == BINARY_VDF_OBJECT:
                value, position = self.parse_binary_vdf_object(
                    data,
                    position,
                    string_table,
                )
            elif value_type == BINARY_VDF_STRING:
                value, position = self.read_binary_vdf_string(data, position)
            elif value_type == BINARY_VDF_INT32:
                value = self.read_uint32(data, position)
                position += 4
            elif value_type == BINARY_VDF_UINT64:
                value = self.read_uint64(data, position)
                position += 8
            elif value_type == BINARY_VDF_INT64:
                value = int.from_bytes(data[position : position + 8], "little", signed=True)
                position += 8
            elif value_type in (BINARY_VDF_FLOAT32, BINARY_VDF_COLOR):
                value = None
                position += 4
            elif value_type == BINARY_VDF_POINTER:
                value = None
                position += 8
            elif value_type == BINARY_VDF_WSTRING:
                value, position = self.read_binary_vdf_wstring(data, position)
            else:
                return values, len(data)

            values[key] = value

        return values, position

    def read_binary_vdf_string(
        self,
        data: bytes,
        position: int,
    ) -> tuple[str, int]:
        end_position = data.find(b"\x00", position)
        if end_position == -1:
            return "", len(data)

        return (
            data[position:end_position].decode("utf-8", errors="replace"),
            end_position + 1,
        )

    def read_binary_vdf_wstring(
        self,
        data: bytes,
        position: int,
    ) -> tuple[str, int]:
        end_position = position
        while end_position + 1 < len(data):
            if data[end_position : end_position + 2] == b"\x00\x00":
                break
            end_position += 2

        if end_position + 1 >= len(data):
            return "", len(data)

        return (
            data[position:end_position].decode("utf-16-le", errors="replace"),
            end_position + 2,
        )

    def binary_vdf_key_name(self, key_id: int, string_table: list[str]) -> str:
        if 0 <= key_id < len(string_table):
            return string_table[key_id].casefold()

        return str(key_id)

    def read_uint32(self, data: bytes, position: int) -> int:
        return int.from_bytes(data[position : position + 4], "little")

    def read_uint64(self, data: bytes, position: int) -> int:
        return int.from_bytes(data[position : position + 8], "little")

    def parse_appmanifest(self, manifest_path: Path) -> dict[str, str]:
        manifest = {}
        try:
            content = manifest_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return manifest

        object_stack = []
        pending_object_key = None
        for line in content.splitlines():
            match = ACF_VALUE_PATTERN.match(line)
            if match:
                key = match.group(1)
                value = match.group(2)
                manifest[key.casefold()] = value
                if (
                    key.casefold() == "manifest"
                    and len(object_stack) >= 2
                    and object_stack[-2].casefold() == "installeddepots"
                ):
                    depot_id = object_stack[-1]
                    manifest[self.get_manifest_depot_manifest_key(depot_id)] = value
                continue

            stripped_line = line.strip()
            object_match = ACF_OBJECT_KEY_PATTERN.match(stripped_line)
            if object_match:
                pending_object_key = object_match.group(1)
                continue

            if stripped_line == "{":
                if pending_object_key is not None:
                    object_stack.append(pending_object_key)
                    pending_object_key = None
                continue

            if stripped_line == "}":
                if object_stack:
                    object_stack.pop()
                pending_object_key = None

        return manifest

    def find_header_path(self, steam_path: Path, app_id: str) -> Path | None:
        library_cache_root = steam_path / "appcache" / "librarycache"
        library_cache_path = library_cache_root / app_id
        if not library_cache_path.is_dir():
            return self.find_root_header_path(library_cache_root, app_id)

        for header_file_name in ("header.jpg", "library_header.jpg"):
            header_path = self.find_file_recursively(
                library_cache_path,
                header_file_name,
            )
            if header_path is not None:
                return header_path

        return self.find_best_header_candidate(library_cache_path)

    def find_root_header_path(
        self,
        library_cache_root: Path,
        app_id: str,
    ) -> Path | None:
        if not library_cache_root.is_dir():
            return None

        for header_file_name in (
            f"{app_id}_header.jpg",
            f"{app_id}_library_header.jpg",
            f"{app_id}_header.png",
            f"{app_id}_library_header.png",
        ):
            header_path = library_cache_root / header_file_name
            if header_path.is_file():
                return header_path

        return None

    def find_best_header_candidate(self, folder: Path) -> Path | None:
        try:
            matches = [
                path
                for path in folder.rglob("*")
                if path.is_file()
                and path.suffix.casefold() in HEADER_IMAGE_EXTENSIONS
                and "header" in path.stem.casefold()
            ]
        except OSError:
            return None

        if not matches:
            return None

        return sorted(
            matches,
            key=lambda path: (
                0 if path.name.casefold() == "header.jpg" else 1,
                0 if path.name.casefold() == "library_header.jpg" else 1,
                len(path.relative_to(folder).parts),
                str(path.relative_to(folder)).casefold(),
            ),
        )[0]

    def find_file_recursively(self, folder: Path, file_name: str) -> Path | None:
        try:
            matches = [
                path
                for path in folder.rglob("*")
                if path.is_file() and path.name.casefold() == file_name.casefold()
            ]
        except OSError:
            return None

        if not matches:
            return None

        return sorted(
            matches,
            key=lambda path: (
                len(path.relative_to(folder).parts),
                str(path.relative_to(folder)).casefold(),
            ),
        )[0]

    def show_steam_path_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("dialog_steam_path_title"))
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        content = tk.Frame(dialog, padx=16, pady=16)
        content.pack(fill="both", expand=True)

        tk.Label(
            content,
            text=self.t("dialog_steam_path_prompt"),
            anchor="w",
        ).pack(fill="x")

        current_path = self.config.data.get("steam_path") or self.t("dialog_no_path")
        path_label = tk.Label(
            content,
            text=current_path,
            anchor="w",
            fg="#555555",
            wraplength=420,
        )
        path_label.pack(fill="x", pady=(8, 16))

        button_frame = tk.Frame(content)
        button_frame.pack(fill="x")

        def select_steam_path() -> None:
            selected_path = filedialog.askdirectory(
                parent=dialog,
                title=self.t("dialog_select_steam_folder"),
                initialdir=self.config.data.get("steam_path") or str(Path.home()),
            )
            if selected_path:
                self.config.save_steam_path(selected_path)
                self.refresh_game_list()
                dialog.destroy()

        def ask_later() -> None:
            dialog.destroy()

        tk.Button(
            button_frame,
            text=self.t("button_select_path"),
            command=select_steam_path,
        ).pack(side="left")
        tk.Button(
            button_frame,
            text=self.t("button_ask_later"),
            command=ask_later,
        ).pack(side="right")

        dialog.protocol("WM_DELETE_WINDOW", ask_later)
        self.center_dialog(dialog)
        dialog.wait_window()

    def center_dialog(self, dialog: tk.Toplevel) -> None:
        dialog.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()

        position_x = root_x + (root_width - dialog_width) // 2
        position_y = root_y + (root_height - dialog_height) // 2
        dialog.geometry(f"+{position_x}+{position_y}")

    def quit_application(self) -> None:
        if self.is_operation_running:
            messagebox.showwarning(
                APP_TITLE,
                self.t("message_quit_operation_running"),
            )
            return

        self.stop_autoscroll()
        self.root.update_idletasks()
        self.config.save_window_size(self.root.winfo_width(), self.root.winfo_height())
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    SteamManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
