#!/bin/bash

# extract_subgraph_sequences.sh
# Usage: ./extract_subgraph_sequences.sh -f input.fasta -g graph.gfa -d output_dir -p "path1,path2" -n 2 -L 1000 -r long

usage() {
    echo "Usage: $0 -f <fasta_file> -g <gfa_file> -d <output_dir> [-p <paths>] [-n <node_steps>] [-L <bp_steps>] -r <read_type: short|long>"
    exit 1
}

# Initialize variables
FASTA_FILE=""
GFA_FILE=""
OUTPUT_DIR=""
CONTEXT_STEPS="" # Default handled in logic
CONTEXT_BP=""
READ_TYPE="long"
PATHS=""

# Parse arguments
while getopts ":f:g:d:p:n:L:r:h" opt; do
    case ${opt} in
        f ) FASTA_FILE=$OPTARG ;;
        g ) GFA_FILE=$OPTARG ;;
        d ) OUTPUT_DIR=$OPTARG ;;
        p ) PATHS=$OPTARG ;;
        n ) CONTEXT_STEPS=$OPTARG ;;
        L ) CONTEXT_BP=$OPTARG ;;
        r ) READ_TYPE=$OPTARG ;;
        h ) usage ;;
        * ) usage ;;
    esac
done

if [[ -z "$FASTA_FILE" || -z "$GFA_FILE" || -z "$OUTPUT_DIR" ]]; then
    echo "Error: Missing required arguments."
    usage
fi

# Locate helper scripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROCESS_GAF_SCRIPT="${SCRIPT_DIR}/process_gaf.py"
EXTRACT_SUBGRAPH_SCRIPT="${SCRIPT_DIR}/extract_subgraphs.sh"

# ---------------------------------------------------------
# Read executable paths from panexplorer_config.yaml
# ---------------------------------------------------------
CONFIG_FILE="${SCRIPT_DIR}/panexplorer_config.yaml"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Warning: panexplorer_config.yaml not found — using default executable names."
    VG_EXE="vg"
else
    VG_EXE=$(python3 -c "import yaml; d=yaml.safe_load(open('$CONFIG_FILE')); print(d.get('vg_exe','vg'))" 2>/dev/null || echo "vg")
fi
echo "vg executable: $VG_EXE"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"
GAF_FILE="$OUTPUT_DIR/alignment.gaf"

echo "=========================================="
echo "Starting Sequence Alignment Extraction"
echo "Fasta: $FASTA_FILE"
echo "Read Type: $READ_TYPE"
echo "=========================================="

# Derive BASE_NAME once — used for index checks and alignment
BASE_NAME="${GFA_FILE%.*}"

# ---------------------------------------------------------
# 0. Ensure vg giraffe indexes exist (build if missing)
# ---------------------------------------------------------
# Common files required by both workflows
GBZ_FILE="${BASE_NAME}.giraffe.gbz"
DIST_FILE="${BASE_NAME}.dist"
TMP_GIRAFFE="${BASE_NAME}_tmp_giraffe"

if [ "$READ_TYPE" == "short" ]; then
    # Short-read giraffe needs: .giraffe.gbz  .dist  .shortread.withzip.min  .shortread.zipcodes
    INDEX_MISSING=false
    for f in "$GBZ_FILE" "$DIST_FILE" \
              "${BASE_NAME}.shortread.withzip.min" \
              "${BASE_NAME}.shortread.zipcodes"; do
        if [[ ! -f "$f" ]]; then
            echo "  Missing index: $f"
            INDEX_MISSING=true
        fi
    done

    if $INDEX_MISSING; then
        echo "[$(date)] Building short-read giraffe indexes..."
        mkdir -p "$TMP_GIRAFFE"
        "$VG_EXE" autoindex \
            --workflow sr-giraffe \
            --gfa "$GFA_FILE" \
            --prefix "$BASE_NAME" \
            --tmp-dir "$TMP_GIRAFFE"
        if [[ $? -ne 0 ]]; then
            echo "Error: vg autoindex (sr-giraffe) failed."
            exit 1
        fi
        echo "[$(date)] Short-read indexes built successfully."
    else
        echo "[$(date)] Short-read giraffe indexes already present — skipping autoindex."
    fi
else
    # Long-read giraffe needs: .giraffe.gbz  .dist  .longread.zipcodes
    INDEX_MISSING=false
    for f in "$GBZ_FILE" "$DIST_FILE" \
              "${BASE_NAME}.longread.zipcodes"; do
        if [[ ! -f "$f" ]]; then
            echo "  Missing index: $f"
            INDEX_MISSING=true
        fi
    done

    if $INDEX_MISSING; then
        echo "[$(date)] Building long-read giraffe indexes..."
        mkdir -p "$TMP_GIRAFFE"
        "$VG_EXE" autoindex \
            --workflow lr-giraffe \
            --gfa "$GFA_FILE" \
            --prefix "$BASE_NAME" \
            --tmp-dir "$TMP_GIRAFFE"
        if [[ $? -ne 0 ]]; then
            echo "Error: vg autoindex (lr-giraffe) failed."
            exit 1
        fi
        echo "[$(date)] Long-read indexes built successfully."
    else
        echo "[$(date)] Long-read giraffe indexes already present — skipping autoindex."
    fi
fi

# ---------------------------------------------------------
# 1. Align Sequences to Graph
# ---------------------------------------------------------
if [ "$READ_TYPE" == "short" ]; then
    echo "Aligning using vg giraffe sr..."
    "$VG_EXE" giraffe -Z "${BASE_NAME}.giraffe.gbz" -z "${BASE_NAME}.shortread.zipcodes" -d "${BASE_NAME}.dist" -f "$FASTA_FILE" -o gaf -M 50 -c 500 -C 1000 --cluster-score 1000 -E -b default > "$GAF_FILE"
else
    echo "Aligning using vg giraffe lr..."
    "$VG_EXE" giraffe -Z "${BASE_NAME}.giraffe.gbz" -z "${BASE_NAME}.longread.zipcodes" -d "${BASE_NAME}.dist" -f "$FASTA_FILE" -o gaf -M 50 -c 500 -C 1000 --cluster-score 1000 -E -b hifi > "$GAF_FILE"
fi

if [[ ! -s "$GAF_FILE" ]]; then
    echo "Error: Alignment produced empty GAF file."
    exit 1
fi

# ---------------------------------------------------------
# 2. Process GAF to identify Hits
# ---------------------------------------------------------
echo "Processing GAF file to extract hits..."
if [ -f "$PROCESS_GAF_SCRIPT" ]; then
    python3 "$PROCESS_GAF_SCRIPT" "$GAF_FILE" "$OUTPUT_DIR"
else
    echo "Error: process_gaf.py not found at $PROCESS_GAF_SCRIPT"
    exit 1
fi

# ---------------------------------------------------------
# 3. Extract Subgraphs for every hit in hits_info.tsv
# ---------------------------------------------------------
# hits_info.tsv columns (tab-separated, written by process_gaf.py):
#   1. hit_name   – unique alignment name
#   2. num_nodes  – number of unique nodes in this hit
#   3. start_node – numerically smallest node ID
#   4. end_node   – numerically largest node ID
#   5. nodes      – comma-separated list of all node IDs
# ---------------------------------------------------------
echo "Extracting subgraphs for hits..."
HITS_INFO="$OUTPUT_DIR/hits_info.tsv"

if [[ ! -f "$HITS_INFO" ]]; then
    echo "Error: hits_info.tsv not found in $OUTPUT_DIR — process_gaf.py may have failed."
    exit 1
fi

NB_HITS=$(tail -n +2 "$HITS_INFO" | wc -l)
echo "Found $NB_HITS hit(s) in hits_info.tsv"

if [[ "$NB_HITS" -eq 0 ]]; then
    echo "No hits to process. Exiting."
    exit 0
fi

# Process each hit — skip the header line with tail -n +2
tail -n +2 "$HITS_INFO" | while IFS=$'\t' read -r HIT_NAME NUM_NODES START_NODE END_NODE NODES; do

    echo "------------------------------------------"
    echo "Hit: $HIT_NAME"
    echo "  Nodes  : $NUM_NODES  ($START_NODE ... $END_NODE)"
    echo "  Node list: $NODES"

    if [[ -z "$NODES" ]]; then
        echo "  Warning: empty node list, skipping."
        continue
    fi

    OUTPUT_PREFIX="$OUTPUT_DIR/$HIT_NAME"

    # Build extraction command arguments
    CMD_ARGS=(
        "-i" "$GFA_FILE"
        "-o" "${OUTPUT_PREFIX}.og"
        "-l" "$NODES"
    )

    if [[ -n "$PATHS" ]]; then
        CMD_ARGS+=("-p" "$PATHS")
    fi

    # Context priority: BP (-L) > Steps (-c) > default 1 node step
    if [[ -n "$CONTEXT_BP" ]]; then
        CMD_ARGS+=("-L" "$CONTEXT_BP")
        echo "  Context: $CONTEXT_BP bp"
    elif [[ -n "$CONTEXT_STEPS" ]]; then
        CMD_ARGS+=("-c" "$CONTEXT_STEPS")
        echo "  Context: $CONTEXT_STEPS node steps"
    else
        CMD_ARGS+=("-c" "1")
        echo "  Context: default (1 node step)"
    fi

    # Always produce both odgi PNG and Bandage SVG visualizations
    CMD_ARGS+=("--odgi" "--bandage")

    echo "  Running: bash $EXTRACT_SUBGRAPH_SCRIPT ${CMD_ARGS[*]}"
    bash "$EXTRACT_SUBGRAPH_SCRIPT" "${CMD_ARGS[@]}"

    if [[ $? -ne 0 ]]; then
        echo "  Warning: extraction failed for hit '$HIT_NAME'."
        continue
    fi

    echo "  Done -> ${OUTPUT_PREFIX}_odgi.png  |  ${OUTPUT_PREFIX}_bandage.svg"

done

echo "=========================================="
echo "All hits processed."
echo "Results in: $OUTPUT_DIR"