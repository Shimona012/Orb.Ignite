#Using Spotipy to access Spotify API and Streamlit for web app interface, SI usage to debug API implementation
import streamlit as st
import streamlit.components.v1 as components
import base64
import json
import os
import random
#some track IDs from three playlists:
# 1. NASA Wake Up Music
# 2. NASA Moon Tunes
# 3. Voyager Golden Record
'''TO PUT ALL TRACKS IN A JSON FILE AND READ FROM IT, SO THAT IT IS EASIER TO ADD MORE TRACKS AND PLAYLISTS IN THE FUTURE.'''
#links: https://open.spotify.com/playlist/3Z9bBKzJIH1CDOHbocizHN
#https://open.spotify.com/playlist/7y7hnyXo4wtBSfigri0vgg
#https://open.spotify.com/playlist/6pcuzwZSIw7OgL149bgJmZ

#MAJOR BUG: API asks to login, is appearing patch and doesn't play track songs
#Either use another solution or hardcode the tracks with proper licenses
# Worst case: scrap for base elevator music
#worst to worst case: scrap music as a whole
#Need to add multi browser and window support
TRACKS = [
    {
        "name": "Space Oddity - David Bowie",
        "playlist": "NASA Wake Up Music",
        "id": "72Z17vmmeQKAg8bptWvpVG",
    },
    {
        "name": "Here Comes The Sun - The Beatles",
        "playlist": "NASA Wake Up Music",
        "id": "6dGnYIeXmHdcikdzNNDMm2",
    },
    {
        "name": "Rocket Man - Elton John",
        "playlist": "NASA Moon Tunes",
        "id": "3gdewACMIVMEWVbyb8O9sY",
    },
    {
        "name": "Starman - David Bowie",
        "playlist": "NASA Moon Tunes",
        "id": "0pQskrTITgmCMyr85tb9qq",
    },
    {
        "name": "Johnny B. Goode - Chuck Berry",
        "playlist": "Voyager Golden Record",
        "id": "2QfiRTz5Yc8DdShCxG1tB2",
    },
    {
        "name": "Brandenburg Concerto No. 2 - Bach",
        "playlist": "Voyager Golden Record",
        "id": "4c2W3VKsOFoIg2SFaO6DY5",
    },
]


def _load_vinyl_b64():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_dir, "Data", "vinyl.png")
    if os.path.exists(icon_path):
        with open(icon_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""


def render_header_player():
    vinyl_b64 = _load_vinyl_b64()
    tracks_json = json.dumps(TRACKS)
    initial_idx = random.randrange(len(TRACKS))

    html_code = f"""
    <style>
        html, body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
    </style>
    <div id="music-widget" style="display:flex; flex-direction:column; align-items:flex-end; font-family:Inter,sans-serif; user-select:none; width:100%;">
        <div id="vinyl-btn" title="Click: On/Mute | Double-click: Change track"
             style="position:relative; width:34px; height:34px; cursor:pointer; display:flex; align-items:center; justify-content:center; border-radius:6px; padding:3px; box-sizing:border-box;">
            <img id="vinyl-img" src="data:image/png;base64,{vinyl_b64}"
                 style="width:26px; height:26px; object-fit:contain; opacity:0.7; transition:transform 0.2s, opacity 0.2s;" />
            <svg id="mute-slash" viewBox="0 0 36 36"
                 style="position:absolute; top:0; left:0; width:34px; height:34px; pointer-events:none; display:block;">
                <line x1="6" y1="30" x2="30" y2="6" stroke="#FC3D21" stroke-width="2.8" stroke-linecap="round" />
            </svg>
        </div>
        <div id="track-label" style="font-size:10px; color:#8C9FB5; max-width:100%; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; text-align:right; margin-top:2px;">
            Muted
        </div>
        <div id="player-wrap" style="display:none; margin-top:4px; width:100%;">
            <iframe id="sp-iframe" src="" width="100%" height="80" frameBorder="0"
                    allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"
                    style="border-radius:6px; display:block;"></iframe>
        </div>
    </div>
    <script>
        const tracks = {tracks_json};
        let idx = {initial_idx};
        let isOn = false;
        let clickTimer = null;

        const btn = document.getElementById("vinyl-btn");
        const img = document.getElementById("vinyl-img");
        const slash = document.getElementById("mute-slash");
        const label = document.getElementById("track-label");
        const wrap = document.getElementById("player-wrap");
        const iframe = document.getElementById("sp-iframe");

        try {{
            const bg = window.parent.getComputedStyle(window.parent.document.body).backgroundColor;
            const m = bg.match(/\d+/g);
            if (m && (0.299 * m[0] + 0.587 * m[1] + 0.114 * m[2]) > 128) {{
                btn.style.backgroundColor = "transparent";
            }} else {{
                btn.style.backgroundColor = "#FFFFFF";
            }}
        }} catch (e) {{
            btn.style.backgroundColor = "transparent";
        }}

        function updateUI() {{
            if (isOn) {{
                slash.style.display = "none";
                img.style.opacity = "1";
                label.textContent = tracks[idx].name;
                label.style.color = "#02BFE7";
                wrap.style.display = "block";
                iframe.src = "https://open.spotify.com/embed/track/" + tracks[idx].id + "?utm_source=generator&theme=0";
            }} else {{
                slash.style.display = "block";
                img.style.opacity = "0.55";
                label.textContent = "Muted";
                label.style.color = "#8C9FB5";
                wrap.style.display = "none";
                iframe.src = "";
            }}
        }}

        btn.addEventListener("click", function() {{
            if (clickTimer) return;
            clickTimer = setTimeout(function() {{
                clickTimer = null;
                isOn = !isOn;
                updateUI();
            }}, 230);
        }});

        btn.addEventListener("dblclick", function(e) {{
            e.preventDefault();
            if (clickTimer) {{
                clearTimeout(clickTimer);
                clickTimer = null;
            }}
            idx = (idx + 1) % tracks.length;
            isOn = true;
            updateUI();
        }});
    </script>
    """
    components.html(html_code, height=130)
