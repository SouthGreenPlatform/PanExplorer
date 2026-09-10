#!/usr/bin/env python3

"""
PAV matrix analysis functions.

This module provides a generic analysis pipeline for binary
presence/absence matrices.

Input:
    A TSV file containing a binary presence/absence matrix.
    The first column contains strain identifiers.

Example:

    strain    gene1    gene2    gene3
    strain1   1        0        1
    strain2   1        1        1
    strain3   0        1        0

Analyses:
    - Jaccard distance matrix
    - Hierarchical clustering (UPGMA)
    - Cluster assignment
    - PCoA based on Jaccard distances
    - Newick tree export

The function can be used with different types of PAV matrices:
    - gene PAV
    - graph segment PAV
    - CRISPR spacer PAV
    - AMR PAV
    - virulence factor PAV
    - etc.
"""

import pandas as pd
import matplotlib.pyplot as plt

from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram

from skbio.stats.ordination import pcoa

from Bio import Phylo
from Bio.Phylo.TreeConstruction import (
    DistanceMatrix,
    DistanceTreeConstructor
)


def analyze_pav_matrix(
    input_file,
    distance_output,
    cluster_output,
    pcoa_output,
    newick_output,
    pcoa_plot=None,
    dendrogram_plot=None,
    cluster_distance_threshold=0.3,
    clustering_method="average",
    criterion="distance"
):
    """
    Analyze a binary presence/absence matrix.

    Parameters
    ----------
    input_file : str
        Input TSV file containing the presence/absence matrix.
        The first column must contain strain identifiers.

    distance_output : str
        Output TSV file for the Jaccard distance matrix.

    cluster_output : str
        Output TSV file containing strain-to-cluster assignments.

    pcoa_output : str
        Output TSV file containing PCoA coordinates.

    newick_output : str
        Output Newick tree file.

    pcoa_plot : str, optional
        Output file for the PCoA plot.
        Example: "pcoa.pdf".
        If None, no PCoA plot is generated.

    dendrogram_plot : str, optional
        Output file for the dendrogram.
        Example: "dendrogram.pdf".
        If None, no dendrogram is generated.

    cluster_distance_threshold : float, default=0.3
        Distance threshold used to define clusters.

        For example:
            0.3 means that groups are defined by cutting
            the hierarchical clustering tree at a Jaccard
            distance of 0.3.

    clustering_method : str, default="average"
        Linkage method used for hierarchical clustering.

        "average" corresponds to UPGMA.

        Other possible methods include:
            - "complete"
            - "single"
            - "ward"

        Note that Ward linkage should not be used with
        Jaccard distances.

    criterion : str, default="distance"

        Other possible criterion include: maxclust

    Returns
    -------
    dict
        Dictionary containing the main analysis results:

            {
                "matrix": input matrix,
                "distance": distance matrix,
                "clusters": cluster assignments,
                "pcoa": PCoA coordinates,
                "linkage": linkage matrix
            }

    """

    # ==========================================================
    # 1. Read the presence/absence matrix
    # ==========================================================

    print("Reading presence/absence matrix...")

    df = pd.read_csv(
        input_file,
        sep="\t",
        index_col=0
    )

    print(
        f"Number of strains: {df.shape[0]}"
    )

    print(
        f"Number of features: {df.shape[1]}"
    )


    # ==========================================================
    # 2. Validate the matrix
    # ==========================================================

    print("Checking matrix...")

    # Check that all values are 0 or 1.
    unique_values = set(df.values.flatten())

    if not unique_values.issubset({0, 1}):
        raise ValueError(
            "The presence/absence matrix must contain only "
            "0 and 1 values."
        )

    # Check for duplicated strain identifiers.
    if df.index.duplicated().any():
        duplicated = df.index[
            df.index.duplicated()
        ].tolist()

        raise ValueError(
            "Duplicated strain identifiers found: "
            + ", ".join(duplicated)
        )

    # Convert the matrix to boolean.
    # This is appropriate for presence/absence data.
    X = df.astype(bool)


    # ==========================================================
    # 3. Calculate Jaccard distances
    # ==========================================================

    print("Calculating Jaccard distances...")

    # Jaccard distance is appropriate for PAV data because
    # shared absences (0/0) are ignored.
    #
    # pdist returns a condensed distance matrix.
    jaccard_condensed = pdist(
        X,
        metric="jaccard"
    )

    # Convert the condensed matrix into a square matrix.
    jaccard_square = squareform(
        jaccard_condensed
    )

    distance_df = pd.DataFrame(
        jaccard_square,
        index=df.index,
        columns=df.index
    )

    # Save the distance matrix.
    distance_df.to_csv(
        distance_output,
        sep="\t"
    )

    print(
        f"Jaccard distance matrix written to: "
        f"{distance_output}"
    )


    # ==========================================================
    # 4. Hierarchical clustering
    # ==========================================================

    print(
        f"Performing hierarchical clustering "
        f"({clustering_method})..."
    )

    # Average linkage corresponds to UPGMA.
    linkage_matrix = linkage(
        jaccard_condensed,
        method=clustering_method
    )


    # ==========================================================
    # 5. Assign strains to clusters
    # ==========================================================

    print(
        "Assigning strains to clusters..."
    )

    # Cut the hierarchical tree using the specified
    # Jaccard distance threshold.
    clusters = fcluster(
        linkage_matrix,
        t=cluster_distance_threshold,
        criterion=criterion
    )

    cluster_df = pd.DataFrame({
        "strain": df.index,
        "HierarchicalClustering": clusters
    })
    cluster_df.index.name = "strain_index"
    cluster_df = cluster_df.reset_index()
    cluster_df.to_csv(
        cluster_output,
        sep="\t",
        index=False
    )

    print(
        f"Cluster assignments written to: "
        f"{cluster_output}"
    )

    print("\nCluster sizes:")

    print(
        cluster_df["HierarchicalClustering"]
        .value_counts()
        .sort_index()
    )


    # ==========================================================
    # 6. Generate dendrogram
    # ==========================================================

    if dendrogram_plot is not None:

        print("Generating dendrogram...")

        plt.figure(
            figsize=(12, 8)
        )

        dendrogram(
            linkage_matrix,
            labels=df.index.tolist(),
            leaf_rotation=90,
            leaf_font_size=8
        )

        plt.xlabel("Strains")

        plt.ylabel(
            "Jaccard distance"
        )

        plt.title(
            "Hierarchical clustering based on "
            "Jaccard distance"
        )

        plt.tight_layout()

        plt.savefig(
            dendrogram_plot,
            bbox_inches="tight"
        )

        plt.close()

        print(
            f"Dendrogram written to: "
            f"{dendrogram_plot}"
        )


    # ==========================================================
    # 7. Perform PCoA
    # ==========================================================

    print("Performing PCoA...")

    # PCoA is performed directly on the Jaccard distance matrix.
    #
    # This is different from PCA, which would operate directly
    # on the original feature matrix.
    pcoa_result = pcoa(
        distance_df
    )

    # Extract the first two PCoA axes.
    pcoa_coordinates = (
        pcoa_result.samples.iloc[:, :2]
        .copy()
    )

    pcoa_coordinates.columns = [
        "PCoA1",
        "PCoA2"
    ]

    # Add cluster assignments.
    pcoa_coordinates["HierarchicalClustering"] = clusters

    # df_propre = pcoa_coordinates.drop(columns='HierarchicalClustering')
    pcoa_coordinates.index.name = "strain_index"
    pcoa_coordinates = pcoa_coordinates.reset_index()

    cluster_df = cluster_df.drop(columns=['HierarchicalClustering'])
    cluster_df['strain_index'] = cluster_df['strain_index'].astype(str)
    pcoa_coordinates_merged = pd.merge(cluster_df, pcoa_coordinates, left_on='strain_index', right_on='strain_index')
    

    # pcoa_coordinates.index.name = "strain"
    # pcoa_coordinates = pcoa_coordinates.reset_index()

    # Save PCoA coordinates.
    pcoa_coordinates_merged.to_csv(
        pcoa_output,
        sep="\t",
        index=False
    )
    # pcoa_coordinates.to_csv(
    #     pcoa_output,
    #     sep="\t"
    # )

    print(
        f"PCoA coordinates written to: "
        f"{pcoa_output}"
    )


    # ==========================================================
    # 8. Get explained variance
    # ==========================================================

    axis1_variance = (
        pcoa_result
        .proportion_explained
        .iloc[0]
        * 100
    )

    axis2_variance = (
        pcoa_result
        .proportion_explained
        .iloc[1]
        * 100
    )

    print(
        f"PCoA1 explained variance: "
        f"{axis1_variance:.2f}%"
    )

    print(
        f"PCoA2 explained variance: "
        f"{axis2_variance:.2f}%"
    )


    # ==========================================================
    # 9. Generate PCoA plot
    # ==========================================================

    if pcoa_plot is not None:

        print("Generating PCoA plot...")

        plt.figure(
            figsize=(8, 7)
        )

        # Plot each cluster separately.
        for cluster_id in sorted(
            pcoa_coordinates["HierarchicalClustering"].unique()
        ):

            subset = pcoa_coordinates[
                pcoa_coordinates["HierarchicalClustering"] == cluster_id
            ]

            plt.scatter(
                subset["PCoA1"],
                subset["PCoA2"],
                label=f"Cluster {cluster_id}",
                s=50
            )

        plt.xlabel(
            f"PCoA1 ({axis1_variance:.1f}%)"
        )

        plt.ylabel(
            f"PCoA2 ({axis2_variance:.1f}%)"
        )

        plt.title(
            "PCoA based on Jaccard distance"
        )

        plt.legend(
            title="Cluster"
        )

        plt.tight_layout()

        plt.savefig(
            pcoa_plot,
            bbox_inches="tight"
        )

        plt.close()

        print(
            f"PCoA plot written to: "
            f"{pcoa_plot}"
        )


    # ==========================================================
    # 10. Build UPGMA tree
    # ==========================================================

    print("Building UPGMA tree...")

    names = list(df.index)

    # Biopython requires a lower-triangular distance matrix.
    lower_triangle = []

    for i in range(len(names)):

        row = []

        for j in range(i + 1):

            row.append(
                float(
                    jaccard_square[i, j]
                )
            )

        lower_triangle.append(row)

    biopython_distance = DistanceMatrix(
        names=names,
        matrix=lower_triangle
    )

    # Build the UPGMA tree.
    constructor = DistanceTreeConstructor()

    tree = constructor.upgma(
        biopython_distance
    )


    # ==========================================================
    # 11. Export Newick tree
    # ==========================================================

    Phylo.write(
        tree,
        newick_output,
        "newick"
    )

    print(
        f"Newick tree written to: "
        f"{newick_output}"
    )


    # ==========================================================
    # 12. Return results
    # ==========================================================

    return {
        "matrix": df,
        "distance": distance_df,
        "clusters": cluster_df,
        "pcoa": pcoa_coordinates,
        "linkage": linkage_matrix,
        "tree": tree
    }
