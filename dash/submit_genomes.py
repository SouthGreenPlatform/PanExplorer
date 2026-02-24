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
import sys
import shlex
import secrets

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
import logging

from pathlib import Path

# optional libs: python-magic (python-magic-bin on Windows) and pyclamd for ClamAV
try:
    import magic
    HAS_MAGIC = True
except Exception:
    magic = None
    HAS_MAGIC = False

try:
    import pyclamd
    HAS_PYCLAMD = True
except Exception:
    pyclamd = None
    HAS_PYCLAMD = False

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
ADMIN_MAIL = conf.get("admin_mail")
UPLOAD_DIR = conf.get("upload_dir")

ncbi_datasets_exe = conf.get("ncbi_datasets_exe") or "datasets"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# Upload safety configuration
MAX_UPLOAD_SIZE_MB = conf.get("max_upload_size_mb", 50)
MAX_UPLOAD_SIZE_BYTES = int(MAX_UPLOAD_SIZE_MB * 1024 * 1024)
ALLOWED_EXT = {"gb", "gbk", "gbff", "genbank"}
VALIDATION_SENTINEL = ".upload_validation_done"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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
            dcc.Dropdown(id="input-type", options=[{"label": "Prokaryotic public genomes: Enter a list of assembly accessions (GCA or GCF)", "value": "public"}, 
                                                   {"label": "Prokaryotic private genomes: Upload genbank files", "value": "upload"}, 
                                                   #{"label": "Eukaryotic genomes: Upload FASTA + GFF files", "value": "eukaryotic"}
                                                   ], style={"width":"750px"}),

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

def fix_locus_line(line):
    MONTH_MAP = {
        # english
        "JAN": "JAN", "JAN.": "JAN",
        "FEB": "FEB", "FEB.": "FEB",
        "MAR": "MAR", "MAR.": "MAR",
        "APR": "APR", "APR.": "APR",
        "MAY": "MAY",
        "JUN": "JUN", "JUN.": "JUN",
        "JUL": "JUL", "JUL.": "JUL",
        "AUG": "AUG", "AUG.": "AUG",
        "SEP": "SEP", "SEPT": "SEP", "SEPT.": "SEP",
        "OCT": "OCT", "OCT.": "OCT",
        "NOV": "NOV", "NOV.": "NOV",
        "DEC": "DEC", "DEC.": "DEC",

        # french
        "JANV": "JAN", "JANV.": "JAN",
        "FÉVR": "FEB", "FÉVR.": "FEB",
        "FEVR": "FEB", "FEVR.": "FEB",
        "MARS": "MAR",
        "AVR": "APR", "AVR.": "APR",
        "MAI": "MAY",
        "JUIN": "JUN",
        "JUIL": "JUL", "JUIL.": "JUL",
        "AOÛT": "AUG", "AOUT": "AUG",
        "SEPT": "SEP", "SEPT.": "SEP",
        "OCT": "OCT", "OCT.": "OCT",
        "NOV": "NOV", "NOV.": "NOV",
        "DÉC": "DEC", "DÉC.": "DEC",
        "DEC": "DEC", "DEC.": "DEC",
    }
    
    if line.startswith("LOCUS"):
        # capture LOCUS + nom + taille collée + unité
        match = re.match(r"(LOCUS\s+)(\w+)\s+(bp|aa)", line)
        if match:
            return f"{match.group(1)}{match.group(2)} 100 {match.group(3)}\n"
        
        # correct date format in LOCUS line
        match = re.search(r'(\d{1,2})-([A-Za-z\.]+)-(\d{4})$', line.strip())
        if match:
            day, month, year = match.groups()
            month = month.upper()
            if month in MONTH_MAP:
                month = MONTH_MAP[month]
                new_date = f"{int(day):02d}-{month}-{year}"
                line = re.sub(r'\d{1,2}-[A-Za-z\.]+-\d{4}$', new_date, line)
    return line




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

def validate_session_id(session_id):
    """
    Validate that session_id is a valid UUID format.
    """
    try:
        uuid.UUID(str(session_id))
        return True
    except (ValueError, AttributeError):
        return False

def validate_gca_accession(accession: str) -> bool:
    """
    Validate that accession matches GCA/GCF format strictly.
    Format: GCA_XXXXXX.X or GCF_XXXXXX.X
    """
    return bool(re.fullmatch(r"^GC[AF]_\d{9}(\.\d+)?$", accession.strip()))

def validate_email_strict(email: str) -> bool:
    """
    Validate email address more strictly.
    """
    # Simple but effective regex for emails
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip())) and len(email) < 254

def is_safe_path(path: str, base_dir: str) -> bool:
    """
    Verify that `path` is within `base_dir` to prevent directory traversal.
    Returns True if safe, False otherwise.
    """
    try:
        real_path = os.path.realpath(path)
        real_base = os.path.realpath(base_dir)
        return real_path.startswith(real_base + os.sep) or real_path == real_base
    except (OSError, ValueError):
        return False

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and injection attacks.
    Only allows alphanumeric, underscores, hyphens, and dots (for extension).
    Removes any path separators and traversal attempts.
    """
    # Remove any path separators
    filename = os.path.basename(filename)
    # Remove null bytes
    filename = filename.replace('\x00', '')
    # Only allow safe characters
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    # Prevent empty filenames
    if not safe_name:
        safe_name = 'unnamed'
    return safe_name

def save_genbank_file(decoded_bytes, original_filename,session):
    """
    Save a validated GenBank file to disk.
    """

    filepath = os.path.join(f"{UPLOAD_DIR}/{session}", sanitize_filename(original_filename))

    with open(filepath, "wb") as f:
        f.write(decoded_bytes)

    return filepath


def is_string_without_special_character(valeur):
    return isinstance(valeur, str) and re.fullmatch(r"[a-zA-Z0-9_-]+", valeur) is not None

def is_list_GCA(valeur):
    return isinstance(valeur, str) and re.fullmatch(r"[a-zA-Z0-9_, .]+", valeur) is not None

def has_valid_gene_identifiers(records):
    """
    Check if GenBank records contain either locus_tag or protein_id qualifiers.
    Returns (True, None) if valid, (False, error_message) otherwise.
    """
    has_locus_tag = False
    has_protein_id = False
    
    for record in records:
        for feature in record.features:
            if feature.type == "CDS":
                if "locus_tag" in feature.qualifiers:
                    has_locus_tag = True
                if "protein_id" in feature.qualifiers:
                    has_protein_id = True
                
                if has_locus_tag or has_protein_id:
                    return True, None
    
    if not has_locus_tag and not has_protein_id:
        return False, "GenBank file must contain either locus_tag or protein_id qualifiers in CDS features"
    
    return True, None

def summarize_records(records, original_name, stored_filename):
    """
    Summarize a GenBank file at the FILE level.
    """
    contig_count = len(records)
    genome_size = sum(len(r.seq) for r in records)

    cds_count = 0
    gene_count = 0
    country = ""
    for record in records:
        for feature in record.features:
            if feature.type == "CDS":
                cds_count += 1
            elif feature.type == "gene":
                gene_count += 1
            elif feature.type == "source":
                country = feature.qualifiers.get("country", ["unknown"])[0]

    return {
        "File name": original_name,
        "Valid": "✅",
        "Error": "",
        "Country": country,
        "Number of contigs": contig_count,
        "Genome size (bp)": genome_size,
        "CDS": cds_count,
        "Stored file": stored_filename,
    }


def run_external_command(project_name, email_address, valid_list, min_percentage_identity, session, software):

    # Validate session to prevent injection attacks
    if not validate_session_id(session):
        logger.error("Invalid session ID attempted: %s", session)
        return

    path = UPLOAD_DIR + "/" + str(session)

    if os.path.exists(path) and os.path.exists(f"{session_dir}/{session}/summary_upload.csv"):

            countries = {}
            # Remove invalid genomes before proceeding
            df = pd.read_csv(f"{session_dir}/{session}/summary_upload.csv", sep="\t")
            for row in df.itertuples():
                file_name = row[1]
                valid = row[2]
                country = row[4]
                file_name = file_name.replace("_", "")
                file_name = file_name.replace("-", "")
                file_name = file_name.replace(".", "")
                countries[file_name] = country
                if valid == "✅":
                    pass
                else:
                    file_to_remove = os.path.join(UPLOAD_DIR, session, file_name)
                    if is_safe_path(file_to_remove, UPLOAD_DIR) and os.path.exists(file_to_remove):
                        os.remove(file_to_remove)
            
            upload_path = os.path.join(UPLOAD_DIR, session)
            result = subprocess.run(['perl', 'modifyGenbank.pl', upload_path, upload_path],
                                   capture_output=True, text=True)

            dict_strains = {}
            filepaths = []
            forzip_dir = os.path.join(UPLOAD_DIR, session, "forzip")
            if os.path.isdir(forzip_dir):
                for file in os.listdir(forzip_dir):
                    if file.endswith(".gb"):
                        filepaths.append(os.path.join(forzip_dir, file))
                    
            for filepath in filepaths:
                name = os.path.basename(filepath)
                safe_name = sanitize_filename(name)

                dest_gbff = os.path.join(session_dir, session, "genomes", "genomes", f"{safe_name}.gbff")
                if not is_safe_path(dest_gbff, session_dir):
                    logger.warning("Path traversal attempt detected: %s", dest_gbff)
                    continue

                shutil.copyfile(filepath, dest_gbff)
                
                subprocess.run(["gzip", dest_gbff], check=True)

                dest_gbff_gz = f"{dest_gbff}.gz"
                result = subprocess.run(['zgrep', '-A', '2', 'DEFINITION', dest_gbff_gz],
                                                   capture_output=True, text=True)
                get_organism_line = result.stdout
                
                lines_organism = get_organism_line.split("\n")
                first_line = lines_organism[0]
                second_line = lines_organism[1] if len(lines_organism) > 1 else ""
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
                
                # Sanitize strain name before using in filesystem
                safe_strain = sanitize_filename(strain) if strain else safe_name
                dest_strain_gz = os.path.join(session_dir, session, "genomes", "genomes", f"{safe_strain}.gbff.gz")
                
                if is_safe_path(dest_strain_gz, session_dir):
                    subprocess.run(['mv', dest_gbff_gz, dest_strain_gz], check=True)

                dict_strains[name] = strain
                print(strain+" "+name + "\n")
                name2 = pathlib.Path(name).stem
                country = countries[name2] 
                countries[strain] = country
                
            subprocess.run(['perl', 'GetSequences.pl', '-i', os.path.join(session_dir, session, "genomes", "genomes")], check=True)

            metadata_file = os.path.join(session_dir, session, "metadata.xls")
            if is_safe_path(metadata_file, session_dir):
                with open(metadata_file, "w") as f:
                    f.write("Strain name\tCountry\tContinent\tOrganism\n")
                    for accession, strain in dict_strains.items():
                        country = countries.get(strain, "")
                        f.write(f"{strain}\t{country}\t\t\n")
                os.chmod(metadata_file, 0o644)

    elif valid_list and valid_list.count(",") + 1 > 1:

        accessions = [acc.strip() for acc in valid_list.split(",") if acc.strip()]
        
        # Validate all accessions before processing
        for accession in accessions:
            if not validate_gca_accession(accession):
                logger.error("Invalid accession format: %s", accession)
                continue
        
        dict_strains = {}   
        countries = {}
        for accession in accessions:
                    
                cmd = [ncbi_datasets_exe, 'download', 'genome', 'accession', accession, 
                       '--filename', os.path.join(tmp_dir, f"{accession}.zip"), '--include', 'genome,gbff,protein']
                result = subprocess.run(cmd)
                returned_value = result.returncode

                if returned_value == 0:
                    filepath = os.path.join(tmp_dir, f"{accession}.zip")
                    import zipfile
                    extract_dir = os.path.join(tmp_dir, accession)
                    os.makedirs(extract_dir, exist_ok=True)
                    with zipfile.ZipFile(filepath, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)

                    gbff_files = []
                    for root, dirs, files in os.walk(extract_dir):
                        for file in files:
                            if file.endswith(".gbff") or file.endswith(".gbk") or file.endswith(".gb"):
                                gbff_files.append(os.path.join(root, file))

                    if gbff_files:
                        
                        for gbff_file in gbff_files:
                            with open(gbff_file, "r", encoding="utf-8", errors="replace") as f:
                                decoded_text = f.read()

                            is_valid, result = is_valid_genbank(decoded_text)


                            # Valid GenBank → save and summarize
                            with open(gbff_file, "rb") as f:
                                decoded_bytes = f.read()
                            filepath = save_genbank_file(decoded_bytes, os.path.basename(gbff_file), session)
                            stored_filename = os.path.basename(filepath)

                            summary = summarize_records(result, accession, stored_filename)

                            dest_gbff = os.path.join(session_dir, session, "genomes", "genomes", f"{accession}.gbff")
                            if is_safe_path(dest_gbff, session_dir):
                                subprocess.run(['cp', '-rf', gbff_file, dest_gbff], check=True)
                                subprocess.run(['gzip', dest_gbff], check=True)

                                countries[accession] = summary['Country']

                                dest_gbff_gz = f"{dest_gbff}.gz"
                                result = subprocess.run(['zgrep', '-A', '2', 'DEFINITION', dest_gbff_gz],
                                                       capture_output=True, text=True)
                                get_organism_line = result.stdout


                                lines_organism = get_organism_line.split("\n")
                                first_line = lines_organism[0]
                                second_line = lines_organism[1] if len(lines_organism) > 1 else ""
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
                            
                            # Sanitize strain name before using in filesystem
                            safe_strain = sanitize_filename(strain) if strain else accession
                            dest_strain_gz = os.path.join(session_dir, session, "genomes", "genomes", f"{safe_strain}.gbff.gz")
                            
                            if is_safe_path(dest_strain_gz, session_dir):
                                subprocess.run(['mv', dest_gbff_gz, dest_strain_gz], check=True)

                                dict_strains[accession] = safe_strain
        
        genomes_dir = os.path.join(session_dir, session, "genomes", "genomes")
        subprocess.run(['perl', 'GetSequences.pl', '-i', genomes_dir], check=True)

        metadata_file = os.path.join(session_dir, session, "metadata.xls")
        if is_safe_path(metadata_file, session_dir):
            with open(metadata_file, "w") as f:
                f.write("Strain name\tCountry\tContinent\tOrganism\n")
                for accession, strain in dict_strains.items():
                    country = countries.get(accession, "")
                    f.write(f"{strain}\t{country}\t\t\n")
            os.chmod(metadata_file, 0o644)

    try:
        script_path = os.path.join(os.path.dirname(__file__), "PanExplorer_galaxy_bioblend.py")
        logpath = os.path.join(tmp_dir, f"panexplorer_{session}.log")

        cmd_args = None
        upload_genomes_zip = os.path.join(UPLOAD_DIR, session, "forzip", "genomes.zip")
        if os.path.exists(upload_genomes_zip) and validate_session_id(session) and is_string_without_special_character(software):
            try:
                pct_identity = int(min_percentage_identity)
                if 1 <= pct_identity <= 100:
                    cmd_args = [sys.executable, script_path, "--z", upload_genomes_zip,
                                "--o", os.path.join(session_dir, str(session)), "--p", str(pct_identity),
                                "--s", software, "--n", str(session)]
            except (ValueError, TypeError):
                logger.error("Invalid min_percentage_identity: %s", min_percentage_identity)

        elif valid_list and valid_list.count(",") + 1 > 1 and validate_session_id(session) and is_string_without_special_character(software):
            try:
                pct_identity = int(min_percentage_identity)
                if 1 <= pct_identity <= 100:
                    cmd_args = [sys.executable, script_path, "--i", valid_list,
                                "--o", os.path.join(session_dir, str(session)), "--p", str(pct_identity),
                                "--s", software, "--n", str(session)]
            except (ValueError, TypeError):
                logger.error("Invalid min_percentage_identity: %s", min_percentage_identity)

        if cmd_args:
            os.makedirs(tmp_dir, exist_ok=True)
            with open(logpath, "ab") as logf:
                popen_kwargs = {"stdout": logf, "stderr": subprocess.STDOUT, "stdin": subprocess.DEVNULL}
                if os.name != "nt":
                    popen_kwargs["start_new_session"] = True

                proc = subprocess.Popen(cmd_args, **popen_kwargs)
                proc.wait()

    except subprocess.CalledProcessError as e:
        logger.error("Subprocess error: %s", str(e))
    except Exception as e:
        logger.error("Error in run_external_command: %s", str(e))

    send_email(email_address, session)
    

def send_email(to, session):
    """
    Send email notification with validation.
    """
    # Validate session and email
    if not validate_session_id(session):
        logger.error("Invalid session ID: %s", session)
        return
    
    if not validate_email_strict(to):
        logger.error("Invalid recipient email: %s", to)
        return

    if validate_session_id(session):
        message = f"""
Hi,

Your PanExplorer job {session} is done. You can click the link below to see your results:
https://panexplorer2.ird.fr/browse?session={session}

Your data will be available on the server for 15 days from the time they are generated.

See you soon on PanExplorer,

The PanExplorer team
"""

        msg_file = os.path.join(tmp_dir, f"{session}.message.txt")
        with open(msg_file, "w") as f:
            f.write(message)
        
        # Set restrictive permissions on message file
        os.chmod(msg_file, 0o600)

        # Use subprocess with list form (safer against injection) and pipe stdin
        cat_result = subprocess.run(['cat', msg_file], capture_output=True, text=True)
        subprocess.run(['mail', '-s', f'Panexplorer results session {session}', to],
                      input=cat_result.stdout, text=True, check=True)
        try:
            subprocess.run(['service', 'postfix', 'start'], check=True)
        except subprocess.CalledProcessError:
            logger.warning("Could not start postfix service")

        message_for_admin = f"""
The PanExplorer job {session} is done. It has been sent to {to}:
https://panexplorer2.ird.fr/browse?session={session}
"""

        admin_msg_file = os.path.join(tmp_dir, f"{session}.message_for_admin.txt")
        with open(admin_msg_file, "w") as f:
            f.write(message_for_admin)
        
        # Set restrictive permissions on message file
        os.chmod(admin_msg_file, 0o600)

        cat_result = subprocess.run(['cat', admin_msg_file], capture_output=True, text=True)
        subprocess.run(['mail', '-s', f'Panexplorer results session {session}', ADMIN_MAIL],
                      input=cat_result.stdout, text=True, check=True)
        try:
            subprocess.run(['service', 'postfix', 'start'], check=True)
        except subprocess.CalledProcessError:
            logger.warning("Could not start postfix service")
    


# --------------------------------------------------
# Callback
# --------------------------------------------------

def register_callbacks(app):
    du.configure_upload(app, folder=UPLOAD_DIR)

    @app.callback(
        Output("output-area", "children", allow_duplicate=True),
        Input("check-gca-button", "n_clicks"),
        State("public-genomes", "value"),
        State("session","value"),
        State("GCA_GCF", "value"),
        prevent_initial_call=True,
    )
    def check_public_genomes(n_clicks, gca_list,session,gca_gcf):
        if n_clicks == 0:
            return html.Div("No check performed yet.")

        if not validate_session_id(session):
            return html.Div("Error: Invalid session.")

        if not gca_list:
            return html.Div("Please enter at least 3 Genbank assembly accession (GCA).")

        if is_list_GCA(gca_list) == False:
            return html.Div("Please enter at least 3 Genbank assembly accession (GCA). The list is not recognized...")
        
        gca_accessions = [gca.strip() for gca in gca_list.split(",") if gca.strip()]

        # Validate each accession format
        for accession in gca_accessions:
            if not validate_gca_accession(accession):
                return html.Div(f"Invalid accession format: {accession}. Must be GCA_XXXXXX.X or GCF_XXXXXX.X")

        if len(gca_accessions) > 200:
            return html.Div("Error: maximum number of genomes exceeded (200 allowed).")
        
        rows = []
        valid_genome_count = 0
        list_of_valid_accessions = []
        os.makedirs(f"{UPLOAD_DIR}/{session}", exist_ok=True)  # Fix race condition with exist_ok=True
        

        os.makedirs(f"{session_dir}/{session}/genomes/genomes", exist_ok=True)  # Fix race condition
        dict_strains = {}   
        countries = {}
        for accession in gca_accessions:

            if gca_gcf == "GCA":
                x = re.search("^GCA_\d+(\.\d+)?$", accession)
            elif gca_gcf == "GCF":
                x = re.search("^GCF_\d+(\.\d+)?$", accession)
            if not x:
                return html.Div(f"Does not respect {gca_gcf} accession format. Must be {gca_gcf}_XXXXXX.X only")
            else:

                # cmd = [ncbi_datasets_exe, 'download', 'genome', 'accession', accession, 
                #        '--filename', f'{tmp_dir}/{accession}.zip', '--include', 'genome,gbff,protein']

                
                

                with open(f"{tmp_dir}/{accession}.json", "w") as json_file:
                    cmd = [ncbi_datasets_exe, 'summary', 'genome', 'accession', accession, "--as-json-lines"]
                    subprocess.run(cmd, stdout=json_file, check=True)

                assemblies = {}
                accession_valid = 0
                with open(f"{tmp_dir}/{accession}.json") as f:
                    for line in f:
                        data = json.loads(line)


                        acc = data["accession"]
                        if acc:
                            accession_valid = 1
                        asm = data["assembly_stats"]
                        organism = data["organism"]["organism_name"]
                        if "annotation_info" in data.keys() and "assembly_stats" in data.keys():
                            cds = data["annotation_info"]["stats"]["gene_counts"]["protein_coding"]
                            contigs = data["assembly_stats"]["number_of_scaffolds"]
                            genome_size = data["assembly_stats"]["total_sequence_length"]
                            rows.append({
                                "File name": accession,
                                "Valid": "✅",
                                "Error": "",
                                "Country": None,
                                "Number of contigs": contigs,
                                "Genome size (bp)": genome_size,
                                "CDS": cds,
                                "Stored file": accession,
                            })

                            list_of_valid_accessions.append(accession)
                            valid_genome_count += 1

                        else:
                            rows.append({
                                    "File name": accession,
                                    "Valid": "❌",
                                    "Error": "Genome is not annotated",
                                    "Country": None,
                                    "Number of contigs": None,
                                    "Genome size (bp)": None,
                                    "CDS": None,
                                    "Stored file": None,
                                })
                            continue

                if accession_valid == 0:
                    rows.append({
                                        "File name": accession,
                                        "Valid": "❌",
                                        "Error": "GCA accession not recognized",
                                        "Country": None,
                                        "Number of contigs": None,
                                        "Genome size (bp)": None,
                                        "CDS": None,
                                        "Stored file": None,
                                    })
                    continue
        
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
    def go_to_pipeline_public(n_clicks, project_name, email_address, valid_list, software, session, min_percentage_identity):
        if n_clicks == 0:
            return html.Div()

        if (not project_name or not re.match("^[A-Za-z0-9_-]+$", project_name)):
            return dbc.Alert("Error: Invalid project name. Must be alphanumeric with no spaces, underscores (_) or hyphens (-) only.", color="danger") , {"display": "block"}
        if (not email_address or not validate_email_strict(email_address)):
            return dbc.Alert("Error: Invalid email address.", color="danger") , {"display": "block"}
        if (not min_percentage_identity or not (1 <= int(min_percentage_identity) <= 100)):
            return dbc.Alert("Error: Minimum percentage identity must be between 1 and 100.", color="danger") , {"display": "block"}
        if not validate_session_id(session):
            return dbc.Alert("Error: Invalid session.", color="danger") , {"display": "block"}


        thread = threading.Thread(
            target=run_external_command,
            args=(project_name, email_address, valid_list, min_percentage_identity, session, software),
            daemon=True
        )
        thread.start()

        return dbc.Alert(
            [
                html.H4("Well done!", className="alert-heading"),
                html.P("Data have been sent to the pipeline. You will receive an email once it is complete. Data are available in the URL: "),
                #html.Hr(),
                html.A(f"{web_url}/browse?session={session}", href=f"{web_url}/browse?session={session}", target="_blank", className="alert-link"),
            ],
            color="success",
        ) , {"display": "none"}
        
    @app.callback(
        Output("input-options", "children"),
        Input("input-type", "value"),
    )
    def apply_import(input_type):
        session = str(uuid.uuid4())  # Generate secure UUID instead of random number
        if input_type == "public":
            return html.Div([
                dcc.Input(id="session", type="hidden", value=str(session)),
                html.H5("Choose the pan-genome software"),
                dcc.Dropdown(id="software", options=[{"label": "PanACoTA (faster)", "value": "panacota"}, {"label": "PGGB (Pan Genome Graph Builder)", "value": "pggb"}], value="panacota", style={"width":"300px"}),

                html.H5("Public genomes. Enter a list of assembly accessions (GCA or GCF). Must be annotated (up to 200 genomes)"),
                dcc.Dropdown(id="GCA_GCF", options=[{"label": "GCA (GenBank assembly)", "value": "GCA"}, {"label": "GCF (RefSeq assembly)", "value": "GCF"}], value="GCA", style={"width":"300px"}),
                html.Label("Restrict the analysis to either GenBank assemblies (GCA) or RefSeq assemblies (GCF)"),
                dcc.Input(id="public-genomes", type="text", placeholder="GCA_000001234.1,GCA_000005678.1", style={"width": "75%"}),
                html.Label("Coma separated list (Genbank assembly GCA,GCF)"),
                html.Button("Check accessions", id="check-gca-button", className="thin-button", n_clicks=0)
            ])
        elif input_type == "upload":
            MAX_GENOMES = 200
            return html.Div([
                dcc.Input(id="session", type="hidden", value=str(session)),
                html.H5("Choose the pan-genome software"),
                dcc.Dropdown(id="software", options=[{"label": "PanACoTA (faster)", "value": "panacota"}, {"label": "PGGB (Pan Genome Graph Builder)", "value": "pggb"}], value="panacota", style={"width":"300px"}),

                html.H5("Upload your own genomes. Must be annotated (up to 200 genomes)"),
                html.Label("Upload genbank files (accepted extension: .gb, .gbk, .gbff, .genbank). Selection of multiple files is possible. Must be annotated genomes. "),
                html.Label(f"Maximum: {MAX_GENOMES} genomes."),
                
                du.Upload(
                    id="upload-genbank",
                    text="Upload GenBank files",
                    upload_id=session,
                    max_files=80,
                    filetypes=["gb", "gbk", "gbff", "genbank"],
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

        # Process any new upload directories under UPLOAD_DIR.
        # dash_uploader creates a subfolder per upload_id (we configured upload_id=session).
        processed_any = False

        for sub in os.listdir(UPLOAD_DIR):
            subpath = os.path.join(UPLOAD_DIR, sub)
            
            # Validate session ID format before processing
            if not validate_session_id(sub):
                logger.warning("Skipping invalid session ID: %s", sub)
                continue
            
            if not os.path.isdir(subpath):
                continue
            
            # Verify path safety to prevent directory traversal
            if not is_safe_path(subpath, UPLOAD_DIR):
                logger.warning("Path outside allowed directory: %s", subpath)
                continue
                
            sentinel = os.path.join(subpath, VALIDATION_SENTINEL)
            if os.path.exists(sentinel):
                continue

            # process files in this upload folder
            for fname in os.listdir(subpath):
                fpath = os.path.join(subpath, fname)
                if os.path.isdir(fpath):
                    continue

                # sanitize name on disk
                safe_name = sanitize_filename(fname)
                safe_path = os.path.join(subpath, safe_name)
                if safe_name != fname:
                    try:
                        os.rename(fpath, safe_path)
                        fpath = safe_path
                    except Exception:
                        pass


                # check extension
                ext = os.path.splitext(fpath)[1].lstrip('.').lower()
                if ext not in ALLOWED_EXT:
                    logger.warning("Rejected upload (extension not allowed): %s", fpath)
                    try:
                        os.remove(fpath)
                    except Exception:
                        pass
                    continue

                # check size
                try:
                    size = os.path.getsize(fpath)
                except Exception:
                    size = 0


                print(safe_name + ": size: " + str(size))
                if size > MAX_UPLOAD_SIZE_BYTES:
                    logger.warning("Rejected upload (too large): %s (%d bytes)", fpath, size)
                    try:
                        os.remove(fpath)
                    except Exception:
                        pass
                    continue

                # optional magic check
                if HAS_MAGIC:
                    try:
                        mime = magic.from_file(fpath, mime=True)
                        low = str(mime).lower()
                        if not (low.startswith('text') or 'genbank' in low or 'plain' in low):
                            logger.warning("Rejected upload (magic mismatch): %s -> %s", fpath, mime)
                            try:
                                os.remove(fpath)
                            except Exception:
                                pass
                            continue
                    except Exception:
                        # if magic fails, we continue but log
                        logger.exception("magic check failed for %s", fpath)

                # optional ClamAV scan
                if HAS_PYCLAMD:
                    try:
                        cd = pyclamd.ClamdNetworkSocket()
                        scan_result = cd.scan_file(fpath)
                        if scan_result:
                            logger.warning("Infected file detected and removed: %s", fpath)
                            try:
                                os.remove(fpath)
                            except Exception:
                                pass
                            continue
                    except Exception:
                        logger.exception("ClamAV scan failed for %s", fpath)

                # set restrictive permissions
                try:
                    os.chmod(fpath, 0o600)
                except Exception:
                    pass

                processed_any = True

            # mark as processed to avoid re-checking
            try:
                open(sentinel, 'w').close()
            except Exception:
                pass

        if not uploaded_files and not processed_any:
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

        if not validate_session_id(session):
            return html.Div("Error: Invalid session.")

        filepaths = []

        session_genomes_dir = f"{session_dir}/{session}/genomes/genomes"
        os.makedirs(session_genomes_dir, exist_ok=True)

        rows = []
        valid_genome_count = 0
        
        dict_strains = {}

        upload_session_dir = f"{UPLOAD_DIR}/{session}"
        if not os.path.isdir(upload_session_dir):
            return html.Div("Error: Upload directory not found.")

        for file in os.listdir(upload_session_dir):
            original_name = os.path.basename(file)
            if file.endswith(".gb") or file.endswith(".gbk") or file.endswith(".gbff") or file.endswith(".genbank"):
                newfile = sanitize_filename(file)

                print(f"Processing uploaded file: {file} -> {newfile}")
                filepath = os.path.join(upload_session_dir, newfile)
                filepaths.append(filepath)

                
                with open(os.path.join(upload_session_dir, file)) as infile, open(os.path.join(upload_session_dir, newfile+".2"), "w") as outfile:
                    for line in infile:
                        outfile.write(fix_locus_line(line))
                
                os.rename(os.path.join(upload_session_dir, newfile+".2"), filepath)
                original_name = os.path.basename(filepath)

                if file != newfile:
                    os.remove(os.path.join(upload_session_dir, file))

                # skip if file already in table
                if any(r["Stored file"] == original_name for r in rows):
                    continue

                #records = list(SeqIO.parse(filepath, "genbank"))
                #summary = summarize_records(records, original_name, original_name)
                #rows.append(summary)

                try:

                    records = list(SeqIO.parse(filepath, "genbank"))

                    if not records:
                        raise ValueError("No GenBank records found")

                    contigs = len(records)
                    genome_size = sum(len(r.seq) for r in records)
                    country = ""
                    for r in records:
                        for feature in r.features:
                            if feature.type == "source":
                                if "country" in feature.qualifiers:
                                    country = feature.qualifiers.get("country", ["unknown"])[0]
                                elif "geo_loc_name" in feature.qualifiers:
                                    country = feature.qualifiers.get("geo_loc_name", ["unknown"])[0]

                    genes = sum(1 for r in records for f in r.features if f.type == "gene")
                    cds = sum(1 for r in records for f in r.features if f.type == "CDS")

                    if cds < 10:
                        rows.append({
                            "File name": original_name,
                            "Valid": "❌",
                            "Error": "Genome is not annotated",
                            "Country": None,
                            "Number of contigs": None,
                            "Genome size (bp)": None,
                            "CDS": None,
                            "Stored file": None,
                            })
                        continue
                    
                    # Check for locus_tag or protein_id identifiers
                    has_identifiers, identifier_error = has_valid_gene_identifiers(records)
                    if not has_identifiers:
                        rows.append({
                            "File name": original_name,
                            "Valid": "❌",
                            "Error": identifier_error,
                            "Country": None,
                            "Number of contigs": None,
                            "Genome size (bp)": None,
                            "CDS": None,
                            "Stored file": None,
                            })
                        continue
                    
                    rows.append({
                        "File name": original_name,
                        "Valid": "✅",
                        "Error": "",
                        "Country": country,
                        "Number of contigs": contigs,
                        "Genome size (bp)": genome_size,
                        "CDS": cds,
                        "Stored file": original_name,
                    })

                    valid_genome_count += 1

                except Exception as e:
                    rows.append({
                        "File name": original_name,
                        "Valid": "❌",
                        "Error": str(e),
                        "Country": None,
                        "Number of contigs": None,
                        "Genome size (bp)": None,
                        "CDS": None,
                        "Stored file": None,
                    })

        

        df = pd.DataFrame(rows)
        df.to_csv(f"{session_dir}/{session}/summary_upload.csv", sep="\t", index=False)
        

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
    




