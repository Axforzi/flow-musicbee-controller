# -*- coding: utf-8 -*-
import os, sys
import json
from pathlib import Path

from dotenv import load_dotenv

setting_pyfile = Path(__file__).resolve()
pludir = setting_pyfile.parent
basedir = pludir.parent
PROG_DIR = basedir
icon_path = os.path.join(basedir, "assets/favicon.png")


DEFAULT_ICON = os.path.join(basedir, "assets", "music.png")
PLAY_ICON = os.path.join(basedir, "assets", "play.png")
NEXT_ICON = os.path.join(basedir, "assets", "next.png")
PREVIOUS_ICON = os.path.join(basedir, "assets", "previous.png")
SHUFFLE_ICON = os.path.join(basedir, "assets", "shuffle.png")
SHUFFLE_ON_ICON = os.path.join(basedir, "assets", "shuffle_on.png")
STOP_ICON = os.path.join(basedir, "assets", "stop.png")
SONG_ICON = os.path.join(basedir, "assets", "song.png")
ARTIST_ICON = os.path.join(basedir, "assets", "artist.png")
ALBUM_ICON = os.path.join(basedir, "assets", "album.png")
LIBRARY_ICON = os.path.join(basedir, "assets", "library.png")
CACHE_DIR = os.path.join(basedir, "img_cache")
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# GET PLUGIN ID AND NAME
base_plugin_settings = os.path.join(basedir, "plugin.json")
with open(base_plugin_settings, 'r') as f:
    settings = json.load(f)
    plugin_id = settings["ID"]
    plugin_name = settings["Name"]

# GET ACTION KEYWORD
plugins_settings_flowlauncher = os.path.join(basedir.parent.parent, "Settings", "settings.json")
with open(plugins_settings_flowlauncher, 'r') as f:
    settings = json.load(f)
    settings = settings["PluginSettings"]["Plugins"]
    find_plugin = {key: value for key, value in settings.items() if key == plugin_id}
    ActionKeyword = find_plugin[plugin_id]["ActionKeywords"][0]

# GET SETTINGS
settings_file = os.path.join(basedir, "config.json")
if not os.path.exists(settings_file):
    with open(settings_file, 'w') as f:
        json.dump({"musicbee_path": "", "xml_path": "", "shuffle_enabled": True}, f, indent=4)

with open(settings_file, 'r') as f:
    settings = json.load(f)
    MB_PATH = settings.get("musicbee_path", "")
    XML_PATH = settings.get("xml_path", "")
    SHUFFLE_ENABLED = settings.get("shuffle_enabled", True)


# Add lib directory to path
lib_path = basedir / "lib"
sys.path.insert(0, str(lib_path))

dotenv_path = basedir / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)


# The default value can work, if no user config.
CONFIG = os.getenv("CONFIG", "default config")

# Detect language from Flow Launcher settings
try:
    with open(plugins_settings_flowlauncher, 'r', encoding='utf-8') as f:
        fl_settings = json.load(f)
        # Flow Launcher language setting
        fl_language = fl_settings.get("Language", "en")
        
        # Map Flow Launcher language codes to our translation codes
        language_map = {
            "en": "en_US",
            "en-US": "en_US",
            "es": "es_ES",
            "es-ES": "es_ES",
            "es-MX": "es_ES",
            "zh-CN": "zh_CN",
        }
        
        LOCAL = language_map.get(fl_language, "en_US")
except:
    # Fallback to environment variable or default
    LOCAL = os.getenv("local", "en_US")

# the information of package
__package_name__ = "MusicBee Quick Commands"
__version__ = "1.0.0"
__short_description__ = "Play music from MusicBee"
GITHUB_USERNAME = "Axforzi"


readme_path = basedir / "README.md"
try:
    __long_description__ = open(readme_path, "r").read()
except:
    __long_description__ = __short_description__


# extensions
TRANSLATIONS_PATH = basedir / "plugin/translations"

# plugin.json
PLUGIN_ID = "223865a6-3f16-403f-9180-70ec3061602c"  # could generate via python `uuid` official package
ICON_PATH = "assets/favicon.ico"
PLUGIN_AUTHOR = "Maikel García"
PLUGIN_ACTION_KEYWORD = "mb"
PLUGIN_PROGRAM_LANG = "python"
PLUGIN_EXECUTE_FILENAME = "main.py"
PLUGIN_ZIP_NAME = f"{__package_name__}-{__version__}.zip"
PLUGIN_URL = f"https://github.com/{GITHUB_USERNAME}/{__package_name__}"
PLUGIN_URL_SOURCE_CODE = f"https://github.com/{GITHUB_USERNAME}/{__package_name__}"
PLUGIN_URL_DOWNLOAD = (
    f"{PLUGIN_URL_SOURCE_CODE}/releases/download/v{__version__}/{PLUGIN_ZIP_NAME}"
)
