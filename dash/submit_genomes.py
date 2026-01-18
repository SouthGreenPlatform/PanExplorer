import cmd
from email.message import EmailMessage
import os
import base64
import io
import pathlib
import random
import shutil
import smtplib
from sys import meta_path
import uuid
import re

import pandas as pd
import json
import yaml
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord

from dash import Dash, dcc, html, Input, Output, State
import dash_ag_grid as dag

import dash_bootstrap_components as dbc

import threading
import subprocess
import time

import dash_uploader as du



# --------------------------------------------------
# Configuration
# --------------------------------------------------

MAX_GENOMES = 80
MIN_VALID_GENOMES = 3



CONFIG_YAML = "panexplorer_config.yaml"
tmp_dir = "tmp"
with open(CONFIG_YAML, "r") as f:
    conf = yaml.safe_load(f)
session_dir = conf.get("session_dir")
web_url = conf.get("web_url")
UPLOAD_DIR = conf.get("upload_dir")

ncbi_datasets_exe = conf.get("ncbi_datasets_exe") or "datasets"

os.makedirs(UPLOAD_DIR, exist_ok=True)

#session = random.randint(1, 9000000)


# --------------------------------------------------
# Layout
# --------------------------------------------------

layout = html.Div(
    
    children=[
        dcc.Store(id="session", storage_type="session"),
        html.Div(id="page-submission-content",style={"display": "block"}, children=[
            html.Br(),
            html.H5("Project name:"),
            dcc.Input(id="project-name", type="text", placeholder="Enter project name",style={"width":"550px"}),
            html.Label("Alphanumeric, no spaces, underscores (_) or hyphens (-) only."),

            html.H5("Email address:"),
            dcc.Input(id="email-address", type="email", placeholder="Enter email address", style={"width": "50%"}),
            html.Label("Must be a valid email address."),

            html.H5("Minimum percentage identity:"),
            dcc.Input(id="min-percentage-identity", type="number", placeholder="Enter minimum percentage identity", value=80,style={"width": "50%"}),
            html.Label("Percentage identity for protein Blast. Must be between 1 and 100."),

            html.H5("What is your inputs:"),
            dcc.Dropdown(id="input-type", options=[{"label": "Prokaryotic public genomes: Enter a list of Genbank assembly accessions (GCA)", "value": "public"}, {"label": "Prokaryotic private genomes: Upload genbank files", "value": "upload"}, {"label": "Eukaryotic genomes: Upload FASTA + GFF files", "value": "eukaryotic"}], style={"width":"750px"}),

            html.Br(),
            html.Div(id="input-options"),
            #dcc.Input(id="session", type="hidden", value=str(session)),
            html.Br(),
            dcc.Loading(
                type="circle",
                children=html.Div(id="output-area")
            ),
            html.Br(),
            dcc.Loading(
                type="circle",
                children=html.Div(id="output-area3")
            ),
            
        ]),
        html.Br(),
        dcc.Loading(
                type="circle",
                children=html.Div(id="output-area2")
            ),
        
    ]
)

# --------------------------------------------------
# Utility functions
# --------------------------------------------------

def is_valid_genbank(decoded_text):
    """
    Check whether the uploaded file is a valid GenBank file.
    Returns (is_valid, records_or_error).
    """
    try:
        handle = io.StringIO(decoded_text)
        records = list(SeqIO.parse(handle, "genbank"))

        if not records:
            return False, "No GenBank records found"

        if not all(isinstance(r, SeqRecord) for r in records):
            return False, "Invalid GenBank structure"

        return True, records

    except Exception as e:
        return False, str(e)


def save_genbank_file(decoded_bytes, original_filename,session):
    """
    Save a validated GenBank file to disk.
    """
    filepath = os.path.join(f"{UPLOAD_DIR}/{session}", original_filename)

    with open(filepath, "wb") as f:
        f.write(decoded_bytes)

    return filepath


def summarize_records(records, original_name, stored_filename):
    """
    Summarize a GenBank file at the FILE level.
    """
    contig_count = len(records)
    genome_size = sum(len(r.seq) for r in records)

    cds_count = 0
    gene_count = 0

    for record in records:
        for feature in record.features:
            if feature.type == "CDS":
                cds_count += 1
            elif feature.type == "gene":
                gene_count += 1

    return {
        "File name": original_name,
        "Valid": "✅",
        "Error": "",
        "Number of contigs": contig_count,
        "Genome size (bp)": genome_size,
        "Genes": gene_count,
        "CDS": cds_count,
        "Stored file": stored_filename,
    }


def run_external_command(project_name, email_address, valid_list, min_percentage_identity, session, software):

    try:
        if os.path.exists(f"{UPLOAD_DIR}/{session}/forzip/genomes.zip"):
            cmd= "python PanExplorer_galaxy_bioblend.py --z {} --o {} --p {} --s {} --n {}".format(f"{UPLOAD_DIR}/{session}/forzip/genomes.zip", session_dir+"/"+str(session), min_percentage_identity, software, session)
            os.system(cmd)
        elif valid_list.count(",") + 1 > 1:
            cmd= "python PanExplorer_galaxy_bioblend.py --i {} --o {} --p {} --s {} --n {}".format(valid_list, session_dir+"/"+str(session), min_percentage_identity, software, session)
            os.system(cmd)

    except subprocess.CalledProcessError as e:
        stderr = e.stderr
        stdout = e.stdout


    # Une fois terminé → email
    #send_email(email_address, stdout, stderr)

def send_email(to):
    msg = EmailMessage()
    msg["Subject"] = "Script terminé"
    msg["From"] = "noreply@tonapp.com"
    msg["To"] = to
    msg.set_content("Votre script est terminé.")

    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls()
        s.login("email@gmail.com", "mot_de_passe")
        s.send_message(msg)


# --------------------------------------------------
# Callback
# --------------------------------------------------

def register_callbacks(app):
    du.configure_upload(app, folder=UPLOAD_DIR)

    @app.callback(
        Output("output-area", "children", allow_duplicate=True),
        Input("check-gca-button", "n_clicks"),
        State("public-genomes", "value"),
        prevent_initial_call=True,
    )
    def check_public_genomes(n_clicks, gca_list):
        if n_clicks == 0:
            return html.Div("No check performed yet.")

        if not gca_list:
            return html.Div("Please enter at least 3 Genbank assembly accession (GCA).")

        gca_accessions = [gca.strip() for gca in gca_list.split(",") if gca.strip()]

        if len(gca_accessions) > 200:
            return html.Div("Error: maximum number of genomes exceeded (200 allowed).")
        
        rows = []
        valid_genome_count = 0
        list_of_valid_accessions = []
        session = random.randint(1, 9000000)
        os.mkdir(f"{UPLOAD_DIR}/{session}")
        

        mkdir_cmd = f"mkdir -p {session_dir}/{session}/genomes/genomes"
        os.system(mkdir_cmd)
        dict_strains = {}
        for accession in gca_accessions:

            x = re.search("^GC[AF]_\d+(\.\d+)?$", accession)
            if not x:
                return html.Div("Does not respect GCA accession format")
            else:
                cmd = ncbi_datasets_exe + " download genome accession " + accession + " --filename " + tmp_dir + "/" +accession + ".zip --include genome,gbff,protein"
                returned_value = os.system(cmd)

                if returned_value == 0:
                    filepath = tmp_dir + "/" +accession + ".zip"
                    import zipfile
                    with zipfile.ZipFile(filepath, 'r') as zip_ref:
                        zip_ref.extractall(tmp_dir + "/" +accession)

                    gbff_files = []
                    for root, dirs, files in os.walk(tmp_dir + "/" +accession):
                        for file in files:
                            if file.endswith(".gbff") or file.endswith(".gbk") or file.endswith(".gb"):
                                gbff_files.append(os.path.join(root, file))

                    if not gbff_files:
                        rows.append({
                            "File name": accession,
                            "Valid": "❌",
                            "Error": "No GenBank files found in the dataset",
                            "Number of contigs": None,
                            "Genome size (bp)": None,
                            "Genes": None,
                            "CDS": None,
                            "Stored file": None,
                        })
                    else:
                        for gbff_file in gbff_files:
                            with open(gbff_file, "r", encoding="utf-8", errors="replace") as f:
                                decoded_text = f.read()

                            is_valid, result = is_valid_genbank(decoded_text)

                            
                            if not is_valid:
                                rows.append({
                                    "File name": accession,
                                    "Valid": "❌",
                                    "Error": result,
                                    "Number of contigs": None,
                                    "Genome size (bp)": None,
                                    "Genes": None,
                                    "CDS": None,
                                    "Stored file": None,
                                })
                                continue

                            # Valid GenBank → save and summarize
                            with open(gbff_file, "rb") as f:
                                decoded_bytes = f.read()
                            filepath = save_genbank_file(decoded_bytes, os.path.basename(gbff_file),session)
                            stored_filename = os.path.basename(filepath)

                            summary = summarize_records(result, accession, stored_filename)
                            rows.append(summary)

                            valid_genome_count += 1
                            list_of_valid_accessions.append(accession)

                            cmd = f"cp -rf {gbff_file} {session_dir}/{session}/genomes/genomes/{accession}.gbff "
                            os.system(cmd)
                            cmd = f"gzip {session_dir}/{session}/genomes/genomes/{accession}.gbff"
                            os.system(cmd)

                            cmd = f"zgrep -A 2 'DEFINITION' {session_dir}/{session}/genomes/genomes/{accession}.gbff.gz"
                            os.system(cmd)  
                            get_organism_line = os.popen(cmd).read()
                            lines_organism = get_organism_line.split("\n")
                            first_line = lines_organism[0]
                            second_line = lines_organism[1]
                            if re.match(r"^            (.*)", second_line):
                                get_organism_line = first_line + " " + re.match(r"^            (.*)", second_line).group(1)
                            else:
                                get_organism_line = first_line
                            strain = ""
                            if re.match(r"DEFINITION  (.*)$", get_organism_line):
                                strain = re.match(r"DEFINITION  (.*)$", get_organism_line).group(1)
                                strain = strain.replace(".", "")
                                info = strain.split(",")
                                strain = info[0]
                                strain = strain.replace(" ", "_")
                                strain = strain.replace("strain_", "")
                                strain = strain.replace("_chromosome", "")
                                strain = strain.replace("_genome", "")
                                strain = strain.replace("_str_", "_")
                                strain = re.sub(r"[^\w\-\_]", "", strain)
                                strain = strain.replace("-", "_")
                            cmd = f"mv {session_dir}/{session}/genomes/genomes/{accession}.gbff.gz {session_dir}/{session}/genomes/genomes/{strain}.gbff.gz"
                            os.system(cmd) 

                            dict_strains[accession] = strain
                else:
                    rows.append({
                        "File name": accession,
                        "Valid": "❌",
                        "Error": "Failed to download dataset from NCBI Datasets",
                        "Number of contigs": None,
                        "Genome size (bp)": None,
                        "Genes": None,
                        "CDS": None,
                        "Stored file": None,
                    })
                    continue
            
                
        cmd = f"perl GetSequences.pl -i {session_dir}/{session}/genomes/genomes"
        os.system(cmd) 

        with open(f"{session_dir}/{session}/metadata.xls", "w") as f:
            f.write("Strain name\tCountry\tContinent\tOrganism\n")
            for accession, strain in dict_strains.items():
                f.write(f"{strain}\t\t\t\n")
        
        df = pd.DataFrame(rows)

        grid = dag.AgGrid(
            rowData=df.to_dict("records"),
            columnDefs=[
                {
                    "headerName": col,
                    "field": col,
                    "sortable": True,
                    "filter": True,
                }
                for col in df.columns
            ],
            defaultColDef={
                "resizable": True,
                "minWidth": 120,
            },
            dashGridOptions={
                "pagination": True,
                "paginationPageSize": 10,
            },
            style={"height": "420px", "width": "100%"},
        )

        go_button = html.Div(
            style={"marginTop": "20px"},
            children=[
                html.Button(
                    f"  (Send data to the pipeline ({valid_genome_count} valid genomes)",
                    id="go-button",
                    style={"display": "block"},
                    n_clicks=0
                ),
                
            ]
        )
        divs = [html.H4("Upload validation summary"), grid]

        if valid_genome_count >= MIN_VALID_GENOMES:
            divs.append(go_button)
            divs.append(dcc.Input(id="valid_list", type="hidden", value=",".join(list_of_valid_accessions)))
            divs.append(dcc.Input(id="session_id", type="hidden", value=str(session)))

        return html.Div(divs)
    


    @app.callback(
        Output("output-area2", "children",allow_duplicate=True),
        Output("page-submission-content", "style", allow_duplicate=True),
        Input("go-button", "n_clicks"),
        State("project-name", "value"),
        State("email-address", "value"),
        State("valid_list", "value"),
        State("software", "value"),
        State("session", "value"),
        State("min-percentage-identity", "value"),
        prevent_initial_call=True,
    )
    def go_to_pipeline_public(n_clicks, project_name, email_address, valid_list, software, session_id, min_percentage_identity):
        if n_clicks == 0:
            return html.Div()

        if (not project_name or not re.match("^[A-Za-z0-9_-]+$", project_name)):
            return dbc.Alert("Error: Invalid project name. Must be alphanumeric with no spaces, underscores (_) or hyphens (-) only.", color="danger") , {"display": "block"}
        if (not email_address or not re.match(r"[^@]+@[^@]+\.[^@]+", email_address)):
            return dbc.Alert("Error: Invalid email address.", color="danger") , {"display": "block"}
        if (not min_percentage_identity or not (1 <= min_percentage_identity <= 100)):
            return dbc.Alert("Error: Minimum percentage identity must be between 1 and 100.", color="danger") , {"display": "block"}
        
        
        thread = threading.Thread(
            target=run_external_command,
            args=(project_name, email_address, valid_list, min_percentage_identity, session_id, software),
            daemon=True
        )
        
        thread.start()

        return dbc.Alert(
            [
                html.H4("Well done!", className="alert-heading"),
                html.P("Data have been sent to the pipeline. You will receive an email once it is complete. Data are available in the URL: "),
                #html.Hr(),
                html.A(f"{web_url}/?session={session_id}", href=f"{web_url}/?session={session_id}", target="_blank", className="alert-link"),
            ],
            color="success",
        ) , {"display": "none"}
        
    @app.callback(
        Output("input-options", "children"),
        Input("input-type", "value"),
    )
    def apply_import(input_type):
        session = random.randint(1, 9000000)
        if input_type == "public":
            return html.Div([
                dcc.Input(id="session", type="hidden", value=str(session)),
                html.H5("Choose the pan-genome software"+str(session)),
                dcc.Dropdown(id="software", options=[{"label": "PanACoTA (faster)", "value": "panacota"}, {"label": "Roary", "value": "roary"}, {"label": "PGGB (Pan Genome Graph Builder)", "value": "pggb"}], value="panacota", style={"width":"300px"}),

                html.H5("Public genomes. Enter a list of Genbank assembly accessions (GCA). Must be annotated (up to 200 genomes)"),
                dcc.Input(id="public-genomes", type="text", placeholder="GCA_000001234.1,GCA_000005678.1", style={"width": "75%"}),
                html.Label("Coma separated list (Genbank assembly GCA,GCF)"),
                html.Button("Check accessions", id="check-gca-button", className="thin-button", n_clicks=0)
            ])
        elif input_type == "upload":
            MAX_GENOMES = 200
            return html.Div([
                dcc.Input(id="session", type="hidden", value=str(session)),
                html.H5("Choose the pan-genome software"),
                dcc.Dropdown(id="software", options=[{"label": "PanACoTA (faster)", "value": "panacota"}, {"label": "Roary", "value": "roary"}, {"label": "PGGB (Pan Genome Graph Builder)", "value": "pggb"}], value="panacota", style={"width":"300px"}),

                html.H5("Upload your own genomes. Must be annotated (up to 200 genomes)"),
                html.Label("Upload genbank files (accepted extension: .gb, .gbk, .gbff). Selection of multiple files is possible. Must be annotated genomes. "),
                html.Label(f"Maximum: {MAX_GENOMES} genomes."),
                
                du.Upload(
                    id="upload-genbank",
                    text="Upload GenBank files",
                    upload_id=session,
                    max_files=80,
                    filetypes=["gb", "gbk"],
                ),
                dcc.Store(id="upload-dir-state", data=None),
                dcc.Interval(id="upload-watchdog", interval=1500, disabled=True),

                # dcc.Upload(
                #     id="upload-genbank",
                #     children=html.Div([
                #         "Drag and drop GenBank files here or ",
                #         html.A("select files")
                #     ]),
                #     style={
                #         "width": "100%",
                #         "height": "80px",
                #         "lineHeight": "80px",
                #         "borderWidth": "2px",
                #         "borderStyle": "dashed",
                #         "borderRadius": "10px",
                #         "textAlign": "center",
                #     },
                #     multiple=True,
                # ),
            ])
        elif input_type == "eukaryotic":
            MAX_GENOMES = 20
            return html.Div([
                dcc.Input(id="session", type="hidden", value=str(session)),
                html.H5("Choose the pan-genome software"),
                dcc.Dropdown(id="software", options=[{"label": "Orthofinder", "value": "orthofinder"}, {"label": "PGGB (Pan Genome Graph Builder)", "value": "pggb"}], value="orthofinder", style={"width":"300px"}),

                html.H5("Eukaryotic genomes. Upload your own annotated genomes (FASTA + GFF files) (up to 20 genomes)"),
                html.Label("For each genome, upload a gzipped FASTA file of the genome sequence + a GFF annotation file."),
                html.Label("In order to make the association between sequence and annotation, they must be named with the same basename as follows: genome1.fasta.gz, genome1.gff, myspeciesXXX.fasta.gz, myspeciesXXX.gff... "),
                html.Label("Selection of multiple files is possible."),
                html.Label(f"Maximum: {MAX_GENOMES} genomes."),
                
                du.Upload(
                    id="upload-gff-fasta",
                    children=html.Div([
                        "Drag and drop GenBank files here or ",
                        html.A("select files")
                    ]),
                    style={
                        "width": "100%",
                        "height": "80px",
                        "lineHeight": "80px",
                        "borderWidth": "2px",
                        "borderStyle": "dashed",
                        "borderRadius": "10px",
                        "textAlign": "center",
                    },
                    multiple=True,
                ),
            ])
        else:
            return html.Div()

    

    # @du.callback(
    #     Output("output-area", "children"),
    #     Input("upload-genbank", "contents"),
    #     State("upload-genbank", "filename"),
    # )
    @du.callback(
        output=Output("output-area", "children"),
        id="upload-genbank",
    )
    def handle_uploaded_files(uploaded_files):

        if not uploaded_files:
            return html.Div("No files uploaded yet.")
        
        return html.Div(html.Button(
                    "Check status of uploaded files",
                    id="check-status-button",
                    style={"display": "block"},
                    n_clicks=0
                ),
        )
    
    @app.callback(
        Output("output-area3", "children", allow_duplicate=True),
        Input("check-status-button", "n_clicks"),
        State("session", "value"),
        prevent_initial_call=True,
    )
    def refresh_table(n_clicks, session):

        filepaths = []
        for file in os.listdir(UPLOAD_DIR+"/"+str(session)):
            original_name = os.path.basename(file)
            if file.endswith(".gb") or file.endswith(".gbk") or file.endswith(".gbff"):
                filepaths.append(UPLOAD_DIR+"/"+str(session)+"/"+file)
        print(filepaths)

        rows = []
        valid_genome_count = 0
        
        dict_strains = {}

        if not os.path.exists(session_dir+"/"+str(session)+"/genomes/genomes"):
            mkdir_cmd = f"mkdir -p {session_dir}/{session}/genomes/genomes"
            os.system(mkdir_cmd)
        else:
            shutil.rmtree(session_dir+"/"+str(session)+"/genomes/genomes")


        

        for filepath in filepaths:
            original_name = os.path.basename(filepath)
            print(original_name)

            # skip if file already in table
            if any(r["Stored file"] == original_name for r in rows):
                continue

            try:

                records = list(SeqIO.parse(filepath, "genbank"))
                if not records:
                    raise ValueError("No GenBank records found")

                contigs = len(records)
                genome_size = sum(len(r.seq) for r in records)
                genes = sum(1 for r in records for f in r.features if f.type == "gene")
                cds = sum(1 for r in records for f in r.features if f.type == "CDS")

                rows.append({
                    "File name": original_name,
                    "Valid": "✅",
                    "Error": "",
                    "Number of contigs": contigs,
                    "Genome size (bp)": genome_size,
                    "Genes": genes,
                    "CDS": cds,
                    "Stored file": original_name,
                })

                valid_genome_count += 1

            except Exception as e:
                rows.append({
                    "File name": original_name,
                    "Valid": "❌",
                    "Error": str(e),
                    "Number of contigs": None,
                    "Genome size (bp)": None,
                    "Genes": None,
                    "CDS": None,
                    "Stored file": None,
                })



        # for contents, name in zip(list_of_contents, list_of_names):

        #     content_type, content_string = contents.split(",")
        #     decoded_bytes = base64.b64decode(content_string)
        #     decoded_text = decoded_bytes.decode("utf-8", errors="replace")

        #     is_valid, result = is_valid_genbank(decoded_text)

        #     if not is_valid:
        #         rows.append({
        #             "File name": name,
        #             "Valid": "❌",
        #             "Error": result,
        #             "Number of contigs": None,
        #             "Genome size (bp)": None,
        #             "Genes": None,
        #             "CDS": None,
        #             "Stored file": None,
        #         })
        #         continue

        #     # Valid GenBank → save and summarize
        #     filepath = save_genbank_file(decoded_bytes, name,session)
        #     stored_filename = os.path.basename(filepath)

        #     summary = summarize_records(result, name, stored_filename)
        #     rows.append(summary)
        #     valid_genome_count += 1

        cmd = f"perl modifyGenbank.pl {UPLOAD_DIR}/{session} {UPLOAD_DIR}/{session}"
        os.system(cmd)

        filepaths = []
        for file in os.listdir(UPLOAD_DIR+"/"+str(session)+"/forzip"):
            if file.endswith(".gb"):
                filepaths.append(UPLOAD_DIR+"/"+str(session)+"/forzip/"+file)
                

        for filepath in filepaths:
            name = os.path.basename(filepath)
            print(name)

            cmd = f"cp -rf {UPLOAD_DIR}/{session}/forzip/{name} {session_dir}/{session}/genomes/genomes/{name}.gbff "
            os.system(cmd)
            cmd = f"gzip {session_dir}/{session}/genomes/genomes/{name}.gbff"
            os.system(cmd)

            cmd = f"zgrep -A 2 'DEFINITION' {session_dir}/{session}/genomes/genomes/{name}.gbff.gz"
            os.system(cmd)  
            get_organism_line = os.popen(cmd).read()
            lines_organism = get_organism_line.split("\n")
            first_line = lines_organism[0]
            second_line = lines_organism[1]
            if re.match(r"^            (.*)", second_line):
                get_organism_line = first_line + " " + re.match(r"^            (.*)", second_line).group(1)
            else:
                get_organism_line = first_line
            strain = ""
            if re.match(r"DEFINITION  (.*)$", get_organism_line):
                strain = re.match(r"DEFINITION  (.*)$", get_organism_line).group(1)
                strain = strain.replace(".", "")
                info = strain.split(",")
                strain = info[0]
                strain = strain.replace(" ", "_")
                strain = strain.replace("strain_", "")
                strain = strain.replace("_chromosome", "")
                strain = strain.replace("_genome", "")
                strain = strain.replace("_str_", "_")
                strain = re.sub(r"[^\w\-\_]", "", strain)
                strain = strain.replace("-", "_")
            cmd = f"mv {session_dir}/{session}/genomes/genomes/{name}.gbff.gz {session_dir}/{session}/genomes/genomes/{strain}.gbff.gz"
            os.system(cmd) 

            dict_strains[name] = strain

        

        cmd = f"perl GetSequences.pl -i {session_dir}/{session}/genomes/genomes"
        os.system(cmd) 

        with open(f"{session_dir}/{session}/metadata.xls", "w") as f:
            f.write("Strain name\tCountry\tContinent\tOrganism\n")
            for accession, strain in dict_strains.items():
                f.write(f"{strain}\t\t\t\n")

        df = pd.DataFrame(rows)

        grid = dag.AgGrid(
            rowData=df.to_dict("records"),
            columnDefs=[
                {
                    "headerName": col,
                    "field": col,
                    "sortable": True,
                    "filter": True,
                }
                for col in df.columns
            ],
            defaultColDef={
                "resizable": True,
                "minWidth": 120,
            },
            dashGridOptions={
                "pagination": True,
                "paginationPageSize": 10,
            },
            style={"height": "420px", "width": "100%"},
        )

        go_button = html.Div(
            style={"marginTop": "20px"},
            children=[
                html.Button(
                    f"  Send data to the pipeline ({valid_genome_count} valid genomes)",
                    id="go-button",
                    style={"display": "block"},
                    n_clicks=0
                ),
                
            ]
        )
        divs = [html.H4("Upload validation summary"), grid]

        if valid_genome_count >= MIN_VALID_GENOMES:
            divs.append(go_button)
            divs.append(dcc.Input(id="valid_list", type="hidden", value=""))
            divs.append(dcc.Input(id="session_id", type="hidden", value=str(session)))
        return html.Div(divs)
    




