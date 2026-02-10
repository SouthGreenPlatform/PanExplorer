from dash import Dash, dcc, html, Input, Output, State
import dash_ag_grid as dag

import dash_bootstrap_components as dbc

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
