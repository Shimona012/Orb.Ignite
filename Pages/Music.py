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
#ONLY taking 10 tracks from the three playlists, as the API is not working properly and is asking to login, which is not ideal for a public-facing app.
#links: https://open.spotify.com/playlist/3Z9bBKzJIH1CDOHbocizHN
#https://open.spotify.com/playlist/7y7hnyXo4wtBSfigri0vgg
#https://open.spotify.com/playlist/6pcuzwZSIw7OgL149bgJmZ

#Only available after login
#To add if fails elevator royalty free music or lofi.
#FALLBACKS:
'''
Music: 'Golden Age' by Walz on #Uppbeat https://uppbeat.io/c/walz
License code: 3TI5DPK80SFLD86C (IN DATA/MUSIC)
Music by Bensound.com/royalty-free-music (Moonlight drive)
License code: RUOL1IOWB4D33SIE
Artist: : Yunior Arronte (IN DATA/MUSIC
Music track: Time by Avanti
Source: https://freetouse.com/music
Vlog Music for Video (Free Download) (IN MUSIC/DATA))
'''
TRACKS = [
    {
        "name": "Space Oddity - David Bowie",
        "playlist": "NASA Wake Up Music",
        "id": "72Z17vmmeQKAg8bptWvpVG",
    },
    {
        "name": "Space Song - Beach House",
        "playlist": "NASA Moon Tunes",
        "id": "7H0ya83CMmgFcOhw0UB6ow",
    },
    {
        "name": "Contact - Daft Punk",
        "playlist": "NASA Moon Tunes",
        "id": "2KHRENHQzTIQ001nlP9Gdc",
    },
    {
        "name": "The Great Gig in the Sky - Pink Floyd",
        "playlist": "NASA Moon Tunes",
        "id": "1BzrVqFPMh2wGkybtkvNBn",
    },
    {
        "name": "Rocket Man - Elton John",
        "playlist": "NASA Wake Up Music",
        "id": "3gdewACMIVMEWVbyb8O9sY",
    },
    {
        "name": "Fly Me to the Moon - Frank Sinatra",
        "playlist": "NASA Wake Up Music",
        "id": "0yg49bYAl6VLzqqXKKRYvA",
    },
    {
        "name": "Brandenburg Concerto No. 2 - J.S. Bach",
        "playlist": "Voyager Golden Record",
        "id": "7pIkLvY2JWlmjyF6MBZBbC",
    },
    {
        "name": "Jaat Kahan Ho - Kesarbai Kerkar",
        "playlist": "Voyager Golden Record",
        "id": "2UJ8Fg20zeJiC8WQEEE9uQ",
    },
    {
        "name": "Dark Was the Night, Cold Was the Ground - Blind Willie Johnson",
        "playlist": "Voyager Golden Record",
        "id": "6u4FEA3oRz5kxriZVYpoQJ",
    },
    {
        "name": "El Cascabel - Trio Aguilillas",
        "playlist": "Voyager Golden Record",
        "id": "2ID2393aRMYjbt14fuP735",
    },
]

@st.cache_data(show_spinner=False)
def _load_vinyl_b64():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_dir, "Data", "vinyl.png")
    if os.path.exists(icon_path):
        with open(icon_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""


def render_header_player():
    col_fb, col_sp = st.columns([1.0, 1.25], gap="medium", vertical_alignment="top")

    with col_fb:
        with st.expander("NASA Audio / Fallback", expanded=False):
            fallback_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Data", "MUSIC")
            fallback_tracks = [
                {"name": "Golden Age (Walz)", "file": "golden-age-walz-main-version-4077-03-22.mp3", "credit": "Uppbeat | License: 3TI5DPK80SFLD86C"},
                {"name": "Moonlight Drive (Bensound)", "file": "bensound-moonlightdrive.mp3", "credit": "Bensound / Yunior Arronte | License: RUOL1IOWB4D33SIE"},
                {"name": "Time (Avanti)", "file": "Avanti - Time (freetouse.com).mp3", "credit": "Avanti / freetouse.com (Free Download)"},
            ]
            options = ["Off (Select track to play)"] + [t["name"] for t in fallback_tracks]
            sel_name = st.selectbox(
                "Select Fallback Track",
                options,
                index=0,
                key="header_fb_music_sel",
                label_visibility="collapsed",
            )
            track_obj = next((t for t in fallback_tracks if t["name"] == sel_name), None)
            if track_obj:
                local_path = os.path.join(fallback_dir, track_obj["file"])
                if os.path.exists(local_path):
                    st.audio(local_path, format="audio/mp3")
                    st.caption(track_obj["credit"])

    with col_sp:
        vinyl_b64 = _load_vinyl_b64()
        tracks_json = json.dumps(TRACKS)
        initial_idx = random.randrange(len(TRACKS))

        html_code = f"""
        <style>
            html, body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
        </style>
        <div id="music-widget" style="display:flex; flex-direction:column; align-items:flex-end; font-family:Inter,sans-serif; user-select:none; width:100%; padding-top:4px; padding-right:12px; box-sizing:border-box;">
            <div id="vinyl-btn" title="Click: On/Mute | Double-click: Change track"
                 style="position:relative; width:34px; height:34px; cursor:pointer; display:flex; align-items:center; justify-content:center; border-radius:6px; padding:3px; box-sizing:border-box; transition:background-color 0.2s, border-color 0.2s;">
                <img id="vinyl-img" src="data:image/png;base64,{vinyl_b64}"
                     style="width:26px; height:26px; object-fit:contain; opacity:0.75; transition:transform 0.2s, opacity 0.2s;" />
                <svg id="mute-slash" viewBox="0 0 36 36"
                     style="position:absolute; top:0; left:0; width:34px; height:34px; pointer-events:none; display:block;">
                    <line x1="6" y1="30" x2="30" y2="6" stroke="#FC3D21" stroke-width="2.8" stroke-linecap="round" />
                </svg>
            </div>
            <div id="track-label" style="font-size:10px; color:#8C9FB5; max-width:100%; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; text-align:right; margin-top:2px; font-weight:500;">
                Muted
            </div>
            <div id="player-wrap" style="display:none; margin-top:4px; width:100%; min-width:260px; max-width:360px;">
                <iframe id="sp-iframe" src="" width="100%" height="80" frameBorder="0"
                        allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"
                        style="border-radius:6px; display:block; border:none; box-shadow:0 4px 14px rgba(0,0,0,0.28);"></iframe>
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

            function syncTheme() {{
                try {{
                    const body = window.parent.document.body;
                    const app = window.parent.document.querySelector('.stApp');
                    const isLight = (body && body.getAttribute('data-theme') === 'light') ||
                                    (app && app.getAttribute('data-theme') === 'light');
                    if (isLight) {{
                        btn.style.backgroundColor = "rgba(15, 23, 42, 0.06)";
                        btn.style.border = "1px solid rgba(15, 23, 42, 0.16)";
                        if (!isOn) {{
                            label.style.color = "#64748B";
                        }}
                    }} else {{
                        btn.style.backgroundColor = "#FFFFFF";
                        btn.style.border = "1px solid rgba(255, 255, 255, 0.2)";
                        if (!isOn) {{
                            label.style.color = "#8C9FB5";
                        }}
                    }}
                }} catch (e) {{
                    btn.style.backgroundColor = "#FFFFFF";
                }}
            }}
            syncTheme();

            try {{
                const target = window.parent.document.body;
                if (target && window.MutationObserver) {{
                    const obs = new MutationObserver(syncTheme);
                    obs.observe(target, {{ attributes: true, attributeFilter: ['data-theme', 'data-base-theme'] }});
                }}
            }} catch (e) {{}}

            function updateUI() {{
                try {{
                    if (window.frameElement) {{
                        const h = isOn ? "148px" : "56px";
                        window.frameElement.style.height = h;
                        let p = window.frameElement.parentElement;
                        while (p && p !== window.parent.document.body) {{
                            if (p.getAttribute && (
                                p.getAttribute('data-testid') === 'stCustomComponentV1' ||
                                p.getAttribute('data-testid') === 'stElementContainer' ||
                                p.classList.contains('element-container')
                            )) {{
                                p.style.height = h;
                                p.style.minHeight = h;
                                p.style.overflow = "visible";
                            }}
                            p = p.parentElement;
                        }}
                    }}
                }} catch (e) {{}}

                if (isOn) {{
                    slash.style.display = "none";
                    img.style.opacity = "1";
                    label.textContent = tracks[idx].name;
                    label.style.color = "#EA580C";
                    wrap.style.display = "block";
                    iframe.src = "https://open.spotify.com/embed/track/" + tracks[idx].id + "?utm_source=generator&theme=0";
                }} else {{
                    slash.style.display = "block";
                    img.style.opacity = "0.6";
                    label.textContent = "Muted";
                    wrap.style.display = "none";
                    iframe.src = "";
                    syncTheme();
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
        components.html(html_code, height=56)
