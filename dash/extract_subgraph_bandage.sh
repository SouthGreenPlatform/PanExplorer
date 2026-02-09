#!/bin/bash

# extract_subgraph_bandage.sh
# Usage: ./extract_subgraph_bandage.sh -f input.fasta -g graph.gfa -d output_dir -p "path1,path2" [options]

usage() {
    echo "Usage: $0 -f <fasta_file> -g <gfa_file> -d <output_dir> [-p <paths>] [-n <node_steps>] [-L <bp_steps>] [--topn <N>] [BLAST options] [query path options]"
    exit 1
}

# Initialize variables
FASTA_FILE=""
GFA_FILE=""
OUTPUT_DIR=""
CONTEXT_STEPS="" 
CONTEXT_BP=""
PATHS=""
BLAST_OPTS=""
TOPN=""
QPATH_OPTS=""

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -f) FASTA_FILE="$2"; shift ;;
        -g) GFA_FILE="$2"; shift ;;
        -d) OUTPUT_DIR="$2"; shift ;;
        -p) PATHS="$2"; shift ;;
        -n) CONTEXT_STEPS="$2"; shift ;;
        -L) CONTEXT_BP="$2"; shift ;;
        --blastp) BLAST_OPTS="$BLAST_OPTS --blastp \"$2\""; shift ;;
        --alfilter) BLAST_OPTS="$BLAST_OPTS --alfilter $2"; shift ;;
        --qcfilter) BLAST_OPTS="$BLAST_OPTS --qcfilter $2"; shift ;;
        --ifilter) BLAST_OPTS="$BLAST_OPTS --ifilter $2"; shift ;;
        --evfilter) BLAST_OPTS="$BLAST_OPTS --evfilter $2"; shift ;;
        --bsfilter) BLAST_OPTS="$BLAST_OPTS --bsfilter $2"; shift ;;
        --pathnodes) QPATH_OPTS="$QPATH_OPTS --pathnodes $2"; shift ;;
        --minpatcov) QPATH_OPTS="$QPATH_OPTS --minpatcov $2"; shift ;;
        --minhitcov) QPATH_OPTS="$QPATH_OPTS --minhitcov $2"; shift ;;
        --minmeanid) QPATH_OPTS="$QPATH_OPTS --minmeanid $2"; shift ;;
        --maxevprod) QPATH_OPTS="$QPATH_OPTS --maxevprod $2"; shift ;;
        --minpatlen) QPATH_OPTS="$QPATH_OPTS --minpatlen $2"; shift ;;
        --maxpatlen) QPATH_OPTS="$QPATH_OPTS --maxpatlen $2"; shift ;;
        --minlendis) QPATH_OPTS="$QPATH_OPTS --minlendis $2"; shift ;;
        --maxlendis) QPATH_OPTS="$QPATH_OPTS --maxlendis $2"; shift ;;
        --topn) TOPN="$2"; shift ;;
        -h) usage ;;
        *) 
            # If unexpected args, create error
            echo "Unknown parameter: $1"
            usage 
            ;;
    esac
    shift
done

if [[ -z "$FASTA_FILE" || -z "$GFA_FILE" || -z "$OUTPUT_DIR" ]]; then
    echo "Error: Missing required arguments."
    usage
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROCESS_BANDAGE_SCRIPT="${SCRIPT_DIR}/process_bandage_hits.py"
EXTRACT_SUBGRAPH_SCRIPT="${SCRIPT_DIR}/extract_subgraphs.sh"

mkdir -p "$OUTPUT_DIR"
OUTPUT_PREFIX="$OUTPUT_DIR/bandage_out"

# 1. Run Bandage querypaths
echo "Running Bandage querypaths..."
# We use eval to handle quotes properly if needed, but array is safer.
# However, BLAST_OPTS is a string.

CMD="Bandage querypaths \"$GFA_FILE\" \"$FASTA_FILE\" \"$OUTPUT_PREFIX\" $QPATH_OPTS --hitsfasta $BLAST_OPTS"
echo "Command: $CMD"
eval $CMD

TSV_FILE="${OUTPUT_PREFIX}.tsv"
if [[ ! -s "$TSV_FILE" ]]; then
    echo "Error: Bandage did not produce a TSV file or file is empty."
    # If standard error has info, it might be in console output.
    exit 1
fi

# 2. Process TSV 
echo "Processing Bandage output..."
if [[ -n "$TOPN" ]]; then
    python3 "$PROCESS_BANDAGE_SCRIPT" "$TSV_FILE" "$OUTPUT_DIR" "$TOPN"
else
    python3 "$PROCESS_BANDAGE_SCRIPT" "$TSV_FILE" "$OUTPUT_DIR"
fi

# 3. Extract Subgraphs & Generate Manifest
echo "Extracting subgraphs for hits..."
JSON_FILE="$OUTPUT_DIR/hits.json"
echo "[" > "$JSON_FILE"
FIRST_ENTRY=true

# Iterate through hit files
# Handle case with no matches
shopt -s nullglob
FILES=("$OUTPUT_DIR"/*_hit.txt)

for NODE_FILE in "${FILES[@]}"; do
    
    NODES=$(head -n 1 "$NODE_FILE")
    HIT_NAME=$(basename "$NODE_FILE" _hit.txt)
    OUTPUT_PREFIX_HIT="$OUTPUT_DIR/$HIT_NAME"
    echo "Processing hit: $HIT_NAME"

    CMD_ARGS=(
        "-i" "$GFA_FILE"
        "-o" "${OUTPUT_PREFIX_HIT}.og"
        "-l" "$NODES"
        "--odgi"
        "--bandage"
    )

    if [[ -n "$PATHS" ]]; then
        CMD_ARGS+=("-p" "$PATHS")
    fi

    if [[ -n "$CONTEXT_BP" ]]; then
        CMD_ARGS+=("-L" "$CONTEXT_BP")
    elif [[ -n "$CONTEXT_STEPS" ]]; then
        CMD_ARGS+=("-c" "$CONTEXT_STEPS")
    else
        CMD_ARGS+=("-c" "1")
    fi

    bash "$EXTRACT_SUBGRAPH_SCRIPT" "${CMD_ARGS[@]}"

    if [ "$FIRST_ENTRY" = true ]; then
        FIRST_ENTRY=false
    else
        echo "," >> "$JSON_FILE"
    fi
    
    ODGI_IMG="${HIT_NAME}_odgi.png"
    BANDAGE_IMG="${HIT_NAME}_bandage.svg"
    
    # Extract metadata using python for safe JSON formatting
    # We rely on process_bandage_hits.py having created hits_metadata.json
    # We use a small python snippet to extract the object for this hit
    
    PYTHON_JSON_EXTRACT="
import json, sys
try:
    with open('$OUTPUT_DIR/hits_metadata.json') as f:
        data = json.load(f)
    hit = data.get('$HIT_NAME', {})
    hit['odgi_image'] = '$ODGI_IMG'
    hit['bandage_image'] = '$BANDAGE_IMG'
    print(json.dumps(hit))
except:
    print('{}')
"
    HIT_JSON=$(python3 -c "$PYTHON_JSON_EXTRACT")
    echo "$HIT_JSON" >> "$JSON_FILE"

done

echo "]" >> "$JSON_FILE"
echo "Extraction complete. Manifest saved to $JSON_FILE"
