from dash import Dash, dcc, html, Input, Output, State
import dash_ag_grid as dag

import dash_bootstrap_components as dbc

how_to_cite = html.Div(
    style={
        "position": "absolute",
        "width": "92%",
        "padding": "10px 10px 5px 10px",
        "backgroundColor": "white",
        "border": "1px solid lightgrey",
        "borderRadius": "5px",
        "marginTop": "15px",
        "marginLeft": "10px",
    },
    children=[

        html.Span(
            "How to cite",
            className="badge badge-primary how-to-cite-badge",
            style={
                "position": "absolute",
                "top": "-10px",
                "left": "-10px",
                "backgroundColor": "#007bff",
                "color": "white",
                "padding": "2px 8px",
                "borderRadius": "10px",
                "fontSize": "0.95em",
                "fontWeight": "600",
                "fontFamily": "Arial, sans-serif",
            },
        ),

        html.Span(
            [
                "Dereeper A, Summo M, Meyer DF. (2022) ",
                html.B(
                    "PanExplorer: a web-based tool for exploratory analysis and visualization of bacterial pan-genomes."
                ),
                " Bioinformatics. 2022 Sep 15;38(18):4412-4414. ",
                html.A(
                    "https://doi.org/10.1093/bioinformatics/btac504",
                    href="https://doi.org/10.1093/bioinformatics/btac504",
                    target="_blank",
                ),
            ],
            style={
                "fontWeight": "bold",
                "fontSize": "1em",
                "fontFamily": "Arial, sans-serif",
            },
        ),
    ],
)


layout = html.Div(
    [



        html.Div([
            html.P("""
            PanExplorer is a web application designed to facilitate the exploration and analysis of pangenomic data.
        """),
        html.P("""
            It provides interactive visualizations and tools to help researchers understand the genetic diversity within a set of genomes.
        """),

        html.Img(src="/assets/GraphicalAbstract.png", style={"width": "1200px", "marginTop": "20px"}),
        html.Br(),
        html.P("The application allows interactive data exploration at different levels :"),
        html.P("""

(i) Pan-genome visualization as a presence/absence heatmap. This overview allows to easily identify and distinguish core-genes (present in all strains), cloud genes (genes from the accessory genome) and genome-specific genes.
               """),
        
        html.P("""
(ii)    Physical map of core-genes and strain-specific genes can be displayed as a circular genomic representation (Circos), for each genome taken independently.
               """),
        html.P("""
(iii)   Synteny analysis. The conservation of gene order between genomes can be investigated using graphical representations
               """),
        html.P("""
(iv)    Visual inspection of a specific cluster.
               """),

        html.Br(),
        ],style={'fontSize': 18}
        ),
        dcc.Markdown('''
For general questions, comments or problems about the site or the data, please contact [alexis.dereeper@ird.fr](mailto:alexis.dereeper@ird.fr)    
'''),

        how_to_cite,
        html.Br(), 
        html.Br(),
        html.Br(), 
        html.Br(),
        html.Footer(
                    className="footer",
                    children=[
                        html.Div(
                            className="footer-logos",
                            children=[
                                html.Img(src="/assets/phim_logo.png", className="footer-logo"),
                                html.Img(src="/assets/southgreen_logo.png", className="footer-logo"),
                                html.Img(src="/assets/ird_logo.png", className="footer-logo"),
                                html.Img(src="/assets/cirad_logo.png", className="footer-logo"),
                            ]
                        )
                    ]
                )
        
    ],
    style={"padding": "20px"}
)
