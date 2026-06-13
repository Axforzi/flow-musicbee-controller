# -*- coding: utf-8 -*-

import subprocess
import os, json
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, unquote
import hashlib
from plugin.settings import CACHE_DIR, DEFAULT_ICON, settings_file, MB_PATH, XML_PATH, icon_path
import logging
from mutagen import File
from mutagen.id3 import APIC
from plugin.extensions import _l
import random
import tempfile

# --- HELPER FUNCTIONS ---

_xml_cache_data = None
_xml_cache_mtime = 0
_no_cover_cache = set()

def get_clean_path(location_url):
    """Clean XML URL to Windows path"""
    if not location_url:
        return ""
    parsed_url = urlparse(location_url)
    path = unquote(parsed_url.path)
    if path.startswith('/') and ':' in path:
        path = path[1:]
    return path.replace('/', '\\')

def get_library_data():
    """Read library data from XML file, parse into structured list of song dicts (cached)"""
    global _xml_cache_data, _xml_cache_mtime
    if not os.path.exists(XML_PATH):
        return []
    try:
        mtime = os.path.getmtime(XML_PATH)
        if _xml_cache_data is not None and _xml_cache_mtime == mtime:
            return _xml_cache_data
        
        tree = ET.parse(XML_PATH)
        root = tree.getroot()
        tracks_node = root.findall("./dict/dict/dict")
        
        parsed_songs = []
        for track in tracks_node:
            track_data = {}
            children = list(track)
            for i in range(0, len(children), 2):
                key = children[i].text
                value = children[i+1].text
                track_data[key] = value
            
            location = track_data.get('Location', '')
            if not location:
                continue
                
            clean_path = get_clean_path(location)
            if not clean_path:
                continue
                
            name = track_data.get('Name', 'Desconocido')
            artist = track_data.get('Artist') or track_data.get('Artista') or 'Desconocido'
            album = track_data.get('Album') or track_data.get('Álbum') or ''
            
            try:
                disc = int(track_data.get('Disc Number', 1))
            except:
                disc = 1
                
            try:
                track_num = int(track_data.get('Track Number', 0))
            except:
                track_num = 0
                
            parsed_songs.append({
                "name": name,
                "artist": artist,
                "album": album,
                "path": clean_path,
                "disc": disc,
                "track_number": track_num
            })
            
        _xml_cache_data = parsed_songs
        _xml_cache_mtime = mtime
        return _xml_cache_data
    except Exception as e:
        logging.error(f"Error parsing XML library: {e}")
        return []

def create_temp_playlist(file_paths):
    """Create temporary M3U8 playlist file (handles Unicode safely)"""
    temp_dir = tempfile.gettempdir()
    playlist_path = os.path.join(temp_dir, "musicbee_temp_playlist.m3u8")
    
    with open(playlist_path, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        f.write('\n'.join(file_paths))
    
    return playlist_path

# --- MAIN FUNCTIONS ---

def save_config(musicbee_path=None, toggle_shuffle=None):
    # Load existing config to preserve other settings
    data = {"musicbee_path": "", "xml_path": "", "shuffle_enabled": True}
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                data.update(json.load(f))
        except:
            pass

    with open(settings_file, 'w') as f:
        if musicbee_path:
            data["musicbee_path"] = musicbee_path
            # Búsqueda inteligente de ruta de biblioteca XML
            possible_paths = [
                os.path.join(os.path.dirname(musicbee_path), "Library", "iTunes Music Library.xml"),
                os.path.expandvars(r"%USERPROFILE%\Music\MusicBee\iTunes Music Library.xml"),
                os.path.expandvars(r"%USERPROFILE%\Music\MusicBee\MusicBee Library.xml"),
                os.path.expandvars(r"%USERPROFILE%\Music\MusicBee\MusicBeeMusicLibrary.xml"),
            ]
            xml_path = possible_paths[0]  # default fallback
            for p in possible_paths:
                if os.path.exists(p):
                    xml_path = p
                    break
            data["xml_path"] = xml_path
        
        if toggle_shuffle is not None:
            data["shuffle_enabled"] = toggle_shuffle

        json.dump(data, f, indent=4)

def musicbee_command(action):
    try:
        command = [MB_PATH]
        
        if action == "toggle":
            command.append("/PlayPause")
        elif action == "next":
            command.append("/Next")
        elif action == "prev":
            command.append("/Previous")
        elif action == "stop":
            command.append("/Stop")
            
        subprocess.Popen(command)
        
    except Exception as e:
        logging.error(f"Error executing MusicBee: {e}")

def execute_mode(mode, target_path, target_artist, target_album):
    """
    Execute playback with different contexts.
    Modes: 'single', 'album', 'artist', 'all'
    """
    import time
    
    # Single song - just play it
    if mode == "single":
        subprocess.Popen([MB_PATH, "/Play", target_path])
        return
    
    # For other modes, build playlist from library
    songs = get_library_data()
    playlist_files = []
    album_sorter = []  # For album mode sorting
    
    for song in songs:
        clean_path = song["path"]
        
        # Filter based on mode
        if mode == "all":
            # Include everything except target (will add it first later)
            if clean_path != target_path:
                playlist_files.append({"path": clean_path, "name": song["name"]})
                
        elif mode == "artist":
            # Same artist, exclude target song
            if song["artist"] == target_artist and clean_path != target_path:
                playlist_files.append({"path": clean_path, "name": song["name"]})
                
        elif mode == "album":
            # Same album and artist
            if song["album"] == target_album and song["artist"] == target_artist:
                album_sorter.append({
                    "path": clean_path,
                    "disc": song["disc"],
                    "track": song["track_number"],
                    "name": song["name"]
                })
    
    # Check current shuffle state from settings (live reload)
    current_shuffle = True
    try:
        with open(settings_file, 'r') as f:
            current_shuffle = json.load(f).get("shuffle_enabled", True)
    except:
        pass

    final_playlist = []

    if mode == "album":
        if current_shuffle:
            # Shuffle but keep target first
            target_item = None
            others = []
            
            for item in album_sorter:
                if item['path'] == target_path:
                    target_item = item['path']
                else:
                    others.append(item['path'])
            
            random.shuffle(others)
            
            if target_item:
                final_playlist = [target_item] + others
            else:
                final_playlist = [target_path] + others
        else:
            # Sort by disc and track number (Ordered)
            album_sorter.sort(key=lambda x: (x['disc'], x['track']))
            final_playlist = [item['path'] for item in album_sorter]
            
    else:  
        # Artist or All mode
        if current_shuffle:
            # Shuffle and put target first
            paths = [item["path"] for item in playlist_files]
            random.shuffle(paths)
            final_playlist = [target_path] + paths
        else:
            # Sort alphabetically by Song Name
            playlist_files.sort(key=lambda x: x["name"].lower())
            final_playlist = [target_path] + [item["path"] for item in playlist_files]
    
    # Create and play playlist (force clear queue)
    playlist_path = create_temp_playlist(final_playlist)
    subprocess.Popen([MB_PATH, "/Play", playlist_path])
    
    # For album mode, jump to target song if not first
    if mode == "album" and not current_shuffle:
        time.sleep(0.5)
        subprocess.Popen([MB_PATH, "/Play", target_path])

def get_cover_art(audio_path):
    global _no_cover_cache
    path_hash = hashlib.md5(audio_path.encode('utf-8')).hexdigest()
    image_save_path = os.path.abspath(os.path.join(CACHE_DIR, f"{path_hash}.jpg"))

    if os.path.exists(image_save_path):
        return image_save_path

    if audio_path in _no_cover_cache:
        return DEFAULT_ICON

    try:
        audio = File(audio_path)
        
        artwork_data = None
        if audio.tags:
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    artwork_data = tag.data
                    break

        if artwork_data:
            with open(image_save_path, "wb") as img:
                img.write(artwork_data)
            return image_save_path
            
    except Exception:
        pass

    _no_cover_cache.add(audio_path)
    return DEFAULT_ICON

def parse_musicbee_xml(query):
    """Search MusicBee library and return results sorted by relevance"""
    songs = get_library_data()
    if not songs:
        return []
    
    results = []
    query = query.lower().strip()

    for song in songs:
        name = song["name"]
        artist = song["artist"]
        album = song["album"]
        file_path = song["path"]

        name_lower = name.lower()
        artist_lower = artist.lower()

        score = 0
        if query == name_lower:
            score = 100
        elif name_lower.startswith(query):
            score = 90
        elif query in name_lower:
            score = 80
        elif query == artist_lower:
            score = 75
        elif artist_lower.startswith(query):
            score = 70
        elif query in artist_lower:
            score = 60

        if score > 0:
            icon = get_cover_art(file_path)
            results.append((score, {
                "Title": name,
                "SubTitle": f"{artist} - {album}" if album else artist,
                "IcoPath": icon,
                "JsonRPCAction": {
                    "method": "show_play_options",
                    "parameters": [file_path, artist, album, name],
                    "dontHideAfterAction": True
                }
            }))

    # Sort results by relevance score (descending)
    results.sort(key=lambda x: x[0], reverse=True)
    
    # Return top 10 matched results
    return [item[1] for item in results[:10]]

def play_song(file_path):
    """Legacy function - kept for compatibility"""
    if os.path.exists(file_path):
        subprocess.Popen([MB_PATH, file_path])