# -*- coding: utf-8 -*-

import copy, os
from typing import List

from flowlauncher import FlowLauncher, FlowLauncherAPI
from plugin.templates import *
from plugin.extensions import _l

from plugin.settings import icon_path, ActionKeyword
from plugin.utils import save_config, musicbee_command, parse_musicbee_xml
from plugin.settings import MB_PATH, PROG_DIR, PLAY_ICON, NEXT_ICON, PREVIOUS_ICON, SHUFFLE_ICON, SHUFFLE_ON_ICON, STOP_ICON, SONG_ICON, ARTIST_ICON, ALBUM_ICON, LIBRARY_ICON
import json
import logging
import uuid
import glob
import time

class Main(FlowLauncher):
    messages_queue = []

    def sendNormalMess(self, title: str, subtitle: str):
        message = copy.deepcopy(RESULT_TEMPLATE)
        message["Title"] = title
        message["SubTitle"] = subtitle

        self.messages_queue.append(message)

    def sendActionMess(self, title: str, subtitle: str, method: str, value: List):
        # information
        message = copy.deepcopy(RESULT_TEMPLATE)
        message["Title"] = title
        message["SubTitle"] = subtitle

        # action
        action = copy.deepcopy(ACTION_TEMPLATE)
        action["JsonRPCAction"]["method"] = method
        action["JsonRPCAction"]["parameters"] = value
        message.update(action)

        self.messages_queue.append(message)

    def musicbee_command(self, param: str): 
        return musicbee_command(param)

    def change_set_path(self): 
        FlowLauncherAPI.change_query(ActionKeyword + " setpath ", False)
    
    def browse_file(self):
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Bring dialog to front
        
        file_path = filedialog.askopenfilename(
            title=_l("Select MusicBee executable"),
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")],
            initialdir="C:\\Program Files"
        )
        
        root.destroy()
        
        if file_path:
            save_config(file_path)
            FlowLauncherAPI.show_msg(
                _l("Path saved successfully"),
                file_path
            )

    def set_path(self, param: str): return save_config(param)

    def toggle_shuffle(self):
        """Toggle shuffle state and reload"""
        # Read current state first to be safe
        current_shuffle = True
        try:
            with open(os.path.join(PROG_DIR, "config.json"), 'r') as f:
                current_shuffle = json.load(f).get("shuffle_enabled", True)
        except:
            pass
        
        new_state = not current_shuffle
        save_config(toggle_shuffle=new_state)
        
        # Re-trigger query to update UI
        FlowLauncherAPI.change_query(ActionKeyword, True)
    
    def show_play_options(self, file_path: str, artist: str, album: str, title: str):
        """Store song data in file and change query to show options elegantly"""
        # Store song data to single context file (user only interacts with one song at a time)
        context_file = os.path.join(PROG_DIR, "context.json")
        data = {
            "file_path": file_path,
            "artist": artist,
            "album": album,
            "title": title
        }
        try:
            with open(context_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            logging.error(f"Failed to save context: {e}")
            
        # Change query to something that looks nice, like a "now selected" header
        # using a disc emoji as a prefix indicator
        FlowLauncherAPI.change_query(f"{ActionKeyword} 💿 {title}", True)
    
    def execute_mode(self, mode: str, target_path: str, target_artist: str, target_album: str):
        """Execute playback mode"""
        from plugin.utils import execute_mode
        return execute_mode(mode, target_path, target_artist, target_album)

    def query(self, param: str) -> List[dict]:
        clean_query = param.strip().lower()

        # New MusicBee path
        if clean_query.startswith("setpath"):
            new_path = param[7:].strip()

            if not new_path:
                 return [{
                     "Title": _l("Browse for MusicBee.exe"),
                     "SubTitle": _l("Open file browser to select MusicBee executable"),
                     "IcoPath": icon_path,
                     "JsonRPCAction": {
                         "method": "browse_file",
                         "parameters": [],
                         "dontHideAfterAction": False
                     }
                 }, {
                     "Title": _l("Set path manually"),
                     "SubTitle": _l("Type the path (Ex. C:\\Program Files\\MusicBee\\MusicBee.exe)"),
                     "IcoPath": icon_path,
                     "JsonRPCAction": {
                         "method": "change_set_path",
                         "parameters": [],
                         "dontHideAfterAction": False
                     }
                 }]

            return [{
                "Title": _l("Save Path: {}...").format(new_path[:15]),
                "SubTitle": _l("Save path of MusicBee"),
                "IcoPath": icon_path,
                "JsonRPCAction": {
                    "method": "set_path",
                    "parameters": [new_path],
                    "dontHideAfterAction": False
                }
            }]
        
        # Quick Commands (Symbols)
        # > or >> : Next
        if clean_query in [">", ">>", "next", "n"]:
            return [{
                "Title": _l("Next"),
                "SubTitle": _l("Next song"),
                "IcoPath": NEXT_ICON,
                "JsonRPCAction": {"method": "musicbee_command", "parameters": ["next"], "dontHideAfterAction": False}
            }]
        
        # < or << : Previous
        if clean_query in ["<", "<<", "prev", "previous", "p"]:
            return [{
                "Title": _l("Previous"),
                "SubTitle": _l("Previous song"),
                "IcoPath": PREVIOUS_ICON,
                "JsonRPCAction": {"method": "musicbee_command", "parameters": ["prev"], "dontHideAfterAction": False}
            }]
            
        # || or !! : Play/Pause
        if clean_query in ["||", "!!", "pp", "play", "pause"]:
            return [{
                 "Title": _l("Play/Pause"),
                 "SubTitle": _l("Play/Pause song"),
                 "IcoPath": PLAY_ICON,
                 "JsonRPCAction": {"method": "musicbee_command", "parameters": ["toggle"], "dontHideAfterAction": False}
            }]
            
        # . or stop : Stop
        if clean_query in [".", "stop", "s"]:
            return [{
                 "Title": _l("Stop"),
                 "SubTitle": _l("Stop song"),
                 "IcoPath": STOP_ICON,
                 "JsonRPCAction": {"method": "musicbee_command", "parameters": ["stop"], "dontHideAfterAction": False}
            }]

        # Check if MusicBee path is configured
        if not MB_PATH or not os.path.exists(MB_PATH):
            return [{
                "Title": _l("Path of MusicBee not found"),
                "SubTitle": _l("Press enter to configure MusicBee path"),
                "IcoPath": icon_path,
                "JsonRPCAction": {
                    "method": "change_set_path",
                    "parameters": [],
                    "dontHideAfterAction": True
                }
              }]
         
        # Handle context options display - detect by the disc emoji prefix
        if clean_query.startswith("💿"):
            context_file = os.path.join(PROG_DIR, "context.json")
            song = None
            
            if os.path.exists(context_file):
                try:
                    with open(context_file, "r", encoding="utf-8") as f:
                        song = json.load(f)
                except Exception:
                    pass
            
            # Verify the loaded song matches the title in the query (basic check)
            # query format: "💿 title"
            query_title = clean_query[2:].strip()
            
            if song:
                # Check shuffle state for dynamic subtitles
                current_shuffle = True
                try:
                    with open(os.path.join(PROG_DIR, "config.json"), 'r') as f:
                        current_shuffle = json.load(f).get("shuffle_enabled", True)
                except:
                    pass

                # Dynamic subtitles
                album_sub = _l("Play album '{}' (Randomized)").format(song["album"]) if current_shuffle else _l("Play album '{}' (Ordered)").format(song["album"])
                artist_sub = _l("Play '{}' then random songs from {}").format(song["title"], song["artist"]) if current_shuffle else _l("Play '{}' then aligned songs from {}").format(song["title"], song["artist"])
                all_sub = _l("Play '{}' then random songs from Library").format(song["title"]) if current_shuffle else _l("Play '{}' then aligned songs from Library").format(song["title"])

                # Optional: match title to ensure context is valid, but loose matching is safer for UX
                # if song["title"].lower() in query_title.lower(): 
                return [{
                    "Title": _l("Single song only"),
                    "SubTitle": _l("Clear queue and play only this song"),
                    "IcoPath": SONG_ICON,
                    "Score": 100,
                    "JsonRPCAction": {
                        "method": "execute_mode",
                        "parameters": ["single", song["file_path"], song["artist"], song["album"]],
                        "dontHideAfterAction": False
                    }
                }, {
                    "Title": _l("Play context: Album"),
                    "SubTitle": album_sub,
                    "IcoPath": ALBUM_ICON,
                    "Score": 80,
                    "JsonRPCAction": {
                        "method": "execute_mode",
                        "parameters": ["album", song["file_path"], song["artist"], song["album"]],
                        "dontHideAfterAction": False
                    }
                }, {
                    "Title": _l("Play context: Artist"),
                    "SubTitle": artist_sub,
                    "IcoPath": ARTIST_ICON,
                    "Score": 90,
                    "JsonRPCAction": {
                        "method": "execute_mode",
                        "parameters": ["artist", song["file_path"], song["artist"], song["album"]],
                        "dontHideAfterAction": False
                    }
                }, {
                    "Title": _l("Play context: Full Library"),
                    "SubTitle": all_sub,
                    "IcoPath": LIBRARY_ICON,
                    "Score": 70,
                    "JsonRPCAction": {
                        "method": "execute_mode",
                        "parameters": ["all", song["file_path"], song["artist"], song["album"]],
                        "dontHideAfterAction": False
                    }
                }]
            else:
                return []
        
        # Search for songs if user provides a query
        if param.strip():
            search_results = parse_musicbee_xml(param.strip())
            
            if search_results:
                return search_results
            else:
                return [{
                    "Title": _l("No songs found"),
                    "SubTitle": _l("Try a different search term"),
                    "IcoPath": icon_path
                }]
        
        # Show control buttons if no query
        # Get current shuffle state for display
        current_shuffle_state = True
        try:
             with open(os.path.join(PROG_DIR, "config.json"), 'r') as f:
                current_shuffle_state = json.load(f).get("shuffle_enabled", True)
        except:
            pass

        return  [{
                "Title": "{}: {}".format(_l("Shuffle"), _l("ON") if current_shuffle_state else _l("OFF")),
                "SubTitle": _l("Randomize playback order") if current_shuffle_state else _l("Play in track/alphabetical order"),
                "IcoPath": SHUFFLE_ON_ICON if current_shuffle_state else SHUFFLE_ICON,
                "Score": 0,
                "JsonRPCAction": {
                    "method": "toggle_shuffle",
                    "parameters": [],
                    "dontHideAfterAction": True
                }
            }, {
                "Title": _l("Play/Pause"),
                "SubTitle": _l("Play/Pause song"),
                "IcoPath": PLAY_ICON,
                "Score": 100,
                "JsonRPCAction": {
                    "method": "musicbee_command",
                    "parameters": ["toggle"],
                    "dontHideAfterAction": False
                }
            }, {
                "Title": _l("Next"),
                "SubTitle": _l("Next song"),
                "IcoPath": NEXT_ICON,
                "Score": 90,
                "JsonRPCAction": {
                    "method": "musicbee_command",
                    "parameters": ["next"],
                    "dontHideAfterAction": False
                }
            }, {
                "Title": _l("Previous"),
                "SubTitle": _l("Previous song"),
                "IcoPath": PREVIOUS_ICON,
                "Score": 80,
                "JsonRPCAction": {
                    "method": "musicbee_command",
                    "parameters": ["prev"],
                    "dontHideAfterAction": False
                }
            }, {
                "Title": _l("Stop"),
                "SubTitle": _l("Stop song"),
                "IcoPath": STOP_ICON,
                "Score": 70,
                "JsonRPCAction": {
                    "method": "musicbee_command",
                    "parameters": ["stop"],
                    "dontHideAfterAction": False
                }
            }]