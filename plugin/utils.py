import subprocess
import os, json
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, unquote
import hashlib
from plugin.settings import CACHE_DIR, DEFAULT_ICON, settings_file, MB_PATH, XML_PATH, icon_path, SHUFFLE_ENABLED
import logging
from mutagen import File
from mutagen.id3 import APIC
from plugin.extensions import _l
import random
import tempfile

import logging

# --- HELPER FUNCTIONS ---

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
    """Read library data from XML file"""
    if not os.path.exists(XML_PATH):
        return []
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    return root.findall("./dict/dict/dict")

def create_temp_playlist(file_paths):
    """Create temporary M3U playlist file"""
    temp_dir = tempfile.gettempdir()
    playlist_path = os.path.join(temp_dir, "musicbee_temp_playlist.m3u")
    
    with open(playlist_path, 'w', encoding='utf-8') as f:
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
            data["xml_path"] = os.path.join(os.path.dirname(musicbee_path), "Library", "iTunes Music Library.xml")
        
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
        elif action == "show":
            command.append("/Show")
            
        subprocess.Popen(command)
        
    except Exception as e:
        print(f"Error executing MusicBee: {e}")

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
    tracks_node = get_library_data()
    playlist_files = []
    album_sorter = []  # For album mode sorting
    
    
    for track in tracks_node:
        children = list(track)
        location = None
        t_artist = ""
        t_album = ""
        t_disc = 1
        t_track = 0
        
        # Extract only needed fields
        for i in range(0, len(children), 2):
            key = children[i].text
            val = children[i+1].text
            if key == 'Location':
                location = val
            elif key in ['Artist', 'Artista']:
                t_artist = val
            elif key in ['Album', 'Álbum', 'Album']:
                t_album = val
            elif key == 'Disc Number':
                t_disc = int(val) if val else 1
            elif key == 'Track Number':
                t_track = int(val) if val else 0
        
        if not location:
            continue
        
        clean_path = get_clean_path(location)
        
        # Filter based on mode
        if mode == "all":
            # Include everything except target (will add it first later)
            if clean_path != target_path:
                playlist_files.append(clean_path)
                
        elif mode == "artist":
            # Same artist, exclude target song
            if t_artist == target_artist and clean_path != target_path:
                playlist_files.append(clean_path)
                
        elif mode == "album":
            # Same album and artist
            if t_album == target_album and t_artist == target_artist:
                album_sorter.append({
                    "path": clean_path,
                    "disc": t_disc,
                    "track": t_track,
                    "name": track.findtext("Name", "") or "Desconocido"
                })
        
        # Collect name for sorting in other modes
        if mode in ["all", "artist"]:
             if (mode == "all" and clean_path != target_path) or \
                (mode == "artist" and t_artist == target_artist and clean_path != target_path):
                 
                 # Store as tuple (name, path) for sorting
                 # Retrieve name again strictly if not in album loop
                 t_name = ""
                 for i in range(0, len(children), 2):
                     if children[i].text == "Name":
                         t_name = children[i+1].text
                         break
                 
                 playlist_files.append({"path": clean_path, "name": t_name})
    
    # Post-process based on mode
    # Post-process based on mode
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
            # First, find target in the list if it exists (it should)
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
                # Fallback if target path mismatch (unlikely)
                final_playlist = [target_path] + others

        else:
            # Sort by disc and track number (Ordered)
            album_sorter.sort(key=lambda x: (x['disc'], x['track']))
            final_playlist = [item['path'] for item in album_sorter]
            
    else:  
        # Artist or All mode
        # playlist_files contains dicts {"path": p, "name": n}
        
        if current_shuffle:
            # Shuffle and put target first
            paths = []
            for item in playlist_files:
                if isinstance(item, dict):
                     paths.append(item["path"])
                else:
                     paths.append(item)
            
            random.shuffle(paths)
            final_playlist = [target_path] + paths
        else:
            # Sort alphabetically by Song Name
            # Ensure items are dicts logic
            valid_items = [x for x in playlist_files if isinstance(x, dict)]
            valid_items.sort(key=lambda x: x["name"].lower())
            
            final_playlist = [target_path] + [item["path"] for item in valid_items]
    
    # Create and play playlist (force clear queue)
    playlist_path = create_temp_playlist(final_playlist)
    subprocess.Popen([MB_PATH, "/Play", playlist_path])
    
    # For album mode, jump to target song if not first (Only needed if NOT shuffling and NOT first)
    if mode == "album" and not current_shuffle:
        time.sleep(0.5)
        subprocess.Popen([MB_PATH, "/Play", target_path])

def get_cover_art(audio_path):
    path_hash = hashlib.md5(audio_path.encode('utf-8')).hexdigest()
    image_save_path = os.path.abspath(os.path.join(CACHE_DIR, f"{path_hash}.jpg"))

    if os.path.exists(image_save_path):
        return image_save_path

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

    return DEFAULT_ICON


def parse_musicbee_xml(query):
    """Search MusicBee library and return results with play options"""
    tracks_node = get_library_data()
    if not tracks_node:
        return []
    
    results = []
    query = query.lower()

    for track in tracks_node:
        track_data = {}
        children = list(track)
        for i in range(0, len(children), 2):
            key = children[i].text
            value = children[i+1].text
            track_data[key] = value

        name = track_data.get('Name', 'Desconocido')
        # Check both English and Spanish keys
        artist = track_data.get('Artist') or track_data.get('Artista') or 'Desconocido'
        album = track_data.get('Album') or track_data.get('Álbum') or ''
        location = track_data.get('Location', '')

        if query in name.lower() or query in artist.lower():
            if location:
                file_path = get_clean_path(location)
                
                if file_path:
                    icon = get_cover_art(file_path)

                    logging.debug(f"Found {name} by {artist} in {album}, playing {file_path}")
                    results.append({
                        "Title": name,
                        "SubTitle": f"{artist} - {album}" if album else artist,
                        "IcoPath": icon,
                        "JsonRPCAction": {
                            "method": "show_play_options",
                            "parameters": [file_path, artist, album, name],
                            "dontHideAfterAction": True
                        }
                    })

        if len(results) >= 10:
            break

    return results

def play_song(file_path):
    """Legacy function - kept for compatibility"""
    if os.path.exists(file_path):
        subprocess.Popen([MB_PATH, file_path])