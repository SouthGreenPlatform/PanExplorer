import sys
import os
import csv
import re
import json

def process_bandage_files(tsv_file, output_directory, top_n=None):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Dictionary to keep track of hit counts for naming
    hit_counts = {}
    hits_metadata = {}
    
    print(f"Processing Bandage TSV: {tsv_file}")

    try:
        hits_written = 0

        with open(tsv_file, 'r', newline='') as f:
            # Bandage output is typically tab-delimited
            reader = csv.DictReader(f, delimiter='\t')
            
            # Normalize column names just in case (strip whitespace)
            reader.fieldnames = [name.strip() for name in reader.fieldnames]
            
            for row in reader:
                if top_n is not None and hits_written >= top_n:
                    break

                query_name = row.get("Query", "").strip()
                path_str = row.get("Path", "").strip()
                
                if not query_name or not path_str:
                    continue

                # Unique ID generation
                if query_name in hit_counts:
                    hit_counts[query_name] += 1
                else:
                    hit_counts[query_name] = 1
                
                if hit_counts[query_name] > 1:
                    unique_name = f"{query_name}_{hit_counts[query_name]-1}"
                else:
                    unique_name = query_name

                # Parse the path to get nodes
                # Bandage path format: 12+ 13- (space separated usually, or comma?)
                raw_segments = re.split(r'[,\s]+', path_str)
                nodes = []
                for seg in raw_segments:
                    # Remove + or - at the end or beginning
                    clean_node = seg.replace('+', '').replace('-', '')
                    if clean_node:
                        nodes.append(clean_node)
                
                if not nodes:
                    continue

                # Write to hit file
                hit_file = os.path.join(output_directory, f"{unique_name}_hit.txt")
                with open(hit_file, 'w') as out:
                    out.write(",".join(nodes))

                # Collect metadata
                hits_metadata[unique_name] = {
                    "id": unique_name,
                    "query": query_name,
                    "path_string": path_str,
                    "sequence": row.get("Sequence", ""),
                    "identity": row.get("Mean hit identity", ""),
                    "coverage_query": row.get("Query covered by path", ""),
                    "coverage_hits": row.get("Query covered by hits", ""),
                    "e_value_product": row.get("E-value product", ""),
                    "mismatches": row.get("Total hit mismatches", ""),
                    "gap_opens": row.get("Total hit gap opens", ""),
                    "length_discrepancy": row.get("Length discrepancy", ""),
                    "relative_length": row.get("Relative length", ""),
                    "nodes": nodes
                }

                hits_written += 1
        
        # Save metadata to JSON
        metadata_file = os.path.join(output_directory, "hits_metadata.json")
        with open(metadata_file, 'w') as mf:
            json.dump(hits_metadata, mf, indent=4)
                    
    except Exception as e:
        print(f"Error processing TSV file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python process_bandage_hits.py <tsv_file> <output_dir> [top_n]")
        sys.exit(1)

    top_n = None
    if len(sys.argv) >= 4:
        try:
            top_n = int(sys.argv[3])
        except ValueError:
            top_n = None
        if top_n is not None and top_n <= 0:
            top_n = None

    process_bandage_files(sys.argv[1], sys.argv[2], top_n)
