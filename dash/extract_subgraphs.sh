#!/bin/bash

# Function to display usage information
usage() {
    echo "Usage: $0 -i <GFA_FILE> -o <OUTPUT_FILE> [-n <NODE_ID>] [-l <NODE_LIST>] [-p <PATHS_TO_EXTRACT>] [-c <NODE_STEPS>] [-L <BP_STEPS>] [-d <DISTANCE>] [-B <BED_FILE>] [--odgi] [--vg] [--bandage]"
    echo "  -i  Input GFA file"
    echo "  -o  Output file"
    echo "  -n  Node ID (for -n flag)"
    echo "  -l  Node list (comma-separated) (for -l flag)"
    echo "  -d  Distance for extraction (default: 0)"
    echo "  -p  Paths to extract (comma-separated list)"
    echo "  -c  Node steps (for -c flag)"
    echo "  -L  BP steps (for -L flag)"
    echo "  -B  BED file containing gene coordinates to inject into the graph"
    echo "  --odgi  Run odgi sort and viz"
    echo "  --vg  Run vg view and dot"
    echo "  --bandage Run Bandage"
    exit 1
}

# Initialize variables
GFA_FILE=""
OUTPUT_FILE=""
NODE_ID=""
NODE_LIST=""
PATHS_TO_EXTRACT=""
NODE_STEPS=""
BP_STEPS=""
BED_FILE=""
DISTANCE=0
RUN_ODGI=false
RUN_VG=false
RUN_BANDAGE=false

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -i) GFA_FILE=$2; shift ;;
        -o) OUTPUT_FILE=$2; shift ;;
        -n) NODE_ID=$2; shift ;;
        -l) NODE_LIST=$2; shift ;;
        -d) DISTANCE=$2; shift ;;
        -p) PATHS_TO_EXTRACT=$2; shift ;;
        -c) NODE_STEPS=$2; shift ;;
        -L) BP_STEPS=$2; shift ;;
        -B) BED_FILE=$2; shift ;;
        --odgi) RUN_ODGI=true ;;
        --vg) RUN_VG=true ;;
        --bandage) RUN_BANDAGE=true ;;
        *) usage ;;
    esac
    shift
done

# Verify required arguments are provided
if [[ -z $GFA_FILE || -z $OUTPUT_FILE ]]; then
    usage
fi

# Verify mutually exclusive flags
if [[ -n $NODE_ID && -n $NODE_LIST ]]; then
    echo "Error: You cannot use both -n and -l flags at the same time."
    exit 1
fi

if [[ -n $NODE_STEPS && -n $BP_STEPS ]]; then
    echo "Error: You cannot use both -c and -L flags at the same time."
    exit 1
fi

# ---------------------------------------------------------
# Read executable paths from panexplorer_config.yaml
# ---------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/panexplorer_config.yaml"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Warning: panexplorer_config.yaml not found at $CONFIG_FILE — using default executable names."
    VG_EXE="vg"
    ODGI_EXE="odgi"
    BANDAGE_EXE="Bandage"
else
    VG_EXE=$(python3 -c "import yaml; d=yaml.safe_load(open('$CONFIG_FILE')); print(d.get('vg_exe','vg'))" 2>/dev/null || echo "vg")
    ODGI_EXE=$(python3 -c "import yaml; d=yaml.safe_load(open('$CONFIG_FILE')); print(d.get('odgi_exe','odgi'))" 2>/dev/null || echo "odgi")
    BANDAGE_EXE=$(python3 -c "import yaml; d=yaml.safe_load(open('$CONFIG_FILE')); print(d.get('bandage_exe','Bandage'))" 2>/dev/null || echo "Bandage")
fi
echo "Executables: vg=$VG_EXE  odgi=$ODGI_EXE  bandage=$BANDAGE_EXE"

# ---------------------------------------------------------
# NEW: Logging Setup
# ---------------------------------------------------------
LOG_FILE="${OUTPUT_FILE}.log"

# Create the log file (overwrite if exists)
: > "$LOG_FILE"

# Redirect all stdout (1) and stderr (2) to the log file AND the console (tee)
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=========================================="
echo "Starting Subgraph Extraction: $(date)"
echo "Log file location: $LOG_FILE"
echo "=========================================="

# Create temporary files for node list and paths to extract
NODE_LIST_FILE=$(mktemp)
PATHS_FILE=$(mktemp)

# Function to cleanup temporary files
cleanup() {
    rm -f "$NODE_LIST_FILE"
    rm -f "$PATHS_FILE"
}

# Ensure cleanup is done on script exit
trap cleanup EXIT

# ---------------------------------------------------------
# 1. Prepare the Graph (GFA -> OG)
# ---------------------------------------------------------
INPUT_DIR=$(dirname "$GFA_FILE")
INPUT_NAME=$(basename "$GFA_FILE" .gfa)
OG_FILE="${INPUT_DIR}/${INPUT_NAME}.og"

# If the .og file doesn't exist, build it from GFA
if [[ ! -f "$OG_FILE" ]]; then
    echo "[$(date)] Building optimized graph (.og) from GFA..."
    "$ODGI_EXE" build -g "$GFA_FILE" -o "$OG_FILE"
fi

# The graph we will perform operations on
WORKING_OG="$OG_FILE"


# ---------------------------------------------------------
# 3. Extract Subgraph
# ---------------------------------------------------------

echo "[$(date)] Extracting genome list..."
"$ODGI_EXE" paths -i "$WORKING_OG" -L | awk -F '#' '{print $1}' | sort | uniq > "${OUTPUT_FILE%.og}_genomes.txt"

# Convert NODE_LIST to file if provided
if [[ -n $NODE_LIST ]]; then
    IFS=',' read -ra ADDR <<< "$NODE_LIST"
    for i in "${ADDR[@]}"; do
        echo "$i" >> "$NODE_LIST_FILE"
    done
fi

# Convert PATHS_TO_EXTRACT to file if provided
if [[ -n $PATHS_TO_EXTRACT ]]; then
    # Get all path names present in the graph
    GRAPH_PATHS_FILE=$(mktemp)
    "$ODGI_EXE" paths -i "$WORKING_OG" -L > "$GRAPH_PATHS_FILE"
    echo "[$(date)] Graph contains $(wc -l < "$GRAPH_PATHS_FILE") paths."

    # For each requested strain, grep the graph path list for a matching line
    # This avoids any hardcoded naming convention — we let the graph tell us
    # the exact path identifier(s) that contain the strain name.
    if [[ -f "$PATHS_TO_EXTRACT" ]]; then
        REQUESTED_STRAINS=()
        while IFS= read -r line; do
            [[ -n "$line" ]] && REQUESTED_STRAINS+=("$line")
        done < "$PATHS_TO_EXTRACT"
    else
        IFS=',' read -ra REQUESTED_STRAINS <<< "$PATHS_TO_EXTRACT"
    fi

    MATCHED=0
    for strain in "${REQUESTED_STRAINS[@]}"; do
        strain="${strain// /}"          # trim spaces
        [[ -z "$strain" ]] && continue
        # grep for lines that contain the strain name (fixed-string, case-sensitive)
        matches=$(grep -F "$strain" "$GRAPH_PATHS_FILE" || true)
        if [[ -z "$matches" ]]; then
            echo "  Warning: no graph path found matching '$strain' — skipping."
        else
            echo "$matches" >> "$PATHS_FILE"
            count=$(echo "$matches" | wc -l)
            echo "  Matched $count path(s) for '$strain'."
            MATCHED=$((MATCHED + count))
        fi
    done

    rm -f "$GRAPH_PATHS_FILE"
    echo "[$(date)] Total matched paths: $MATCHED"

    # If nothing matched, clear PATHS_TO_EXTRACT so odgi extract won't use -p
    if [[ $MATCHED -eq 0 ]]; then
        echo "  Warning: no paths matched — proceeding without path filter."
        PATHS_TO_EXTRACT=""
    fi
fi

# Build the odgi extract command
COMMAND="$ODGI_EXE extract -i $WORKING_OG -o $OUTPUT_FILE -d $DISTANCE"

if [[ -n $NODE_ID ]]; then
    COMMAND+=" -n $NODE_ID"
fi

if [[ -n $NODE_LIST ]]; then
    COMMAND+=" -l $NODE_LIST_FILE"
fi

if [[ -n $PATHS_TO_EXTRACT ]]; then
    COMMAND+=" -p $PATHS_FILE"
fi

if [[ -n $NODE_STEPS ]]; then
    COMMAND+=" -c $NODE_STEPS"
fi

if [[ -n $BP_STEPS ]]; then
    COMMAND+=" -L $BP_STEPS"
fi

# Execute the odgi extract command
echo "[$(date)] Executing command: $COMMAND"
$COMMAND
WORKING_OG="$OUTPUT_FILE"
# ---------------------------------------------------------
# 2. Inject Genes (Renaming Path -> procbed -> inject)
# ---------------------------------------------------------
if [[ -n $BED_FILE ]]; then
    echo "[$(date)] Processing BED file..."
    
    # 1. Define filenames
    BED_RENAMED="${BED_FILE}.renamed.bed"
    BED_PROCESSED="${BED_FILE}.proc"
    INJECTED_OG="${OUTPUT_FILE%.og}.injected.og"
    
    # 2. CUSTOM RENAMING STEP
    # Goal: Transform "Genus_species_STRAIN" -> "Genus_species_STRAIN#1#STRAIN"
    echo "[$(date)] Renaming BED paths to match Graph format..."
    
    awk -v OFS="\t" '{
        original = $1;
        
        # Create the suffix by removing "Genus_species_" from the start
        suffix = original;
        sub(/^Genus_species_/, "", suffix);
        
        # Construct the new path: Original + #1# + Suffix
        # Example: Genus_species_X... -> Genus_species_X...#1#X...
        new_path = original "#1#" suffix;
        
        # Update column 1 and print
        $1 = new_path;
        print $0;
    }' "$BED_FILE" > "$BED_RENAMED"

    echo "Renamed BED sample line: $(head -n 1 "$BED_RENAMED")"
    
    # 3. Step A: odgi procbed (using the RENAMED bed file)
    echo "[$(date)] Running odgi procbed..."
    "$ODGI_EXE" procbed -i "$WORKING_OG" -b "$BED_RENAMED" > "$BED_PROCESSED"
    
    # 4. Step B: odgi inject
    echo "[$(date)] Running odgi inject..."
    "$ODGI_EXE" inject -i "$WORKING_OG" -b "$BED_PROCESSED" -o "$INJECTED_OG"
    
    # Update our working graph to be the injected one
    WORKING_OG="$INJECTED_OG"
    echo "Injection complete. Using graph: $WORKING_OG"
fi
# ---------------------------------------------------------
# 4. Visualization
# ---------------------------------------------------------


# Run odgi sort and viz if --odgi flag is used
if $RUN_ODGI; then
    echo "[$(date)] Generating ODGI visualization..."
    ODGI_PNG="${OUTPUT_FILE%.og}_odgi.png"
    "$ODGI_EXE" sort -i "$OUTPUT_FILE" -o - -O | "$ODGI_EXE" viz -i - -o "$ODGI_PNG" -s "#" -M "${OUTPUT_FILE%.og}_genomes.txt"
    echo "ODGI PNG: $ODGI_PNG"
fi

# Run vg view and dot if --vg flag is used
if $RUN_VG; then
    echo "[$(date)] Generating VG visualization..."
    SUBGRAPH_GFA="${OUTPUT_FILE%.og}.gfa"
    if [[ ! -f "$SUBGRAPH_GFA" ]]; then
        "$ODGI_EXE" view -i "$OUTPUT_FILE" -g > "$SUBGRAPH_GFA"
    fi
    "$VG_EXE" view -g "$SUBGRAPH_GFA" -dpn - | dot -Tsvg -o "${OUTPUT_FILE%.og}_vg.svg"
    echo "VG SVG: ${OUTPUT_FILE%.og}_vg.svg"
fi

if $RUN_BANDAGE; then
    echo "[$(date)] Generating Bandage visualization..."
    SUBGRAPH_GFA="${OUTPUT_FILE%.og}.gfa"
    if [[ ! -f "$SUBGRAPH_GFA" ]]; then
        "$ODGI_EXE" view -i "$OUTPUT_FILE" -g > "$SUBGRAPH_GFA"
    fi
    "$BANDAGE_EXE" image "$SUBGRAPH_GFA" "${OUTPUT_FILE%.og}_bandage.svg" --names --lengths --depth --colour random --centre --fontsize 12 
    echo "Bandage SVG: ${OUTPUT_FILE%.og}_bandage.svg"
fi 

"$ODGI_EXE" paths -i "$OUTPUT_FILE" -L > "${OUTPUT_FILE%.og}_paths.txt"
echo "=========================================="
echo "Finished Successfully: $(date)"
echo "=========================================="