import os
import streamlit

p = os.path.join(os.path.dirname(streamlit.__file__), "static", "index.html")
if os.path.exists(p):
    with open(p, "r", encoding="utf-8") as f:
        c = f.read()
    
    tags = (
        '<meta name="description" content="𝘕𝘰𝘵 𝘢𝘭𝘭 𝘧𝘭𝘢𝘮𝘦𝘴 𝘢𝘳𝘦 𝘮𝘦𝘢𝘯𝘵 𝘵𝘰 𝘣𝘦 𝘧𝘭𝘰𝘸𝘯 𝘵𝘰𝘰 𝘤𝘭𝘰𝘴𝘦 𝘵𝘰." />'
        '<meta property="og:title" content="Orb.Ignite" />'
        '<meta property="og:description" content="𝘕𝘰𝘵 𝘢𝘭𝘭 𝘧𝘭𝘢𝘮𝘦𝘴 𝘢𝘳𝘦 𝘮𝘦𝘢𝘯𝘵 𝘵𝘰 𝘣𝘦 𝘧𝘭𝘰𝘸𝘯 𝘵𝘰𝘰 𝘤𝘭𝘰𝘴𝘦 𝘵𝘰." />'
        '<meta property="og:type" content="website" />'
        '<meta property="og:url" content="https://orbignite.earth" />'
        '<meta property="og:site_name" content="Orb.Ignite" />'
        '<meta name="twitter:card" content="summary" />'
        '<meta name="twitter:title" content="Orb.Ignite" />'
        '<meta name="twitter:description" content="𝘕𝘰𝘵 𝘢𝘭𝘭 𝘧𝘭𝘢𝘮𝘦𝘴 𝘢𝘳𝘦 𝘮𝘦𝘢𝘯𝘵 𝘵𝘰 𝘣𝘦 𝘧𝘭𝘰𝘸𝘯 𝘵𝘰𝘰 𝘤𝘭𝘰𝘴𝘦 𝘵𝘰." />'
    )
    if '<title>Streamlit</title>' in c:
        c = c.replace('<title>Streamlit</title>', '<title>Orb.Ignite</title>' + tags)
    elif '<title>Orb.Ignite</title>' in c and '<meta property="og:description"' not in c:
        c = c.replace('<title>Orb.Ignite</title>', '<title>Orb.Ignite</title>' + tags)
    
    with open(p, "w", encoding="utf-8") as f:
        f.write(c)
    print("Patched index.html successfully!")
