import os
import sys

def process_gaf_file(gaf_file, output_directory):
    alignments = {}
    sequence_counts = {}

    # Read the GAF file and process each line
    with open(gaf_file, 'r') as f:
        for line in f:
            fields = line.strip().split('\t')
            sequence_name = fields[0]
            sequence_path = fields[5]

            # Increment the count for the sequence name
            if sequence_name in sequence_counts:
                sequence_counts[sequence_name] += 1
            else:
                sequence_counts[sequence_name] = 1

            # Generate a unique sequence name if there are multiple occurrences
            unique_sequence_name = f"{sequence_name}_{sequence_counts[sequence_name] - 1}" if sequence_counts[sequence_name] > 1 else sequence_name

            if unique_sequence_name not in alignments:
                alignments[unique_sequence_name] = {}
                alignments[unique_sequence_name]["gaf"]=line
                alignments[unique_sequence_name]["nodes"]=[]

            # Split nodes by both '>' and '<' delimiters
            nodes = []
            temp = ""
            for char in sequence_path:
                if char in (">", "<"):
                    if temp:
                        nodes.append(temp)
                    temp = ""
                else:
                    temp += char
            if temp:
                nodes.append(temp)
            
            alignments[unique_sequence_name]["nodes"].extend(nodes)

    # Ensure the output directory exists
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Write the unique, sorted nodes to files in the output directory
    hits_info_path = os.path.join(output_directory, "hits_info.tsv")
    with open(hits_info_path, 'w') as hits_info_file:
        hits_info_file.write("hit_name\tstart_node\tend_node\n")
        for sequence_name, elements in alignments.items():
            nodes = elements["nodes"]
            gaf = elements["gaf"]
            sorted_nodes = sorted(set(nodes))
            output_file = os.path.join(output_directory, f'{sequence_name}_hit.txt')
            gaf_file = os.path.join(output_directory, f'{sequence_name}.gaf')

            with open(output_file, 'w') as out_f:
                out_f.write(",".join(sorted_nodes) + "\n")
            with open(gaf_file, 'w') as out_g:
                out_g.write(gaf)

            # Write the unique sequence name and first/last node IDs to hits_info.tsv
            first_node = sorted_nodes[0] if sorted_nodes else "N/A"
            last_node = sorted_nodes[-1] if sorted_nodes else "N/A"
            hits_info_file.write(f"{sequence_name}\t{first_node}\t{last_node}\n")

            print(f"Processed {sequence_name}: {len(sorted_nodes)} unique nodes, saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python process_gaf.py <input_gaf_file> <output_directory>")
        sys.exit(1)

    gaf_file = sys.argv[1]
    output_directory = sys.argv[2]

    if not os.path.isfile(gaf_file):
        print(f"Error: File {gaf_file} not found.")
        sys.exit(1)

    process_gaf_file(gaf_file, output_directory)
