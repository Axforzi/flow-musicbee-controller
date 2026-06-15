# MusicBee Controller for Flow Launcher

Instantly search your music library, play songs, and control playback of **MusicBee** directly from Flow Launcher.

Optimized with advanced XML caching and cover art miss-caching for near-zero search latency, even with libraries of tens of thousands of tracks.

---

## 🚀 Features
* 🔍 **Instant Search:** Find songs by title or artist.
* 🎛️ **Quick Controls:** Play, pause, stop, or skip tracks using simple commands or symbols.
* 💿 **Playback Contexts:** Play a single song, its entire album, all songs by the artist, or randomize the entire library.
* 🖼️ **Cover Art Display:** Automatically extracts and caches track cover art using `mutagen`.
* ⚡ **High Performance:** Caches XML library parsing in memory based on file modification time, preventing lag while typing.
* 🌍 **Multilingual:** Supports English and Spanish localization based on Flow Launcher settings.

---

## 🛠️ Requirements
* **Flow Launcher**
* **MusicBee** installed on Windows
* **iTunes XML Export enabled** in MusicBee:
  1. Open MusicBee.
  2. Go to `Edit` > `Preferences` > `Library`.
  3. Enable **"export library in iTunes format"** (in Spanish: *"guardar una copia de las etiquetas de la biblioteca como archivo xml de iTunes"* o *"exportar biblioteca en formato iTunes"*).


---

## 📖 How to Use

Interact with the plugin using the default action keyword **`mb`**.

### 1. Initial Setup
The plugin needs to know where your MusicBee executable and library XML are:
1. Open Flow Launcher and type `mb setpath`.
2. Select **"Browse for MusicBee.exe"** to open a file browser and locate your `MusicBee.exe` (usually in `C:\Program Files\MusicBee\MusicBee.exe`), or type it manually.
3. The plugin will automatically try to detect your exported library XML file from default locations.
4. **If auto-detection fails (e.g., MS Store version):** The plugin will show options to **"Browse for iTunes Music Library XML"** or type it manually using the command:
   ```cmd
   mb setxml [path]
   ```

### 2. Control Playback via Symbols/Shortcuts
Open Flow Launcher and type the following short symbols to trigger instant controls:
* **Play / Pause**: `mb ||` or `mb pp` or `mb play`
* **Next Track**: `mb >` or `mb >>` or `mb next`
* **Previous Track**: `mb <` or `mb <<` or `mb prev`
* **Stop Playback**: `mb .` or `mb stop`
* **Toggle Shuffle**: Pressing `mb` without query shows a toggle button to turn Shuffle **ON** or **OFF** globally.

### 3. Search and Play Contexts
1. Type `mb <song or artist name>` to list matches.
2. Selecting a track changes the view and lets you choose:
   * 🎵 **Single song only**: Clears the queue and plays only this track.
   * 💿 **Play context: Album**: Plays the entire album (ordered or randomized depending on your Shuffle setting).
   * 👤 **Play context: Artist**: Plays the selected track followed by other songs from the same artist.
   * 📚 **Play context: Full Library**: Plays the selected track followed by your entire library randomized.

---

## License
MIT
