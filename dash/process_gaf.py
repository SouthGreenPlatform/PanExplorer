import os
import sys
import json


def parse_nodes_from_path(path):
    """
    Extract node IDs from a GAF path string such as:
      >564722>564723<564724>564725
    Returns a list of node ID strings in traversal order.
    """
    nodes = []
    current = ""
    for ch in path:
        if ch in ('>', '<'):
            if current:
                nodes.append(current)
            current = ""
        else:
            current += ch
    if current:
        nodes.append(current)
    return nodes


def process_gaf_file(gaf_file, output_directory):
    """
    Parse a GAF alignment file and produce per-hit outputs:

    GAF format (tab-separated, 12 mandatory columns):
      col 0  query name
      col 1  query length
      col 2  query start
      col 3  query end
      col 4  strand (+/-)
      col 5  path  (e.g. >564722>564723<564724)
      col 6  path length
      col 7  path start
      col 8  path end
      col 9  residue matches
      col 10 alignment block length
      col 11 mapping quality
      col 12+ optional tags

    Lines starting with '@' are SAM-style header lines and are skipped.

    Outputs written to output_directory:
      {hit_name}_hit.txt      — comma-separated node IDs (numerically sorted)
      {hit_name}.gaf          — the raw GAF line for that hit
      hits_info.tsv           — TSV summary used by the shell script:
                                hit_name | num_nodes | start_node | end_node | nodes
      hits_metadata.json      — same structure as process_bandage_hits.py output,
                                with method='vg_giraffe' and GAF-specific fields
    """
    os.makedirs(output_directory, exist_ok=True)

    hits      = {}   # unique_name -> {'gaf': str, 'nodes': [str, ...]}
    name_seen = {}   # original name -> count of occurrences so far

    with open(gaf_file, 'r') as fh:
        for raw_line in fh:
            line = raw_line.rstrip('\n')

            # Skip SAM-style header lines (@HD, @SQ, @RG, ...)
            if line.startswith('@') or not line.strip():
                continue

            fields = line.split('\t')

            # Need at least 6 columns to have a path
            if len(fields) < 6:
                print(f"Warning: skipping malformed line (only {len(fields)} fields): {line[:80]}")
                continue

            read_name = fields[0]
            path      = fields[5]

            # Build a unique hit name for duplicate read names
            if read_name in name_seen:
                name_seen[read_name] += 1
                unique_name = f"{read_name}_{name_seen[read_name]}"
            else:
                name_seen[read_name] = 0
                unique_name = read_name

            nodes = parse_nodes_from_path(path)

            hits[unique_name] = {
                'gaf':   line,
                'nodes': nodes,
            }

    if not hits:
        print("Warning: no alignment records found in GAF file.")
        # Still create empty output files so the shell script doesn't fail
        with open(os.path.join(output_directory, "hits_info.tsv"), 'w') as fh:
            fh.write("hit_name\tnum_nodes\tstart_node\tend_node\tnodes\n")
        with open(os.path.join(output_directory, "hits_metadata.json"), 'w') as fh:
            json.dump({}, fh)
        return

    hits_info_path    = os.path.join(output_directory, "hits_info.tsv")
    metadata_path     = os.path.join(output_directory, "hits_metadata.json")
    hits_metadata     = {}

    with open(hits_info_path, 'w') as info_fh:
        info_fh.write("hit_name\tnum_nodes\tstart_node\tend_node\tnodes\n")

        for hit_name, data in hits.items():
            raw_line = data['gaf']
            fields   = raw_line.split('\t')

            # GAF mandatory columns
            query_name     = fields[0]  if len(fields) > 0  else hit_name
            query_length   = fields[1]  if len(fields) > 1  else "N/A"
            query_start    = fields[2]  if len(fields) > 2  else "N/A"
            query_end      = fields[3]  if len(fields) > 3  else "N/A"
            strand         = fields[4]  if len(fields) > 4  else "N/A"
            path_str       = fields[5]  if len(fields) > 5  else "N/A"
            path_length    = fields[6]  if len(fields) > 6  else "N/A"
            path_start     = fields[7]  if len(fields) > 7  else "N/A"
            path_end       = fields[8]  if len(fields) > 8  else "N/A"
            residue_matches= fields[9]  if len(fields) > 9  else "N/A"
            block_length   = fields[10] if len(fields) > 10 else "N/A"
            mapq           = fields[11] if len(fields) > 11 else "N/A"

            # Optional tags (key:type:value)
            tags = {}
            for tag_field in fields[12:]:
                parts = tag_field.split(':')
                if len(parts) == 3:
                    tags[parts[0]] = parts[2]

            # Deduplicate and sort node IDs numerically
            sorted_nodes = sorted(
                set(data['nodes']),
                key=lambda x: int(x) if x.isdigit() else x
            )
            node_str = ",".join(sorted_nodes)
            first    = sorted_nodes[0]  if sorted_nodes else "N/A"
            last     = sorted_nodes[-1] if sorted_nodes else "N/A"

            # Pre-compute expected image filenames (populated by extract_subgraphs.sh later)
            odgi_image    = f"{hit_name}_odgi.png"
            bandage_image = f"{hit_name}_bandage.svg"

            # Write per-hit node file (used by shell script)
            node_file = os.path.join(output_directory, f"{hit_name}_hit.txt")
            with open(node_file, 'w') as nf:
                nf.write(node_str + "\n")

            # Write per-hit GAF line (one alignment per file)
            gaf_out = os.path.join(output_directory, f"{hit_name}.gaf")
            with open(gaf_out, 'w') as gf:
                gf.write(raw_line + "\n")

            # hits_info.tsv row — used by the shell script for node-list iteration
            info_fh.write(f"{hit_name}\t{len(sorted_nodes)}\t{first}\t{last}\t{node_str}\n")

            # hits_metadata.json entry — mirrors process_bandage_hits.py structure
            # Fields absent in GAF are set to empty string for UI compatibility.
            hits_metadata[hit_name] = {
                "id":               hit_name,
                "query":            query_name,
                "method":           "vg_giraffe",
                # GAF-specific
                "query_length":     query_length,
                "query_start":      query_start,
                "query_end":        query_end,
                "strand":           strand,
                "path_string":      path_str,
                "path_length":      path_length,
                "path_start":       path_start,
                "path_end":         path_end,
                "residue_matches":  residue_matches,
                "block_length":     block_length,
                "mapping_quality":  mapq,
                "alignment_score":  tags.get("AS", "N/A"),
                "divergence":       tags.get("dv", "N/A"),
                # Bandage-compatible fields (empty for vg giraffe)
                "sequence":         "",
                "identity":         "",
                "coverage_query":   "",
                "coverage_hits":    "",
                "e_value_product":  "",
                "mismatches":       "",
                "gap_opens":        "",
                "length_discrepancy": "",
                "relative_length":  "",
                # Visualization
                "nodes":            sorted_nodes,
                "odgi_image":       odgi_image,
                "bandage_image":    bandage_image,
            }

            print(f"Hit '{hit_name}': {len(sorted_nodes)} unique nodes  ({first} ... {last})")

    # Write consolidated JSON for Dash
    with open(metadata_path, 'w') as mf:
        json.dump(hits_metadata, mf, indent=4)

    print(f"\nDone. {len(hits)} hit(s) processed.")
    print(f"  TSV  -> {hits_info_path}")
    print(f"  JSON -> {metadata_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python process_gaf.py <input_gaf_file> <output_directory>")
        sys.exit(1)

    gaf_file_arg   = sys.argv[1]
    output_dir_arg = sys.argv[2]

    if not os.path.isfile(gaf_file_arg):
        print(f"Error: GAF file '{gaf_file_arg}' not found.")
        sys.exit(1)

    process_gaf_file(gaf_file_arg, output_dir_arg)
