# app.py — Application Dash unique + authentification SQLite + mode "session-only"
import os
import sqlite3
from datetime import datetime, time, timedelta
import uuid
from functools import wraps
import time as time_module

from flask import Flask, render_template_string, request, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

import dash
from dash import html, dcc, Input, Output, State, Patch, callback_context
import dash_bootstrap_components as dbc

import pandas as pd
import yaml
import json

import random
import re
import shutil
import base64
import io
import glob

import numpy as np

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from dash.dependencies import Output, Input
from dash.exceptions import PreventUpdate

import pandas as pd
import folium
import folium.plugins

import subprocess


import dash_bio as dash_bio

from plotly_upset.plotting import plot_upset

import submit_genomes
import homepage

import xml.etree.ElementTree as ET
import struct

# Helper to get image dimensions without external heavy dependencies
def get_image_dimensions(path):
    width, height = 800, 600 # Default fallback
    try:
        if path.endswith('.png'):
            with open(path, 'rb') as f:
                head = f.read(24)
                if len(head) == 24 and head.startswith(b'\211PNG\r\n\032\n'):
                    # PNG header: 8 bytes magic + 4 bytes chunk len + 4 bytes 'IHDR' + 4 bytes width + 4 bytes height
                    check = struct.unpack('>i', head[4:8])[0]
                    if check != 0x0d0a1a0a: # Check for not matching IHDR (rare)
                        width, height = struct.unpack('>ii', head[16:24])
                    else:
                        width, height = struct.unpack('>ii', head[16:24])
        elif path.endswith('.svg') or path.endswith('svg'):
            # Simple SVG parsing
            tree = ET.parse(path)
            root = tree.getroot()
            # Try width/height attributes
            w_str = root.attrib.get('width', '')
            h_str = root.attrib.get('height', '')
            # Try viewBox if width/height missing
            if not w_str or not h_str:
                viewbox = root.attrib.get('viewBox', '').split()
                if len(viewbox) == 4:
                    width = float(viewbox[2])
                    height = float(viewbox[3])
            else:
                width = float(w_str.replace('px', '').replace('pt', ''))
                height = float(h_str.replace('px', '').replace('pt', ''))
    except Exception as e:
        print(f"Could not determine image dimensions: {e}")
    
    return width, height


def validate_fasta_input(raw_text):
    max_len = 200000
    if not raw_text or not raw_text.strip():
        return False, "", "FASTA input is empty.", ""

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines or not lines[0].startswith(">"):
        return False, "", "FASTA must start with a header line beginning with '>'", ""

    # Include U for RNA, and standard ambiguity codes
    valid_chars = set("ACDEFGHIKLMNPQRSTVWYBXZJUO*-")
    # Core nucleotides used to calculate if the sequence is mostly DNA/RNA
    core_nucleotides = set("ACGTUN-") 
    
    total_len = 0
    nucleotide_count = 0
    cleaned_lines = []

    for line in lines:
        if line.startswith(">"):
            cleaned_lines.append(line)
            continue

        cleaned = re.sub(r"\s+", "", line).upper()
        if not cleaned:
            continue

        for ch in cleaned:
            if ch not in valid_chars:
                return False, "", f"Invalid character in FASTA: '{ch}'", ""
            if ch in core_nucleotides:
                nucleotide_count += 1

        total_len += len(cleaned)
        cleaned_lines.append(cleaned)

    if total_len < 20:
        return False, "", "FASTA sequence is too short (min 20 bp/aa).", ""

    if total_len > max_len:
        return False, "", f"FASTA sequence is too long (max {max_len} bp/aa).", ""

    # Threshold-based detection: If > 85% of chars are standard DNA/RNA bases, call it DNA.
    # This prevents proteins composed of ambiguous DNA letters from being misclassified.
    seq_type = "dna" if (nucleotide_count / total_len) > 0.85 else "protein"
    
    # Reconstruct the cleaned FASTA text safely
    processed_text = "\n".join(cleaned_lines) + "\n"
    
    return True, processed_text, "", seq_type

# Optional: ag-grid (used in original app). If absent, fallback to html table.
try:
    import dash_ag_grid as dag
    AGGRID_AVAILABLE = True
except Exception:
    AGGRID_AVAILABLE = False

colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', '#800000', '#008000', '#000080', '#808000', '#800080', '#008080', '#C0C0C0', '#808080']

tabs_styles = {
    'height': '44px'
}
tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '6px'
}

layout_config = {
#    "labels": {"display": False},
    "innerRadius": 365,
    "outerRadius": 370,
    "cornerRadius": 4,
    "labels": {
        "size": 22,
        "color": "#4d4d4d",
        "outerRadius": 100
    },
    "ticks": {
        "color": "#4d4d4d",
        "labelColor": "#4d4d4d",
        "spacing": 1000000,
        "labelSuffix": "Mb",
        "labelDenominator": 1000000,
        "labelSize": 12,
    },
    "legend": {
        "title": "Legend",
    }
}

stack_config = {
    "innerRadius": 0.7,
    "outerRadius": 1,
    "thickness": 2,
    "margin": 800000,
    "direction": "out",
    "color": {"name": "color"},
    "strokeWidth": 0,
}

highlight_config1 = {
    "innerRadius": 330,
    "outerRadius": 350,
    "color": "blue",
}
highlight_config2 = {
    "innerRadius": 300,
    "outerRadius": 320,
    "color": "red",
}
highlight_config3 = {
    "innerRadius": 260,
    "outerRadius": 280,
    "color": "purple",
}
highlight_config4 = {
    "innerRadius": 230,
    "outerRadius": 250,
    "color": "green",
}
columnDefs = [
    {
        "field": "Strain name",
        "checkboxSelection": True,
        "headerCheckboxSelection": True,
        "width": 500
    },
    {"field": "Country","width": 300},
    {"field": "Continent","width": 300},
    {"field": "Organism","width": 800}
]

columnDefs2 = [
    {
        "field": "ID",
        "width": 120,
        "checkboxSelection": True,
        "headerCheckboxSelection": True,
    },
    {"field": "Repeat","width": 200,},
    {"field": "Flanking","width": 1000,},
]


columnDefs4 = [
    {"field": "Species","width": 400},
    {"field": "Genes","width": 400},
]

data = ""
tmp_dir = "tmp"

# ---------- Config ----------
DB_PATH = "example_auth.db"
CONFIG_YAML = "panexplorer_config.yaml"

#session = random.randint(1, 9000000)

with open(CONFIG_YAML, "r") as f:
    conf = yaml.safe_load(f)

plink_exe = conf.get("plink_exe") or "plink"
plink2_exe = conf.get("plink2_exe") or "plink2"
snmf_exe = conf.get("snmf_exe") or "sNMF"
vcf2geno_exe = conf.get("vcf2geno_exe") or "vcf2geno"
scoary_exe = conf.get("scoary_exe") or "scoary2"
SECRET_KEY = conf.get("secret_key")
WEB_URL = conf.get("web_url") or "localhost:8050"

# ---------- DB helpers ----------
def init_db():
    need_create = not os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if need_create:
        c.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                path TEXT NOT NULL,
                is_public INTEGER NOT NULL DEFAULT 1,
                owner_id INTEGER,
                session_code TEXT,
                session_expiration TEXT,
                FOREIGN KEY(owner_id) REFERENCES users(id)
            )
        """)

        conn.commit()
    conn.close()


def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    return (rows[0] if rows else None) if one else rows

def execute_db(query, args=()):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    conn.close()

# ---------- Login Rate Limiting ----------
login_attempts = {}  # {username: [(timestamp, success), ...]}
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_WINDOW = 900  # 15 minutes in seconds
LOCKOUT_DURATION = 1800  # 30 minutes in seconds

def validate_username(username):
    """Validate username format and length."""
    if not username or not isinstance(username, str):
        return False
    if len(username) < 3 or len(username) > 64:
        return False
    # Only alphanumeric, underscore, hyphen
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', username))

def check_rate_limit(username):
    """Check if user has exceeded login attempt limit."""
    now = time_module.time()
    
    if username not in login_attempts:
        login_attempts[username] = []
    
    # Clean old attempts outside the window
    login_attempts[username] = [
        (ts, success) for ts, success in login_attempts[username]
        if now - ts < LOGIN_ATTEMPT_WINDOW
    ]
    
    # Check for lockout (multiple failed attempts)
    recent_failures = [ts for ts, success in login_attempts[username] if not success]
    if len(recent_failures) >= MAX_LOGIN_ATTEMPTS:
        # Check if user is in lockout period
        if now - recent_failures[-1] < LOCKOUT_DURATION:
            return False, "Too many login attempts. Try again later."
    
    return True, ""

def record_login_attempt(username, success):
    """Record a login attempt."""
    if username not in login_attempts:
        login_attempts[username] = []
    login_attempts[username].append((time_module.time(), success))

# ---------- Sync projects (from YAML folder list) ----------
def sync_projects_from_yaml():
    if not os.path.exists(CONFIG_YAML):
        print("panexplorer_config.yaml not found.")
        return
    with open(CONFIG_YAML, "r") as f:
        conf = yaml.safe_load(f)
    data_dir = conf.get("data_dir") or conf.get("directory") or "data"
    if not os.path.isdir(data_dir):
        print(f"data_dir {data_dir} not found. Check panexplorer_config.yaml")
        return
    subdirs = [f.name for f in os.scandir(data_dir) if f.is_dir()]
    # optionally filter numeric folders (like in original)
    # subdirs = [d for d in subdirs if not d[0].isdigit()]
    #execute_db("INSERT INTO projects (title, path, session_code) VALUES (?, ?, ?)", ('3038197835880205192092415', '/mnt/c/Users/dereeper/Documents/formation_python_scientifique_2022/dash/data/3038197835880205192092415', '3038197835880205192092415'))
    for sub in subdirs:
        path = os.path.join(data_dir, sub)
        exists = query_db("SELECT id FROM projects WHERE path = ?", (path,), one=True)
        if not exists:
            execute_db("INSERT INTO projects (title, path, is_public) VALUES (?, ?, ?)", (sub, path, 1))
            print("Add project:", sub, path)

# ---------- Flask + Login ----------
server = Flask(__name__)
server.secret_key = SECRET_KEY
server.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
server.config['SESSION_COOKIE_SECURE'] = True  # Only send over HTTPS
server.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
server.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id_, username):
        self.id = str(id_)
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    r = query_db("SELECT id, username FROM users WHERE id = ?", (int(user_id),), one=True)
    if r:
        return User(r[0], r[1])
    return None

LOGIN_PAGE = """
<!doctype html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Login</title>
<style>
body { font-family: Arial, sans-serif; }
.container { max-width: 400px; margin: 50px auto; padding: 20px; border: 1px solid #ccc; border-radius: 5px; }
.messages { color: red; margin-bottom: 20px; }
form { display: flex; flex-direction: column; }
label { margin-bottom: 5px; margin-top: 10px; }
input[type="text"], input[type="password"] { padding: 8px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 3px; }
input[type="submit"] { padding: 10px; background-color: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; }
input[type="submit"]:hover { background-color: #0056b3; }
.help-text { font-size: 0.85em; color: #666; margin-top: 15px; }
</style>
</head>
<body>
<div class="container">
<h2>Login</h2>
{% with messages = get_flashed_messages() %}
  {% if messages %}
    <div class="messages">
    {% for m in messages %}
      <p>{{ m }}</p>
    {% endfor %}
    </div>
  {% endif %}
{% endwith %}
<form method="post">
  <label for="username">Username:</label>
  <input type="text" id="username" name="username" required maxlength="64" autocomplete="username">
  
  <label for="password">Password:</label>
  <input type="password" id="password" name="password" required autocomplete="current-password">
  
  <input type="submit" value="Login">
</form>
<p><a href="/">Back to home</a></p>
</div>
</body>
</html>
"""

@server.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        # Validate username format
        if not validate_username(username):
            flash("Invalid username format. Use 3-64 alphanumeric characters, underscore, or hyphen.")
            return render_template_string(LOGIN_PAGE)
        
        # Check rate limiting
        allowed, msg = check_rate_limit(username)
        if not allowed:
            flash(msg)
            return render_template_string(LOGIN_PAGE)
        
        # Query user (constant-time comparison)
        r = query_db("SELECT id, username, password_hash FROM users WHERE username = ?", (username,), one=True)
        
        # Always check password (even if user doesn't exist) to prevent user enumeration
        # Use a dummy hash if user not found
        password_hash = r[2] if r else generate_password_hash("dummy_password_that_wont_match")
        password_match = check_password_hash(password_hash, password)
        
        if r and password_match:
            user_obj = User(r[0], r[1])
            login_user(user_obj, remember=False)
            record_login_attempt(username, True)
            return redirect("/")
        
        # Generic error message to prevent user enumeration
        record_login_attempt(username, False)
        flash("Invalid username or password. Please try again.")
    
    return render_template_string(LOGIN_PAGE)

@server.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

# ---------- Dash App ----------
external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.title = "PanExplorer v2"

# IDs used: 'url', 'projets', 'metadata_table', 'project_detail' (keeps similarity with original)
def main_layout():
    

    return html.Div([
        dcc.Location(id="url", refresh=False),
        #build_navbar(),

        dbc.Navbar(
            
            dbc.Nav([
                html.Img(
                                src="/assets/panexplorer_logo8.png",
                                height="65px",
                                className="me-2"
                            ),
                dbc.NavLink("Home", href="/", className="nav-item-box",style={"fontSize":"16px","fontWeight":"bold","marginTop":"10px","marginLeft":"40px"}),
                html.A("Browse projects", href="/browse", className="nav-item-box", style={"fontSize":"16px","fontWeight":"bold","marginTop":"10px","marginLeft":"40px"}),
                dbc.NavLink("Import genomes", href="/submit_genomes", className="nav-item-box",style={"fontSize":"16px","fontWeight":"bold","marginTop":"10px","marginLeft":"40px"}),
            ],

            ),
            color="light",
        ),
        
        html.Div(id="page-content")
    ])

app.layout = main_layout()





def validate_session_id(session_id):
    """
    Validate that session_id is a valid UUID format or legacy numeric format.
    """
    try:
        uuid.UUID(str(session_id))
        return True
    except (ValueError, AttributeError):
        # Also accept legacy numeric sessions for backward compatibility
        return isinstance(session_id, str) and session_id.isdigit()

# Helper: project by session code
def get_project_by_session(code):
    r = query_db("SELECT id, title, path, is_public, owner_id, session_expiration FROM projects WHERE session_code = ?", (code,), one=True)
    if not r:
        return None
    return {"id": r[0], "title": r[1], "path": r[2], "is_public": bool(r[3]), "owner_id": r[4], "session_expiration": r[5]}

# Helper: visible projects for user
def list_visible_projects(user):
    if user is None:
        rows = query_db("SELECT id, title, path, is_public, owner_id FROM projects WHERE is_public = 1 ORDER BY title")
    else:
        rows = query_db("""SELECT id, title, path, is_public, owner_id FROM projects
                           WHERE is_public = 1 OR owner_id = ? ORDER BY title""", (user['id'],))
    return [{"id": r[0], "title": r[1], "path": r[2], "is_public": bool(r[3]), "owner_id": r[4]} for r in rows]


@app.callback(
    Output("page-content", "children", allow_duplicate=True),
    Input("url", "pathname"),
    prevent_initial_call=True
)
def display_page(pathname):

    if pathname == "/submit_genomes":
        return submit_genomes.layout
    elif pathname == "/":
        return homepage.layout
    elif pathname == "/browse":
        # simplified UI inspired from app-pav.py
        ui = html.Div([
            header,
            
            html.Div([
                html.Label("Choose a project: "),
                dcc.Dropdown(id="projets", options=options, value=default_value, style={"width":"450px"})
            ], style={"marginBottom":"1rem"}),
            html.Div(id="project-preview"),
            html.Hr(),
            html.Div(id="project-detail-area")  # where full PAV UI would go (graphs, tabs...)
        ], style={"padding":"10px"})

        return ui
    

# Render page: session-only OR normal app
@app.callback(
    Output("page-content", "children"),
    Input("url", "search")
)
def render_page(search):

    # parse session param
    session_code = None
    if search:
        import urllib.parse
        params = urllib.parse.parse_qs(search.lstrip("?"))
        session_code = params.get("session", [None])[0]

    
    if session_code:
        if validate_session_id(session_code):
            proj = get_project_by_session(session_code)
            if not proj:
                dir = conf["session_dir"] + "/" + session_code


                if os.path.isdir(dir):
                    print("exists")
                else:
                    return html.Br(), dbc.Alert(html.P("Session does not exist", className="alert-heading"),color="danger")

        else:
            return html.Br(), dbc.Alert(html.P("Session is not accepted (must be UUID or legacy numeric ID)", className="alert-heading"),color="danger")     


    # Normal mode: header + dropdown + area for the simplified PAV UI
    if current_user.is_authenticated:
        user_row = query_db("SELECT id, username FROM users WHERE id = ?", (int(current_user.get_id()),), one=True)
        
        right_menu = dbc.Button(
                f"Logout ({user_row[1]})",
                href="/logout",
                external_link=True,
                color="secondary",
            )
        
        user_obj = {"id": user_row[0], "username": user_row[1]}
    else:
        
        right_menu = dbc.Button(
                f"Login",
                href="/login",
                external_link=True,
                color="primary"
                
            )
        user_obj = None

    visible = list_visible_projects(user_obj)
    options = []
    if session_code:
        options = [{"label": session_code, "value": session_code} ]
    else:
        options = [{"label": p["title"] + ("" if p["is_public"] else " (private)"), "value": p["title"]} for p in visible]


    # default selection
    default_value = options[0]["value"] if options else None
    
    # simplified UI inspired from app-pav.py
    if os.path.exists(conf["session_dir"]+"/"+str(session_code)+"/1.Orthologs_Cluster.txt") and os.path.getsize(conf["session_dir"]+"/"+str(session_code)+"/1.Orthologs_Cluster.txt") == 0:
        ui = html.Div([
                html.Br(),
                dbc.Alert("Error: The pipeline failed with this dataset.", color="danger")
            ])
    else:

        ui = html.Div([
            
            html.Div(right_menu,style={"textAlign":"right","marginTop":"0px","marginRight":"2px"}),
            html.Div([
                html.Label("Choose a project: "),
                dcc.Dropdown(id="projets", options=options, value=default_value, style={"width":"450px"})
            ], style={"marginBottom":"1rem"}),
            html.Div(id="project-preview"),
            html.Hr(),
            html.Div(id="project-detail-area")  # where full PAV UI would go (graphs, tabs...)
        ], style={"padding":"10px"})

    return ui


# Load project metadata and present a table (simplified replacement for big app-pav callbacks)
@app.callback(
    Output("project-preview", "children"),
    Input("projets", "value")
)
def load_project_preview(proj_title):
    if not proj_title:
        return html.Div("Aucun projet sélectionné.")
    row = query_db("SELECT id, title, path, is_public FROM projects WHERE title = ?", (proj_title,), one=True)

    
    print(proj_title)
    proj = None
    if not row:
        #return html.Div(f"Project not found in database. {proj_title}")
        proj = {"title": proj_title, "path": conf["session_dir"] + "/" + proj_title, "is_public": 0}
    else:
        proj = {"id": row[0], "title": row[1], "path": row[2], "is_public": bool(row[3])}
    path = proj["path"]
    meta_path = os.path.join(path, "metadata.xls")
    if not os.path.exists(meta_path):
        return html.Div([html.H6(proj["title"]), html.P("Aucun metadata.xls dans ce projet.")])
    # read metadata (first 500 rows for safety)
    try:
        df = pd.read_csv(meta_path, sep="\t", nrows=500)
    except Exception as e:
        return html.Div([html.H4(proj["title"]), html.P(f"Error reading metadata: {meta_path}")])
    # Show some info and table (ag-grid if available)
    children = [ html.H4(f" {len(df)} genomes")]
    if AGGRID_AVAILABLE:
        
        
        grid = dag.AgGrid(id="metadata_table",
                          #columnDefs=[{"field": c} for c in df.columns],
                          #style={'width': '100vh','margin-left': '15px'},
                          columnDefs=columnDefs,
                          selectedRows=df.to_dict("records"),
                          
                          selectAll=True,
                          #defaultColDef={"filter": True},

                          rowData=df.to_dict("records"),
                          columnSize="sizeToFit",
                          dashGridOptions={"rowSelection": "multiple"},
                          #dashGridOptions={"rowSelection": {'mode': 'multiRow'}, "suppressRowClickSelection": True, "animateRows": False},
                          #dashGridOptions={"rowSelection":"multiple","pagination": True, "animateRows": False}
                          
                          )
        
                          

        children.append(grid)
        children.append(html.Br())
        children.append(html.Label('Reference Genome for projection ', style={'margin-right': '15px'}))
        children.append(
            dcc.Dropdown(
                    id='reference',
                    style={'width': '500px'},
                    multi=False
                )
        )
        

    else:
        # fallback: simple HTML table (first 50 rows)
        tbl = html.Table(
            [html.Tr([html.Th(c) for c in df.columns])] +
            [html.Tr([html.Td(str(v)) for v in row]) for row in df.head(50).values.tolist()],
            style={"maxHeight":"400px","overflow":"auto","display":"block"}
        )
        children.append(tbl)
    # small action buttons placeholders (update graphs)
    
    
    children.append(html.H5("Search for group-specific genes / pan-GWAS using Scoary"))

    children.append(
        html.Div([
            "Search for clusters specific to these genomes",dcc.Dropdown(
                id='specific_to',
                multi=True
            )
        ], style={'width': '100%', 'display': 'inline-block'}),

    )
    children.append(
        dcc.Checklist(
                id='heatmap_selection',
                options=[{'label': ' By checking this box, the selection can be done by clicking in the Heatmap: only genomes harboring the clicked gene will be included.', 'value':'heatmap_selection'}],
            )
    )
    children.append(html.Br())
    children.append(
        dcc.Input(id='current_cluster', type='hidden'),
        
    )
    children.append(
        dcc.Input(id='current_session', type='hidden'),
        
    )
    
    
    #children.append(html.Button("Update Graphes", id="btn-update", n_clicks=0))
    #children.append(html.Div(id="update-status"))

    children+= [
        
        html.Button("Update graphes", 
                    id="btn-update", 
                    style={
                        "backgroundColor": "#1E90FF",   # bleu
                        "color": "white"
                    },
                    n_clicks=0),

        dcc.Loading(id="mainload", children=html.Div(id='mainloading', style={'whiteSpace': 'pre-line'})),

        html.Div(id='results', style={'display': 'none'}, children=[
            dcc.Tabs(id='tab1', style=tabs_styles, children=[
                
                dcc.Tab(label='Genes (Pangene Atlas)', style=tab_style, selected_style=tab_selected_style, children=[
                    dcc.Tabs(id='tab2', style=tabs_styles, children=[
                        
                    dcc.Tab(label='PAV matrix', style=tab_style, selected_style=tab_selected_style, children=[
                        html.Br(),
                        html.Div(style={"display": "flex","alignItems": "center", "gap": "10px"},children=[
                            html.Div([
                                html.Label("Colors:"),
                                dcc.Dropdown(
                                        ['Presence/absence','Level of presence','Organism','Continent','Country'],
                                        id='colorizing',
                                        value = 'Presence/absence',
                                        style={'width': '200px'},
                                        multi=False
                                    ),
                                 ], style={'display': 'inline-block', 'margin-right': '20px','width':'200px'}),
                            html.Div([
                                html.Label("Highlight:"),
                                dcc.Dropdown(
                                        ['None','Reference genome','Core-genes','Strain-specific genes'],
                                        id='highlight',
                                        value = 'None',
                                        style={'width': '200px'},
                                        multi=False
                                    ),
                                 ], style={'display': 'inline-block', 'margin-right': '20px','width':'200px'}),
                            html.Div([
                                html.Label("Sample ordering:"),
                                dcc.Dropdown(
                                        ['Hierarchical clustering','Population as defined by sNMF'],
                                        id='sample_ordering',
                                        value = 'Hierarchical clustering',
                                        style={'width': '200px'},
                                        multi=False
                                    ),
                                 ], style={'display': 'inline-block', 'margin-right': '20px','width':'200px'}),

                            html.Div([
                                html.Label("Cluster ordering:"),
                                dcc.Dropdown(
                                        ['Hierarchical clustering','Position in genome used for projection'],
                                        value = 'Hierarchical clustering',
                                        id='ordering',
                                        style={'width': '300px'},
                                        multi=False
                                    ),  
                                 ], style={'display': 'inline-block', 'margin-right': '20px','width':'300px'}),
                            html.Div([
                                html.Label("Highlight clusters by keyword or COG:"),
                                dcc.Input(
                                        id='cluster_search',
                                        style={'width': '300px'},
                                        value = '',
                                    ),
                                
                                 ], style={'display': 'inline-block', 'margin-right': '20px','width':'300px'}),
                            html.Div([
                                html.Label("Highlight genomic intervals (bedfile):"),
                                dcc.Textarea(
                                        id='bedfile',
                                        style={'width': '300px', 'height': 30},
                                        value = '',
                                    ),
                                
                                 ], style={'display': 'inline-block', 'margin-right': '20px','width':'300px'}),

                            html.Div([
                                
                                html.Button("Highlight", id="highlight_button",className="thin-button", n_clicks=0),
                                 ], style={'display': 'inline-block', 'margin-right': '20px','width':'300px'}),
                        ]),
                        
                        html.Br(),
                        # html.Div([
                        #     "Search for clusters in these intervals (copy/paste a BED file with intervals of regions): ",
                        #     dcc.Textarea(
                        #         id='bedfile',
                        #         style={'width': '100%', 'height': 50},
                        #     ),
                        # ], style={'width': '600px', 'display': 'inline-block'}),
                        html.Div(id='textarea-example-output', style={'whiteSpace': 'pre-line'}),

                        html.Br(),
                        dcc.Loading(dcc.Graph(id='PAV_graph')),
                        #html.Br(),
                        #html.Div(className="row", id='titles', children=[
                        #     html.H3(id='nb_of_pangenes', style={'width': '60vh','margin-left': '1px'}),
                        #     dcc.Loading(html.H3(id='selected_cluster', style={'width': '60vh','margin-left': '1px'})),
                        # ]),

                        
                        dbc.Row([
                                dbc.Col(
                                    dcc.Loading(
                                        html.Div(children=[
                                            html.H5(id='nb_of_pangenes', style={'width': '60vh','margin-left': '1px'}),
                                            html.H5(id="clustersearch", style={'color': 'red'}),
                                            dag.AgGrid(
                                                    id="table_pangenes",
                                                    rowData=[],
                                                    defaultColDef={"filter": "agTextColumnFilter"},
                                                    #getRowId="params.data.State",
                                                    dashGridOptions={"pagination": True, "animateRows": False}
                                            ),
                                            html.Button("Download table", id="download_table", className="thin-button", n_clicks=0),
                                            dcc.Download(id="download-dataframe2"),
                                        ]),
                                    ),width=8
                                ),
                                dbc.Col(
                                    dcc.Loading(
                                        html.Div(children=[
                                            html.H5(id='selected_cluster', style={'width': '60vh','margin-left': '1px'}),
                                            dag.AgGrid(
                                                        id="genes_cluster",
                                                        rowData=[],
                                                        columnDefs=columnDefs4,
                                                        defaultColDef={"filter": True},
                                                        #columnSize="sizeToFit",
                                                        #getRowId="params.data.State",
                                                        dashGridOptions={"pagination": True, "animateRows": False}
                                                ),
                                            html.Button("Display alignment", id="display_alignment", className="thin-button", n_clicks=0),
                                            html.Button("Display local synteny", id="display_local_synteny", className="thin-button", n_clicks=0),
                                        ]),
                                    ),width=4
                                    
                                ),
                        ]),
                        html.Br(),
                        html.Br(),
                        dcc.Loading(
                                        html.Div(id='default-alignment-viewer-output')
                                    ),
                        
                        
                        
                        
                           
                    ]),
                    # dcc.Tab(label='Upset plot', style=tab_style, selected_style=tab_selected_style, children=[
                    #         html.Br(),
                    #         html.Div(className="row", id='upset', children=[
                    #         dcc.Loading(
                    #                 dcc.Graph(id='graph_upset',style={'width': '200vh', 'height': '50vh','margin-left': '15px'}),
                    #         ),

                            
                    #     ]),
                    # ]),

                    dcc.Tab(label='Statistics', style=tab_style, selected_style=tab_selected_style, children=[
                            html.Br(),
                            html.Div(className="row", id='stats2', children=[
                            dcc.Loading(
                                dbc.Row([
                                    dbc.Col(
                                        dcc.Graph(id='graph_gene2',style={'width': '50vh', 'height': '50vh','margin-left': '15px'}),
                                    ),
                                    dbc.Col(
                                        dcc.Graph(id='graph_pie2',style={'width': '50vh', 'height': '50vh','margin-left': '15px'}),
                                    ),
                                    dbc.Col(
                                        dcc.Graph(id='rarefaction2',style={'width': '50vh', 'height': '50vh','margin-left': '15px'}),
                                    )
                                ]),
                            ),
                        ]),
                    ]),
                    dcc.Tab(label='Circos', style=tab_style, selected_style=tab_selected_style, children=[
                            html.Br(),
                            #dcc.Loading(dcc.Graph(id='circos_graph')),
                            dcc.Loading(
                                html.Div([
                                    html.Div([
                                            html.Span(style={'display': 'inline-block',
                                                'width': '10px',
                                                'height': '10px',
                                                'backgroundColor': "#e74205",
                                                'borderRadius': '3px',
                                                'marginRight': '6px'}),
                                            html.Span("Forward genes", style={'marginRight': '20px'}),
                                            html.Span(style={'display': 'inline-block',
                                                'width': '10px',
                                                'height': '10px',
                                                'backgroundColor': "#1609fd",
                                                'borderRadius': '3px',
                                                'marginRight': '6px'}),
                                            html.Span("Reverse genes", style={'marginRight': '20px'}),
                                            html.Span(style={'display': 'inline-block',
                                                'width': '10px',
                                                'height': '10px',
                                                'backgroundColor': "#7e099b",
                                                'borderRadius': '3px',
                                                'marginRight': '6px'}),
                                            html.Span("Core-genes", style={'marginRight': '20px'}),
                                            html.Span(style={'display': 'inline-block',
                                                'width': '10px',
                                                'height': '10px',
                                                'backgroundColor': '#2ca02c',
                                                'borderRadius': '3px',
                                                'marginRight': '6px'}),
                                            html.Span("Strain-specific genes", style={'marginRight': '20px'}),
                                    ]),
                                    dash_bio.Circos(
                                        id="my-dashbio-default-circos",
                                        layout=[],
                                        config=layout_config,
                                        tracks=[
                                                {
                                                    "type": "HIGHLIGHT",
                                                    "data": [],
                                                    "config": highlight_config1
                                                },
                                                {
                                                    "type": "HIGHLIGHT",
                                                    "data": [],
                                                    "config": highlight_config2
                                                },
                                                {
                                                    "type": "HIGHLIGHT",
                                                    "data": [],
                                                    "config": highlight_config3
                                                },
                                            {
                                                    "type": "HIGHLIGHT",
                                                    "data": [],
                                                    "config": highlight_config4
                                                }
                                            ],
                                    ), 
                                ]),
                        ),
                    ]),
                    
                    dcc.Tab(label='COG/GO', style=tab_style, selected_style=tab_selected_style, children=[
                        html.Br(),
                        # dcc.Loading(dcc.Graph(id='graph_COG_all')),
                        # html.Br(),
                        # dcc.Loading(dcc.Graph(id='graph_COG1')),
                        # html.Br(),
                        dcc.Loading(dcc.Graph(id='graph_COG2')),
                        html.Br(),
                        html.Button('Perform enrichment analysis (core-genes versus accessory genes)', 
                                    id='submit-enrichment', 
                                    style={
                                        "backgroundColor": "#1E90FF",   # bleu
                                        "color": "white",
                                    },
                                    n_clicks=0),
                        html.Br(),
                        html.Br(),
                        dcc.Loading(
                            #dcc.Graph(id='graph_enrichment',style={'display': 'none'})
                            dag.AgGrid(
                                            id="enrichment_table",
                                            style={'display': 'none'},
                                            columnDefs=[{"field": i} for i in ["COG term","odds_ratio","p_value","FDR"]],
                                            rowData=[],
                                        ),
                            
                            
                            ),
                        ]),
                    dcc.Tab(label='Accessory-based tree', style=tab_style, selected_style=tab_selected_style, children=[
                        html.Br(),
                        dbc.Row(
                            [
                                dcc.Loading(html.Iframe(id='iframe-content',style={'width': '1200px', 'height': '800px', 'border': 'none'}))
                            ],
                            align="center",
                        ),
                        html.Br(),
                        ]),
                    dcc.Tab(label='Macro-Synteny', style=tab_style, selected_style=tab_selected_style, children=[
                        html.Br(),
                        html.Div([
                            html.Label('Chromosome: '),
                            dcc.Dropdown(
                                        ['1','2','3','4','5','6','7','8','9','10','11','12'],
                                        id='chromosome',
                                        value = '1',
                                        style={'width': '200px'},
                                        multi=False
                                    ),
                        ], style={'display': 'inline-block', 'margin-right': '20px'}),

                        
                        html.Div([
                            html.Label("Minimum number of genes in a colinear block to be displayed:"),
                            dcc.Dropdown(
                                        ['5','10','15','20'],
                                        id='minimal_size_block',
                                        value = '10',
                                        style={'width': '300px'},
                                        multi=False
                                    ),
                        ], style={'display': 'inline-block', 'margin-right': '20px'}),

                        dcc.Loading(html.Div(id='clinker'),style={'width': '150vh', 'height': '200vh','margin-left': '15px'}),
                        html.Br(),
                        html.Br(),
                        dcc.Loading(dcc.Graph(id='graph_macrosynteny',style={'width': '150vh', 'height': '100vh','margin-left': '15px'})),
                        
                        ]),
                    ]),
                ]),
                dcc.Tab(label='Segments (Pangenome graph)', id='tab_segments', style=tab_style,  selected_style=tab_selected_style, children=[
                    html.Br(),
                    dcc.Loading(dcc.Graph(id='graph_gfa2',style={'width': '100%', 'height': '50vh','margin-left': '15px'})),
                    html.Br(),

                    # ── Search & Highlight panel ─────────────────────────────────────────
                    html.Div(style={'padding':'16px','backgroundColor':'#f7faff','border':'1px solid #ccd6f6','borderRadius':'6px','margin':'0 15px'}, children=[
                        html.H5("Search & Highlight in PAV Matrix", style={'marginBottom':'4px'}),
                        html.Small(
                            "Enter node IDs (e.g. 42,85,120) or a gene name/keyword. "
                            "Auto-detected: all-numeric tokens → node search, text → gene search (matches gene ID and product).",
                            style={'color':'#666'}
                        ),
                        html.Br(), html.Br(),
                        dbc.Row([
                            dbc.Col([
                                dcc.Input(
                                    id='segment-search-input', type='text',
                                    placeholder='Node IDs (e.g. 42,85) or gene keyword…',
                                    debounce=False, className='form-control'
                                ),
                            ], width=8),
                            dbc.Col([
                                html.Button('Search', id='btn-segment-search', n_clicks=0,
                                            className='btn btn-primary', style={'width':'100%'}),
                            ], width=2),
                            dbc.Col([
                                html.Button('Clear', id='btn-segment-clear', n_clicks=0,
                                            className='btn btn-outline-secondary', style={'width':'100%'}),
                            ], width=2),
                        ]),
                        html.Br(),
                        dcc.Loading(html.Div(id='segment-search-results')),
                        html.Br(),
                        dag.AgGrid(
                            id='segment-search-table',
                            rowData=[],
                            columnDefs=[
                                {'field': 'Node',     'headerName': 'Node',       'width': 100, 'checkboxSelection': True, 'headerCheckboxSelection': True},
                                {'field': 'Start',    'headerName': 'Start (bp)', 'width': 130},
                                {'field': 'End',      'headerName': 'End (bp)',   'width': 130},
                                {'field': 'Genes',    'headerName': 'Genes',      'flex': 1},
                                {'field': 'Products', 'headerName': 'Products',   'flex': 2},
                            ],
                            defaultColDef={'filter': 'agTextColumnFilter', 'resizable': True, 'sortable': True},
                            dashGridOptions={
                                'pagination': True, 'paginationPageSize': 20,
                                'animateRows': False,
                                'rowSelection': 'multiple',
                            },
                            style={'height': '320px', 'display': 'none'}
                        ),
                        html.Br(),
                        dbc.Row([
                            dbc.Col([
                                html.Button(
                                    '⬇ Send to Subgraph Extraction',
                                    id='btn-send-to-subgraph', n_clicks=0,
                                    className='btn btn-outline-primary btn-sm',
                                    style={'display': 'none'}
                                ),
                            ], width='auto'),
                            dbc.Col([
                                html.Button(
                                    '⬆ Show on PAV',
                                    id='btn-show-on-pav', n_clicks=0,
                                    className='btn btn-warning btn-sm',
                                    style={'display': 'none'}
                                ),
                            ], width='auto'),
                            dbc.Col([
                                html.Button(
                                    '✕ Clear PAV highlights',
                                    id='btn-clear-pav-highlight', n_clicks=0,
                                    className='btn btn-outline-secondary btn-sm',
                                    style={'display': 'none'}
                                ),
                            ], width='auto'),
                        ], className='g-2', style={'marginTop': '6px'}),
                        html.Div(id='send-to-subgraph-feedback', style={'color':'green','marginTop':'4px','fontSize':'0.85em'}),
                        html.Div(id='show-on-pav-feedback', style={'color':'#b8860b','marginTop':'4px','fontSize':'0.85em'}),
                    ]),
                    dcc.Store(id='pav-node-names-store', data=[]),

                    html.Br(),
                    dcc.Loading(
                                        html.Div(children=[
                                            html.Div(id='selected_node', style={"fontFamily": "Courier",'width': '60vh','margin-left': '1px'}),
                                            
                                        ]),
                                    ),
                    html.Hr(),

                    # subgraph extraction panel
                    html.Div(id="subgraph-control-panel", style={'display': 'block', 'padding': '20px', 'backgroundColor': '#f9f9f9', 'border': '1px solid #ddd'}, children=[
                        html.H4("Subgraph Extraction"),
                        html.Small("Define the context size using either Steps OR Base Pairs (not both)."),
                        html.Br(), html.Br(),

                        dbc.Row([
                            dbc.Col([
                                html.Label("Node(s) to extract:"),
                                dcc.Input(
                                    id='subgraph-node-list', type='text',
                                    placeholder='e.g. 42, 85, 120',
                                    className='form-control'
                                ),
                                html.Small(
                                    "Click a node on the graph above, send from search results, or type IDs manually (comma-separated).",
                                    style={'color': 'grey'}
                                )
                            ], width=12)
                        ]),
                        html.Br(),

                        dbc.Row([
                            # input 1: node steps
                            dbc.Col([
                                html.Label("Context (Node Steps):"),
                                dcc.Input(id="subgraph-steps", type="number", value=2, placeholder="e.g. 3", min=0, className="form-control"),
                                html.Small("Ex: 3 nodes away", style={"color": "grey"})
                            ], width=3),
                            
                            # input 2: base pairs
                            dbc.Col([
                                html.Label("Context (Base Pairs):"),
                                dcc.Input(id="subgraph-bp", type="number", value=200, placeholder="e.g. 1000", min=0, step=100, className="form-control"),
                                html.Small("Ex: 1000 bp away", style={"color": "grey"})
                            ], width=3),
                            
                            # input 3: visualizer
                            dbc.Col([
                                html.Label("Visualizer:"),
                                dcc.Dropdown(
                                    id="subgraph-viz-type",
                                    options=[
                                        {'label': 'ODGI (PNG Image)', 'value': '--odgi'},
                                        {'label': 'Bandage (SVG Image)', 'value': '--bandage'},
                                        {'label': 'VG (Dot Plot)', 'value': '--vg'}
                                    ],
                                    value='--odgi'
                                )
                            ], width=3),
                            
                            # button
                            dbc.Col([
                                html.Br(),
                                html.Button("Extract & Visualize", id="btn-extract-subgraph", className="btn btn-primary", style={"backgroundColor": "#1E90FF", "color": "white"})
                            ], width=3, style={'textAlign': 'center'})
                        ]),
                        
                        html.Br(),
                        dcc.Loading(html.Div(id="subgraph-result-area", children="Select parameters and click extract."))
                    ]),

                    dcc.Store(id='stored-node-id'),

                    html.Hr(),

                    html.Div(style={'padding': '20px', 'backgroundColor': '#f9f9f9', 'border': '1px solid #ddd'}, children=[
                                    html.H4("Align Sequence to Pangenome"),
                                    html.Small("Paste a FASTA sequence to find and extract matching subgraphs."),
                                    html.Br(), html.Br(),
                                    
                                    dbc.Row([
                                        dbc.Col([
                                            html.Label("Sequence (FASTA):"),
                                            dcc.Textarea(
                                                id="seq-input-fasta",
                                                placeholder=">seq1\nATGC...",
                                                style={'width': '100%', 'height': 150},
                                            ),
                                        ], width=6),
                                        dbc.Col([
                                            html.Label("Alignment Method:"),
                                            dcc.RadioItems(
                                                id="align-method",
                                                options=[
                                                    {'label': 'Vg Giraffe', 'value': 'giraffe'},
                                                    {'label': 'Bandage (BLAST)', 'value': 'bandage'}
                                                ],
                                                value='giraffe',
                                                inline=True,
                                                labelStyle={'marginRight': '10px'}
                                            ),
                                            html.Br(),
                                            
                                            html.Div(id="giraffe-options", children=[
                                                html.Label("Read Type:"),
                                                dcc.Dropdown(
                                                    id="seq-read-type",
                                                    options=[{'label': 'Long Reads', 'value': 'long'}, {'label': 'Short Reads', 'value': 'short'}],
                                                    value='long'
                                                ),
                                            ]),
                                            
                                            html.Div(id="bandage-options", style={'display': 'none'}, children=[
                                                dbc.Button("Blast Settings", id="btn-collapse-blast", size="sm", color="info", className="mb-2", outline=True),
                                                dbc.Collapse(
                                                    dbc.Card(dbc.CardBody([
                                                        html.Small("Blast Params (--blastp value)"),
                                                        dcc.Input(id="bandage-blastp", type="text", placeholder='e.g. "-word_size 11"', className="form-control mb-1", style={'fontSize': '0.8em'}),
                                                        
                                                        dbc.Row([
                                                            dbc.Col([html.Small("Ident %"), dcc.Input(id="bandage-ifilter", type="number", value=0, min=0, max=100, placeholder="0-100", className="form-control", style={'fontSize': '0.8em'})], width=6),
                                                            dbc.Col([html.Small("Cov %"), dcc.Input(id="bandage-qcfilter", type="number", value=0, min=0, max=100, placeholder="0-100", className="form-control", style={'fontSize': '0.8em'})], width=6),
                                                        ], className="mb-1"),

                                                        dbc.Row([
                                                            dbc.Col([html.Small("E-value"), dcc.Input(id="bandage-evfilter", type="text", value="1e1", placeholder="1e1", className="form-control", style={'fontSize': '0.8em'})], width=6),
                                                            dbc.Col([html.Small("Min Len"), dcc.Input(id="bandage-alfilter", type="number", value=0, placeholder="bp", className="form-control", style={'fontSize': '0.8em'})], width=6),
                                                        ], className="mb-1"),
                                                        
                                                        dbc.Row([
                                                            dbc.Col([html.Small("BitScore"), dcc.Input(id="bandage-bsfilter", type="number", value=0, placeholder="min score", className="form-control", style={'fontSize': '0.8em'})], width=6),
                                                        ]),

                                                    ], style={'padding': '10px'})),
                                                    id="collapse-blast",
                                                    is_open=False,
                                                ),
                                                html.Br(),
                                                dbc.Button("Query Path Settings", id="btn-collapse-qpaths", size="sm", color="info", className="mb-2", outline=True),
                                                dbc.Collapse(
                                                    dbc.Card(dbc.CardBody([
                                                        html.Small("BLAST query paths"),
                                                        dbc.Row([
                                                            dbc.Col([html.Small("Path nodes"), dcc.Input(id="bandage-pathnodes", type="number", value=6, min=1, max=50, className="form-control", style={'fontSize': '0.8em'})], width=6),
                                                            dbc.Col([html.Small("Min path cov"), dcc.Input(id="bandage-minpatcov", type="number", value=0.9, min=0.3, max=1, step=0.01, className="form-control", style={'fontSize': '0.8em'})], width=6),
                                                        ], className="mb-1"),

                                                        dbc.Row([
                                                            dbc.Col([html.Small("Min hit cov"), dcc.Input(id="bandage-minhitcov", type="number", value=0.9, min=0.3, max=1, step=0.01, className="form-control", style={'fontSize': '0.8em'})], width=6),
                                                            dbc.Col([html.Small("Min mean id"), dcc.Input(id="bandage-minmeanid", type="number", value=0.5, min=0, max=1, step=0.01, className="form-control", style={'fontSize': '0.8em'})], width=6),
                                                        ], className="mb-1"),

                                                        dbc.Row([
                                                            dbc.Col([html.Small("Max e-value product"), dcc.Input(id="bandage-maxevprod", type="text", value="1e-10", className="form-control", style={'fontSize': '0.8em'})], width=6),
                                                            dbc.Col([html.Small("Min path len"), dcc.Input(id="bandage-minpatlen", type="number", value=0.95, min=0, step=0.01, className="form-control", style={'fontSize': '0.8em'})], width=6),
                                                        ], className="mb-1"),

                                                        dbc.Row([
                                                            dbc.Col([html.Small("Max path len"), dcc.Input(id="bandage-maxpatlen", type="number", value=1.05, min=0, step=0.01, className="form-control", style={'fontSize': '0.8em'})], width=6),
                                                            dbc.Col([html.Small("Min len discrepancy"), dcc.Input(id="bandage-minlendis", type="number", placeholder="off", className="form-control", style={'fontSize': '0.8em'})], width=6),
                                                        ], className="mb-1"),

                                                        dbc.Row([
                                                            dbc.Col([html.Small("Max len discrepancy"), dcc.Input(id="bandage-maxlendis", type="number", placeholder="off", className="form-control", style={'fontSize': '0.8em'})], width=6),
                                                        ]),
                                                    ], style={'padding': '10px'})),
                                                    id="collapse-qpaths",
                                                    is_open=False,
                                                ),
                                                html.Br(),
                                                html.Small("Top hits to extract"),
                                                dcc.Input(
                                                    id="bandage-topn",
                                                    type="number",
                                                    min=1,
                                                    placeholder="e.g. 5",
                                                    className="form-control",
                                                    style={'fontSize': '0.8em', 'width': '140px'}
                                                )
                                            ]),
                                    html.Hr(),
                        html.Label("Context Settings (Choose one):"),
                        dbc.Row([
                            dbc.Col([
                                html.Small("Steps (Nodes)"),
                                dcc.Input(id="seq-context", type="number", value=1, min=0, className="form-control"),
                            ], width=6),
                            dbc.Col([
                                html.Small("Distance (bp)"),
                                dcc.Input(id="seq-context-bp", type="number", placeholder="e.g 1000", min=0, step=100, className="form-control"),
                            ], width=6),
                        ]),
                        html.Br(),
                        html.Button("Align & Extract Hits", id="btn-align-sequence", className="btn btn-success", style={"marginTop": "10px", "width": "100%"}),
                    ], width=5)
                ]),
                                    
                                    html.Hr(),
                                    
                                    dcc.Loading(
                                        id="loading-alignment",
                                        type="default",
                                        children=[
                                            html.Div(id="alignment-results-container", style={'display': 'none'}, children=[
                                                html.Div(id="alignment-error"),
                                                html.H5("Alignment Hits"),
                                                dbc.Row([
                                                    dbc.Col([
                                                        html.Label("Select Hit to Visualize:"),
                                                        dcc.Dropdown(id="hit-selector", options=[], placeholder="Select a hit...")
                                                    ], width=6),
                                                    dbc.Col([
                                                        html.Label("Visualizer:"),
                                                        dcc.Dropdown(
                                                            id="hit-viz-type",
                                                            options=[
                                                                {'label': 'ODGI (PNG)', 'value': 'odgi'},
                                                                {'label': 'Bandage (SVG)', 'value': 'bandage'}
                                                            ],
                                                            value='odgi'
                                                        )
                                                    ], width=4)
                                                ]),
                                                html.Br(),
                                                html.Div(id="hit-metrics-area"),
                                                html.Br(),
                                                dcc.Loading(html.Div(id="hit-visualization-area"))
                                            ]),
                                        ]
                                    ),
                                    
                                    dcc.Store(id='store-alignment-hits'),
                                    dcc.Store(id='store-alignment-path')
                                ])
                        ]), 
                dcc.Tab(label='Core-SNPs', id='tab_snps', style=tab_style, selected_style=tab_selected_style, children=[
                    dcc.Tabs(id='tab3', style=tabs_styles, children=[
                        
                        dcc.Tab(label='Genotyping matrix', style=tab_style, selected_style=tab_selected_style, children=[

                            html.Br(),
                            html.H3(id='nb_of_snps', style={'width': '60vh','margin-left': '1px'}),
                            html.Br(),
                            dcc.Loading(dcc.Graph(id='VCF_graph')),
                            
                        ]),
                        dcc.Tab(label='Population structure', style=tab_style, selected_style=tab_selected_style, children=[
                            html.Br(),
                            dcc.Loading(dcc.Graph(id='sNMF',style={'width': '100vh', 'height': '100vh','margin-left': '15px'})),
                            dcc.Loading(dcc.Graph(id='sNMF_cross_entropy',style={'width': '100vh', 'height': '50vh','margin-left': '15px'})),
                        ]),
                        dcc.Tab(label='PCA', style=tab_style, selected_style=tab_selected_style, children=[
                            html.Br(),
                            dbc.Row([
                                    dbc.Col(
                                        html.Label("Colored by: "),style={'width': '150px'},
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(
                                                ['Country','Population as defined by sNMF'],
                                                value='Country',
                                                id='colorizing_pca',
                                                style={'width': '300px'},
                                                multi=False
                                            )
                                    ),
                                    dbc.Col(
                                        html.Label("Number of axes: "),style={'width': '150px'},
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(
                                                ['2D','3D'],
                                                value='3D',
                                                id='dimension_pca',
                                                style={'width': '100px'},
                                                multi=False
                                            )
                                        
                                    ),
                                    
                                ],style={'width': '700px'}),
                            html.Br(),html.Br(),
                            dcc.Loading(dcc.Graph(id='PCA',style={'width': '100vh', 'height': '50vh','margin-left': '15px'})),
                        ]),
                        dcc.Tab(label='SNP-based distance tree', style=tab_style, selected_style=tab_selected_style, children=[
                            html.Br(),
                            dbc.Row([
                                    dbc.Col(
                                        html.Label("Colored by: "),style={'width': '150px'},
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(
                                                ['Country','Population as defined by sNMF'],
                                                value='Country',
                                                id='colorizing_tree',
                                                style={'width': '300px'},
                                                multi=False
                                            )
                                    ),
                                    
                                ],style={'width': '450px'}),
                            html.Br(),
                            dbc.Row(
                                [
                                    dcc.Loading(html.Iframe(id='iframe-snptree',style={'width': '1200px', 'height': '800px', 'border': 'none'}))
                                ],
                                align="center",
                            ),
                            html.Br(),
                        ]),
                    ]),
                    
                ]),
                dcc.Tab(label='Repeats (MLVA)', id='tab_repeats', style=tab_style, selected_style=tab_selected_style, children=[
                    html.Br(),
                    dcc.Loading(dcc.Graph(id='graph_mlva')),
                    html.Button("Download matrix", id="btn-download", n_clicks=0),
                    dcc.Download(id="download-dataframe"),

                    html.H3(id='nb_of_repeats', style={'width': '60vh','margin-left': '1px'}),
                    dbc.Row([
                        dbc.Col(
                            dcc.Loading(
                                    dag.AgGrid(
                                        id="mlva_table",
                                        #style={'width': '180vh','height': '50vh','margin-left': '15px'},
                                        columnDefs=columnDefs2,
                                        rowData=[],
                                        columnSize="sizeToFit",
                                        selectAll=True,
                                        defaultColDef={"filter": True},
                                        dashGridOptions={"rowSelection": "multiple", "suppressRowClickSelection": True, "animateRows": False},
                                    ), 
                                ),
                        ),
                    ]),
                    
                    
                    html.Br(),
                    html.Button('Update heatmap and generate haplotype network', 
                                style={
                                    "backgroundColor": "#1E90FF",   # bleu
                                    "color": "white",
                                },
                                id='submit-vntr', 
                                n_clicks=0),
                    html.Br(),
                    dcc.Loading(html.Div(id='dynamic_network')),
                ]),
                
                dcc.Tab(label='ANI', id='tab_ani', style=tab_style, selected_style=tab_selected_style, children=[
                    html.Br(),
                    dcc.Loading(dcc.Graph(id='graph_ANI')),
                    ]),
                dcc.Tab(label='Geographical map', id='tab_geo', style=tab_style, selected_style=tab_selected_style, children=[
                    html.Br(),
                        dcc.Loading(dcc.Graph(id='geo_map',style={'width': '150vh', 'height': '100vh','margin-left': '15px'})),
                    ]),
            ]),

        ]),

        html.Div(id="update-status", style={"marginTop": "0.5rem"}),
        html.Hr(),
        # --- conteneur pour les onglets (vide au départ) ---
        dcc.Loading(
            id="loading-tabs",
            type="circle",
            children=html.Div(id="tabs-container")
        )
    ]


    return html.Div(children)

#############################################################
# Callback for alignment viewer
#############################################################
@app.callback(
    Output('default-alignment-viewer-output', 'children'),
    Input('display_alignment', 'n_clicks'),
    State('current_cluster', 'value'),
    State('metadata_table','selectedRows'),
    State('projets', 'value'),
    State('current_session', 'value')
)

def display_alignment(display_alignment,current_cluster,metadata_table,projets,session):
    
    list_of_strains = []
    if metadata_table:
        wjdata1 = json.loads(json.dumps(metadata_table, indent=2))
        for strain in wjdata1:
            strain_name = strain['Strain name']
            list_of_strains.append(strain_name)

    nb_presence,dictionaries,data = get_cluster_details(current_cluster,projets,list_of_strains)

    # create fasta file from selected genes
    data = ""
    for dict in dictionaries:
        species = dict['Species']
        gene = dict['Genes']
        cmd = f"grep -A 1 '{gene}' {directory}/genomes/genomes/{species}.faa | tail -1"
        protein_fasta = os.popen(cmd).read()
        data = data + ">"+gene+"\n"+protein_fasta

    # write data to a temporary fasta file
    with open(f"{tmp_dir}/{session}.temp.fasta", "w") as text_file:
        text_file.write(data)

    if os.path.exists(f"{tmp_dir}/{session}.muscle.log"):
        os.remove(tmp_dir+"/"+str(session)+".muscle.log")
    
    # run muscle to generate alignment
    if os.path.exists(f"{tmp_dir}/{session}.temp.fasta") and validate_session_id(session):

        cmd_args = ["muscle", "-align", f"{tmp_dir}/{session}.temp.fasta", "-output", f"{tmp_dir}/{session}.temp.aln.fasta"]
        with open(f"{tmp_dir}/{session}.muscle.log", "a") as log_file:
            subprocess.run(cmd_args, stdout=log_file, stderr=subprocess.STDOUT, check=True)

    # read alignment file
    with open(f"{tmp_dir}/{session}.temp.aln.fasta", "r") as file:
        data = file.read()
    
    # create alignment viewer 
    fig = dash_bio.AlignmentChart(
        id='alignment',
        data=data,
        height=600,
        tilewidth=30,
        width=1800
    ),
    return fig

############################################################
# Callback for clinker viewer
############################################################
@app.callback(
    Output('default-alignment-viewer-output', 'children', allow_duplicate=True),
    Input('display_local_synteny', 'n_clicks'),
    State('current_cluster', 'value'),
    State('metadata_table','selectedRows'),
    State('projets', 'value'),
    State('current_session', 'value'),
    prevent_initial_call=True
)
def display_local_synteny(display_local_synteny,current_cluster,metadata_table,projets,session):

    
    list_of_strains = []
    if metadata_table:
        wjdata1 = json.loads(json.dumps(metadata_table, indent=2))
        for strain in wjdata1:
            strain_name = strain['Strain name']
            list_of_strains.append(strain_name)

    nb_presence,dictionaries,data = get_cluster_details(current_cluster,projets,list_of_strains)

    list_strains = ",".join(list_of_strains)
    
    cmd_args = [
        "perl", "ClinkerPlotFromMatrix.pl",
        f"{directory}/1.Orthologs_Cluster.txt",
        str(current_cluster),
        f"{directory}/genomes/genomes/",
        list_strains,
        f"{tmp_dir}/{session}_clinker.html"
    ]
    subprocess.run(cmd_args, check=True)

    fig = html.Iframe(srcDoc=open(f"{tmp_dir}/{session}_clinker.html", 'r').read(), style={'width': '1800px', 'height': '600px', 'border': 'none'})
    return fig

#############################################################
# Callback for node selection from heatmap
#############################################################
@app.callback(
# 1. The visible text area
    Output('selected_node', 'children'),
    # 2. The hidden memory store
    Output('stored-node-id', 'data'),
    # 3. The visibility of the subgraph panel
    Output('subgraph-control-panel', 'style'),
    # 4. Reset context Inputs
    Output('subgraph-steps', 'value'),
    Output('subgraph-bp', 'value'),
    # 5. Reset Visualization Area
    Output('subgraph-result-area', 'children'),
    # 6. Append clicked node to the node-list input
    Output('subgraph-node-list', 'value'),

    Input('graph_gfa2', 'clickData'),
    State('metadata_table','selectedRows'),
    State('projets', 'value'),
    State('url','hash'),
    State('reference', 'value'),
    State('current_session', 'value'),
    State('subgraph-node-list', 'value'),
)

def display_click_data_GFA(clickData, metadata_table, projets, url, reference, session, current_node_list):
    node = 1
    if clickData:
        wjdata = json.loads(json.dumps(clickData, indent=2))
        node = wjdata['points'][0]['x']

    selected_node = "Selected node: " + str(node)
    infos = get_node_details(node, projets, reference, session)
    node_data = get_node_genes_metadata(node, projets, reference, session)

    panel_style = {
        'display': 'block',
        'padding': '20px',
        'backgroundColor': '#f9f9f9',
        'border': '1px solid #ddd',
        'marginTop': '20px'
    }

    # Append node to the node-list input (avoid duplicates).
    # The heatmap x-value has the format "prefix_NODEID" (e.g. "1610_180654");
    # extract only the numeric part after the last underscore.
    raw = str(node)
    parts = raw.split('_')
    node_str = parts[-1] if len(parts) > 1 and parts[-1].isdigit() else raw

    if current_node_list:
        existing = [n.strip() for n in current_node_list.split(',') if n.strip()]
        if node_str not in existing:
            existing.append(node_str)
        new_node_list = ', '.join(existing)
    else:
        new_node_list = node_str

    return infos, node_data, panel_style, 2, 200, "Select parameters and click extract.", new_node_list


#############################################################
# Search callback — node IDs or gene keyword
#############################################################
@app.callback(
    Output('segment-search-results', 'children'),
    Output('segment-search-table', 'rowData'),
    Output('segment-search-table', 'columnDefs'),
    Output('segment-search-table', 'style'),
    Output('btn-send-to-subgraph', 'style'),
    Output('btn-show-on-pav', 'style'),
    Output('btn-clear-pav-highlight', 'style'),
    Input('btn-segment-search', 'n_clicks'),
    Input('btn-segment-clear', 'n_clicks'),
    State('segment-search-input', 'value'),
    State('projets', 'value'),
    State('reference', 'value'),
    State('current_session', 'value'),
    prevent_initial_call=True
)
def search_and_highlight_segments(n_search, n_clear, search_value, projets, reference, session):
    ctx = callback_context
    hidden_table = {'height': '320px', 'display': 'none'}
    hidden_btn   = {'display': 'none'}
    col_defs = [
        {'field': 'Node',     'headerName': 'Node',       'width': 100, 'checkboxSelection': True, 'headerCheckboxSelection': True},
        {'field': 'Start',    'headerName': 'Start (bp)', 'width': 130},
        {'field': 'End',      'headerName': 'End (bp)',   'width': 130},
        {'field': 'Genes',    'headerName': 'Genes',      'flex': 1},
        {'field': 'Products', 'headerName': 'Products',   'flex': 2},
    ]
    if not ctx.triggered:
        return "", [], col_defs, hidden_table, hidden_btn, hidden_btn, hidden_btn
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'btn-segment-clear' or not search_value or not session or not reference:
        return "", [], col_defs, hidden_table, hidden_btn, hidden_btn, hidden_btn

    # Resolve project directory
    row = query_db("SELECT path FROM projects WHERE title = ?", (projets,), one=True)
    proj_directory = row[0] if row else conf["session_dir"] + "/" + str(projets)

    # Load node positions
    node_pos_file = f"{tmp_dir}/{session}.{reference}.segments.node_positions.tsv"
    if not os.path.exists(node_pos_file):
        return html.Div(
            "Node positions file not found — please run the analysis first.",
            style={'color': 'red'}
        ), [], col_defs, hidden_table, hidden_btn, hidden_btn, hidden_btn
    df_node_pos = pd.read_csv(node_pos_file, sep='\t')

    # Load gene annotation (.2.ptt)
    ptt_file = f"{proj_directory}/genomes/genomes/{reference}.2.ptt"
    df_genes = pd.DataFrame()
    if os.path.exists(ptt_file):
        df_genes = pd.read_csv(ptt_file, sep='\t')
        if 'start' not in df_genes.columns:
            try:
                df_genes[['start', 'end']] = df_genes['Location'].str.split(r'\.\.', expand=True).astype(int)
            except Exception:
                df_genes['start'] = pd.to_numeric(df_genes.get('start'), errors='coerce')
                df_genes['end'] = pd.to_numeric(df_genes.get('end'), errors='coerce')
        else:
            df_genes['start'] = pd.to_numeric(df_genes['start'], errors='coerce')
            df_genes['end'] = pd.to_numeric(df_genes['end'], errors='coerce')

    # Auto-detect search mode: all numeric tokens → node IDs, otherwise gene keyword
    tokens = [t.strip() for t in search_value.split(',') if t.strip()]
    is_node_search = all(t.isdigit() for t in tokens)

    matched_node_ids = []   # list of str node IDs matching node_names format
    table_rows = []

    if is_node_search:
        node_ids = [int(t) for t in tokens]
        for nid in node_ids:
            row_match = df_node_pos[df_node_pos['Node'] == nid]
            if row_match.empty:
                continue
            start = int(row_match.iloc[0]['Start'])
            end = int(row_match.iloc[0]['End'])
            matched_node_ids.append(str(nid))
            genes_str, products_str = "", ""
            if not df_genes.empty:
                ov = df_genes[(df_genes['start'] < end) & (df_genes['end'] > start)]
                genes_str = ", ".join(ov['PID'].astype(str).tolist())
                products_str = ", ".join(ov['Product'].astype(str).tolist()) if 'Product' in ov.columns else ""
            table_rows.append({'Node': nid, 'Start': start, 'End': end,
                                'Genes': genes_str, 'Products': products_str})
    else:
        # Gene keyword search
        if df_genes.empty:
            return html.Div("Gene annotation file (.2.ptt) not found.", style={'color': 'red'}), [], col_defs, hidden_table, hidden_btn, hidden_btn, hidden_btn
        kw = search_value.strip().lower()
        mask = df_genes['PID'].astype(str).str.lower().str.contains(kw, na=False)
        if 'Product' in df_genes.columns:
            mask = mask | df_genes['Product'].astype(str).str.lower().str.contains(kw, na=False)
        matched_genes = df_genes[mask]
        if matched_genes.empty:
            return html.Div(f"No genes found matching '{search_value}'.", style={'color': 'orange'}), [], col_defs, hidden_table, hidden_btn, hidden_btn, hidden_btn

        found_node_ids = set()
        for _, gr in matched_genes.iterrows():
            g_start, g_end = int(gr['start']), int(gr['end'])
            ov_nodes = df_node_pos[
                (df_node_pos['Start'] < g_end) & (df_node_pos['End'] > g_start)
            ]
            for _, nr in ov_nodes.iterrows():
                nid = int(nr['Node'])
                if nid in found_node_ids:
                    continue
                found_node_ids.add(nid)
                n_start, n_end = int(nr['Start']), int(nr['End'])
                ov_all = df_genes[(df_genes['start'] < n_end) & (df_genes['end'] > n_start)]
                genes_str = ", ".join(ov_all['PID'].astype(str).tolist())
                products_str = ", ".join(ov_all['Product'].astype(str).tolist()) if 'Product' in ov_all.columns else ""
                matched_node_ids.append(str(nid))
                table_rows.append({'Node': nid, 'Start': n_start, 'End': n_end,
                                   'Genes': genes_str, 'Products': products_str})

    if not table_rows:
        return html.Div("No matching nodes found.", style={'color': 'orange'}), [], col_defs, hidden_table, hidden_btn, hidden_btn, hidden_btn

    df_result = pd.DataFrame(table_rows).sort_values('Start').reset_index(drop=True)

    summary = html.Div([
        html.Strong(f"Found {len(matched_node_ids)} node(s) "),
        html.Span(
            f"matching '{search_value}'. Select rows then click Show on PAV to highlight, "
            "or Send to Subgraph Extraction.",
            style={'color': '#555'}
        ),
    ])
    visible_table = {'height': '320px', 'display': 'block'}
    visible_btn   = {'display': 'inline-block'}
    return summary, df_result.to_dict('records'), col_defs, visible_table, visible_btn, visible_btn, visible_btn


#############################################################
# Send selected rows from search table → subgraph node-list
#############################################################
@app.callback(
    Output('subgraph-node-list', 'value', allow_duplicate=True),
    Output('send-to-subgraph-feedback', 'children'),
    Input('btn-send-to-subgraph', 'n_clicks'),
    State('segment-search-table', 'selectedRows'),
    State('subgraph-node-list', 'value'),
    prevent_initial_call=True
)
def send_selected_to_subgraph(n_clicks, selected_rows, current_list):
    if not selected_rows:
        return current_list or "", "No rows selected in the table."
    new_ids = [str(r['Node']) for r in selected_rows]
    # Merge with existing IDs, keeping order and avoiding duplicates
    existing = [n.strip() for n in (current_list or "").split(',') if n.strip()]
    for nid in new_ids:
        if nid not in existing:
            existing.append(nid)
    merged = ', '.join(existing)
    feedback = f"Added {len(new_ids)} node(s): {', '.join(new_ids)}"
    return merged, feedback


#############################################################
# Show on PAV / Clear PAV highlights callbacks
# Draws yellow rectangle shapes over selected node columns
# in graph_gfa2 using Plotly Patch (no figure rebuild)
#############################################################
@app.callback(
    Output('graph_gfa2', 'figure', allow_duplicate=True),
    Output('show-on-pav-feedback', 'children'),
    Input('btn-show-on-pav', 'n_clicks'),
    Input('btn-clear-pav-highlight', 'n_clicks'),
    State('segment-search-table', 'selectedRows'),
    State('pav-node-names-store', 'data'),
    prevent_initial_call=True
)
def show_nodes_on_pav(n_show, n_clear, selected_rows, node_names):
    ctx = callback_context
    patched = Patch()

    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # ── Clear ──────────────────────────────────────────────────────────────
    if trigger_id == 'btn-clear-pav-highlight':
        patched['layout']['shapes'] = []
        return patched, ""

    # ── Show ──────────────────────────────────────────────────────────────
    if not selected_rows:
        raise PreventUpdate
    if not node_names:
        return patched, html.Span("PAV not loaded yet — run the analysis first.", style={'color':'red'})

    # node_names are in "count_nodeid" format, e.g. ["1_180654", "2_180700", ...]
    # Build a lookup: plain GFA node ID (str) → 0-based index position on the x-axis
    node_id_to_index = {}
    for i, label in enumerate(node_names):
        parts = str(label).split('_')
        gfa_id = parts[-1] if len(parts) > 1 else label
        node_id_to_index[gfa_id] = i

    # Selected rows carry plain integer Node IDs from the search table
    selected_ids = [str(r['Node']) for r in selected_rows]

    shapes = []
    matched = []
    for nid in selected_ids:
        idx = node_id_to_index.get(nid)
        if idx is None:
            continue
        matched.append(nid)
        shapes.append(dict(
            type='rect',
            xref='x',
            yref='paper',
            x0=idx - 0.5,
            x1=idx + 0.5,
            y0=0,
            y1=1,
            fillcolor='#39FF14',
            opacity=0.6,
            line=dict(width=0),
            layer='above',
        ))

    if not shapes:
        return patched, html.Span(f"None of the selected nodes were found on the PAV x-axis.", style={'color':'orange'})

    patched['layout']['shapes'] = shapes
    feedback = html.Span(
        f"🟢 {len(matched)} node(s) highlighted on PAV: {', '.join(matched)}",
        style={'color': '#1a7a00', 'fontWeight': 'bold'}
    )
    return patched, feedback


#############################################################
# Callback for cluster selection from heatmap or from table
#############################################################
@app.callback(
    Output('selected_cluster', 'children'),
    Output('genes_cluster', 'rowData'),
    Output("current_cluster",'options'),
    Output("specific_to",'value'),
    Input('PAV_graph', 'clickData'),
    Input('metadata_table','selectedRows'),
    State('projets', 'value'),
    State('url','hash'),
    State('heatmap_selection','value'),
    #prevent_initial_call=True
)

def display_click_data(clickData,metadata_table,projets,url,heatmap_selection):
         
    cluster = 1
    pathname = projets
    if url:
        pathname=url
    list_of_strains = []
    if metadata_table:
        wjdata1 = json.loads(json.dumps(metadata_table, indent=2))
        for strain in wjdata1:
            strain_name = strain['Strain name']
            list_of_strains.append(strain_name)
            
    if clickData:
        wjdata = json.loads(json.dumps(clickData, indent=2))
        cluster = wjdata['points'][0]['x']
    
    inf = cluster.split(":")
    cluster = inf[-1]

    nb_presence,dictionary,data = get_cluster_details(cluster,projets,list_of_strains)
    rowData = dictionary

    cmd = "grep '\t"+str(cluster)+"\t' "+directory+"/merged_with_cog.txt"
    infos_cluster = os.popen(cmd).read().split("\t")
    selected_cluster = "Selected cluster: " + str(cluster) + ", " + str(infos_cluster[2])

    list_strains = []
    if (heatmap_selection and 'heatmap_selection' in heatmap_selection):
        list_strains = get_combination(cluster,pathname,list_of_strains)


    
        
    #return selected_cluster,dictionary,data, [{'label': str(cluster), 'value': str(cluster)}],list_strains
    return selected_cluster,dictionary, [{'label': str(cluster), 'value': str(cluster)}],list_strains


##########################################
# when clicking in the table of pangenes
##########################################
@app.callback(
    Output('selected_cluster', 'children', allow_duplicate=True),
    Output('genes_cluster', 'rowData', allow_duplicate=True),
    Output("current_cluster",'options', allow_duplicate=True),
    Input('table_pangenes', 'cellClicked'),
    Input('metadata_table','selectedRows'),
    State('projets', 'value'),
    State('url','hash'),
    prevent_initial_call=True
)
def display_click_data(cell,metadata_table,projets,url):
         
    pathname = projets
    if url:
        pathname=url
    cluster = 1
    list_of_strains = []

    if metadata_table:
        print("ok")
        wjdata1 = json.loads(json.dumps(metadata_table, indent=2))
        for strain in wjdata1:
            strain_name = strain['Strain name']
            list_of_strains.append(strain_name)  
    if cell:
        wjdata = json.loads(json.dumps(cell, indent=2))
        cluster = wjdata['value']
        nb_presence,dictionary,data = get_cluster_details(cluster,projets,list_of_strains)

        cmd = "grep '\t"+str(cluster)+"\t' "+directory+"/merged_with_cog.txt"
        infos_cluster = os.popen(cmd).read().split("\t")
        selected_cluster = "Selected cluster: " + str(cluster) + ", " + str(infos_cluster[2])
        
        #return selected_cluster,dictionary, data, [{'label': str(cluster), 'value': str(cluster)}]
        return selected_cluster,dictionary, [{'label': str(cluster), 'value': str(cluster)}]
    else:
        #return "",[],"",[]
        return "",[],[]


@app.callback(
    Output('current_cluster', 'value'),
    Input('current_cluster', 'options')
)
def set_current_cluster(available_options):
    if available_options:
        return available_options[0]['value']
    else:
        return ''
    


def get_node_details(node,pathname,reference,session):
    global directory

    if not pathname:
        return "No project."
    row = query_db("SELECT path FROM projects WHERE title = ?", (pathname,), one=True)
    path = ""
    if not row:
        path = conf["session_dir"] + "/" + pathname
    else:
        path = row[0]
    directory = path

    list_of_infos = node.split("_")
    num_node = list_of_infos[1]

    df_node_details = pd.read_csv(tmp_dir +"/"+str(session) + "." + reference+".segments.node_positions.tsv" ,sep='\t')
    
    mini_df = df_node_details[df_node_details["Node"] == int(num_node)]
    start_node = mini_df['Start'].tolist()[0]
    end_node = mini_df['End'].tolist()[0]

    cmd = "grep -P '^S\s"+num_node+"\s' "+directory+"/pangenome.gfa"
    result = os.popen(cmd).read()
    list_of_infos = result.split("\t")
    node_sequence = list_of_infos[2]
    node_sequence2 = re.sub("(.{80})", "\\1\n", node_sequence, 0, re.DOTALL)

    df_gene_positons = pd.read_csv(directory+'/genomes/genomes/'+reference+'.2.ptt',sep='\t')
    df_gene_positons[['start', 'end']] = df_gene_positons['Location'].str.split('\.\.', expand=True)
    df_gene_positons['start'] = pd.to_numeric(df_gene_positons['start'], downcast='integer', errors='coerce')
    df_gene_positons['end'] = pd.to_numeric(df_gene_positons['end'], downcast='integer', errors='coerce')

    query = 'start < ' + str(start_node) + ' and end > ' + str(start_node) + ' or start < ' + str(end_node) + ' and end > ' + str(end_node) + ' or start >= ' + str(start_node) + ' and end <= ' + str(end_node)
    filtered_df_gene_positions = df_gene_positons.query(query)
    genes = filtered_df_gene_positions['PID'].tolist()
    product = filtered_df_gene_positions['Product'].tolist()

    return html.Div([
        html.Div("Node: " + str(num_node)),
        html.Div("Positions in reference genome: " + str(start_node) + "-" + str(end_node)),
        html.Div("Genes in this node: "),
        html.Ul([html.Li(genes[i] + ": " + product[i]) for i in range(len(genes))]),

        html.Div("Sequence:"),
        html.Pre(node_sequence2)
    ])
        
#"Node: " + str(num_node) + "</div>Positions in reference genome: " + str(start_node) + "-" + str(end_node)+ "\n\n" + str(node_sequence2) 

def get_node_genes_metadata(node, pathname, reference, session):
    """
    Extracts the node ID and a list of overlapping genes with:
    - reference genome
    - start
    - end
    - gene_name
    """
    if not pathname:
        return None

    # 1. Resolve Project Path
    row = query_db("SELECT path FROM projects WHERE title = ?", (pathname,), one=True)
    directory = row[0] if row else conf["session_dir"] + "/" + pathname

    # 2. Parse clean Node ID
    # Handles "Node_123" or just "123"
    num_node = str(node).replace("Node_", "").split("_")[1] if "_" in str(node) else str(node)

    # 3. Get Node Coordinates
    # Reads the node position file generated during the heavy update
    node_pos_file = f"{tmp_dir}/{session}.{reference}.segments.node_positions.tsv"
    
    if not os.path.exists(node_pos_file):
        return {"node_id": num_node, "genes": [], "error": "Node positions file not found"}

    try:
        df_node_details = pd.read_csv(node_pos_file, sep='\t')
        mini_df = df_node_details[df_node_details["Node"] == int(num_node)]
        
        if mini_df.empty:
            return {"node_id": num_node, "genes": [], "error": "Node not found in positions"}

        start_node = int(mini_df['Start'].iloc[0])
        end_node = int(mini_df['End'].iloc[0])

        # 4. Find Overlapping Genes in PTT
        ptt_file = f"{directory}/genomes/genomes/{reference}.2.ptt"
        genes_list = []
        
        if os.path.exists(ptt_file):
            df_genes = pd.read_csv(ptt_file, sep='\t')
            
            # Ensure start/end columns exist (parse 'Location' if needed)
            if 'start' not in df_genes.columns:
                df_genes[['start', 'end']] = df_genes['Location'].str.split(r'\.\.', expand=True).astype(int)
            else:
                df_genes['start'] = pd.to_numeric(df_genes['start'], errors='coerce')
                df_genes['end'] = pd.to_numeric(df_genes['end'], errors='coerce')

            # Filter logic: Overlap
            # (Gene Start < Node End) AND (Gene End > Node Start)
            query = f"(start < {end_node}) & (end > {start_node})"
            overlapping_genes = df_genes.query(query)

            for _, row in overlapping_genes.iterrows():
                genes_list.append({
                    "reference_genome": reference,
                    "start": int(row['start']),
                    "end": int(row['end']),
                    "gene_name": row['PID']
                })

        return {
            "node_id": num_node,
            "genes": genes_list
        }

    except Exception as e:
        print(f"Error in get_node_genes_metadata: {e}")
        return {"node_id": num_node, "genes": [], "error": str(e)}
        
def get_cluster_details(cluster,pathname,list_of_strains):
    
    global directory

    if not pathname:
        return "No project."
    row = query_db("SELECT path FROM projects WHERE title = ?", (pathname,), one=True)
    path = ""
    if not row:
        path = conf["session_dir"] + "/" + pathname
    else:
        path = row[0]
    directory = path

    
    df_matrix = pd.read_csv(directory+'/1.Orthologs_Cluster.txt',sep='\t')
    mini_df = df_matrix[df_matrix["ClutserID"] == int(cluster)]
    
    # generate a new dataframe from a list of list
    list_of_list = []
    nb_presence = 0
    combination = ""
    for item in mini_df.columns:
        if item != 'ClutserID' and item in list_of_strains:
            genes = mini_df[item]
            keep = True
            
            for gene in genes:
                if gene == "-":
                    keep = False
            if keep:
                list_genes = ','.join(map(str,genes)) 

                # for gene in genes:
                #     print(gene)
                #     cmd = "grep '"+gene+"' "+directory+"/genomes/genomes/"+item+".gff | tail -1"
                #     result = os.popen(cmd).read()
                #     print(result)

                list = [int(cluster),item,list_genes]
                list_of_list.append(list)
                nb_presence+=1
                combination = combination+str(item)

    mydf = pd.DataFrame(list_of_list, columns = ['Cluster','Species','Genes']) 
    
    concat = ""
    for gene in list_of_list:
        speciesname = gene[1]
        genename = gene[2]
        cmd = "grep -A 1 '"+genename+"' "+directory+"/genomes/genomes/"+speciesname+".faa | tail -1"
        result = os.popen(cmd).read()

        concat = concat + ">"+genename + "_" + speciesname + "\n" + result
        
    data = concat
    #print(data)
    #data = ">test\nP\t>test2\nP"
    mydf.to_csv('export_cluster_details.txt')
    dictionary = mydf.to_dict('records')

    return nb_presence,dictionary,data



#################################################
# callback for changing list of strains for pivot
#################################################
@app.callback(
    Output('reference', 'options'),
    Output('specific_to','options'),
    Input('metadata_table','selectedRows'),
    Input('projets', 'value'),
    Input('url','hash')
     )
def update_pivot(metadata_table,projets,url):
    pathname = projets
    if url:
        pathname=url
        
    reference_list = []
    if metadata_table:
        wjdata = json.loads(json.dumps(metadata_table, indent=2))
        val = wjdata
        for strain in wjdata:
            strain_name = strain['Strain name']
            reference_list.append(strain_name)

    return [{'label': i, 'value': i} for i in reference_list] , [{'label': i, 'value': i} for i in reference_list]


@app.callback(
    Output('reference', 'value'),
    Input('reference', 'options')
)
def set_reference_value(available_options):
    if available_options:
        return available_options[0]['value']
    else:
        return ''
    


# Placeholder callback to trigger (heavy) graph update — you can replace body with original update_graph function
@app.callback(
        
    Output("update-status", "children"),
    Output("nb_of_pangenes",'children'),
    Output('textarea-example-output', 'children'),
    Output('PAV_graph', 'figure'),
    #Output('graph_upset', 'figure'),
    Output('table_pangenes', 'rowData'),
    Output('table_pangenes','columnDefs'),
        #Output('datatable-paging','srcDoc'),
    Output('graph_ANI', 'figure'),
    Output('graph_gene2', 'figure'),
    Output('graph_pie2', 'figure'),
    #Output('graph_COG_all', 'figure'),
    #Output('graph_COG1', 'figure'),
    Output('graph_COG2', 'figure'),
    Output('rarefaction2', 'figure'),
    Output("my-dashbio-default-circos", "layout"),
    Output("my-dashbio-default-circos", "tracks"),
    #Output("table_of_search",'rowData'),
    Output("clustersearch",'children'),
    Output("graph_macrosynteny", 'figure'),
    Output('clinker','children'),
    Output('mlva_table', 'rowData'),
    Output('nb_of_repeats', 'children'),
    Output('graph_mlva', 'figure', allow_duplicate=True),
    Output('PCA','figure'),
    Output('iframe-content', 'src'),
    Output('iframe-snptree', 'src'),
    Output('results', 'style'),
    Output("nb_of_snps",'children'),
    Output('VCF_graph', 'figure'),
    Output('sNMF', 'figure'),
    Output('sNMF_cross_entropy', 'figure'),
    Output('geo_map', 'figure'),
    #Output('graph_gfa', 'figure'),
    Output('graph_gfa2', 'figure'),
    Output('pav-node-names-store', 'data'),
    Output('mainloading','children'),
    Output('tab_segments','style'),
    Output('tab_repeats','style'),
    Output('tab_snps','style'),
    Output('tab_ani','style'),
    Output('tab_geo','style'),
    Output('current_session','value'),
    Output('colorizing_pca','options'),
    Output('colorizing_tree','options'),
    State('reference', 'value'),
    State('ordering', 'value'),
    State('sample_ordering', 'value'),
    State('colorizing', 'value'),
    State('highlight', 'value'),
    State('projets', 'value'),
    State('url','hash'),
    Input("btn-update", "n_clicks"),
    State('specific_to','value'),
    State('cluster_search','value'),
    State('bedfile','value'),
    State('metadata_table','selectedRows'),
    State("my-dashbio-default-circos", "layout"),
    State("my-dashbio-default-circos", "tracks"),
    State("chromosome",'value'),
    State("minimal_size_block",'value'),


    prevent_initial_call=True
)
def trigger_heavy_update(reference,ordering,sample_ordering,colorizing,highlight,proj_title,url,n_clicks,specific_to,cluster_search,bedfile,metadata_table,current_layout,current_tracks,chromosome, minimal_size_block):
    if not proj_title:
        return "No project."
    row = query_db("SELECT path FROM projects WHERE title = ?", (proj_title,), one=True)
    path = ""
    if not row:
        path = conf["session_dir"] + "/" + proj_title
    else:
        path = row[0]
    directory = path

    if is_stringlist_without_special_character(cluster_search) == False:
        cluster_search = ""

    if is_bed(bedfile) == False:
        bedfile = ""

    session = str(uuid.uuid4())

    df,df_metadata,df_ANI,merged_with_positions,list_species,list_continent,list_organisms,karyotype_dict_list,dict_list_gene_plus,dict_list_gene_minus,df_matrix = init_dataframes(path)
    
    list_of_lists = []
    # with clusterID
    df_metadata2 = df_metadata
    # without clusterID
    df_metadata3 = df_metadata[(df_metadata["Continent"] != "none")]
    
    #if (continent != "all"):
    #    df_metadata2 = df_metadata2[(df_metadata2["Continent"] == continent) | (df_metadata2["Continent"] == "none")]
    #    df_metadata3 = df_metadata3[df_metadata3["Continent"] == continent]
        
    #if (organism != "all"):
    #    df_metadata2 = df_metadata2[(df_metadata2["Organism"] == organism) | (df_metadata2["Organism"] == "none")]
    #    df_metadata3 = df_metadata3[df_metadata3["Organism"] == organism]

    

    list_selected = ['ClutserID']
    #if submit_samples:
    if metadata_table:
        wjdata = json.loads(json.dumps(metadata_table, indent=2))
        val = wjdata
        for strain in wjdata:
            strain_name = strain['Strain name']
            list_selected.append(strain_name)
                
    else:
        for value in df_metadata2['Strain name']:
            list_selected.append(value)
            
    
    ####################################################################
    # intersection between ordered list of samples and selected samples
    ####################################################################
    
    list_sp2 = []
    list_sp = []
    list1 = []
    for value in df.columns:
        list1.append(value)


    for value in list1:
        if value in list_selected:
            list_sp.append(value)
            if value != 'ClutserID':
                list_sp2.append(value)
      
    
    nb_pangenes = 0
    nb_coregenes = 0
    nb_specific_genes = 0
    cluster_names=[]
    cluster_indexes=[]
    
    
    df2 = df[list_sp]

    
    # add sum column indicating the number of strains holding the gene
    df2['sum'] = df2.drop('ClutserID', axis=1).sum(axis=1)
    

    # get only if at least one gene is present
    df2 = df2[df2["sum"] > 0]
    
    # remove CLUSTER tag (TODO: to be removed)
    df2['ClutserID']= df2['ClutserID'].astype(str)
    df2['ClutserID'] = df2['ClutserID'].str.replace('CLUSTER000','')
    df2['ClutserID'] = df2['ClutserID'].str.replace('CLUSTER00','')
    df2['ClutserID'] = df2['ClutserID'].str.replace('CLUSTER0','')
    df2['ClutserID'] = df2['ClutserID'].str.replace('CLUSTER','')
    cluster_names = df2["ClutserID"]
    
    print("df2")
    print(df2)
    df2.loc[df2['sum'] == 1, 'type'] = 'Strain-specific'
    df2.loc[df2['sum'] == len(list_sp2), 'type'] = 'Core-gene'
    df2.loc[(df2['sum'] < len(list_sp2)) & (df2['sum'] > 1), 'type'] = 'Dispensable-gene'
    
    df2.to_csv("export_df2.csv")
    df.to_csv("export_df.csv")

    ##############################################
    # Generate Core-gene and accessory files
    ##############################################
    with open(directory+"/cog_of_clusters.2.txt", "w") as out:
        subprocess.run(
            ["awk" , "{print $1\"\t\"$2\"\t\"$3}", directory+"/cog_of_clusters.txt"],
            stdout=out,
            check=True
        )

    df_cog_of_clusters = pd.DataFrame(columns=['Cluster', 'COG', 'COGcat'])
    if os.path.exists(directory+"/cog_of_clusters.2.txt") and os.path.getsize(directory+"/cog_of_clusters.2.txt") > 0:
        df_cog_of_clusters = pd.read_csv(directory+'/cog_of_clusters.2.txt',sep='\t')
        df_cog_of_clusters.columns = ['Cluster', 'COG', 'COGcat']

    # get only values of column ClutserID from df2, and put empty values for COG and COGcat
    else:
        df_cog_of_clusters = df2[["ClutserID"]]
        df_cog_of_clusters['COG'] = ""
        df_cog_of_clusters['COGcat'] = ""
        df_cog_of_clusters.rename(columns={'ClutserID': 'Cluster'}, inplace=True)
        df_cog_of_clusters["Cluster"] = df_cog_of_clusters["Cluster"].astype(int)
    
        
    print(df_cog_of_clusters)
    


    df2[['ClutserID']] = df2[['ClutserID']].apply(pd.to_numeric)

    # get only the first COG assigned to a cluster
    df_cog_of_clusters_grouped_by_cluster = df_cog_of_clusters.groupby('Cluster').first()
    print(df_cog_of_clusters_grouped_by_cluster)

    #df_cog_of_clusters_grouped_by_cluster = df_cog_of_clusters_grouped_by_cluster.astype({"Cluster": int})
    merged_with_cog = pd.merge(df2, df_cog_of_clusters_grouped_by_cluster, how="left", left_on='ClutserID', right_on='Cluster')

    df_cog_terms = pd.read_csv('COG_terms.txt',sep='\t')

    merged_with_cog_term = pd.merge(df_cog_terms, merged_with_cog, how="right", left_on='COG', right_on='COG')

    merged_with_cog = merged_with_cog_term
    merged_with_cog.to_csv(directory+"/merged_with_cog.txt",sep="\t")
    #merged_with_cog_term.to_csv(directory+"/merged_with_cog_term.txt")




    core_df = merged_with_cog[merged_with_cog["sum"] == len(list_sp2)]
    specific_df = merged_with_cog[merged_with_cog["sum"] == 1]
    accessory_df = merged_with_cog[(merged_with_cog["sum"] != 1) & (merged_with_cog["sum"] < len(list_sp2))]
    
    nb_pangenes = len(df2)

    
    
    nb_specific_genes = len(specific_df)
    nb_coregenes = len(core_df)
    nb_accessory = nb_pangenes - nb_specific_genes - nb_coregenes

    print("Nb specific: "+str(nb_specific_genes))

    #################################################
    # pie chart
    #################################################
    dic = {}
    dic['Type'] = ['Strain-specific','Core genes','Accessory genes']
    dic['Nb'] = [nb_specific_genes,nb_coregenes,nb_accessory]
    df_synthesis = pd.DataFrame.from_dict(dic)
    
    fig_pie = px.pie(df_synthesis, values='Nb', names='Type', title='Distribution of core-genes and accessory genes')

    ####################################################################
    # Generate rarefaction curve. Takes randomly N columns from dataframe
    # and counts number of pan- and core-genes
    ####################################################################
    strain_index = 0
    df01_only = df[list_sp2]
    
    list1 = []
    list2 = []
    list3 = []
    
    for strain in list_sp2:
        strain_index+=1
        for number in range(3):
            df_random = df01_only.sample(n=strain_index, axis='columns') 
            
            df_random['sum'] = df_random.sum(axis=1)
            # get pangenes: keep only if at least one gene is present
            df_random = df_random[df_random["sum"] > 0]
            n_pangenes = len(df_random)
            df_random = df_random[df_random["sum"] == strain_index]
            n_coregenes = len(df_random)
            list1.append(str(strain_index))
            list1.append(str(strain_index))
            list2.append(str(n_pangenes))
            list2.append(str(n_coregenes))
            list3.append("Pan-genes")
            list3.append("Core-genes")

    data = {'Number strains': list1,'Number genes': list2,"Type": list3}
    df_rarefaction = pd.DataFrame(data)
    df_rarefaction.to_csv(tmp_dir + "/" +"rarefactiontest2.txt",index=False)
    df_rarefaction2 = pd.read_csv(tmp_dir + "/" +'rarefactiontest2.txt',sep=',')
    fig_rarefaction = px.box(df_rarefaction2, title="Rarefaction curve",x="Number strains", y="Number genes",color="Type")

    # ##########################################################
    # # test for changing color for specific genes or strains
    # ##########################################################
    search_res2 = []
 
    # ##############################################
    # # get clusters specific to a subset of samples
    # ##############################################
    if specific_to is not None and len(specific_to) > 0:
        list_of_clusters = [1000]
        
        # 1) get clusters for which gene is present for these samples
        specific_to.append("ClutserID")
        df_specific_to = df[specific_to]
        df_specific_to['sum'] = df_specific_to.drop('ClutserID', axis=1).sum(axis=1)
        # get only if at least one gene is present
        df_specific_to = df_specific_to[df_specific_to["sum"] == len(specific_to)-1]
        # remove CLUSTER tag (TODO: to be removed)

        df_specific_to.to_csv("df_specific_to.csv")
        list1 = df_specific_to['ClutserID'].tolist()
        #list1bis = [eval(i) for i in list1]
        
        
        # 2) get clusters for which the number of presence correspond to the number of selected samples
        same_number_df = merged_with_cog[merged_with_cog["sum"] == len(specific_to)-1]
        same_number_df.to_csv("df_specific_to2.csv")
        list2 = same_number_df['ClutserID'].tolist()
        
        # 3) get overlapping clusters between the two dataframes
        intersected_list = [value for value in list1 if value in list2]

        df_search = pd.DataFrame(intersected_list, columns=['ClutserID'])
        search_res2 = df_search.to_dict('records')
        #df_specific_final2.to_csv("df_specific_to.csv")
        
        list_of_clusters = intersected_list

        df_search = pd.DataFrame(list_of_clusters, columns=['ClutserID'])
        search_res2 = df_search.to_dict('records')
        
        for sample in list_sp2:
            df2[sample] =  np.where( (df2[sample] == 1) & (df2["ClutserID"].isin(list_of_clusters)==False),0.67,df2[sample])

    
    #################################################
    # manage Circos
    #################################################
    
    
    gene_position_file = directory+'/genomes/genomes/'+str(reference)+'.ptt'
    gene_position_file2 = directory+'/genomes/genomes/'+str(reference)+'.2.ptt'

    # Remove lines from ptt
    if is_string_without_special_character(reference):
        with open(directory+"/genomes/genomes/"+reference+".2.ptt", "w") as out:
            subprocess.run(
                ["grep" , "-P", "Location|^\d+\.\.",  directory+"/genomes/genomes/"+reference+".ptt"],
                stdout=out,
                check=True
            )


    merged_with_positions2 = []
    if os.path.exists(gene_position_file) & os.path.exists(gene_position_file2):
        #df_gene_positons = pd.read_csv('data/Xo/'+reference+'.ptt',sep='\t')
        df_gene_positons = pd.read_csv(directory+'/genomes/genomes/'+reference+'.2.ptt',sep='\t')
        df_gene_positons["PID"] = df_gene_positons["PID"].str.replace(":", "", regex=False)

        if 'block_id' not in df_gene_positons.columns:
            df_gene_positons.insert(0, 'block_id', 'chr1')

        # create a simplified matrix, with only the first gene if a list of genes for the reference
        simplified_df_matrix = df_matrix
        simplified_df_matrix[[reference]] = simplified_df_matrix[reference].str.extract('([^,]+),*', expand=True)

        merged_with_positions = pd.merge(simplified_df_matrix, df_gene_positons, left_on=reference, right_on='PID')
        #merged_with_positions = pd.merge(df_matrix, df_gene_positons, left_on=reference, right_on='PID')

        print("merged_with_positions")
        df_gene_positons.to_csv("export_gene_positions.csv")

        if len(merged_with_positions) != 0:

            # rename and reorganize columns
            merged_with_positions = merged_with_positions.rename(columns={'ClutserID': 'name'})
            merged_with_positions[['start', 'end']] = merged_with_positions['Location'].str.split('\.\.', expand=True)
            merged_with_positions2 = merged_with_positions
            #merged_with_positions.insert(0, 'block_id', 'chr1')
            merged_with_positions.insert(0, 'color', 'black')
            merged_with_positions = merged_with_positions[['name','block_id','start', 'end','color','Strand']]
            merged_with_positions['start'] = merged_with_positions['start'].astype(int)
            gene_plus_df = merged_with_positions[merged_with_positions["Strand"] == "+"]
            gene_minus_df = merged_with_positions[merged_with_positions["Strand"] == "-"]
            dict_list_gene_plus = gene_plus_df.to_dict('records')
            dict_list_gene_minus = gene_minus_df.to_dict('records')
            karyotype_df = merged_with_positions.groupby('block_id').max().reset_index()
            karyotype_df = karyotype_df.rename(columns={'block_id': 'id'})
            karyotype_df['label'] = karyotype_df.loc[:, 'id']
            karyotype_df = karyotype_df.rename(columns={'start': 'len'})
            karyotype_df = karyotype_df[['id','label','len','color']]
            karyotype_dict_list = karyotype_df.to_dict('records')
        else:
            merged_with_positions = simplified_df_matrix
            merged_with_positions = merged_with_positions.rename(columns={'ClutserID': 'name'})

    
    core_df['ClutserID'] = core_df['ClutserID'].astype(int)
    
    core_df_merged_with_positions = pd.merge(core_df, merged_with_positions, left_on='ClutserID', right_on='name')
    core_df_merged_with_positions = core_df_merged_with_positions[['name','block_id','start', 'end','color','Strand']]
    core_df_merged_with_positions.to_csv(tmp_dir + "/" + str(session) + ".core.txt",index=False,sep='\t')
    core_list_dict = core_df_merged_with_positions.to_dict('records')

    specific_df['ClutserID'] = specific_df['ClutserID'].astype(int)
    specific_df_merged_with_positions = pd.merge(specific_df, merged_with_positions, left_on='ClutserID', right_on='name')
    specific_df_merged_with_positions = specific_df_merged_with_positions[['name','block_id','start', 'end','color','Strand']]
    specific_df_merged_with_positions.to_csv(directory+"/specific.txt",index=False,sep='\t')
    specific_list_dict = specific_df_merged_with_positions.to_dict('records')

    

    #specific_df_merged_with_positions.to_csv(directory+"/specific.txt",index=False,sep='\t')
    
    fig_gene = px.histogram(df2, x="sum")


    #################################################
    # pan-GWAS
    #################################################
    scoary_table = []
    scoary_output_file = tmp_dir + "/" + str(session) + ".scoary_results.txt"
    if specific_to is not None and len(specific_to) > 0:
        # write traits file for Scoary
        with open(tmp_dir + "/" + str(session) + ".traits.csv", "a") as f:
            f.write(",Trait1\n")
            for strain in list_selected:
                if strain != "ClutserID":
                    f.write(str(strain))
                    f.write(",")
                    if strain in specific_to:
                        f.write("1\n")
                    else:
                        f.write("0\n")

        # write input file for Scoary
        with open(tmp_dir + "/" + str(session) + ".scoary_input.csv", "a") as i:
            df_for_scoary = pd.read_csv(directory+'/1.Orthologs_Cluster.txt',sep='\t')
            col_position = df.columns.get_loc("ClutserID") + 1
            df_for_scoary.insert(col_position, "Non-unique Gene name", None)
            df_for_scoary.insert(col_position + 1, "Annotation", None)
            df_for_scoary.insert(col_position + 2, "No. isolates", None)
            df_for_scoary.insert(col_position + 3, "No. sequences", None)
            df_for_scoary.insert(col_position + 4, "Avg sequences per isolate", None)
            df_for_scoary.insert(col_position + 5, "Genome Fragment", None)
            df_for_scoary.insert(col_position + 6, "Order within Fragment", None)
            df_for_scoary.insert(col_position + 7, "Accessory Fragment", None)
            df_for_scoary.insert(col_position + 8, "Accessory Order with Fragment", None)
            df_for_scoary.insert(col_position + 9, "QC", None)
            df_for_scoary.insert(col_position + 10, "Min group size nuc", None)
            df_for_scoary.insert(col_position + 11, "Max group size nuc", None)
            df_for_scoary.insert(col_position + 12, "Avg group size nuc", None)
            df_for_scoary.rename(columns={'ClutserID': 'Gene'}, inplace=True)
            df_for_scoary.to_csv(tmp_dir + "/" + str(session) + ".scoary_input.csv",index=False)

        #cmd = scoary_exe + " " + tmp_dir + "/" + str(session) + ".scoary_input.csv " + tmp_dir + "/" + str(session) + ".traits.csv " + tmp_dir + "/" + str(session) + "_scoary_output --trait-data-type binary --gene-data-type gene-list"
        if validate_session_id(session):
            subprocess.run(
                [scoary_exe , "-g", tmp_dir + "/" + str(session) + ".scoary_input.csv", "-t", tmp_dir + "/" + str(session) + ".traits.csv", "-o", tmp_dir + "/" + str(session) + "_scoary_output"],
                check=True
            )

            src_pattern = f"{tmp_dir}/{session}_scoary_output/*results.csv"
            src_files = glob.glob(src_pattern)
            if src_files:
                dst = f"{tmp_dir}/{session}.scoary_results.txt"
                shutil.copy(src_files[0], dst)
                
        #merged_with_positions_scoary = pd.DataFrame(columns=["Gene","fisher_p","odds_ratio","log_pval","start"])
        #df_scoary_results = pd.DataFrame(columns=["Gene","fisher_p","odds_ratio"])

        merged_with_positions_scoary = pd.DataFrame(columns=["Gene","Naive_p","Bonferroni_p","Odds_ratio","log_pval","start"])
        df_scoary_results = pd.DataFrame(columns=["Gene","Naive_p","Bonferroni_p","Odds_ratio"])

        if os.path.exists(scoary_output_file):

            df_scoary_results = pd.read_csv(scoary_output_file)

            merged_with_positions_scoary = pd.merge(df_scoary_results, merged_with_positions, left_on='Gene', right_on='name')

            #merged_with_positions_scoary["log_pval"] = -np.log10(merged_with_positions_scoary["fisher_p"])
            merged_with_positions_scoary["log_pval"] = -np.log10(merged_with_positions_scoary["Naive_p"])

        scoary_table = df_scoary_results.to_dict('records')
        
    df_matrix.to_csv(tmp_dir + "/" + str(session) + ".df_matrix.csv")
    df2.to_csv(tmp_dir + "/" + str(session) + ".df2.csv")
    merged_with_positions2.to_csv(tmp_dir + "/" + str(session) + ".merged_with_positions2.csv")
    df_metadata3.to_csv(tmp_dir + "/" + str(session) + ".df_metadata3.csv")
    merged_with_cog.to_csv(tmp_dir + "/" + str(session) + ".merged_with_cog.csv")
    df.to_csv(tmp_dir + "/" + str(session) + ".df.csv")
    fig = heatmap_PAV(proj_title,session,specific_to,ordering,sample_ordering,metadata_table,reference,highlight,cluster_search,bedfile,colorizing,1)

    text_stat="Number of genomes: " + str(len(list_sp2)) + ", Pangenome size: " + str(nb_pangenes)+" pan-genes and "+str(nb_coregenes)+" core-genes and "+str(nb_specific_genes)+" strain-specific genes"
    #fig.update_traces(showscale=False)
    fig.update_layout(clickmode='event+select')




###################
# TODO: pour ajouter legende sur le circos
###################
    # colors = ['red', 'green', 'blue', 'orange']
    # labels = ['Catégorie A', 'Catégorie B', 'Catégorie C', 'Catégorie D']
    # for color, label in zip(colors, labels):
    #     fig.add_trace(go.Scatter(
    #         x=[None],  # Pas de données
    #         y=[None],
    #         mode='markers',
    #         marker=dict(size=10, color=color),
    #         legendgroup=label,
    #         showlegend=True,
    #         name=label
    #     ))

    # fig.update_layout(
    #     showlegend=True,
    #     legend=dict(
    #         title="Légende personnalisée",
    #         x=1,
    #         y=1,
    #         bgcolor="rgba(255,255,255,0.7)"
    #     )
    # )


    
    ################
    # Upset plot
    ################
    df_upset = df2.drop(["ClutserID","sum","type"], axis='columns')
    df_upset = df_upset[list_sp2[:6]]

    print("df_upset")
    print(df_upset)

    upset_plot = None

    # upset_plot = plot_upset(
    #     dataframes=[df_upset],
    #     exclude_zeros=True,
    #     sorted_x="d",
    #     sorted_y="a",
    #     legendgroups=["Strains"],
    #     marker_size=11,
    # )
    # upset_plot.update_layout(
    #     title_text='Upset plot for accessory genes (for the first 6 samples).',
    #     width=1800,
    #     height=800
    # )
    


    #######################
    # ANI
    #######################

    
    fig_ANI = None
    tab_style_ani = {'display': 'none'}
    if os.path.exists(directory + "/fastani.out.matrix.complete.xls") and os.path.getsize(directory + "/fastani.out.matrix.complete.xls") > 0:
        tab_style_ani = tab_style 
        print(list_sp2)
        df_ANI_selected = df_ANI[df_ANI["Genomes"].isin(list_sp2)]
        df_ANI_selected = df_ANI_selected[list_sp2]
        df_ANI_selected.to_csv("export_ani.tsv")
        
        fig_ANI = dash_bio.Clustergram(
            data=df_ANI_selected,
            column_labels=list(df_ANI_selected.columns.values),
            row_labels=list(df_ANI_selected.index),
            #row_labels=list(df_ANI_selected.columns.values),
            height=1200,
            width=1700,
            center_values=False,
            line_width=2,
            color_map= [
                [0.0, 'yellow'],
                [1.0, 'red']
            ]
        )
    #fig_ANI.update_traces(showlegend=False) # does not work

    #df_ANI_selected.to_csv("export2.tsv")

    table_specific = specific_df.to_dict('records')
    table_core = core_df.to_dict('records')
    
    table_pangenes = merged_with_cog.to_dict('records')
    merged_with_cog.to_csv(tmp_dir + "/" + str(session) + ".export_merged_with_cog.csv")
    
    current_layout = karyotype_dict_list
    
    #current[0].update(data=circos_graph_data["cytobands"], type="HIGHLIGHT",config=highlight_config)
    current_tracks[0].update(data=dict_list_gene_plus,type="HIGHLIGHT",config=highlight_config1)
    current_tracks[1].update(data=dict_list_gene_minus,type="HIGHLIGHT",config=highlight_config2)
    current_tracks[2].update(data=core_list_dict,type="HIGHLIGHT",config=highlight_config3)
    current_tracks[3].update(data=specific_list_dict,type="HIGHLIGHT",config=highlight_config4)


    ##############################
    # COG graphes
    ##############################
    data_COG1 = pd.DataFrame()
    data_COG2 = pd.DataFrame()
    fig_COG1 = None
    fig_COG2 = None
    if os.path.exists(directory+"/cog_category_counts.txt") and os.path.getsize(directory+"/cog_category_counts.txt") > 0 and os.path.exists(directory+"/cog_category_2_counts.txt") and os.path.getsize(directory+"/cog_category_2_counts.txt") > 0:
        data_COG1 = pd.read_csv(directory+'/cog_category_counts.txt',sep='\t')
        data_COG1 = data_COG1.rename(columns={'COG': 'Genome'})
        data_COG2 = pd.read_csv(directory+'/cog_category_2_counts.txt',sep='\t')
        data_COG2 = data_COG2.rename(columns={'COG': 'Genome'})
        data_COG1_selected = data_COG1[data_COG1["Genome"].isin(list_sp2)]
        data_COG2_selected = data_COG2[data_COG2["Genome"].isin(list_sp2)]

        df_count = merged_with_cog.groupby(['COGcat']).size().reset_index(name='counts')
        df_count.to_csv("COG.count.txt")

        occur = df_cog_of_clusters.groupby(['COG']).size()
        top30 = df_cog_of_clusters['COG'].value_counts().head(30).reset_index()
        top30.columns = ['COG', 'counts']
        top30_with_cog_term = pd.merge(df_cog_terms, top30, how="right", left_on='COG', right_on='COG')

        top30_with_cog_term.to_csv("cog_occurrences.csv")

        #dftet = px.data.tips()
        #dftet.to_csv("COG.count.txt")

        #fig_COG_all = px.pie(df_count, values='counts', names='COGcat', title='Distribution of COG categories among all clusters')
        fig_COG_all = px.bar(df_count, x='COGcat', y='counts', title='Distribution of COG categories among all clusters')
        
        #data_COG2_selected.to_csv("export_COG.tsv")
        
        fig_COG1 = px.bar(data_COG1_selected, x='Genome', y=data_COG1_selected.columns, title="Distribution of COG functional categories")
        fig_COG2 = px.bar(data_COG2_selected, x='Genome', y=data_COG2_selected.columns, title="Distribution of COG functional categories")
        fig_COG1.update_layout(
            yaxis_title="Number of genes with COG category"
        )
        fig_COG2.update_layout(
            yaxis_title="Number of genes with COG category"
        )

        fig_COG2 = px.bar(top30_with_cog_term, x='counts', y='COG term', orientation='h', title="Top 30 most frequent COGs in the pangenome")


    ############################################################
    # accessory-based tree
    ############################################################

    
    newick = ""
    
    # get tree in newick format as a variable
    with open(directory+'/heatmap.svg.complete.pdf.distance_matrix.hclust.newick') as fp:
        newick = fp.read()

    df_metadata.to_csv(directory+'/metadata.csv',sep=',',index=False)
    metadata_csv = ""
    with open(directory+'/metadata.csv') as fp:
        metadata_csv = fp.read()

    #generate_tree_html(newick, df_metadata, "Country", tmp_dir + "/" + str(session) + ".tree.html")
    generate_tree_html(newick, df_metadata, "Country", "assets/tree."+str(session)+".html")

    print("resulats recherche cluster: "+str(len(search_res2)))
    nb_of_pangenes = "Pan-genes (" + str(nb_pangenes) + ")"

    clustersearch = ""
    if len(search_res2) > 1:
        clustersearch = str(len(search_res2)) + " clusters (specifically present in selected strains)"

    ############################################################
    # Calculate coordinates of core-genes for macrosynteny
    ############################################################

    print("Number of genes:")
    # remove duplicates from a list
    list_selected = list(dict.fromkeys(list_selected))
    
    df_matrix_filtered = df_matrix[list_selected]
    df_core_genes = pd.merge(df_matrix_filtered, core_df, how='inner', on=['ClutserID', 'ClutserID']) 

    df_core_genes.to_csv(tmp_dir + "/" + str(session) + ".core_genes.txt",sep="\t")

    list_selected.remove("ClutserID")
    max_nb_strains_macrosynteny = 20
    if len(list_selected) < max_nb_strains_macrosynteny:
        max_nb_strains_macrosynteny = len(list_selected)

    print("Max nb for synteny: " + str(max_nb_strains_macrosynteny))
    print(list_selected)

    
    selection_dir = tmp_dir+"/selection."+str(session)
    print(selection_dir)

    try:
        os.makedirs(selection_dir)
        print(f"Nested directories '{selection_dir}' created successfully.")
    except FileExistsError:
        print(f"One or more directories in '{selection_dir}' already exist.")
    except PermissionError:
        print(f"Permission denied: Unable to create '{selection_dir}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

    c=0
    list_of_species_macrosyneny = []
    for sp in list_selected:
        c+=1
        if (c >=1 and c <=(max_nb_strains_macrosynteny)):
            if validate_session_id(session):
                shutil.copy(directory+"/genomes/genomes/"+sp+".ptt", selection_dir)
                list_of_species_macrosyneny.append(sp)

    

    if validate_session_id(session) and is_string_without_special_character(chromosome) and int(minimal_size_block):
        subprocess.run(
            ["perl" , "GetSyntenicBlocks.pl", selection_dir, tmp_dir + "/" + str(session) + ".core_genes.txt", tmp_dir + "/" + str(session) + ".syntenic_blocks.txt", str(minimal_size_block), str(chromosome)],
            check=True
        )

    # add the prefix haplo to indexes
    #haplotype_freq_df.index = [f"haplo{i+1}" for i in range(len(haplotype_freq_df))]

    with open("assets/clinker."+str(session)+".html", "w") as out:
        subprocess.run(
            ["cat" , "assets/clinker_template.part1.html", tmp_dir + "/" + str(session) + ".syntenic_blocks.txt.clinker.json", "assets/clinker_template.part2.html"],
            stdout=out,
            check=True
        )

    clinker = html.Iframe(src="assets/clinker."+str(session)+".html",style={"height": "2000px", "width": "100%"}),

    df_macrosynteny = pd.read_csv(tmp_dir + "/" + str(session) + ".syntenic_blocks.txt",sep=',')
    list_of_species_macrosyneny = df_macrosynteny.columns.tolist()
    print(list_of_species_macrosyneny)
    list_of_species_macrosyneny.remove("num_block")
    list_of_species_macrosyneny.remove("Unnamed: 0")
    graph_macrosynteny = go.Figure()
    if not df_macrosynteny.empty:
        graph_macrosynteny = px.parallel_coordinates(df_macrosynteny,color="num_block",
                                dimensions=list_of_species_macrosyneny,
                                #color_continuous_scale=px.colors.diverging.Tealrose,
                                #color_continuous_midpoint=2
                                )

    ##############################################################################################
    # VNTR table / MLVA
    ##############################################################################################
    vntr_file = directory+'/vntr_matrix.tsv'

    list_selected = ['ID','Repeat','Flanking']
    #if submit_samples:
    if metadata_table:
        wjdata = json.loads(json.dumps(metadata_table, indent=2))
        val = wjdata
        for strain in wjdata:
            strain_name = strain['Strain name']
            list_selected.append(strain_name)


    df_vntr = pd.DataFrame(columns=['ID','Repeat','Flanking'])
    flanking_sequences = ""
    tab_style_repeats = {'display': 'none'}
    if os.path.exists(vntr_file) and os.path.getsize(vntr_file) > 0:

        tab_style_repeats = tab_style

        # remove lines/markers with missing data
        vntr_file_nomissing = directory+'/vntr_matrix.nomissing.tsv'

        with open(vntr_file_nomissing, "w") as out:
            subprocess.run(
                ["grep" , "-v", "-", vntr_file],
                stdout=out,
                check=True
            )

        df_vntr = pd.read_csv(vntr_file_nomissing,sep='\t')
        df_vntr_filtered = df_vntr[list_selected]
        df_vntr = df_vntr_filtered

        # df_vntr_filtered = df_vntr.drop(list_selected, axis=1)
        # df_vntr = df_vntr_filtered

        # for row in df_vntr.itertuples():
        #     id = row[1]
        #     flanking = row[3]
        #     flanking_sequences = flanking_sequences + ">" + str(id) + "\n" + str(flanking) + "\n"
            

    
    repeat_names = df_vntr["ID"].astype(str).tolist()

    df_vntr.to_csv(tmp_dir + "/" + str(session) + ".vntr_matrix.tsv",sep='\t',index=False)
    nb_of_repeats = "VNTR loci (" + str(len(repeat_names)) + ")"


    newdf = df_vntr.drop(["ID","Repeat","Flanking"], axis='columns')
    graph_mlva = px.imshow(newdf.T, 
                           aspect="auto",
                           labels=dict(y="Samples", x="VNTR loci", color="Number of repeats"),
                           x=repeat_names,
                           #y=list_sp2,
                           text_auto=True
                           )
    mlva_table = df_vntr.to_dict('records')
    newdf.T.to_csv(directory+ "/export_mlva.tsv",sep='\t')

    ##############################################################################################
    # SNP
    ##############################################################################################
    vcf_file = directory+"/variants.vcf"
    df_vcf_transposed = pd.DataFrame()
    df_pca = pd.DataFrame(columns=['#IID', 'PC1', 'PC2','PC3'])
    df_crossentropy = pd.DataFrame(columns=['K', 'Cross-entropy'])
    dfsnmf = pd.DataFrame(columns=['Individual','Ancestry','Cluster','K'])
    individual_order = []
    individual_order_by_Pop1 = []
    col_names = []
    nb_of_snps = 0
    tab_style_snps = {'display': 'none'}
    if os.path.exists(vcf_file) and os.path.getsize(vcf_file) > 0:

        tab_style_snps = tab_style

        #################################################################
        # Phylogenetic tree from SNPs
        #################################################################
        # filter samples
        selected_file = open(tmp_dir + "/" + str(session) + ".selected_genomes.txt", "w")
        list_selected.remove("ID")
        list_selected.remove("Repeat")
        list_selected.remove("Flanking")
        with open(tmp_dir + "/" + str(session) + ".selected_genomes.txt", "w") as f:
            f.write("\n".join(list_selected) + "\n")

        cmd_args = [
            plink2_exe, "--vcf", vcf_file,
            "--keep", f"{tmp_dir}/{session}.selected_genomes.txt",
            "--maf", "0.0001",
            "--export", "vcf",
            "--max-alleles", "2",
            "--min-alleles", "2",
            "--geno", "0.001",
            "--out", f"{tmp_dir}/{session}.selected_genomes"
        ]
        subprocess.run(cmd_args, capture_output=True)

        
        vcf_file = tmp_dir + "/" + str(session) + ".selected_genomes.vcf"

        # make bed
        cmd_args = [
            plink2_exe, "--vcf", vcf_file,
            "--max-alleles", "2",
            "--min-alleles", "2",
            "--make-bed",
            "--out", f"{tmp_dir}/{session}.dataset"
        ]
        subprocess.run(cmd_args, capture_output=True)

        # distance calculation
        cmd_args = [
            plink_exe,
            "--bfile", f"{tmp_dir}/{session}.dataset",
            "--distance", "square",
            "--allow-extra-chr",
            "--out", f"{tmp_dir}/{session}.dataset"
        ]
        subprocess.run(cmd_args, capture_output=True)

        with open(f"{tmp_dir}/{session}.dataset.dist.id", "r") as infile, \
            open(f"{tmp_dir}/{session}.dataset.dist.id.2", "w") as outfile:
            for line in infile:
                if not line.startswith("#FID"):
                    outfile.write(line)


        #################################################################
        # --- Heatmap of genotypes from VCF ---
        #################################################################
        order_samples = pd.read_csv(directory+"/1.Orthologs_Cluster.txt", nrows=0, sep="\t").columns.tolist()
        order_samples.remove("ClutserID")
        list_sp2_sorted = [sample for sample in order_samples if sample in list_sp2]
        list_sp2 = list_sp2_sorted



        try:
            df_vcf = parse_vcf(vcf_file, int(5000), list_sp2)
            df_vcf_transposed = df_vcf.T
        except Exception as e:
            fig_VCF = px.imshow(np.zeros((2,2)))
            fig_VCF.update_layout(title=f"Error during parsing: {str(e)}")

        if df.shape[0] == 0 or df.shape[1] == 0:
            fig_VCF = px.imshow(np.zeros((2,2)))

            fig_VCF.update_layout(title="No variant or sample found(check VCF file)")

        
        

        #################################################################
        # Phylogenetic tree from SNPs
        #################################################################

        from skbio import DistanceMatrix
        from skbio.tree import nj

        nb_of_snps = "SNPs (" + str(sum(1 for line in open(vcf_file)) - 1) + ")"

        # Charger les identifiants
        ids = pd.read_csv(tmp_dir + "/" + str(session) + ".dataset.dist.id.2", delim_whitespace=True, header=None)
        ids = ids[1].tolist()

        # Charger la matrice de distances
        D = np.loadtxt(tmp_dir + "/" + str(session) + ".dataset.dist")

        # Construire la matrice de distances scikit-bio
        dm = DistanceMatrix(D, ids)

        # Construire un arbre neighbor-joining
        tree = nj(dm)

        rooted_tree = tree.root_at_midpoint()

        # Sauvegarder au format Newick
        with open(tmp_dir + "/" + str(session) + ".dataset.tree", "w") as f:
            f.write(str(rooted_tree))

        # Extraire l'ordre des taxons dans l'arbre
        individual_order_by_Pop1 = [tip.name for tip in rooted_tree.tips()]

        snp_based_newick = ""
        # get tree in newick format as a variable
        with open(tmp_dir + "/" + str(session) + ".dataset.tree") as fp:
            snp_based_newick = fp.read()
            df_metadata_selected = df_metadata[df_metadata['Strain name'].isin(list_selected)] 
            df_metadata_selected.to_csv("metadata_selected.csv",sep=',')
            generate_tree_html(snp_based_newick, df_metadata_selected, "Country", "assets/snp_based_tree."+str(session)+".html")



        #################################################################
        # Population structure with sNMF
        #################################################################
        max_K = 5
        if len(list_selected) < max_K:
            max_K = len(list_selected)

        cmd_args = [vcf2geno_exe, vcf_file, f"{tmp_dir}/{session}.variants.geno"]
        subprocess.run(cmd_args, capture_output=True)

        result = subprocess.run(
            ["grep", "#CHROM", vcf_file],
            capture_output=True,
            text=True,
            check=True
        )
        list_sp3 = result.stdout.strip().split("\t")[9:]

        with open(directory + "/1.Orthologs_Cluster.txt") as f:
            ordered_ids = f.readline().strip().split("\t")

        ordered_ids.remove("ClutserID")


        results = []
        list_entropy = []
        
        snmf_failure = 0
        # Launch sNMF for K from 2 to max_K
        for K in range(2, max_K+1):
            cmd = snmf_exe + " -x " + tmp_dir + "/" + str(session) + ".variants.geno" + " -c -K " + str(K)
            returned_value = os.popen(cmd).read()
            match = re.search(r"Cross-Entropy \(masked data\):\s*([0-9]+(?:\.[0-9]+)?)", returned_value)
            if match:
                valeur = float(match.group(1))
                list_entropy.append(valeur)
            else:
                list_entropy.append(None)
                snmf_failure = 1

        previous_qmat = pd.DataFrame(columns=['Individual', 'Assigned_to_pop', 'max_prop'])
        if snmf_failure == 0:
            # get the assignation of individuals to populations
            previous_dict_groups = {}
            
            for K in range(2, max_K+1):
                ancestry_cols = [f"Pop_{i+1}" for i in range(K)]
                qmat = pd.read_csv(tmp_dir + "/" + str(session) + ".variants."+str(K)+".Q", sep=" ", header=None, names=ancestry_cols)
                qmat['Individual'] = list_sp3
                qmat['Assigned_to_pop'] = qmat[ancestry_cols].idxmax(axis=1)
                qmat['max_prop'] = qmat[ancestry_cols].max(axis=1)

                #print("\n\n")

                groups = qmat.groupby("Assigned_to_pop")["Individual"].agg(concat=lambda x: ", ".join(sorted(x)),size="count").reset_index().sort_values("size", ascending=False)
                #print(groups)
                #print(str(K))
                dict_groups = {}
                dict_renaming = {}
                dict_renaming2 = {}
                dict_done = {}
                dict_splitted = {}

                
                # first assignment for population with exact same individuals
                for row in groups.itertuples():
                    pop_name = row[1]
                    individuals = row[2]
                    dict_groups[individuals] = pop_name
                    #print(pop_name + " : " + individuals)
                    # keep the same name of population if it exists in previous dict
                    if individuals in previous_dict_groups:
                        previous_pop_name = previous_dict_groups[individuals]
                        dict_renaming[pop_name] = previous_pop_name
                        dict_done[previous_pop_name] = 1
                        #print("same as previous" + previous_pop_name)

                for row in groups.itertuples():
                    pop_name = row[1]
                    individuals = row[2]
                    dict_groups[individuals] = pop_name
                    #print(pop_name + " : " + individuals)
                    # keep the same name of population if it exists in previous dict
                    if individuals in previous_dict_groups:
                        print("do nothing here")
                    # else it means that the pop has been splitted into two populations
                    else:
                        if len(previous_dict_groups) > 0:
                            individuals_list = individuals.split(", ")
                            dict_of_pop_in_previous = {}
                            for ind in individuals_list:
                                # get the pop in previous qmat
                                pop = previous_qmat.loc[previous_qmat["Individual"] == ind, "Assigned_to_pop"].iloc[0]
                                
                                if pop not in dict_of_pop_in_previous:
                                    dict_of_pop_in_previous[pop] = 1
                                else:
                                    dict_of_pop_in_previous[pop] += 1
                                if pop not in dict_splitted:
                                    dict_splitted[pop] = pop_name
                                else:
                                    dict_splitted[pop] += ","+pop_name

                                    

                            print("splitted")
                            
                            

                            # renaming for all except the last one
                            if len(dict_of_pop_in_previous) > 1:
                                #dict_renaming[pop_name] = list(dict_of_pop_in_previous)[0]+","+list(dict_of_pop_in_previous)[1]
                                if dict_of_pop_in_previous[list(dict_of_pop_in_previous)[0]] >= dict_of_pop_in_previous[list(dict_of_pop_in_previous)[1]] and list(dict_of_pop_in_previous)[0] not in dict_done:
                                    dict_renaming[pop_name] = list(dict_of_pop_in_previous)[0]
                                    dict_done[list(dict_of_pop_in_previous)[0]] = 1
                                elif dict_of_pop_in_previous[list(dict_of_pop_in_previous)[1]] >= dict_of_pop_in_previous[list(dict_of_pop_in_previous)[0]] and list(dict_of_pop_in_previous)[1] not in dict_done:
                                    dict_renaming[pop_name] = list(dict_of_pop_in_previous)[1]
                                    dict_done[list(dict_of_pop_in_previous)[1]] = 1
                                
                            else:
                                if list(dict_of_pop_in_previous)[0] not in dict_done:
                                    dict_renaming[pop_name] = list(dict_of_pop_in_previous)[0]
                                    dict_done[list(dict_of_pop_in_previous)[0]] = 1
                                else:
                                    new_pop_name = "Pop_" + str(K)
                                    if len(dict_of_pop_in_previous) > 1:
                                        dict_renaming[list(dict_of_pop_in_previous)[0]+","+list(dict_of_pop_in_previous)[1]] = new_pop_name
                                    else:
                                        dict_renaming[pop_name] = new_pop_name
                                        dict_done[new_pop_name] = 1

                            #print(dict_of_pop_in_previous.keys())
                            #print(list(dict_of_pop_in_previous)[0])
                        else:
                            print("do nothing")

                #print("Dict renaming before adjustment")
                #print(dict_renaming)
                #print("Dict renaming after adjustment")
                #print(dict_renaming2)
                #print("Dict splitted")
                for key, value in dict_splitted.items():
                    listvalue = value.split(",")
                    dict_splitted[key] = list(dict.fromkeys(listvalue))
                
                #print(dict_splitted)
                list_keys_to_removed = []
                for key in dict_renaming.keys():
                    value = dict_renaming[key]
                    print("key: " + key + " => " + value)
                    list_values = value.split(",")
                    
                    if len(list_values) > 1:
                        has_been_adjusted = 0
                        for val in list_values:
                            print("val: " + val)
                            if val not in dict_done:
                                print("to be adjusted :" + val + "=>" + key)
                                has_been_adjusted = 1
                                dict_renaming[key] = val
                        if has_been_adjusted == 0:
                            new_pop_name = "Pop_" + str(K)
                            dict_renaming[key] = new_pop_name
                

                #print(dict_renaming)
                # rename pop for keeping the same as previously
                #qmat = qmat.rename(columns=dict_renaming)
                #qmat2 = qmat.drop('Assigned_to_pop', axis=1)
                #qmat = qmat
                #qmat["Assigned_to_pop"] = qmat[ancestry_cols].idxmax(axis=1)
                #print(qmat)
                #qmat['Assigned_to_pop'] = qmat[ancestry_cols].idxmax(axis=1)

                previous_dict_groups = dict_groups
                previous_qmat = qmat
                #print(dict_groups)
                #print(previous_dict_groups)

                qmat_sorted = qmat.sort_values(
                    by=['Assigned_to_pop', 'max_prop'],
                    ascending=[True, False]
                )

                individual_order = qmat_sorted['Individual'].tolist()

                qmat['Individual'] = pd.Categorical(
                    qmat['Individual'],
                    categories=individual_order,
                    ordered=True
                )

                qmat_long = qmat.melt(id_vars=['Individual'],
                            value_vars=ancestry_cols,
                            var_name='Cluster', value_name='Ancestry')

                qmat_long['K'] = K
                results.append(qmat_long)
        else:
            results = []
            

        if results:
            dfsnmf = pd.concat(results)
        else:
            dfsnmf = pd.DataFrame(columns=['Individual','Ancestry','Cluster','K'])

        dict_cross_entropy = {'K': range(2, max_K+1),'Cross-entropy': list_entropy}
        print(dict_cross_entropy)
        df_crossentropy = pd.DataFrame.from_dict(dict_cross_entropy)

        #################################################################
        # PCA with plink
        #################################################################
        output_basename = tmp_dir+"/"+str(session)+".plink"
        pca_output = output_basename + ".eigenvec"

        cmd_args = [
            plink_exe,
            "--vcf", vcf_file,
            "--pca",
            "--double-id",
            "--allow-extra-chr",
            "--out", output_basename
        ]
        subprocess.run(cmd_args, capture_output=True)

        if os.path.exists(pca_output):
            

            cmd_args = ["awk", "{print $1\"\\t\"$3\"\\t\"$4\"\\t\"$5}", pca_output]
            with open(f"{pca_output}.tsv", "w") as outfile:
                result = subprocess.run(cmd_args, stdout=outfile, capture_output=False)

        if os.path.exists(pca_output + ".tsv"):
            df_pca = pd.read_csv(pca_output + ".tsv",sep='\t',header=None, names=['#IID', 'PC1', 'PC2','PC3'])


        df_pca_metadata=pd.merge(df_pca,df_metadata, left_on='#IID', right_on='Strain name' )
        df_pca_pop_metadata=pd.merge(df_pca_metadata,previous_qmat, left_on='Strain name', right_on='Individual' )
        df_pca_pop_metadata.to_csv(tmp_dir+"/"+str(session) + "." +"metadata.txt")
        
    fig_VCF = px.imshow(
            df_vcf_transposed.values,
            labels={'x': 'Variants', 'y': 'Samples', 'color': 'Alt allele count'},
            x=df_vcf_transposed.columns,
            y=df_vcf_transposed.index,
            aspect='auto',
            origin='upper',
            zmin=0,
            zmax=2,
            color_continuous_scale='Viridis'
    )

    fig_VCF.update_layout(
            margin=dict(l=200, r=20, t=50, b=150),
            #height=800,
            title="SNP Genotyping matrix (only the first 5000 variants are displayed)"
    )  

    
    
    
    fig_scatter = pca("3D","Country",session)

    # Création des barcharts avec facettes
    fig_snmf = px.bar(
        dfsnmf, 
        x="Individual", y="Ancestry", color="Cluster", category_orders={"Individual": individual_order_by_Pop1}, 
        facet_row="K",  # un graphique par valeur de K
        height=800
    )

    fig_snmf.update_layout(
        title="Population structure (by sNMF) for different K",
        barmode='stack',
        showlegend=True
    )

    fig_cross_entropy = px.line(df_crossentropy, x="K", y="Cross-entropy", title='Values of the cross-entropy criterion for 4 sNMF runs (K=2 to K=5)')


    #############################################################################################
    # GFA viewer
    #############################################################################################
    tab_style_segments = { 'display' : 'none'}
    node_names = []   # populated below if GFA file is present
    gfa_file = directory+"/pangenome.gfa"
    graph_gfa = go.Figure()
    graph_gfa2 = go.FigureWidget()
    if os.path.exists(gfa_file) and os.path.getsize(gfa_file) > 0:

        tab_style_segments = tab_style  
        
        cmd_args = [
            "perl", "generateNodePAVfromGFA.pl",
            f"{directory}/pangenome.gfa",
            str(reference),
            f"{tmp_dir}/{session}.{reference}.segments",
            ",".join(list_sp2)
        ]
        subprocess.run(cmd_args, capture_output=True)


        x_segments = []
        y_segments = []
        dict_segments_x = {}
        dict_segments_y = {}
        with open(tmp_dir +"/"+str(session) + "." + str(reference)+".segments.segments_x.txt",'r') as file:
            for line in file:
                text = line.strip()
                text2 = text.rstrip(text[-1])
                infos = text2.split("###")
                dict_segments_x[infos[0]] = infos[1]


        with open(tmp_dir +"/"+str(session) + "." +str(reference)+".segments.segments_y.txt",'r') as file:
            for line in file:
                text = line.strip()
                text2 = text.rstrip(text[-1])
                infos = text2.split("###")
                dict_segments_y[infos[0]] = infos[1]


        #x_segments = [0,10,None,20,30,None,40,50,None]
        #y_segments = [2,2,None,6,6,None,80,80,None]


        for key in dict_segments_x.keys():
            if key in dict_segments_y:
                sample = key
                print("key: " + key)
                x_segments = dict_segments_x[key].split(",")
                print(x_segments)
                for i in range(0, len(x_segments)):
                    if x_segments[i] != 'None':
                        x_segments[i] = int(x_segments[i])
                    else:
                        x_segments[i] = None

                y_segments = dict_segments_y[key].split(",")
                for i in range(0, len(y_segments)):
                    if y_segments[i] != 'None':
                        y_segments[i] = int(y_segments[i])
                    else:
                        y_segments[i] = None

                x_segments3 = np.array(x_segments)
                x_segments = x_segments3 
                y_segments3 = np.array(y_segments)
                y_segments = y_segments3 


                graph_gfa.add_trace(go.Scatter(
                    x=x_segments,
                    y=y_segments,
                    mode='lines',
                    name=key,
                    line=dict(width=25),
                    #hoverinfo='skip'
                ))

        scoary_table2 = []
        scoary_output_file2 = tmp_dir + "/" + str(session) + ".scoary_results2.txt"
        if specific_to is not None and len(specific_to) > 0:
            with open(tmp_dir + "/" + str(session) + ".scoary_input2.csv", "a") as i:
                df_for_scoary = pd.read_csv(tmp_dir + "/" + str(session) + "." + str(reference) + ".segments.node_pav.tsv",sep='\t')
                col_position = df_for_scoary.columns.get_loc("Node") + 1
                df_for_scoary.insert(col_position, "Non-unique Gene name", None)
                df_for_scoary.insert(col_position + 1, "Annotation", None)
                df_for_scoary.insert(col_position + 2, "No. isolates", None)
                df_for_scoary.insert(col_position + 3, "No. sequences", None)
                df_for_scoary.insert(col_position + 4, "Avg sequences per isolate", None)
                df_for_scoary.insert(col_position + 5, "Genome Fragment", None)
                df_for_scoary.insert(col_position + 6, "Order within Fragment", None)
                df_for_scoary.insert(col_position + 7, "Accessory Fragment", None)
                df_for_scoary.insert(col_position + 8, "Accessory Order with Fragment", None)
                df_for_scoary.insert(col_position + 9, "QC", None)
                df_for_scoary.insert(col_position + 10, "Min group size nuc", None)
                df_for_scoary.insert(col_position + 11, "Max group size nuc", None)
                df_for_scoary.insert(col_position + 12, "Avg group size nuc", None)
                df_for_scoary.rename(columns={'ClutserID': 'Gene'}, inplace=True)
                df_for_scoary.to_csv(tmp_dir + "/" + str(session) + ".scoary_input2.csv",index=False)

            cmd_args = [
                scoary_exe,
                "-g", f"{tmp_dir}/{session}.scoary_input2.csv",
                "-t", f"{tmp_dir}/{session}.traits.csv",
                "-o", f"{tmp_dir}/{session}_scoary_output2"
            ]
            subprocess.run(cmd_args, capture_output=True)

            src_pattern = f"{tmp_dir}/{session}_scoary_output2/*results.csv"
            src_files = glob.glob(src_pattern)
            if src_files:
                dst = f"{tmp_dir}/{session}.scoary_results2.txt"
                shutil.copy(src_files[0], dst)

            #merged_with_positions_scoary = pd.DataFrame(columns=["Gene","Naive_p","Bonferroni_p","Odds_ratio","log_pval","start"])
            df_scoary_results2 = pd.DataFrame(columns=["Gene","Naive_p","Bonferroni_p","Odds_ratio"])

            if os.path.exists(scoary_output_file2):

                df_scoary_results2 = pd.read_csv(scoary_output_file2)

                #merged_with_positions_scoary = pd.merge(df_scoary_results, merged_with_positions, left_on='Gene', right_on='name')

                #merged_with_positions_scoary["log_pval"] = -np.log10(merged_with_positions_scoary["fisher_p"])
                df_scoary_results2["log_pval"] = -np.log10(df_scoary_results2["Naive_p"])

            scoary_table2 = df_scoary_results2.to_dict('records')

        df_pav_node = pd.read_csv(tmp_dir +"/"+str(session) + "." + str(reference) + ".segments.node_pav.tsv", sep="\t")
        list_strains = df_pav_node.columns.tolist()
        list_strains.remove("Node")
        node_names = df_pav_node["Node"].astype(str).tolist()
        #df_pav_node = df_pav_node[list_strains]
        z_original = pd.DataFrame(columns=[])
        if not df_pav_node.empty:
            transposed_df_pav_node = df_pav_node[list_strains].transpose()
            df_ordered = transposed_df_pav_node.loc[list_sp2]
            z_original = df_ordered.values

        # Transformation symlog
        z_symlog = np.sign(z_original) * np.log10(np.abs(z_original) + 1) 

        if specific_to is not None and len(specific_to) > 0 and os.path.exists(scoary_output_file):

            df_scoary_results2 = pd.read_csv(scoary_output_file2)
            df_scoary_results2["log_pval"] = -np.log10(df_scoary_results2["Naive_p"])
            #df_pav_node = pd.read_csv(tmp_dir +"/"+str(session) + "." + str(reference) + ".segments.node_pav.tsv", sep="\t")
            merged_with_positions_scoary2 = pd.merge(df_scoary_results2, df_pav_node, left_on='Node', right_on='Node', how='right')
            pvalues_list2 = merged_with_positions_scoary2['log_pval'].tolist()
            graph_gfa2 = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                row_heights=[0.5, 0.5], 
                vertical_spacing=0.05
            )
            # Heatmap
            graph_gfa2.add_trace(
                go.Heatmap(
                        z=z_symlog,
                        y=list_sp2,
                        x=node_names,
                        colorscale='RdBu',
                        zmid=0,
                        customdata=z_original,
                        hovertemplate='x: %{x}<br>y: %{y}<br>valeur: %{z}<extra></extra>',
                        hoverongaps = False),
                row=1,
                col=1
            )
            # Scatter
            graph_gfa2.add_trace(
                go.Scatter(
                    
                    x=node_names,
                    y=pvalues_list2,
                    mode="markers",
                    #hover_data=["Gene","log_pval"],
                    marker=dict(size=5, color='MediumPurple')
                ),
                row=2,
                col=1
            )
            graph_gfa2.update_yaxes(title_text="-log10(pvalues)", row=2, col=1)
            graph_gfa2.update_layout(height=900)
            graph_gfa2.update_layout(title='Presence/absence matrix of segments in the pangenome graph. <br>Segments are ordered according to their position in the reference genome. The color scale is symlog transformed (base 10) of the segment size. <br>Pan-GWAS results are shown below the PAV matrix.')

        else:

            graph_gfa2 = go.FigureWidget(data=go.Heatmap(
                    z=z_symlog,
                    y=list_sp2,
                    x=node_names,
                    colorscale='RdBu',
                    zmid=0,
                    customdata=z_original,
                    hovertemplate='x: %{x}<br>y: %{y}<br>valeur: %{z}<extra></extra>',
                    hoverongaps = False))
            graph_gfa2.update_layout(
                title='Presence/absence matrix of segments in the pangenome graph. <br>Segments are ordered according to their position in the reference genome. The color scale is symlog transformed (base 10) of the segment size.',
            )

        
    
    ##############################################################################################
    # geographical map of strains
    ##############################################################################################
    counts = df_metadata3.groupby(["Country", "Continent"]).size().reset_index(name="number_strains")

    tab_style_geo = {'display': 'none'}
    fig_geomap = go.Figure()

    if not counts.empty:

        tab_style_geo = tab_style

        # Create the map
        fig_geomap = px.choropleth(
                counts,
                locations="Country",            # Colonne avec les noms des pays
                locationmode="country names", # On utilise les noms de pays
                color="number_strains",      # Couleur selon le nombre de souches
                color_continuous_scale="Viridis",
                title="Number of strains by country"
        )



    
    ##############################################################################################
    # merge main cluster table and cluster search in order to report the same columns
    ##############################################################################################
    if (len(search_res2) > 1):
        df_search = pd.DataFrame.from_dict(search_res2)
        df_search = pd.merge(df_search,merged_with_cog, left_on='ClutserID', right_on='ClutserID')
        search_res2 = df_search.to_dict('records')
        df_search = pd.merge(df_search,df_matrix, left_on='ClutserID', right_on='ClutserID')
        df_search.to_csv(directory+ "/search_results.txt",sep="\t",index=False)


    columnDefs3 = [
        {"field": "ClutserID", "width": 120},
        {"field": "COG term", "width": 500},
        {"field": "type", "width": 150}
    ]
    if (len(scoary_table) > 1):
        df_scoary = pd.DataFrame.from_dict(scoary_table)
        merged_with_cog = pd.merge(df_scoary,merged_with_cog, left_on='Gene', right_on='ClutserID',how = 'outer')
        table_pangenes = merged_with_cog.to_dict('records')
        columnDefs3 = [
            {"field": "ClutserID", "width": 120},
            {"field": "COG term", "width": 500},
            {"field": "type", "width": 150},
            {"field": "Odds_ratio", "width": 150},
            {"field": "Naive_p", "width": 150},
            {"field": "Bonferroni_p", "width": 150}
        ]
        
    # export final merged table
    merged_with_cog.to_csv(tmp_dir+ "/"+str(session)+".merged_with_cog_final.csv",sep="\t",index=False)

    list_metadata_columns = df_metadata.columns.tolist()
    list_metadata_columns.remove("Strain name")
    
    return "",nb_of_pangenes,text_stat,fig,table_pangenes,columnDefs3,fig_ANI,fig_gene,fig_pie,fig_COG2,fig_rarefaction,current_layout,current_tracks,clustersearch, graph_macrosynteny, clinker, mlva_table, nb_of_repeats, graph_mlva, fig_scatter, "assets/tree."+str(session)+".html", "assets/snp_based_tree."+str(session)+".html", {'display': 'block'}, nb_of_snps, fig_VCF, fig_snmf, fig_cross_entropy, fig_geomap, graph_gfa2, node_names, '', tab_style_segments, tab_style_repeats, tab_style_snps, tab_style_ani, tab_style_geo,session,list_metadata_columns,list_metadata_columns


@app.callback(
    Output('btn-update', 'disabled'),
    Input('btn-update', 'n_clicks'),
    prevent_initial_call=True
)
def hide_update_button(n_clicks):
    return True


@app.callback(
    Output('btn-update', 'disabled', allow_duplicate=True),
    Input('current_session', 'value'),
    prevent_initial_call=True
)
def show_update_button(session_value):
    return False

    #############################################################################################
    # Extraction and visualization of a subgraph
    #############################################################################################  

@app.callback(
    Output("subgraph-result-area", "children", allow_duplicate=True),
    Input("btn-extract-subgraph", "n_clicks"),
    State("subgraph-node-list", "value"),
    State("stored-node-id", "data"),
    State("subgraph-steps", "value"),
    State("subgraph-bp", "value"),
    State("subgraph-viz-type", "value"),
    State("current_session", "value"),
    State('projets', 'value'),
    State('metadata_table', 'selectedRows'),
    prevent_initial_call=True
)
def run_subgraph_extraction(n_clicks, node_list_input, node_data, steps, bp_dist, viz_type, session, project_name, selected_rows):
    # Prefer the node-list text input; fall back to the stored single node
    node_ids_raw = ""
    if node_list_input and node_list_input.strip():
        node_ids_raw = node_list_input.strip()
    elif node_data and "node_id" in node_data:
        node_ids_raw = str(node_data['node_id'])
    else:
        return dbc.Alert("No node specified! Enter node IDs in the field above or click a node on the graph.", color="warning")

    # Parse and clean the list
    node_ids_list = [n.strip() for n in node_ids_raw.split(',') if n.strip().isdigit()]
    if not node_ids_list:
        return dbc.Alert("No valid numeric node IDs found. Please enter comma-separated integers.", color="warning")

    node_id = node_ids_list[0]    # primary ID (kept for BED logic / single-node paths)
    node_ids_csv = ','.join(node_ids_list)  # for -l flag
    
    # --- 1. Setup Paths ---
    row = query_db("SELECT path FROM projects WHERE title = ?", (project_name,), one=True)
    project_path = row[0] if row else conf["session_dir"] + "/" + project_name
    input_gfa = os.path.join(project_path, "pangenome.gfa")
    
    import time
    timestamp = int(time.time())
    output_base = os.path.join(tmp_dir, f"{session}_node{node_id}_{timestamp}")
    output_og = output_base + ".og"

    # --- 2. Generate BED File (from stored single-node gene metadata, if available) ---
    bed_file_path = output_base + ".genes.bed"
    has_genes = False

    if node_data and isinstance(node_data, dict) and node_data.get("genes"):
        try:
            with open(bed_file_path, "w") as f:
                for gene in node_data["genes"]:
                    f.write(f"{gene['reference_genome']}\t{gene['start']}\t{gene['end']}\t{gene['gene_name']}\n")
            has_genes = True
        except Exception as e:
            print(f"Error writing BED: {e}")

    # --- 3. Build Command ---
    # Use -l (comma-separated list) for one or more nodes
    cmd_parts = [
        "bash", "extract_subgraphs.sh",
        "-i", input_gfa,
        "-o", output_og,
        "-l", node_ids_csv,
    ]

    # Add Selected Genomes (Paths)
    if selected_rows:
        selected_genomes = [row["Strain name"] for row in selected_rows if "Strain name" in row]
        if selected_genomes:
            paths_file_path = output_base + ".paths.txt"
            with open(paths_file_path, "w") as f:
                for genome in selected_genomes:
                    f.write(f"{genome}\n")
            cmd_parts.extend(["-p", paths_file_path])

    # Handle Mutually Exclusive Context Flags
    if bp_dist is not None and bp_dist > 0:
        cmd_parts.extend(["-L", str(bp_dist)])
    elif steps is not None and steps > 0:
        cmd_parts.extend(["-c", str(steps)])
    else:
        cmd_parts.extend(["-c", "1"])

    if has_genes:
        cmd_parts.extend(["-B", bed_file_path])
    
    # Add Visualization Flag
    
    cmd_parts.append(viz_type)

    # --- 4. Run Script ---
    full_cmd = " ".join(cmd_parts)
    print(f"Running: {full_cmd}")
    
    try:
        subprocess.run(cmd_parts, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        return html.Div([
            dbc.Alert("Error during extraction", color="danger"),
            html.Pre(e.stderr)
        ])

    # --- 5. Return Visualization (Now Interactive) ---
    

    # Handle Image Formats (PNG/SVG) using dcc.Graph for Zoom/Pan
    image_path = None
    mime_type = ""
    
    if viz_type == '--odgi':
        image_path = output_base + "_odgi.png"
        mime_type = "data:image/png;base64"
    elif viz_type == '--bandage':
        image_path = output_base + "_bandage.svg"
        mime_type = "data:image/svg+xml;base64"
    elif viz_type == '--vg':
        image_path = output_base + "_vg.svg"
        mime_type = "data:image/svg+xml;base64"
        
    if image_path and os.path.exists(image_path):
        # 1. Read and Encode Image
        encoded_image = base64.b64encode(open(image_path, 'rb').read()).decode('ascii')
        source_url = f"{mime_type},{encoded_image}"
        
        # 2. Get Dimensions to set graph ratio
        img_w, img_h = get_image_dimensions(image_path)
        
        # 3. Create Figure with Image Layout
        fig = go.Figure()
        
        # Add the image
        fig.add_layout_image(
            dict(
                source=source_url,
                xref="x",
                yref="y",
                x=0,
                y=0, # Plotly places image top-left at y=size_y usually, or we flip axis
                sizex=img_w,
                sizey=img_h,
                sizing="contain",
                layer="below"
            )
        )
        
        # Configure Axes
        fig.update_xaxes(visible=False, range=[0, img_w])
        # Invert Y axis so image coordinates match (0,0 at top-left)
        fig.update_yaxes(visible=False, range=[img_h, 0], scaleanchor="x")
        
        # Configure Layout for Interaction
        fig.update_layout(
            width=1200, # or '100%' via style
            height=800,
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
            dragmode="pan", # Enable Panning by default
            plot_bgcolor="white"
        )
        
        # Return Graph with config enabling scroll zoom
        return dcc.Graph(
            figure=fig, 
            config={'scrollZoom': True, 'displayModeBar': True},
            style={"width": "100%", "height": "80vh"}
        )

    return dbc.Alert("Extraction finished, but no output file was found.", color="warning")

@app.callback(
    Output("giraffe-options", "style"),
    Output("bandage-options", "style"),
    Input("align-method", "value")
)
def toggle_align_method(method):
    if method == "bandage":
        return {'display': 'none'}, {'display': 'block'}
    return {'display': 'block'}, {'display': 'none'}

@app.callback(
    Output("collapse-blast", "is_open"),
    Input("btn-collapse-blast", "n_clicks"),
    State("collapse-blast", "is_open"),
)
def toggle_blast_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("collapse-qpaths", "is_open"),
    Input("btn-collapse-qpaths", "n_clicks"),
    State("collapse-qpaths", "is_open"),
)
def toggle_qpaths_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

  #############################################################################################
    # Extraction and visualization of a subgraph based on alignments
    #############################################################################################  

# Callback: Run Sequence Alignment Script
@app.callback(
    Output("alignment-results-container", "style"),
    Output("alignment-error", "children"),
    Output("hit-selector", "options"),
    Output("hit-selector", "value"),
    Output("store-alignment-hits", "data"),
    Output("store-alignment-path", "data"),
    Input("btn-align-sequence", "n_clicks"),
    State("seq-input-fasta", "value"),
    State("seq-read-type", "value"),
    State("seq-context", "value"),      # Node Steps
    State("seq-context-bp", "value"),   # Base Pairs (NEW)
    State("current_session", "value"),
    State('projets', 'value'),
    State("align-method", "value"),
    State("bandage-blastp", "value"),
    State("bandage-ifilter", "value"),
    State("bandage-qcfilter", "value"),
    State("bandage-evfilter", "value"),
    State("bandage-alfilter", "value"),
    State("bandage-bsfilter", "value"),
    State("bandage-pathnodes", "value"),
    State("bandage-minpatcov", "value"),
    State("bandage-minhitcov", "value"),
    State("bandage-minmeanid", "value"),
    State("bandage-maxevprod", "value"),
    State("bandage-minpatlen", "value"),
    State("bandage-maxpatlen", "value"),
    State("bandage-minlendis", "value"),
    State("bandage-maxlendis", "value"),
    State("bandage-topn", "value"),
    State("metadata_table", "selectedRows"),
    prevent_initial_call=True
)
def run_sequence_alignment(n_clicks, fasta_content, read_type, context_steps, context_bp, session, project_name, method, blastp, ifilter, qcfilter, evfilter, alfilter, bsfilter, pathnodes, minpatcov, minhitcov, minmeanid, maxevprod, minpatlen, maxpatlen, minlendis, maxlendis, topn, selected_rows):
    is_valid, cleaned_fasta, error_message, seq_type = validate_fasta_input(fasta_content)
    if not is_valid:
        return {'display': 'block'}, dbc.Alert(error_message, color="danger"), [], None, None, None
    
    # 1. Setup Paths
    row = query_db("SELECT path FROM projects WHERE title = ?", (project_name,), one=True)
    project_path = row[0] if row else conf["session_dir"] + "/" + project_name
    input_gfa = os.path.join(project_path, "pangenome.gfa")
    
    # Process selected genomes
    path_list_arg = ""
    if selected_rows:
        selected_genomes = [row["Strain name"] for row in selected_rows if "Strain name" in row]
        if selected_genomes:
            path_list_arg = ",".join(selected_genomes)

    # Unique directory
    import time
    timestamp = int(time.time())
    output_dir = os.path.join(tmp_dir, f"{session}_align_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    # 2. Save Fasta
    fasta_path = os.path.join(output_dir, "input.fasta")
    with open(fasta_path, "w") as f:
        f.write(cleaned_fasta)
        
    # 3. Build Command
    if method == "bandage":
        cmd = [
            "bash", "extract_subgraph_bandage.sh",
            "-f", fasta_path,
            "-g", input_gfa,
            "-d", output_dir
        ]
        if path_list_arg:
            cmd.extend(["-p", path_list_arg])
        if blastp: cmd.extend(["--blastp", str(blastp)])
        if ifilter: cmd.extend(["--ifilter", str(ifilter)])
        if qcfilter: cmd.extend(["--qcfilter", str(qcfilter)])
        if evfilter: cmd.extend(["--evfilter", str(evfilter)])
        if alfilter: cmd.extend(["--alfilter", str(alfilter)])
        if bsfilter: cmd.extend(["--bsfilter", str(bsfilter)])
        if pathnodes: cmd.extend(["--pathnodes", str(int(pathnodes))])
        if minpatcov is not None: cmd.extend(["--minpatcov", str(minpatcov)])
        if minhitcov is not None: cmd.extend(["--minhitcov", str(minhitcov)])
        if minmeanid is not None: cmd.extend(["--minmeanid", str(minmeanid)])
        if maxevprod: cmd.extend(["--maxevprod", str(maxevprod)])
        if minpatlen is not None: cmd.extend(["--minpatlen", str(minpatlen)])
        if maxpatlen is not None: cmd.extend(["--maxpatlen", str(maxpatlen)])
        if minlendis is not None and str(minlendis).strip() != "": cmd.extend(["--minlendis", str(int(minlendis))])
        if maxlendis is not None and str(maxlendis).strip() != "": cmd.extend(["--maxlendis", str(int(maxlendis))])
        if topn: cmd.extend(["--topn", str(int(topn))])
        
    else:
        # Default Vg Giraffe
        cmd = [
            "bash", "extract_subgraph_sequences.sh",
            "-f", fasta_path,
            "-g", input_gfa,
            "-d", output_dir,
            "-r", read_type
        ]
        if path_list_arg:
            cmd.extend(["-p", path_list_arg])

    # Handle mutually exclusive context logic (BP takes precedence if provided)
    if context_bp is not None and str(context_bp).strip() != "":
        cmd.extend(["-L", str(context_bp)])
    elif context_steps is not None:
        cmd.extend(["-n", str(context_steps)])
    
    print(f"Running Alignment: {' '.join(cmd)}")
    
    # 4. Run Script
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Alignment Error: {e.stderr}")
        return {'display': 'block'}, dbc.Alert("Alignment failed. See server logs for details.", color="danger"), [], None, None, None

    # 5. Parse hits_metadata.json  (produced by both process_bandage_hits.py and process_gaf.py)
    manifest_path = os.path.join(output_dir, "hits_metadata.json")
    if not os.path.exists(manifest_path):
        print("No hits_metadata.json found.")
        return {'display': 'block'}, dbc.Alert("No hits found (hits_metadata.json missing).", color="warning"), [], None, None, None

    try:
        with open(manifest_path, 'r') as f:
            hits_dict = json.load(f)
    except Exception as e:
        print(f"JSON Error: {e}")
        return {'display': 'block'}, dbc.Alert("Failed to parse hits_metadata.json.", color="danger"), [], None, None, None

    if not hits_dict:
        return {'display': 'block'}, dbc.Alert("No hits found in the alignment.", color="warning"), [], None, None, None

    # Convert dict → list (both process_* scripts store dicts keyed by hit_name)
    hits_data = list(hits_dict.values())

    # 6. Populate Dropdown
    options = []
    for hit in hits_data:
        nodes = hit.get('nodes', [])
        nodes_str = ",".join(nodes) if isinstance(nodes, list) else str(nodes)
        nodes_display = nodes_str[:40] + "..." if len(nodes_str) > 40 else nodes_str
        method_tag = hit.get('method', '')
        label = f"[{method_tag}] {hit['id']} — {len(nodes) if isinstance(nodes, list) else '?'} nodes"
        options.append({'label': label, 'value': hit['id']})

    first_val = options[0]['value'] if options else None

    return {'display': 'block'}, "", options, first_val, hits_data, output_dir

# Callback 2: Visualize Selected Hit
@app.callback(
    Output("hit-visualization-area", "children"),
    Output("hit-metrics-area", "children"),
    Input("hit-selector", "value"),
    Input("hit-viz-type", "value"),
    State("store-alignment-hits", "data"),
    State("store-alignment-path", "data"),
    prevent_initial_call=True
)
def display_selected_hit(hit_id, viz_type, hits_data, output_dir):
    if not hit_id or not hits_data or not output_dir:
        return html.Div("No hit selected."), ""
    
    # Find hit data
    selected_hit = next((h for h in hits_data if h['id'] == hit_id), None)
    if not selected_hit:
        return html.Div("Hit not found."), ""
    
    # Metrics panel — content depends on alignment method
    method = selected_hit.get('method', 'bandage')

    if method == 'vg_giraffe':
        metrics_div = html.Div([
            html.H6([
                f"Hit: {selected_hit.get('query', hit_id)}",
                dbc.Badge("vg giraffe", color="primary", className="ms-2")
            ]),
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardBody([
                    html.H6("Query length", className="card-subtitle"),
                    html.H4(selected_hit.get('query_length', 'N/A'), className="card-title")
                ])], color="light", outline=True), width=2),
                dbc.Col(dbc.Card([dbc.CardBody([
                    html.H6("Aligned region", className="card-subtitle"),
                    html.H4(f"{selected_hit.get('query_start', '?')} – {selected_hit.get('query_end', '?')}", className="card-title")
                ])], color="light", outline=True), width=3),
                dbc.Col(dbc.Card([dbc.CardBody([
                    html.H6("Strand", className="card-subtitle"),
                    html.H4(selected_hit.get('strand', 'N/A'), className="card-title")
                ])], color="light", outline=True), width=1),
                dbc.Col(dbc.Card([dbc.CardBody([
                    html.H6("Residue matches", className="card-subtitle"),
                    html.H4(selected_hit.get('residue_matches', 'N/A'), className="card-title")
                ])], color="light", outline=True), width=2),
                dbc.Col(dbc.Card([dbc.CardBody([
                    html.H6("Mapping quality", className="card-subtitle"),
                    html.H4(selected_hit.get('mapping_quality', 'N/A'), className="card-title")
                ])], color="light", outline=True), width=2),
                dbc.Col(dbc.Card([dbc.CardBody([
                    html.H6("Align score / Div", className="card-subtitle"),
                    html.H4(f"{selected_hit.get('alignment_score', 'N/A')} / {selected_hit.get('divergence', 'N/A')}", className="card-title")
                ])], color="light", outline=True), width=2),
            ], className="mb-2"),
            html.Label("Path (GAF):"),
            dcc.Textarea(
                value=selected_hit.get('path_string', ''),
                style={'width': '100%', 'height': 60},
                readOnly=True,
            ),
        ])
    else:  # bandage
        metrics_div = html.Div([
            html.H6([
                f"Hit: {selected_hit.get('query', hit_id)}",
                dbc.Badge("Bandage", color="success", className="ms-2")
            ]),
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardBody([
                    html.H6("Identity", className="card-subtitle"),
                    html.H4(selected_hit.get('identity', 'N/A'), className="card-title")
                ])], color="light", outline=True), width=3),
                dbc.Col(dbc.Card([dbc.CardBody([
                    html.H6("Query Cov", className="card-subtitle"),
                    html.H4(selected_hit.get('coverage_query', 'N/A'), className="card-title")
                ])], color="light", outline=True), width=3),
                dbc.Col(dbc.Card([dbc.CardBody([
                    html.H6("E-value", className="card-subtitle"),
                    html.H4(selected_hit.get('e_value_product', 'N/A'), className="card-title")
                ])], color="light", outline=True), width=3),
                dbc.Col(dbc.Card([dbc.CardBody([
                    html.H6("Length discrepancy", className="card-subtitle"),
                    html.H4(selected_hit.get('length_discrepancy', 'N/A'), className="card-title")
                ])], color="light", outline=True), width=3),
            ], className="mb-2"),
            html.Label("Hit Sequence:"),
            dcc.Textarea(
                value=selected_hit.get('sequence', ''),
                style={'width': '100%', 'height': 100},
                readOnly=True,
                title="Copy this sequence"
            ),
        ])

    image_filename = ""
    mime_type = ""
    
    if viz_type == 'odgi':
        image_filename = selected_hit.get('odgi_image')
        mime_type = "data:image/png;base64"
    elif viz_type == 'bandage':
        image_filename = selected_hit.get('bandage_image')
        mime_type = "data:image/svg+xml;base64"
        
    full_path = os.path.join(output_dir, image_filename)
    
    if os.path.exists(full_path):
        encoded_image = base64.b64encode(open(full_path, 'rb').read()).decode('ascii')
        source_url = f"{mime_type},{encoded_image}"
        
        # Helper to get dims (reuse the function defined in previous step)
        img_w, img_h = get_image_dimensions(full_path)
        
        fig = go.Figure()
        fig.add_layout_image(
            dict(
                source=source_url,
                xref="x", yref="y",
                x=0, y=0,
                sizex=img_w, sizey=img_h,
                sizing="contain",
                layer="below"
            )
        )
        fig.update_xaxes(visible=False, range=[0, img_w])
        fig.update_yaxes(visible=False, range=[img_h, 0], scaleanchor="x")
        fig.update_layout(
            width=1200, height=800,
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
            dragmode="pan",
            plot_bgcolor="white"
        )
        
        return dcc.Graph(
            figure=fig,
            config={'scrollZoom': True, 'displayModeBar': True},
            style={"width": "100%", "height": "80vh"}
        ), metrics_div
    
    return dbc.Alert(f"Image file {image_filename} not found.", color="danger"), metrics_div

@app.callback(
    Output('PCA', 'figure', allow_duplicate=True),
    Input('dimension_pca', 'value'),
    Input('colorizing_pca', 'value'),
    State('current_session', 'value'),
    prevent_initial_call=True    
)

def pca(dimension_pca,colorizing_pca,session):

    if os.path.exists(f"{tmp_dir}/{session}.metadata.txt"):
        df_pca_metadata = pd.read_csv(f"{tmp_dir}/{session}.metadata.txt")
        if dimension_pca=="3D":
            if colorizing_pca=="Country" or colorizing_pca=="Continent" or colorizing_pca=="Organism":
                fig_scatter = px.scatter_3d(df_pca_metadata, x='PC1', y='PC2', z='PC3', color=colorizing_pca, hover_name="Individual", hover_data=["Assigned_to_pop"])
            else:
                fig_scatter = px.scatter_3d(df_pca_metadata, x='PC1', y='PC2', z='PC3', color='Assigned_to_pop', hover_name="Individual", hover_data=["Assigned_to_pop"])
        else:
            if colorizing_pca=="Country" or colorizing_pca=="Continent" or colorizing_pca=="Organism":
                fig_scatter = px.scatter(df_pca_metadata, x='PC1', y='PC2', color=colorizing_pca, hover_name="Individual", hover_data=["Assigned_to_pop"])
            else:
                fig_scatter = px.scatter(df_pca_metadata, x='PC1', y='PC2', color='Assigned_to_pop', hover_name="Individual", hover_data=["Assigned_to_pop"])
    else:
        fig_scatter = px.scatter(pd.DataFrame({'PC1':[], 'PC2':[], 'PC3':[]}), x='PC1', y='PC2')
        fig_scatter.update_layout(title="No PCA data found.")
    return fig_scatter


@app.callback(
    Output('PAV_graph', 'figure', allow_duplicate=True),
    State('projets', 'value'),
    State('current_session', 'value'),
    State('specific_to', 'value'),
    Input('ordering', 'value'),
    Input('sample_ordering', 'value'),
    State('metadata_table','selectedRows'),
    State('reference','value'),
    Input('highlight', 'value'),
    State('cluster_search', 'value'),
    State('bedfile', 'value'),
    Input('colorizing', 'value'),
    Input('highlight_button', 'n_clicks'),
    prevent_initial_call=True    
)
def heatmap_PAV(proj_title,session,specific_to,ordering,sample_ordering,metadata_table,reference,highlight,cluster_search,bedfile,colorizing,highlight_button):
    if not proj_title:
        return "No project."
    row = query_db("SELECT path FROM projects WHERE title = ?", (proj_title,), one=True)
    path = ""
    if not row:
        path = conf["session_dir"] + "/" + proj_title
    else:
        path = row[0]
    directory = path

    if is_stringlist_without_special_character(cluster_search) == False:
        cluster_search = ""

    if is_bed(bedfile) == False:
        bedfile = ""

    list_sp2 = []
    if metadata_table:
        wjdata = json.loads(json.dumps(metadata_table, indent=2))
        for strain in wjdata:
            strain_name = strain['Strain name']
            list_sp2.append(strain_name)

    cluster_names=[]
    scoary_output_file = tmp_dir + "/" + str(session) + ".scoary_results.txt"
    df_matrix = pd.read_csv(tmp_dir + "/" + str(session) + ".df_matrix.csv")
    df_metadata3 = pd.read_csv(tmp_dir + "/" + str(session) + ".df_metadata3.csv")
    merged_with_cog = pd.read_csv(tmp_dir + "/" + str(session) + ".merged_with_cog.csv")
    df = pd.read_csv(tmp_dir + "/" + str(session) + ".df.csv")
    merged_with_positions2 = pd.read_csv(tmp_dir + "/" + str(session) + ".merged_with_positions2.csv")
    transposed_df = pd.DataFrame()
    df2 = pd.read_csv(tmp_dir + "/" + str(session) + ".df2.csv")
    cluster_names = df2["ClutserID"].astype(str).tolist()

    search_res2 = []
    ticktext = ['Absence']
    tickval = ['0']
    colorscale = []
    zmax = 1
    if highlight != "None" or cluster_search != "" or bedfile != "" or (specific_to is not None and len(specific_to) > 0):
       colorscale = [[0, 'whitesmoke'], [0.67, 'teal'], [1, 'red']]
    else:
        colorscale = [[0, 'whitesmoke'],[0.5, 'whitesmoke'], [0.5, 'teal'], [1, 'teal']]
        ticktext.append("Presence")
        tickval.append(1)
    
    if colorizing == "Level of presence":
        colorscale = [[0, 'whitesmoke'], [1, 'teal']]
        for sample in list_sp2:
            proportion = df2["sum"] / len(list_sp2)
            df2[sample] = np.where( (df2[sample] == 1),proportion,df2[sample])

    elif colorizing == "Organism" or colorizing == "Continent" or colorizing == "Country":
        colorscale = []
        df_metadata4 = df_metadata3[df_metadata3['Strain name'].isin(list_sp2)]
        list_organisms = df_metadata4[colorizing].unique().tolist()
        nb_organisms = len(list_organisms)
        step = 1 / (nb_organisms+1)
        colorscale.append([0.0, "whitesmoke"])
        colorscale.append([step, "whitesmoke"])
        count = 0
        color_level = 0
        association = {}
        s = 0
        for organism in list_organisms:
            count+=0.1
            ticktext.append(organism)
            tickval.append(count)
            s+=step
            color = colors[color_level]
            colorscale.append([s, color])
            colorscale.append([s+step, color])
            color_level += 1
            association[organism] = count
        zmax = count

        ordered_list_organisms = df_metadata4[colorizing].tolist()
        ordered_list_strains = df_metadata4["Strain name"].tolist()
        
        count = 0
        for sample in ordered_list_strains:
            organism = ordered_list_organisms[count]
            count+=1
            val = association[organism]
            df2[sample] = np.where( (df2[sample] == 1),val,df2[sample])
            
            
            
    elif highlight == "Reference genome":
        colorscale = [[0, 'whitesmoke'],[0.5, 'whitesmoke'], [0.5, 'teal'], [0.75, 'teal'], [0.75, 'red'], [1, 'red']]
        ticktext.append("Presence")
        tickval.append(0.67)
        #ticktext.append("Highlight")
        #tickval.append(0.75)
        for sample in list_sp2:
            proportion = df2["sum"] / len(list_sp2)
            if sample == reference:
                df2[sample] = np.where( (df2[sample] == 1),1,df2[sample])
            else:
                df2[sample] = np.where( (df2[sample] == 1),0.67,df2[sample])
    elif highlight == "Core-genes":
        colorscale = [[0, 'whitesmoke'],[0.5, 'whitesmoke'], [0.5, 'teal'], [0.75, 'teal'], [0.75, 'red'], [1, 'red']]
        ticktext.append("Presence")
        tickval.append(0.67)
        for sample in list_sp2:
            proportion = df2["sum"] / len(list_sp2)
            df2[sample] = np.where( (df2[sample] == 1) & (proportion != 1),0.67,df2[sample])
    elif highlight == "Strain-specific genes":
        colorscale = [[0, 'whitesmoke'],[0.5, 'whitesmoke'], [0.5, 'teal'], [0.75, 'teal'], [0.75, 'red'], [1, 'red']]
        ticktext.append("Presence")
        tickval.append(0.67)
        for sample in list_sp2:
            proportion = df2["sum"] / len(list_sp2)
            df2[sample] = np.where( (df2[sample] == 1) & (df2["sum"] > 1),0.67,df2[sample])
            
    ##############################################
    # get clusters specific to a subset of samples
    ##############################################
    elif specific_to is not None and len(specific_to) > 0:
        colorscale = [[0, 'whitesmoke'],[0.5, 'whitesmoke'], [0.5, 'teal'], [0.75, 'teal'], [0.75, 'red'], [1, 'red']]
        ticktext.append("Presence")
        tickval.append(0.67)
        list_of_clusters = [1000]
        
        # 1) get clusters for which gene is present for these samples
        if "ClutserID" not in specific_to:
            specific_to.append("ClutserID")
        df_specific_to = df[specific_to]
        df_specific_to['sum'] = df_specific_to.drop('ClutserID', axis=1).sum(axis=1)
        # get only if at least one gene is present
        df_specific_to = df_specific_to[df_specific_to["sum"] == len(specific_to)-1]
        # remove CLUSTER tag (TODO: to be removed)

        #df_specific_to['ClutserID'] = df_specific_to['ClutserID'].str.replace('CLUSTER000','')
        #df_specific_to['ClutserID'] = df_specific_to['ClutserID'].str.replace('CLUSTER00','')
        #df_specific_to['ClutserID'] = df_specific_to['ClutserID'].str.replace('CLUSTER0','')
        #df_specific_to['ClutserID'] = df_specific_to['ClutserID'].str.replace('CLUSTER','')
        df_specific_to.to_csv("df_specific_to.csv")
        list1 = df_specific_to['ClutserID'].tolist()
        #list1bis = [eval(i) for i in list1]
        
        
        # 2) get clusters for which the number of presence correspond to the number of selected samples
        same_number_df = merged_with_cog[merged_with_cog["sum"] == len(specific_to)-1]
        same_number_df.to_csv("df_specific_to2.csv")
        list2 = same_number_df['ClutserID'].tolist()
        
        # 3) get overlapping clusters between the two dataframes
        intersected_list = [value for value in list1 if value in list2]
        print(intersected_list)
        print("Nb specific genes:")
        print(specific_to)
        print(len(intersected_list))

        
        
        df_search = pd.DataFrame(intersected_list, columns=['ClutserID'])
        search_res2 = df_search.to_dict('records')
        #df_specific_final2.to_csv("df_specific_to.csv")
        
        list_of_clusters = intersected_list

        df_search = pd.DataFrame(list_of_clusters, columns=['ClutserID'])

        


        search_res2 = df_search.to_dict('records')
        
        for sample in list_sp2:
            df2[sample] =  np.where( (df2[sample] == 1) & (df2["ClutserID"].isin(list_of_clusters)==False),0.67,df2[sample])
            
        print(len(search_res2))
        print("specific to: "+str(specific_to))
    elif cluster_search != "":
        
        #cmd = "grep -P '"+cluster_search+"' "+directory+"/1.Orthologs_Cluster.txt | awk {'print $1'}"
        #returned_value = os.popen(cmd).read()
        #cluster_search = returned_value
        #df_search = pd.DataFrame([int(returned_value)], columns=['ClutserID'])
        #search_res2 = df_search.to_dict('records')
        
        colorscale = [[0, 'whitesmoke'],[0.5, 'whitesmoke'], [0.5, 'teal'], [0.75, 'teal'], [0.75, 'red'], [1, 'red']]
        ticktext.append("Presence")
        tickval.append(0.67)

        #COG1192
        print(str(session))
        list_of_clusters = []
        list_of_COGs = cluster_search.split(",")
        for cog in list_of_COGs:
            cog = re.sub(r'[^a-zA-Z0-9]', '', cog)
            cmd = "grep -P '"+cog+"' "+directory+"/cog_of_clusters.txt | awk {'print $1'}"
            cmd = "grep -i -P '"+ cog + "' "+tmp_dir+"/"+str(session)+".merged_with_cog_final.csv | awk -F '\t' {'print $3'}"
            print(cmd)
            returned_value = os.popen(cmd).read()
            print("returned_value: " + returned_value)
            list_of_clusters1 = returned_value.split("\n")
            list_of_clusters.extend(list_of_clusters1)


        
        # remove empty values
        list_of_clusters = list(filter(None, list_of_clusters))
        list_of_clusters = list(map(int, list_of_clusters))
        
        df_search = pd.DataFrame(list_of_clusters, columns=['ClutserID'])
        search_res2 = df_search.to_dict('records')

        

        
        for sample in list_sp2:
            df2[sample] =  np.where( (df2[sample] == 1) & (df2["ClutserID"].isin(list_of_clusters)==False),0.67,df2[sample])

    

    if bedfile is not None and bedfile != "":

        print("analysis of bedfile")
        lines_of_bedfile = bedfile.split("\n")

        df_search = pd.DataFrame(merged_with_positions2, columns=['name','Product','start','end'])
        df_search['start'] = df_search['start'].astype(int)
        df_search['end'] = df_search['end'].astype(int)

        list_of_clusters = []
        for line in lines_of_bedfile:
            elements_of_line = line.split("\t")
            start = int(elements_of_line[1])
            end = int(elements_of_line[2])
            df_subset = df_search.loc[(df_search['start']>=start) & (df_search['end']< end)]
            df_subset.rename(columns={'name': 'ClutserID'}, inplace=True)
            list_of_clusters1 = df_subset['ClutserID'].tolist()
            list_of_clusters.extend(list_of_clusters1)

        df_search = pd.DataFrame(list_of_clusters, columns=['ClutserID'])
        search_res2 = df_search.to_dict('records')

        for sample in list_sp2:
            df2[sample] =  np.where( (df2[sample] == 1) & (df2["ClutserID"].isin(list_of_clusters)==False),0.67,df2[sample])


    if sample_ordering == "Hierarchical clustering":
        order_samples = pd.read_csv(directory+"/1.Orthologs_Cluster.txt", nrows=0, sep="\t").columns.tolist()
        order_samples.remove("ClutserID")
        list_sp2_sorted = [sample for sample in order_samples if sample in list_sp2]
        list_sp2 = list_sp2_sorted
    elif sample_ordering == "Population as defined by sNMF":
        order_samples = pd.read_csv(tmp_dir+"/" + str(session) + ".metadata.txt", sep=",")
        individual_order_by_Pop1 = order_samples.sort_values(by=['Assigned_to_pop'])['Strain name'].tolist()
        list_sp2_sorted = [sample for sample in individual_order_by_Pop1 if sample in list_sp2]
        list_sp2 = list_sp2_sorted


    list_chromosomes = []
    merged_with_positions3 = []
    if ordering == "Hierarchical clustering":
        
        # remove sum and clutserID from the col
        df2 = df2[list_sp2]
        transposed_df = df2.transpose() 
        
        
    else:
        # to be modified for ordering clusters along pivot genome
        merged_with_positions2 = merged_with_positions2[['start','name','block_id']]
        merged_with_positions2['start'] = merged_with_positions2['start'].astype(int)
        df2['ClutserID'] = df2['ClutserID'].astype(int)
        merged_with_positions3 = pd.merge(df2, merged_with_positions2, left_on='ClutserID', right_on='name')
        merged_with_positions3 = merged_with_positions3.sort_values(by=['block_id','start'],ascending=True)
        merged_with_positions3.to_csv("export.tsv")
        merged_with_positions3["col_concat"] = merged_with_positions3["block_id"].astype(str) + ":" + merged_with_positions3["start"].astype(str) + ":" + merged_with_positions3["ClutserID"].astype(str)
        cluster_names = merged_with_positions3["col_concat"].astype(str).tolist()
        list_chromosomes = merged_with_positions3["block_id"].tolist()
        merged_with_positions4 = merged_with_positions3[list_sp2]

        transposed_df = merged_with_positions4.transpose()
    
    y_labels = []
    x_labels = []
    z = []
    for row in transposed_df.itertuples():
        y_labels.append(row[0])
        z.append(list(row[1:]))

    # colorscale = [
    #     [0.00, "whitesmoke"], [0.25, "whitesmoke"],
    #     [0.25, "yellow"], [0.50, "yellow"],
    #     [0.50, "green"], [0.75, "green"],
    #     [0.75, "red"], [1.00, "red"],
    # ]
    print("color scale:")
    print(colorscale)

    if specific_to is not None and len(specific_to) > 0 and os.path.exists(scoary_output_file):

        df_scoary_results = pd.read_csv(scoary_output_file)
        df_scoary_results["log_pval"] = -np.log10(df_scoary_results["Naive_p"])
        merged_with_positions_scoary = pd.merge(df_scoary_results, df_matrix, left_on='Gene', right_on='ClutserID', how='right')
        if ordering != "Hierarchical clustering":
            merged_with_positions_scoary = pd.merge(df_scoary_results, merged_with_positions3, left_on='Gene', right_on='ClutserID', how='right')
        

        pvalues_list = merged_with_positions_scoary['log_pval'].tolist()
        


        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            row_heights=[0.5, 0.5], 
            vertical_spacing=0.05
        )
        # Heatmap
        fig.add_trace(
            go.Heatmap(
                z=z,
                x=cluster_names,
                y=list_sp2,
                zmin=0,
                zmax=zmax,
                colorscale=colorscale,  # ou autre
                colorbar=dict(
                        tickvals=tickval,
                        ticktext= ticktext,
                        y=0.75,
                        len=0.5
                    ),
                showscale=True
            ),
            row=1,
            col=1
        )
        # Scatter
        fig.add_trace(
            go.Scatter(
                x=cluster_names,
                y=pvalues_list,
                mode="markers",
                #hover_data=["Gene","log_pval"],
                marker=dict(size=5, color='MediumPurple')
            ),
            row=2,
            col=1
        )
        fig.update_yaxes(title_text="-log10(pvalues)", row=2, col=1)
        fig.update_yaxes(autorange="reversed", row=1, col=1,tickmode="linear")
        fig.update_layout(height=1100)
        fig.update_layout(title_text='Presence/Absence Variation (PAV) matrix of genes across selected genomes. Pan-GWAS results are shown below the PAV matrix.')
    else:
        print(colorscale)
        fig = go.FigureWidget(data=
                              go.Heatmap(
                                    z=z,
                                    x=cluster_names,
                                    y=list_sp2,
                                    zmin=0,
                                    zmax=zmax,
                                    colorscale=colorscale,  # ou autre
                                    colorbar=dict(
                                            tickvals=tickval,
                                            ticktext= ticktext
                                        ),
                                    showscale=True
                                )
        )
                            
        fig.update_layout(title_text='Presence/Absence Variation (PAV) matrix of genes across selected genomes',xaxis_title="Gene clusters",yaxis_title="Samples")
        fig.update_yaxes(autorange="reversed",tickmode="linear")


    # fig = go.Figure(
    #     go.Heatmap(
    #         z=z,
    #         x=cluster_names,
    #         y=list_sp2,
    #         zmin=0,
    #         zmax=0.3,
    #         colorscale=colorscale,  # ou autre
    #         colorbar=dict(
    #                 tickvals=tickval,
    #                 ticktext= ticktext
    #             ),
    #         showscale=True
    #     )
    # )

    fig.update_layout(
        xaxis_title="Gene clusters",
        yaxis_title="Samples",
        height=1100
    )

    

    return fig


@app.callback(
    Output('iframe-snptree', 'src', allow_duplicate=True),
    Input('colorizing_tree', 'value'),
    State('current_session', 'value'),
    prevent_initial_call=True    
)

def tree(colorizing_tree,session):
    
    with open(tmp_dir + "/" + str(session) + ".dataset.tree") as fp:
        snp_based_newick = fp.read()
        
        list_selected = pd.read_csv(tmp_dir + "/" + str(session) + ".selected_genomes.txt", header=None)[0].tolist()
        df_metadata = pd.read_csv(tmp_dir + "/" + str(session) + ".metadata.txt")
        print(list_selected)
        df_metadata_selected = df_metadata[df_metadata['Strain name'].isin(list_selected)] 
        df_metadata_selected.to_csv("metadata_selected.csv",sep=',')
        generate_tree_html(snp_based_newick, df_metadata_selected, colorizing_tree, "assets/snp_based_tree."+str(session)+"." + colorizing_tree+".html")

    return "assets/snp_based_tree."+str(session)+"." + colorizing_tree+".html"



@app.callback(
        #Output('graph_enrichment', 'figure'),
        Output('enrichment_table', 'rowData'),
        Output('enrichment_table', 'style'),
        Input('submit-enrichment', 'n_clicks'),
        State('metadata_table','selectedRows'),
        State('projets', 'value'),
        State('current_session', 'value'),
        prevent_initial_call=True    
)

def enrichment(submit_enrichment,metadata_table,proj_title,session):

    if not proj_title:
        return "No project."
    row = query_db("SELECT path FROM projects WHERE title = ?", (proj_title,), one=True)
    path = ""
    if not row:
        path = conf["session_dir"] + "/" + proj_title
    else:
        path = row[0]
    directory = path

    # get core genes 
    df_core = pd.read_csv(tmp_dir + "/" + str(session) + ".core.txt",sep="\t")
    df_core_clusters = df_core["name"]
    core_clusters_file = tmp_dir + "/" + str(session) + ".core_clusters.txt"
    df_core_clusters.to_csv(core_clusters_file,sep='\t',index=False)

    # get COG of clusters
    annotation_file = tmp_dir + "/" + str(session) + ".annotations.txt"
    cmd_args = ["cut", "-d", "\t", "-f", "1,2", directory + "/cog_of_clusters.txt"]
    with open(annotation_file, "w") as file:
        subprocess.run(cmd_args, stdout=file, stderr=subprocess.STDOUT, check=True)

    df_merged_with_cog = pd.read_csv(tmp_dir + "/" + str(session) + ".export_merged_with_cog.csv")



    df_cog_of_clusters = pd.read_csv(tmp_dir + "/" + str(session) + ".annotations.txt", sep="\t")
    # TODO: filter les annotations que celles qui sont dans notre selection
    df_cog_of_clusters.columns = ['orthogroup', 'terms']
    df_cog_of_clusters.to_csv(annotation_file,sep='\t',index=False)

    # calculate enrichment (odds ratios and pvalues)
    cmd_args = ["python", "enrichment.py", "--subsetA",core_clusters_file, "--annotations", annotation_file, "--out", tmp_dir + "/" + str(session) + ".enrichment.txt"]
    with open(f"{tmp_dir}/{session}.enrichment.log", "a") as log_file:
        subprocess.run(cmd_args, stdout=log_file, stderr=subprocess.STDOUT, check=True)

    df_enrichment = pd.read_csv(tmp_dir + "/" + str(session) + ".enrichment.txt", sep="\t")
    df_enrichment["-log10_pvalue"] = -np.log10(df_enrichment["p_value"])
    df_enrichment_bis = df_enrichment[df_enrichment['-log10_pvalue'] > 2]
    df_cog_terms = pd.read_csv('COG_terms.txt',sep='\t')
    df_enrichment_with_cog_term = pd.merge(df_enrichment_bis, df_cog_terms, how="right", left_on='term', right_on='COG')

    #df_enrichment["log2_odds_ratios"] = np.log2(df_enrichment["odds_ratio"])

    dictionary = df_enrichment_with_cog_term.to_dict('records')


    #graph_enrichment = px.scatter(df_enrichment_bis, x="odds_ratio", y="-log10_pvalue", text="term", title="Enrichment of COG terms in core genes compared to the pangenome")
    #graph_enrichment = px.bar(df_enrichment, x="term", y="-log10_pvalue", color="odds_ratio", title="Enrichment of COG terms in core genes compared to the pangenome")

    
    return dictionary, {'display': 'block'}


@app.callback(
        Output('dynamic_network','children'),
        Output('graph_mlva', 'figure'),
        Input('submit-vntr', 'n_clicks'),
        State('mlva_table','selectedRows'),
        State('metadata_table','selectedRows'),
        State('projets', 'value'),
        prevent_initial_call=True
        
)

def update_MLVA(submit_vntr,mlva_table,metadata_table,proj_title):

    ###########################################################
    # MLVA
    ###########################################################
    if not proj_title:
        return "No project."
    row = query_db("SELECT path FROM projects WHERE title = ?", (proj_title,), one=True)
    path = ""
    if not row:
        path = conf["session_dir"] + "/" + proj_title
    else:
        path = row[0]
    directory = path


    list_selected = ['ID','Repeat','Flanking']
    #if submit_samples:
    if metadata_table:
        wjdata = json.loads(json.dumps(metadata_table, indent=2))
        val = wjdata
        for strain in wjdata:
            strain_name = strain['Strain name']
            list_selected.append(strain_name)
                
    #else:
    #    for value in df_metadata2['Strain name']:
    #        list_selected.append(value)


    session = random.randint(1, 9000000)
    vntr_file = directory+'/vntr_matrix.tsv'

    #print("submit vntr button" + str(submit_vntr) + " "+str(session))

    df_vntr = pd.DataFrame(columns=['ID'])
    if os.path.exists(vntr_file):

        # remove lines/markers with missing data
        vntr_file_nomissing = directory+'/vntr_matrix.nomissing.tsv'
        cmd_args = ["grep", "-v", "'-'", vntr_file]
        with open(vntr_file_nomissing, "w") as file:
            subprocess.run(cmd_args, stdout=file, stderr=subprocess.STDOUT, check=True)

        df_vntr = pd.read_csv(vntr_file_nomissing,sep='\t')
        df_vntr_filtered = df_vntr[list_selected]
        print(df_vntr_filtered.columns)
        df_vntr = df_vntr_filtered


    repeat_names = df_vntr["ID"].astype(str).tolist()
    print("Filtered vntr")
    print(list_selected)
    

    repeats = []
    if mlva_table:
        wjdata1 = json.loads(json.dumps(mlva_table, indent=2))
        for vntr in wjdata1:
            #print(vntr)
            vntr_name = vntr['ID']
            repeats.append(vntr_name) 

    
    #print(repeats)
    mask = df_vntr['ID'].isin(repeats)
    testdf = df_vntr[mask]
    newdf = testdf.drop(["ID","Repeat","Flanking"], axis='columns')
    graph_mlva = px.imshow(newdf.T, 
                           aspect="auto",
                           labels=dict(y="Samples", x="VNTR loci", color="Number of repeats"),
                           x=repeats,
                           #y=list_sp2,
                           text_auto=True
                           )
    mlva_table = df_vntr.to_dict('records')
    newdf.T.to_csv(directory+ "/export_mlva.tsv",sep='\t')

    
    transposed_newdf = newdf.transpose()

    

    # concatenate numbers of repeats as an haplotype value for each sample
    transposed_newdf['haplotype'] = transposed_newdf.astype(str).agg('_'.join, axis=1)

    # assign metadata to haplotype
    df_metadata_tmp = pd.read_csv(directory+'/metadata.tmp.xls',sep='\t')
    dict_metadata = df_metadata_tmp.set_index('Strain name')['Country'].to_dict()
    dict_haplo = {}
    dict_element_for_colorizing = {}
    for strain, row in transposed_newdf.iterrows():
        country = dict_metadata[strain]
        dict_element_for_colorizing[country]=1
        if row.haplotype in dict_haplo.keys():
            dict_haplo[row.haplotype] = dict_haplo[row.haplotype] + "," + str(country)
        else:
            dict_haplo[row.haplotype] = str(country)

    transposed_newdf.to_csv(tmp_dir+"/"+str(session)+".strain_haplotypes.txt")

    #dictionary_haplotype_of_strain = transposed_newdf.set_index('strains')['haplotype'].to_dict()

    


    # put frequency of haplotypes into a dictionnary 
    dico_freq = transposed_newdf['haplotype'].value_counts().to_dict()
    haplotype_freq_df = pd.DataFrame([dico_freq]).transpose()
    haplotype_freq_df.to_csv(tmp_dir+"/"+str(session)+".haplotype_frequency.txt")


    with open(tmp_dir+"/"+str(session)+".haplotypes.txt", 'a') as f, open("assets/network."+str(session)+".1.json", 'a') as j:
        for i in range(len(newdf)):
            f.write(","+str(i))
        
        j.write("{\n")
        j.write("  \"nodes\": [\n")
        f.write("\n")
        i = 0
        concat = ""
        for row in haplotype_freq_df.itertuples():
            i+=1
            haplotype = row[0]
            size = row[1]
            country = dict_haplo[haplotype]
            list_countries = dict_haplo[haplotype].split(",")
            concat = concat + "{\"id\": \"haplo" + str(i)+"\",\"size\":"+str(10 * size)+","
            color_nb = 0
            concat = concat + "\"pieChart\" : ["
            subconcat = ""
            for country in dict_element_for_colorizing.keys():
                nb_occurence = list_countries.count(country)
                percentage = (nb_occurence / size) * 100
                if nb_occurence > 0:
                    subconcat = subconcat + "{ \"color\": \"" + colors[color_nb] + "\", \"percent\": " + str(percentage) + " },"

                color_nb += 1
            subconcat = subconcat[:len(subconcat)-1]

            concat = concat + subconcat + "]},\n"
            f.write("haplo"+str(i)+","+row[0].replace("_", ",")+"\n")
        
        concat = concat[:len(concat)-2]
        j.write(concat+"\n")
        j.write("],\n")

    # run haplotype network
    cmd_args = ["python", "haplotype_network.py", "-i", tmp_dir+"/"+str(session)+".haplotypes.txt", "-o", tmp_dir+"/"+str(session)]
    with open(tmp_dir+"/haplotype_network.log", "a") as log_file:
        subprocess.run(cmd_args, stdout=log_file, stderr=subprocess.STDOUT, check=True)

    with open("assets/network."+str(session)+".2.json", 'a') as j, open(tmp_dir+"/"+str(session)+".haplotype_network.csv",'r') as n:
        j.write("  \"links\": [\n")

        lines = n.readlines()[1:]
        concat = ""
        for line in lines:
            informations = line.split(',')
            concat = concat + "{\"source\": \""+informations[0]+"\", \"target\": \""+ informations[1] +"\", \"value\": "+ informations[2] +"},\n"

        concat = concat[:len(concat)-2]
        j.write(concat+"\n")
        j.write("]\n")
        j.write("}\n")

    cmd_args = ["cat", "assets/network."+str(session)+".1.json", "assets/network."+str(session)+".2.json"]
    with open("assets/network."+str(session)+".json", "a") as json_file:
        subprocess.run(cmd_args, stdout=json_file, stderr=subprocess.STDOUT, check=True)

    # add the prefix haplo to indexes
    cmd_args = ["sed", "s/SESSION/" + str(session) + "/g", "html_templates/network_template.html"]
    with open("assets/network."+str(session)+".html", "w") as html_file:
        subprocess.run(cmd_args, stdout=html_file, stderr=subprocess.STDOUT, check=True)

    dynamic_network = html.Iframe(src="assets/network."+str(session)+".html",style={"height": "1000px", "width": "100%"}),

    return dynamic_network, graph_mlva




def init_dataframes(pathname):
    
    #directory = get_directory(pathname)
    directory = pathname

    #https://panexplorer.southgreen.fr/tmp/86740638254871261615/1.Orthologs_Cluster.txt
    myfile = directory+'/1.Orthologs_Cluster.txt'
    print(myfile)
    
    df_matrix = pd.read_csv(myfile, sep='\t')
    #df_matrix = pd.read_csv("https://panexplorer.southgreen.fr/tmp/86740638254871261615/1.Orthologs_Cluster.txt")
    #df_matrix = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/solar.csv")
    
    print("yeahhhh: "+str(df_matrix.size))

    df_matrix = df_matrix.replace(to_replace=':', value='_', regex=True)
    df_matrix_modified = df_matrix.replace(to_replace ='[\w\.,:]+', value = 1, regex = True)
    df = df_matrix_modified.replace(to_replace ='-', value = 0, regex = True)

    #df['ClutserID'].replace(to_replace ='\d', value ='CLUSTER',regex = True,inplace=True)
    df.to_csv(directory+"/1.Orthologs_Cluster.2.txt",sep='\t',index=False)
    

    df_ANI = pd.DataFrame()  
    if os.path.exists(directory + "/fastani.out.matrix.complete.xls") and os.path.getsize(directory + "/fastani.out.matrix.complete.xls") > 0:
        df_ANI = pd.read_csv(directory+'/fastani.out.matrix.complete.xls',sep='\t')

    list_species = []
    for col in df.columns:
        if col != "ClutserID":
            list_species.append(col)


    df_metadata = pd.read_csv(directory+'/metadata.xls',sep='\t')
    df_metadata.loc[len(df_metadata.index)] = ['ClutserID', 'none','none','none'] 
    df_metadata3 = df_metadata[(df_metadata["Continent"] != "none")]
    list_continent = ["all"] + df_metadata3["Continent"].unique().tolist()
    list_organisms = ["all"] + df_metadata3["Organism"].unique().tolist()

  
    # Remove lines from ptt
    df_gene_positons = pd.DataFrame(columns=['block_id','Location','Strand','PID','Gene','Synonym','Code','COG','Product'])
    if os.path.exists(directory+"/genomes/genomes/"+list_species[0]+".ptt"):

        cmd_args = ["grep", "-P", "Location|^\d+\.\.", directory+"/genomes/genomes/"+list_species[0]+".ptt"]
        with open(directory+"/genomes/genomes/"+list_species[0]+".2.ptt", "w") as file:
            subprocess.run(cmd_args, stdout=file, stderr=subprocess.STDOUT, check=True)
        
        print("Species:"+list_species[0])

        df_gene_positons = pd.read_csv(directory+'/genomes/genomes/'+list_species[0]+'.2.ptt',sep='\t')
        df_gene_positons["PID"] = df_gene_positons["PID"].str.replace(":", "", regex=False)

        if 'block_id' not in df_gene_positons.columns:
            df_gene_positons.insert(0, 'block_id', 'chr1')
        
    merged_with_positions = pd.merge(df_matrix, df_gene_positons, left_on=list_species[0], right_on='PID')

    # rename and reorganize columns
    merged_with_positions = merged_with_positions.rename(columns={'ClutserID': 'name'})

    merged_with_positions[['start', 'end']] = merged_with_positions['Location'].str.split('\.\.', expand=True)
    #merged_with_positions.insert(0, 'block_id', 'chr1')

    

    merged_with_positions.insert(0, 'color', 'black')
    merged_with_positions = merged_with_positions[['name','block_id','start', 'end','color','Strand']]
    merged_with_positions['start'] = merged_with_positions['start'].astype(int)
    gene_plus_df = merged_with_positions[merged_with_positions["Strand"] == "+"]
    gene_minus_df = merged_with_positions[merged_with_positions["Strand"] == "-"]
    gene_plus_df.to_csv(directory+"/merged_with_positions.csv",index=False,sep='\t')
    dict_list_gene_plus = gene_plus_df.to_dict('records')
    dict_list_gene_minus = gene_minus_df.to_dict('records')
    karyotype_df = merged_with_positions.groupby('block_id').max().reset_index()
    karyotype_df = karyotype_df.rename(columns={'block_id': 'id'})
    karyotype_df['label'] = karyotype_df.loc[:, 'id']
    karyotype_df = karyotype_df.rename(columns={'start': 'len'})
    karyotype_df = karyotype_df[['id','label','len','color']]
    karyotype_df.to_csv(directory+"/karyotype.csv",index=False,sep='\t')
    karyotype_dict_list = karyotype_df.to_dict('records')

    data_summary_filtered_md_template = 'Selected strains'
    data_summary_filtered_md = data_summary_filtered_md_template.format(len(df))


    
    return df,df_metadata,df_ANI,merged_with_positions,list_species,list_continent,list_organisms,karyotype_dict_list,dict_list_gene_plus,dict_list_gene_minus,df_matrix


###############################################
# return list of the same combination as a cluster given as argument
###############################################
def get_combination(cluster,pathname,list_of_strains):
    
    directory = ""
    if not pathname:
        return "No project."
    row = query_db("SELECT path FROM projects WHERE title = ?", (pathname,), one=True)
    path = ""
    if not row:
        path = conf["session_dir"] + "/" + pathname
    else:
        path = row[0]
    directory = path


    df = pd.read_csv(directory+'/1.Orthologs_Cluster.2.txt',sep='\t')

    # convert cluster identifiers into string for filtering
    df = df.astype({'ClutserID': str})
    mini_df = df.loc[df['ClutserID'] == str(cluster)]
    
    # generate a new dataframe from a list of list
    list_of_list = []
    nb_presence = 0
    specific_to = []
    for item in mini_df.columns:
        
        if item != 'ClutserID' and item in list_of_strains:
            
            genes = mini_df[item]
            keep = True

            
            for gene in genes:
                if gene == 0:
                    keep = False
            if keep:
                list_genes = ','.join(map(str,genes)) 
                list = [cluster,item,list_genes]
                list_of_list.append(list)
                nb_presence+=1
                specific_to.append(str(item))

    
    return specific_to

# Utility: create a session code for a project (admin)
def generate_session_code_for_project(project_id, hours_valid=24):
    code = uuid.uuid4().hex[:8].upper()
    expires = (datetime.now() + pd.to_timedelta(hours_valid, unit='h')).isoformat()
    execute_db("UPDATE projects SET session_code=?, session_expiration=? WHERE id=?", (code, expires, project_id))
    return code, expires

# Optional small admin Flask route to create a session code quickly (protected by basic login in this demo)
@server.route("/admin/generate_session/<int:project_id>")
@login_required
def admin_generate_session(project_id):
    # only owner or superuser allowed in prod — here any logged user can create for demo
    code, exp = generate_session_code_for_project(project_id, hours_valid=24)
    return f"Code: {code} (exp: {exp}) — URL: /?session={code}"

@server.route("/cgi-bin/<path:anything>")
def redirect_all_cgi(anything):
    return redirect("/", code=301)


def is_string_without_special_character(valeur):
    return isinstance(valeur, str) and re.fullmatch(r"[a-zA-Z0-9_-]+", valeur) is not None

def is_stringlist_without_special_character(valeur):
    return isinstance(valeur, str) and re.fullmatch(r"[a-zA-Z0-9, _-]+", valeur) is not None

def is_bed(valeur: str) -> bool:
    if not isinstance(valeur, str):
        return False

    # Découpe par tab ou espaces multiples
    champs = re.split(r"\s+", valeur.strip())

    # BED = au moins 3 colonnes
    if len(champs) < 3:
        return False

    chrom, start, end = champs[0], champs[1], champs[2]

    # chromosome valide (chr1, chrX, chrM, etc.)
    if not re.fullmatch(r"chr([1-9][0-9]?|X|Y|M)", chrom):
        return False

    # start / end entiers
    try:
        start = int(start)
        end = int(end)
    except ValueError:
        return False

    # règles BED
    if start < 0 or end < 0:
        return False
    if end <= start:
        return False

    return True

def parse_vcf(vcf_file, max_variants=2000, samples_subset=None):
    """
    Parse minimal VCF to extract GT matrix.
    - VCF file path
    - max_variants: stop after this many variants (to keep la mémoire raisonnable)
    - samples_subset: optional list of sample names to keep (None => all)
    Returns: DataFrame (variants rows, samples columns), index=CHROM:POS:ID or CHROM:POS
    """
    samples = []
    header_re = re.compile(r'^#CHROM')
    gt_index = None
    rows = []
    variant_ids = []
    
    with open(vcf_file, 'r') as file:
        lines = file.readlines()

        for line in lines:
            if line.startswith('##'):
                continue
            if line.startswith('#CHROM'):
                cols = line.strip().split('\t')
                samples = cols[9:]
                if samples_subset is not None:
                    # keep only those present in samples
                    samples = [s for s in samples if s in samples_subset]
                continue
            if line.startswith('#') or line.strip() == '':
                continue

            parts = line.strip().split('\t')
            chrom, pos, vid, ref, alt, qual, filt, info, fmt = parts[:9]
            sample_fields = parts[9:]

            # find GT index in FORMAT
            fmt_keys = fmt.split(':')
            if gt_index is None:
                try:
                    gt_index = fmt_keys.index('GT')
                except ValueError:
                    gt_index = None

            # convert each sample's GT to numeric
            gts = []
            sample_names = parts[9:]  # values
            # iterate original sample names to maintain order and drop if not in subset
            original_sample_names = samples if samples else None

            for i, s_val in enumerate(parts[9:]):
                if samples_subset is not None:
                    # Need original sample name for position i
                    orig_name = None
                    # hack: when header parsed we saved 'samples' as subsetted; to map indices we need full header
                    # To avoid complexity, we assume we only subset by names existing earlier: use placeholder mapping:
                    # Simpler design: we will re-parse header to keep full_sample_names for correct mapping.
                    pass

            # Simpler approach: we will rework to store full sample names when parsing header.
            break

        # -- REWRITE using a single-pass with stored full sample list --
        
        full_samples = []
        gt_index = None
        rows = []
        variant_ids = []
        for line in lines:
            if line.startswith('##'):
                continue
            if line.startswith('#CHROM'):
                cols = line.strip().split('\t')
                full_samples = cols[9:]
                # build index map from full samples to kept samples
                if samples_subset is not None:
                    keep_mask = [s in samples_subset for s in full_samples]
                    kept_sample_names = [s for s, keep in zip(full_samples, keep_mask) if keep]
                else:
                    keep_mask = [True] * len(full_samples)
                    kept_sample_names = full_samples[:]
                try:
                    # find GT index in format
                    # we'll set per-line (safe) but usually same
                    pass
                except Exception:
                    pass
                continue
            if line.startswith('#') or line.strip() == '':
                continue

            parts = line.strip().split('\t')
            chrom, pos, vid, ref, alt, qual, filt, info, fmt = parts[:9]
            sample_values = parts[9:]

            fmt_keys = fmt.split(':')
            if 'GT' in fmt_keys:
                gt_index = fmt_keys.index('GT')
            else:
                gt_index = None

            # gather GTs for selected samples
            row = []
            for keep, sval in zip(keep_mask, sample_values):
                if not keep:
                    continue
                if gt_index is None:
                    row.append(np.nan)
                    continue
                fields = sval.split(':')
                if gt_index >= len(fields):
                    row.append(np.nan)
                    continue
                gt = fields[gt_index]
                # normalized representation: handle phased/unphased, multiple alleles
                if gt in ('.', './.', '.|.'):
                    row.append(np.nan)
                    continue
                # split on / or |
                alleles = re.split(r'[\/\|]', gt)
                # if any allele is '.' -> missing
                if any(a == '.' or a == '' for a in alleles):
                    row.append(np.nan)
                    continue
                try:
                    al_nums = [int(a) for a in alleles]
                except ValueError:
                    row.append(np.nan)
                    continue
                # simple coding: count of alt alleles (works for biallelic)
                alt_count = sum(1 for a in al_nums if a != 0)
                row.append(alt_count)
            # index label
            label = vid if vid != '.' and vid != '' else f"{chrom}:{pos}"
            variant_ids.append(f"{chrom}:{pos}")
            rows.append(row)
            if len(rows) >= max_variants:
                break
    df = pd.DataFrame(rows, index=variant_ids, columns=kept_sample_names)
    
    # reorder columns to match samples_subset if provided
    cols = df.columns.to_list()
    # keep columns if present in VCF (remove reference)
    samples_subset = [x for x in samples_subset if x in cols]
    df_ordered = df[samples_subset]
    
    return df_ordered

def generate_tree_html(newick, df_metadata, colorizing, html_file):

    concat_for_hash = ""
    list_metadata_color = df_metadata[colorizing].unique().tolist()
    dict_colors = {}
    i = 0

    legend = ""
    legend += "<style>"
    legend += ".legend div{display:flex;align-items:center;margin:4px 0}"
    legend += ".legend span{width:16px;height:16px;margin-right:6px}"
    legend += "</style>"
    legend += "<div class=\"legend\">"
    
    for country in list_metadata_color:
        if country != "none" and country != "None" and str(country) != "nan" and country != "":
            col = ""
            if i < len(colors):
                col =  colors[i]
            else:
                col =  "black"
            dict_colors[country] = col
            legend = legend + "<div><span style=\"background:" + str(col) + "\"></span>" + str(country) + "</div>"
            i += 1
    legend += "</div>"

    for index, row in df_metadata.iterrows():
        color = "black"
        if str(row[colorizing]) in dict_colors:
            color = dict_colors[str(row[colorizing])]
        concat_for_hash = concat_for_hash + "hash_colors['" + str(row['Strain name']) + "'] = '" + color + "';\n"

    # remove last caracter
    newick = newick.rstrip(newick[-1])
    f = open(html_file, "w")
    template = open('assets/tree.html', 'r')
    for line in template:
        if re.search(r"NEWICK_TREE", line):
            f.write("var test_string = \""+newick+";\"\n")
        elif re.search(r"WEB_URL",line):
            f.write("<script src='"+ WEB_URL +"/assets/phylotree.js'></script>")
        elif re.search(r"HASH_COLORS", line):
            f.write(concat_for_hash+"\n")
        elif re.search(r"LEGEND", line):
            f.write(legend+"\n")
        else:
            f.write(line)
    template.close()
    f.close()

@app.callback(
    Output("download-dataframe", "data"),
    Input("btn-download", "n_clicks"),
    State('projets', 'value'),
    prevent_initial_call=True
)
def download_matrix(n,pathname):
    directory = ""
    if not pathname:
        return "No project."
    row = query_db("SELECT path FROM projects WHERE title = ?", (pathname,), one=True)
    path = ""
    if not row:
        path = conf["session_dir"] + "/" + pathname
    else:
        path = row[0]
    directory = path
    df = pd.read_csv(directory+'/export_mlva.tsv',sep='\t')
    return dcc.send_data_frame(df.to_csv, "matrix.csv")

@app.callback(
    Output("download-dataframe2", "data"),
    Input("download_table", "n_clicks"),
    State("current_session", 'value'),
    State('projets', 'value'),
    prevent_initial_call=True
)
def download_matrix(n,session,pathname):
    directory = ""
    if not pathname:
        return "No project."
    row = query_db("SELECT path FROM projects WHERE title = ?", (pathname,), one=True)
    path = ""
    if not row:
        path = conf["session_dir"] + "/" + pathname
    else:
        path = row[0]
    directory = path
    df = pd.read_csv(tmp_dir+ "/"+str(session)+".merged_with_cog_final.csv",sep='\t')
    return dcc.send_data_frame(df.to_csv, "search_results.tsv",sep='\t')




# Register dashboard callbacks

submit_genomes.register_callbacks(app)

# ---------- Main ----------
if __name__ == "__main__":
    init_db()
    sync_projects_from_yaml()
    print("Base initialisée, projets synchronisés.")
    server.run(host= '0.0.0.0',debug=True, port=8050)
