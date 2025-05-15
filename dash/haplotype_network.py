import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform

import argparse

def process_file(input_path, output_basename):
    # Lire le contenu du fichier d'entrée
    with open(input_path, 'r', encoding='utf-8') as infile:
        content = infile.read()

    # Exemple de traitement : mettre en majuscules
    processed_content = content.upper()




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a haplotype network from haplotypes")
    parser.add_argument("-i", "--input", required=True, help="Input file")
    parser.add_argument("-o", "--output", required=True, help="Basename of outputs")

    args = parser.parse_args()

    process_file(args.input, args.output)


    # Exemple de matrice MLVA (haplotypes vs loci, valeurs = nombre de répétitions)
    data = pd.DataFrame({
        'Locus1': [3, 5, 3, 4],
        'Locus2': [7, 7, 6, 8],
        'Locus3': [2, 3, 2, 2]
    }, index=['Haplo1', 'Haplo2', 'Haplo3', 'Haplo4'])

    data.to_csv("haplo")

    data = pd.read_csv(args.input,index_col=0)





    ######################################################################
    # Matrice de distance
    ######################################################################

    print("Matrice de génotypage :\n", data)

    # Calcul de la distance de Manhattan entre haplotypes
    dist_matrix = squareform(pdist(data, metric='cityblock'))  # pdist renvoie une matrice compacte, squareform l'étend
    dist_df = pd.DataFrame(dist_matrix, index=data.index, columns=data.index)

    print("\nMatrice de distances (Manhattan) :\n", dist_df)


    ######################################################################
    # Haplotype Network
    ######################################################################

    import networkx as nx
    import matplotlib.pyplot as plt

    # Création du graphe avec NetworkX
    G = nx.Graph()

    # Ajout des sommets
    for haplo in data.index:
        G.add_node(haplo)

    # Ajout des arêtes avec les distances
    for i in range(len(data.index)):
        for j in range(i + 1, len(data.index)):  # Évite la redondance
            G.add_edge(data.index[i], data.index[j], weight=dist_matrix[i, j])

    # Construction du Minimum Spanning Tree (MST)
    mst = nx.minimum_spanning_tree(G, weight='weight')

    print(mst)

    # Dessin du réseau
    plt.figure(figsize=(6, 4))
    pos = nx.spring_layout(mst)  # Positionnement automatique des nœuds
    nx.draw(mst, pos, with_labels=True, node_size=200, node_color='lightblue', edge_color='gray', font_size=5)
    labels = nx.get_edge_attributes(mst, 'weight')
    nx.draw_networkx_edge_labels(mst, pos, edge_labels=labels)
    plt.title("Minimum Spanning Tree des haplotypes")
    plt.savefig(args.output+".myImagePDF.pdf", format="pdf", bbox_inches="tight")
    plt.show()

    ######################################################################
    # export pour cytoscape
    ######################################################################
    edges = []
    for u, v, d in mst.edges(data=True):
        edges.append([u, v, d['weight']])

    edges_df = pd.DataFrame(edges, columns=['Source', 'Target', 'Weight'])
    edges_df.to_csv(args.output+".haplotype_network.csv", index=False)

    print("\nFichier 'haplotype_network.csv' généré pour Cytoscape !")