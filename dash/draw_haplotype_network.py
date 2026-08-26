import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from matplotlib.patches import Wedge


def plot_haplotype_network(
    network_file,
    metadata_file,
    sample_col="Sample",
    haplotype_col="Haplotype",
    origin_col="Country",
    output=None,
    figsize=(18, 16),

    # Layout
    scale=15,
    distance_transform="sqrt",
    min_visual_distance=2.5,

    # Nodes
    node_size_min=0.025,
    node_size_max=None,

    # Appearance
    show_labels=True,
    show_weights=False,
    edge_width=1.2,
    edge_alpha=0.7,

    # Colors
    origin_colors=None,
):
    """
    Plot a weighted haplotype network with geographic pie charts.

    Network CSV:
        Source,Target,Weight

    Metadata CSV:
        Sample,Haplotype,Country

    Parameters
    ----------
    network_file : str
        CSV containing Source, Target and Weight.

    metadata_file : str
        CSV containing sample, haplotype and geographic origin.

    sample_col : str
        Sample identifier column.

    haplotype_col : str
        Haplotype identifier column.

    origin_col : str
        Geographic origin column.

    output : str, optional
        Output filename, e.g. "network.png".

    figsize : tuple
        Figure size.

    scale : float
        Overall scale of the network.

    distance_transform : str
        Transformation applied to genetic distances:
        "linear", "sqrt" or "log".

    min_visual_distance : float
        Minimum visual distance used between connected nodes.

    node_size_min : float
        Radius of a haplotype represented by one sample, relative to
        the network size. Node radius scales as sqrt(frequency), so
        node area is approximately proportional to haplotype frequency.

    node_size_max : float or None
        Optional maximum node radius relative to network size. If None,
        no upper limit is applied and node area remains proportional to
        haplotype frequency. If set, it acts only as a visual cap.

    show_labels : bool
        Display haplotype names.

    show_weights : bool
        Display genetic distances on edges.

    edge_width : float
        Width of network edges.

    edge_alpha : float
        Transparency of network edges.

    origin_colors : dict, optional
        Mapping such as:
            {
                "Uganda": "red",
                "Kenya": "blue"
            }

    Returns
    -------
    fig, ax, G, pos
    """

    # ============================================================
    # 1. NORMALIZE HAPLOTYPE IDENTIFIERS
    # ============================================================

    def normalize_haplotype_id(value):
        """
        Convert all common representations to haploXXX.

        Examples
        --------
        1       -> haplo1
        1.0     -> haplo1
        "1"     -> haplo1
        "1.0"   -> haplo1
        "haplo1" -> haplo1
        "haplo1.0" -> haplo1
        """

        if pd.isna(value):
            return None

        value = str(value).strip()

        # Already haploXXX
        if value.lower().startswith("haplo"):

            number = value[5:].strip()

            try:

                number_float = float(number)

                if number_float.is_integer():
                    return f"haplo{int(number_float)}"

            except ValueError:
                pass

            return value

        # Numeric identifier
        try:

            number_float = float(value)

            if number_float.is_integer():
                return f"haplo{int(number_float)}"

        except ValueError:
            pass

        return value

    # ============================================================
    # 2. LOAD NETWORK
    # ============================================================

    network_df = pd.read_csv(
        network_file,
        dtype={
            "Source": str,
            "Target": str
        }
    )

    required_network = {
        "Source",
        "Target",
        "Weight"
    }

    missing = (
        required_network
        - set(network_df.columns)
    )

    if missing:

        raise ValueError(
            "Network file is missing columns: "
            f"{missing}"
        )

    # Normalize identifiers
    network_df["Source"] = (
        network_df["Source"]
        .apply(normalize_haplotype_id)
    )

    network_df["Target"] = (
        network_df["Target"]
        .apply(normalize_haplotype_id)
    )

    # ============================================================
    # 3. CREATE NETWORKX GRAPH
    # ============================================================

    G = nx.Graph()

    for _, row in network_df.iterrows():

        source = row["Source"]
        target = row["Target"]
        weight = float(row["Weight"])

        G.add_edge(
            source,
            target,
            weight=weight
        )

    print(
        f"Network: "
        f"{G.number_of_nodes()} haplotypes, "
        f"{G.number_of_edges()} edges"
    )

    # ============================================================
    # 4. LOAD METADATA
    # ============================================================

    metadata = pd.read_csv(
        metadata_file
    )

    required_metadata = {
        sample_col,
        haplotype_col,
        origin_col
    }

    missing = (
        required_metadata
        - set(metadata.columns)
    )

    if missing:

        raise ValueError(
            "Metadata file is missing columns: "
            f"{missing}"
        )

    metadata = metadata[
        [
            sample_col,
            haplotype_col,
            origin_col
        ]
    ].copy()

    # Sample ID
    metadata[sample_col] = (
        metadata[sample_col]
        .astype(str)
        .str.strip()
    )

    # Normalize haplotype IDs
    metadata[haplotype_col] = (
        metadata[haplotype_col]
        .apply(normalize_haplotype_id)
    )

    # Geographic origin
    metadata[origin_col] = (
        metadata[origin_col]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

    # ============================================================
    # 5. COUNT ORIGINS BY HAPLOTYPE
    # ============================================================

    counts = (
        metadata
        .dropna(
            subset=[haplotype_col]
        )
        .groupby(
            [
                haplotype_col,
                origin_col
            ]
        )
        .size()
        .unstack(
            fill_value=0
        )
    )

    # List of all origins
    origins = sorted(
        metadata[origin_col]
        .dropna()
        .unique()
    )

    # ============================================================
    # 6. DISPLAY COMPOSITION
    # ============================================================

    print(
        "\nHaplotype geographic composition:"
    )

    for haplotype in G.nodes():

        if haplotype in counts.index:

            composition = (
                counts
                .loc[haplotype]
                .loc[
                    lambda x: x > 0
                ]
                .to_dict()
            )

        else:

            composition = {}

        print(
            f"{haplotype}: "
            f"{composition}"
        )

    # ============================================================
    # 7. COLORS
    # ============================================================

    if origin_colors is None:

        cmap = plt.get_cmap(
            "tab20"
        )

        origin_colors = {
            origin: cmap(i % 20)
            for i, origin
            in enumerate(origins)
        }

    else:

        # Automatically add missing colors
        cmap = plt.get_cmap(
            "tab20"
        )

        for i, origin in enumerate(origins):

            if origin not in origin_colors:

                origin_colors[origin] = (
                    cmap(i % 20)
                )

    # ============================================================
    # 8. CREATE VISUAL EDGE WEIGHTS
    # ============================================================

    for u, v, data in G.edges(
        data=True
    ):

        weight = float(
            data["weight"]
        )

        # --------------------------------------------------------
        # Transform genetic distance
        # --------------------------------------------------------

        if distance_transform == "linear":

            visual_weight = weight

        elif distance_transform == "sqrt":

            visual_weight = np.sqrt(
                weight
            )

        elif distance_transform == "log":

            visual_weight = np.log1p(
                weight
            )

        else:

            raise ValueError(
                "distance_transform must be "
                "'linear', 'sqrt' or 'log'"
            )

        # --------------------------------------------------------
        # Minimum visual separation
        # --------------------------------------------------------

        visual_weight = max(
            visual_weight,
            min_visual_distance
        )

        data["layout_weight"] = (
            visual_weight
        )

    # ============================================================
    # 9. KAMADA-KAWAI LAYOUT
    # ============================================================

    pos = nx.kamada_kawai_layout(
        G,
        weight="layout_weight",
        scale=scale
    )

    # ============================================================
    # 10. NETWORK EXTENT
    # ============================================================

    xs = np.array([
        p[0]
        for p in pos.values()
    ])

    ys = np.array([
        p[1]
        for p in pos.values()
    ])

    network_width = (
        xs.max() - xs.min()
    )

    network_height = (
        ys.max() - ys.min()
    )

    network_size = max(
        network_width,
        network_height
    )

    if network_size == 0:
        network_size = 1

    # ============================================================
    # 11. HAPLOTYPE FREQUENCIES
    # ============================================================

    frequencies = {}

    for haplotype in G.nodes():

        if haplotype in counts.index:

            frequency = int(
                counts
                .loc[haplotype]
                .sum()
            )

        else:

            frequency = 0

        frequencies[haplotype] = frequency

    # ============================================================
    # 12. NODE RADII
    # ============================================================
    #
    # IMPORTANT:
    # The radius is proportional to sqrt(frequency). Therefore the
    # surface (pi*r^2) is proportional to frequency.
    #
    # This deliberately does NOT normalize frequencies between their
    # observed minimum and maximum. Such a min/max normalization would
    # make frequency 1 and frequency 2 potentially map to the minimum
    # and maximum sizes, producing a visually exaggerated difference.
    # ============================================================

    radii = {}

    for haplotype, frequency in frequencies.items():

        if frequency <= 0:
            radius = node_size_min

        else:
            radius = (
                node_size_min
                * np.sqrt(frequency)
            )

        # Optional visual cap. It is disabled by default because a cap
        # breaks the strict area/frequency relationship for large nodes.
        if node_size_max is not None:
            radius = min(
                radius,
                node_size_max
            )

        radii[haplotype] = (
            radius
            * network_size
        )

    # ============================================================
    # 13. CREATE FIGURE
    # ============================================================

    fig, ax = plt.subplots(
        figsize=figsize
    )

    ax.set_aspect(
        "equal",
        adjustable="box"
    )

    # ============================================================
    # 14. DRAW EDGES
    # ============================================================

    nx.draw_networkx_edges(
        G,
        pos,
        ax=ax,
        width=edge_width,
        edge_color="black",
        alpha=edge_alpha
    )

    # ============================================================
    # 15. EDGE LABELS
    # ============================================================

    if show_weights:

        edge_labels = {
            (u, v):
            f"{data['weight']:g}"
            for u, v, data
            in G.edges(data=True)
        }

        nx.draw_networkx_edge_labels(
            G,
            pos,
            edge_labels=edge_labels,
            ax=ax,
            font_size=8
        )

    # ============================================================
    # 16. DRAW PIE CHARTS
    # ============================================================

    for haplotype in G.nodes():

        x, y = pos[haplotype]

        radius = radii[
            haplotype
        ]

        # --------------------------------------------------------
        # Geographic composition
        # --------------------------------------------------------

        if haplotype in counts.index:

            hap_counts = (
                counts
                .loc[haplotype]
            )

            hap_counts = (
                hap_counts[
                    hap_counts > 0
                ]
            )

        else:

            hap_counts = pd.Series(
                dtype=float
            )

        # --------------------------------------------------------
        # No metadata
        # --------------------------------------------------------

        if len(hap_counts) == 0:

            circle = plt.Circle(
                (x, y),
                radius,
                facecolor="lightgray",
                edgecolor="black",
                linewidth=1.5,
                zorder=20
            )

            ax.add_patch(
                circle
            )

        # --------------------------------------------------------
        # Single origin
        # --------------------------------------------------------

        elif len(hap_counts) == 1:

            origin = (
                hap_counts.index[0]
            )

            circle = plt.Circle(
                (x, y),
                radius,
                facecolor=origin_colors[
                    origin
                ],
                edgecolor="black",
                linewidth=1.5,
                zorder=20
            )

            ax.add_patch(
                circle
            )

        # --------------------------------------------------------
        # Multiple origins
        # --------------------------------------------------------

        else:

            total = (
                hap_counts.sum()
            )

            start_angle = 90

            for origin, count in (
                hap_counts.items()
            ):

                fraction = (
                    count / total
                )

                angle = (
                    fraction * 360
                )

                wedge = Wedge(
                    center=(x, y),
                    r=radius,
                    theta1=start_angle,
                    theta2=(
                        start_angle
                        + angle
                    ),
                    facecolor=origin_colors[
                        origin
                    ],
                    edgecolor="white",
                    linewidth=0.0,
                    zorder=20
                )

                ax.add_patch(
                    wedge
                )

                start_angle += angle

            # Outer black border
            border = plt.Circle(
                (x, y),
                radius,
                facecolor="none",
                edgecolor="black",
                linewidth=1.5,
                zorder=21
            )

            ax.add_patch(
                border
            )

    # ============================================================
    # 17. HAPLOTYPE LABELS
    # ============================================================

    if show_labels:

        label_offset = (
            network_size * 0.002
        )

        for haplotype in G.nodes():

            x, y = pos[haplotype]

            radius = radii[
                haplotype
            ]

            ax.text(
                x,
                y + radius + label_offset,
                haplotype,
                ha="center",
                va="bottom",
                fontsize=8,
                zorder=30
            )

    # ============================================================
    # 18. LEGEND
    # ============================================================

    handles = []

    for origin in origins:

        handles.append(
            plt.Line2D(
                [0],
                [0],
                marker="o",
                linestyle="",
                color="none",
                markerfacecolor=(
                    origin_colors[
                        origin
                    ]
                ),
                markeredgecolor="black",
                markersize=10,
                label=origin
            )
        )

    if handles:

        ax.legend(
            handles=handles,
            title=origin_col,
            loc="upper left",
            bbox_to_anchor=(
                1.02,
                1
            ),
            frameon=True
        )

    # ============================================================
    # 19. FINALIZE
    # ============================================================

    ax.set_axis_off()

    plt.tight_layout()

    # ============================================================
    # 20. SAVE
    # ============================================================

    if output:

        fig.savefig(
            output,
            dpi=300,
            bbox_inches="tight"
        )

        print(
            f"\nSaved network to: "
            f"{output}"
        )

    return (
        fig,
        ax,
        G,
        pos
    )






