import dash
from dash import Dash, html, dcc, Input, Output, State, callback
from IPython.display import HTML
import plotly.express as px

import urllib.request as urlreq
from urllib.request import Request, urlopen

import dash_bootstrap_components as dbc


import numpy as np
import json
import subprocess

import dash_ag_grid as dag

import os
import random
import re

import plotly.graph_objects as go

from dash.dependencies import Output, Input
from dash.exceptions import PreventUpdate

import pandas as pd
import folium
import folium.plugins


import dash_bio as dash_bio

#from plotly_upset.plotting import plot_upset
#from upsetplot import plot
#from upsetplot import generate_counts
#from matplotlib import pyplot

#import dash_datatables as ddt

import plotly.figure_factory as ff

import yaml

directory = "data/african_Xo"
tmp_dir = ""
data_dir = ""
with open("panexplorer_config.yaml", "r") as yaml_file:
    conf = yaml.safe_load(yaml_file)
    directory = conf["directory"]
    tmp_dir = conf["tmp_dir"]
    data_dir = conf["data_dir"]

subdirectories = [ f.name for f in os.scandir(data_dir) if f.is_dir() ]


for subdir in subdirectories:
    if subdir.startswith(('1','2','3','4','5','6','7','8','9','0')):
        subdirectories.remove(subdir)


df_metadata = pd.read_csv(data_dir+"/"+subdirectories[0]+'/metadata.xls',sep='\t')

#dftest = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')
#column_defs = [{"title": i, "data": i} for i in dftest.columns]


filtering = 'Continent'


dash.register_page(__name__,path='/app-pav')

colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', '#800000', '#008000', '#000080', '#808000', '#800080', '#008080', '#C0C0C0', '#808080']

tabs_styles = {
    'height': '44px'
}
tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '6px'
}

layout_config = {
#    "labels": {"display": False},
    "innerRadius": 365,
    "outerRadius": 370,
    "cornerRadius": 4,
    "labels": {
        "size": 22,
        "color": "#4d4d4d",
        "innerRadius": 500
    },
    "ticks": {
        "color": "#4d4d4d",
        "labelColor": "#4d4d4d",
        "spacing": 1000000,
        "labelSuffix": "Mb",
        "labelDenominator": 1000000,
        "labelSize": 12,
    },
}

stack_config = {
    "innerRadius": 0.7,
    "outerRadius": 1,
    "thickness": 2,
    "margin": 800000,
    "direction": "out",
    "color": {"name": "color"},
    "strokeWidth": 0,
}

highlight_config1 = {
    "innerRadius": 330,
    "outerRadius": 350,
    "color": "blue",
}
highlight_config2 = {
    "innerRadius": 300,
    "outerRadius": 320,
    "color": "red",
}
highlight_config3 = {
    "innerRadius": 260,
    "outerRadius": 280,
    "color": "purple",
}
highlight_config4 = {
    "innerRadius": 230,
    "outerRadius": 250,
    "color": "green",
}
  
df_matrix = pd. DataFrame()



columnDefs = [
    {
        "field": "Strain name",
        "checkboxSelection": True,
        "headerCheckboxSelection": True,
    },
    {"field": "Country"},
    {"field": "Continent"},
    {"field": "Organism"}
]

columnDefs2 = [
    {
        "field": "ID",
        "width": 40,
        "checkboxSelection": True,
        "headerCheckboxSelection": True,
    },
    {"field": "Repeat","width": 100,},
]


data = ""



PAGE_SIZE = 5
layout = html.Div([
    dcc.Location(id='url', refresh=False),

    
    html.H1('PanExplorer: Pangene Atlas'),
    
    dbc.Row([
        dbc.Col(
            html.Label('Choose a project: ', style={'margin-right': '15px'},),
            
            ),

        dbc.Col(
            dcc.Dropdown(
                subdirectories,
                id='projets',
                value = subdirectories[0],
                multi=False,
                style={'width': '400px'}
            ))
    ]),

    html.Br(),
    html.Div(id='sample_selection',children=[
            dag.AgGrid(
                id="metadata_table",
                style={'width': '100vh','margin-left': '15px'},
                columnDefs=columnDefs,
                rowData=df_metadata.to_dict('records'),
                columnSize="sizeToFit",
                selectAll=True,
                defaultColDef={"filter": True},
                dashGridOptions={
                    "rowSelection": "multiple",
                    "animateRows": False
                },
            ),
        html.Br(),
        dbc.Row([
            dbc.Col(
                html.Label('Reference Genome for projection ', style={'margin-right': '15px'},),
                ),
            dbc.Col(
                dcc.Dropdown(
                    id='reference',
                    style={'width': '500px'},
                    multi=False
                )) 
        ]),
    ]),

    html.H5("PAV configuration"),        
    html.Div(id='PAV_config',children=[
        
        dbc.Row([
            dbc.Col(
                html.Label('Colors: ', style={'margin-right': '15px'},),
            ),
            dbc.Col(
                dcc.Dropdown(
                    ['Presence/absence','Level of presence','Organism','Continent'],
                    id='colorizing',
                    value = 'Presence/absence',
                    style={'width': '300px'},
                    multi=False
                ),
            ),
            dbc.Col(
                html.Label('Highlight: ', style={'margin-right': '15px', 'margin-left': '50px'},),
            ),
            dbc.Col(
                dcc.Dropdown(
                    ['None','Reference genome','Core-genes','Strain-specific genes'],
                    id='highlight',
                    value = 'None',
                    style={'width': '300px'},
                    multi=False
                )
            ),
            dbc.Col(
                html.Label('Cluster ordering: ', style={'margin-right': '15px', 'margin-left': '50px'},),
            ),
            dbc.Col(
                dcc.Dropdown(
                    ['Hierarchical clustering','Position in genome used for projection'],
                    value = 'Hierarchical clustering',
                    id='ordering',
                    style={'width': '300px'},
                    multi=False
                )
            )
        ]),

    ]),
    html.H5("Search for clusters"),

    dbc.Row([
            dbc.Col(
                html.Label('Search for clusters by keyword or COG (comma separated): ', style={'margin-right': '15px'},),
            ),
            dbc.Col(
                dcc.Input(
                    id='cluster_search',
                    value = '',
                )
            )
        ]), 

    html.Div([
            "Search for clusters in these intervals (copy/paste a BED file with intervals of regions): ",
            dcc.Textarea(
                id='bedfile',
                style={'width': '100%', 'height': 100},
            ),


        ], style={'width': '600px', 'display': 'inline-block'}),
    html.H5("Pan-GWAS"),
    html.Div([
            "Search for clusters specific to these genomes",dcc.Dropdown(
                id='specific_to',
                multi=True
            )
        ], style={'width': '100%', 'display': 'inline-block'}),

    dcc.Dropdown(
                [],
                id='current_cluster',
                value = '',
                style ={'visibility': 'hidden'}
            ),
    html.Button('Update Graphes', id='submit-val', n_clicks=0),  

    html.Br(),
    html.Br(),
    

    # The Visuals
    
    dcc.Loading(html.Div(id='results', style={'display': 'none'}, children=[
    dcc.Tabs(id='tab', style=tabs_styles, children=[
        dcc.Tab(label='Stats and Overview', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            html.Div(className="row", id='stats', children=[
                
                dcc.Loading(dcc.Graph(id='graph_gene',style={'width': '50vh', 'height': '50vh','margin-left': '15px'})),
                dcc.Loading(dcc.Graph(id='graph_pie',style={'width': '50vh', 'height': '50vh','margin-left': '15px'})),
                dcc.Loading(dcc.Graph(id='rarefaction',style={'width': '50vh', 'height': '50vh','margin-left': '15px'})),
            ]),
        ]),
        dcc.Tab(label='PAV matrix', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            
            html.Div(id='textarea-example-output', style={'whiteSpace': 'pre-line'}),
            dcc.Loading(html.Div(id='test', style={'whiteSpace': 'pre-line'})),
            html.Div(id='test2'),
            dcc.Loading(dcc.Graph(id='PAV_graph')),
            html.Br(),
            html.Div(className="row", id='tables', children=[
                html.Div(children=[
                    dcc.Loading(html.H3(id='nb_of_pangenes', style={'whiteSpace': 'pre-line'})),
                    dcc.Loading(
                        dag.AgGrid(
                                id="table_pangenes",
                                style={'width': '80vh', 'height': '50vh','margin-left': '15px'},
                                rowData=[],
                                columnDefs=[{"field": i} for i in ["ClutserID","COG","COG term","COGcat","type"]],
                                #defaultColDef={"filter": True},
                                columnSize="sizeToFit",
                                defaultColDef={"filter": "agTextColumnFilter"},
                                #getRowId="params.data.State",
                                dashGridOptions={"pagination": True, "animateRows": False}
                        ),
                    ),
                ]),
                
                
                

                html.Div(style={'marginLeft': 50}, children=[
                    dcc.Loading(html.H3(id="clustersearch", style={'color': 'red'})),
                    dcc.Loading(
                        dag.AgGrid(
                                id="table_of_search",
                                style={'width': '80vh', 'height': '50vh','margin-left': '15px'},
                                #style={'width': '20vh', 'border-style': '1px solid red','height': '50vh','margin-left': '15px'},
                                rowData=[],
                                columnDefs=[{"field": i} for i in ["ClutserID","COG","COG term","COGcat","type"]],
                                defaultColDef={"filter": True},
                                columnSize="sizeToFit",
                                #getRowId="params.data.State",
                                dashGridOptions={"pagination": True, "animateRows": False}
                        ),
                    ),
                ]),
            ]),
           
            html.Br(),
            
            dcc.Loading(html.H3(id='selected_cluster')),
            html.Div(className="row", id='focus', children=[
            #html.Div(style={'marginLeft': 50}, children=[
                    #html.Div(className="row", children=[
                    
                    
                    #    ]),
                    #html.Div(id="cluster_info"),
                    dcc.Loading(
                        dag.AgGrid(
                                    id="genes_cluster",
                                    style={'width': '50vh', 'height': '50vh','margin-left': '15px'},
                                    rowData=[],
                                    columnDefs=[{"field": i} for i in ["Cluster","Species","Genes"] ],
                                    defaultColDef={"filter": True},
                                    columnSize="sizeToFit",
                                    #getRowId="params.data.State",
                                    dashGridOptions={"pagination": True, "animateRows": False}
                            )
                    ),
                    html.Div(style={'marginLeft': 50}, children=[
                        dcc.Loading(
                            dash_bio.AlignmentChart(
                                id='my-default-alignment-viewer',
                                data=data,
                                width=1000,
                                height=600,
                            ),
                        ),
                    ]),
                ]),
                
            
            
            html.Div(id='tbl_out'),
            
        ]),

        dcc.Tab(label='COG', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            dcc.Loading(dcc.Graph(id='graph_COG_all')),
            html.Br(),
            dcc.Loading(dcc.Graph(id='graph_COG1')),
            html.Br(),
            dcc.Loading(dcc.Graph(id='graph_COG2')),
            ]),
        dcc.Tab(label='Accessory-based tree', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            dbc.Row(
                [
                    dcc.Loading(html.Iframe(id='iframe-content',style={'width': '1200px', 'height': '800px', 'border': 'none'}))
                ],
                align="center",
            ),
            html.Br(),
            ]),
        
        dcc.Tab(label='ANI', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            dcc.Loading(dcc.Graph(id='graph_ANI')),
            ]),
        dcc.Tab(label='Macro-Synteny', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            dcc.Loading(html.Div(id='clinker'),style={'width': '150vh', 'height': '200vh','margin-left': '15px'}),
            html.Br(),
            html.Br(),
            dcc.Loading(dcc.Graph(id='graph_macrosynteny',style={'width': '150vh', 'height': '100vh','margin-left': '15px'})),
            
        ]),
        
        dcc.Tab(label='Circos', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            dcc.Loading(dash_bio.Circos(
                id="my-dashbio-default-circos",
                layout=[],
                config=layout_config,
        tracks=[
                {
                    "type": "HIGHLIGHT",
                    "data": [],
                    "config": highlight_config1
                },
                {
                    "type": "HIGHLIGHT",
                    "data": [],
                    "config": highlight_config2
                },
                {
                    "type": "HIGHLIGHT",
                    "data": [],
                    "config": highlight_config3
                },
            {
                    "type": "HIGHLIGHT",
                    "data": [],
                    "config": highlight_config4
                }
            ],
    )),
            ]),
        dcc.Tab(label='MLVA', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            html.Div(className="row", children=[
                dcc.Loading(
                            dag.AgGrid(
                                id="mlva_table",
                                style={'width': '40vh','height': '50vh','margin-left': '15px'},
                                columnDefs=columnDefs2,
                                rowData=[],
                                columnSize="sizeToFit",
                                selectAll=True,
                                defaultColDef={"filter": True},
                                dashGridOptions={"rowSelection": "multiple", "suppressRowClickSelection": True, "animateRows": False},
                            ), 
                        ),
                #html.Pre(id='flanking', style={'width': '60vh', "fontFamily": "Courier", "whiteSpace": "pre-wrap", "border": "1px solid #ccc", "padding": "10px"}),
                
                dcc.Textarea(
                     id='flanking',
                     value='scc',
                     style={'width': '60vh', 'height': '50vh'},
                ),
                html.Button('Show haplotypes', id='submit-vntr', n_clicks=0),

                dcc.Loading(dcc.Graph(id='graph_mlva',style={'width': '100vh', 'height': '50vh','margin-left': '15px'})),
                #html.Iframe(id='dynamic_network',style={"height": "900px", "width": "100%"}),
            ]),
            html.Br(),
            dcc.Loading(html.Div(id='dynamic_network')),
        ]),
        dcc.Tab(label='SNP analysis', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            
            dcc.Loading(dcc.Graph(id='sNMF',style={'width': '100vh', 'height': '100vh','margin-left': '15px'})),
            dcc.Loading(dcc.Graph(id='sNMF_cross_entropy',style={'width': '100vh', 'height': '50vh','margin-left': '15px'})),
            dcc.Loading(dcc.Graph(id='PCA',style={'width': '100vh', 'height': '50vh','margin-left': '15px'})),
            ]),
        dcc.Tab(label='Geographical map', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
                dcc.Loading(dcc.Graph(id='geo_map',style={'width': '150vh', 'height': '100vh','margin-left': '15px'})),
            ]),

        ]),
        
    ]))
    #html.Div(id='cluster_info', style={'whiteSpace': 'pre-line'}),
    
    
])


@callback(
    Output('sample_selection', 'children'), 
    Output('results', 'style', allow_duplicate=True),
    Input('projets', 'value'),
    Input('url','hash'),
    prevent_initial_call=True
)

def display_sample_selection(projets,url):
    #df,df_metadata,df_ANI,merged_with_positions,list_species,list_continent,list_organisms,karyotype_dict_list,dict_list_gene_plus,dict_list_gene_minus,df_matrix = init_dataframes(pathname)

    pathname = "#"+projets
    if url:
        pathname=url

    directory = get_directory(pathname)
    df_metadata = pd.read_csv(directory+'/metadata.xls',sep='\t')


    list_species = df_metadata['Strain name']

    html_div = html.Div(id='sample_selection',children=[
        dag.AgGrid(
            id="metadata_table",
            style={'width': '100vh','margin-left': '15px'},
            columnDefs=columnDefs,
            rowData=df_metadata.to_dict('records'),
            columnSize="sizeToFit",
            selectAll=True,
            #defaultColDef={"filter": True},
            dashGridOptions={
                    "rowSelection": "multiple",
                    "animateRows": False
                },
        ),
        html.Br(),
        dbc.Row([
            dbc.Col(
                html.Label('Reference Genome for projection ', style={'margin-right': '15px'},),
                ),
            dbc.Col(
                dcc.Dropdown(
                    id='reference',
                    style={'width': '500px'},
                    multi=False
                )) 
        ]),

        
    ]), 
    print("yesss")
    return html_div, {'display': 'none'}

#############################################################
# Callback for cluster selection from heatmap or from table
#############################################################
@callback(
    #Output('cluster_info', 'children'),
    Output('selected_cluster', 'children'),
    Output('genes_cluster', 'rowData'),
    Output('my-default-alignment-viewer', 'data'),
    Output("current_cluster",'options'),
    Output("specific_to",'value'),
    Input('PAV_graph', 'clickData'),
    Input('metadata_table','selectedRows'),
    State('projets', 'value'),
    State('url','hash')
)

def display_click_data(clickData,metadata_table,projets,url):
         
    cluster = 1
    pathname = "#"+projets
    if url:
        pathname=url
    list_of_strains = []
    if metadata_table:
        wjdata1 = json.loads(json.dumps(metadata_table, indent=2))
        for strain in wjdata1:
            strain_name = strain['Strain name']
            list_of_strains.append(strain_name)
            
    if clickData:
        wjdata = json.loads(json.dumps(clickData, indent=2))
        cluster = wjdata['points'][0]['x']
    
    nb_presence,dictionary,data = get_cluster_details(cluster,pathname,list_of_strains)
    rowData = dictionary
    selected_cluster = "Selected cluster id: " + str(cluster)

    list_strains = get_combination(cluster,pathname,list_of_strains)
        
    return selected_cluster,dictionary,data, [{'label': str(cluster), 'value': str(cluster)}],list_strains


##########################################
# when clicking in the table of pangenes
##########################################
@callback(
    Output('selected_cluster', 'children', allow_duplicate=True),
    Output('genes_cluster', 'rowData', allow_duplicate=True),
    Output('my-default-alignment-viewer', 'data', allow_duplicate=True),
    Output("current_cluster",'options', allow_duplicate=True),
    Input('table_pangenes', 'cellClicked'),
    Input('metadata_table','selectedRows'),
    State('projets', 'value'),
    State('url','hash'),
    prevent_initial_call=True
)
def display_click_data(cell,metadata_table,projets,url):
         
    pathname = "#"+projets
    if url:
        pathname=url
    cluster = 1
    list_of_strains = []

    if metadata_table:
        print("ok")
        wjdata1 = json.loads(json.dumps(metadata_table, indent=2))
        for strain in wjdata1:
            strain_name = strain['Strain name']
            list_of_strains.append(strain_name)  
    if cell:
        wjdata = json.loads(json.dumps(cell, indent=2))
        cluster = wjdata['value']
        nb_presence,dictionary,data = get_cluster_details(cluster,pathname,list_of_strains)
        selected_cluster = "Selected cluster id:" + str(cluster)
        return selected_cluster,dictionary, data, [{'label': str(cluster), 'value': str(cluster)}]
    else:
        return "",[],"",[]


@callback(
    Output('current_cluster', 'value'),
    Input('current_cluster', 'options')
)
def set_current_cluster(available_options):
    if available_options:
        return available_options[0]['value']
    else:
        return ''
    


    
@callback(
    Output('selected_cluster', 'children', allow_duplicate=True),
    Output('genes_cluster', 'rowData', allow_duplicate=True),
    Output('my-default-alignment-viewer', 'data', allow_duplicate=True),
    Input('table_of_search', 'cellClicked'),
    Input('metadata_table','selectedRows'),
    Input('projets', 'value'),
    Input('url','hash'),
    prevent_initial_call=True
)

def display_click_data(cell,metadata_table,projets,url):
         
    pathname = "#"+projets
    if url:
        pathname=url
    cluster = 1
    list_of_strains = []
    if metadata_table:
        wjdata1 = json.loads(json.dumps(metadata_table, indent=2))
        for strain in wjdata1:
            strain_name = strain['Strain name']
            list_of_strains.append(strain_name)
    print(list_of_strains)    
    if cell:
        wjdata = json.loads(json.dumps(cell, indent=2))
        cluster = wjdata['value']
        nb_presence,dictionary,data = get_cluster_details(cluster,pathname,list_of_strains)
        selected_cluster = "Selected cluster id:" + str(cluster) 
        return selected_cluster,dictionary,data
    else:
        return "",[],""
        


        
def get_cluster_details(cluster,pathname,list_of_strains):
    
    global directory
    if len(pathname) > 1:
        directory = conf["data_dir"] + "/" + pathname.replace("#", "")
    #    if os.path.isdir(directory):
    #        print("exists")
    #    else:
    #        print("dir to be imported")
    
    df_matrix = pd.read_csv(directory+'/1.Orthologs_Cluster.txt',sep='\t')
    mini_df = df_matrix[df_matrix["ClutserID"] == int(cluster)]
    
    # generate a new dataframe from a list of list
    list_of_list = []
    nb_presence = 0
    combination = ""
    print("Combination")
    for item in mini_df.columns:
        if item != 'ClutserID' and item in list_of_strains:
            genes = mini_df[item]
            keep = True
            
            for gene in genes:
                if gene == "-":
                    keep = False
            if keep:
                list_genes = ','.join(map(str,genes)) 
                list = [int(cluster),item,list_genes]
                list_of_list.append(list)
                nb_presence+=1
                combination = combination+str(item)
    print(str(combination))
    mydf = pd.DataFrame(list_of_list, columns = ['Cluster','Species','Genes']) 
    
    concat = ""
    for gene in list_of_list:
        speciesname = gene[1]
        genename = gene[2]
        cmd = "grep -A 1 '"+genename+"' "+directory+"/genomes/genomes/"+speciesname+".faa | tail -1"
        result = os.popen(cmd).read()

        concat = concat + ">"+genename + "_" + speciesname + "\n" + result
        
    data = concat
    #print(data)
    #data = ">test\nP\t>test2\nP"
    mydf.to_csv('export_cluster_details.txt')
    dictionary = mydf.to_dict('records')

    return nb_presence,dictionary,data


#################################################
# callback for changing list of strains for pivot
#################################################
@callback(
    Output('reference', 'options'),
    Output('specific_to','options'),
    #Input('sp', 'value'),
    #Input('continent', 'value'),
    #Input('organism', 'value'),
    Input('metadata_table','selectedRows'),
    Input('projets', 'value'),
    Input('url','hash')
    #Input('datatable-paging', "page_current"),
    #Input('datatable-paging', "page_size"),
     )
def update_pivot(metadata_table,projets,url):
    pathname = "#"+projets
    if url:
        pathname=url
    #df,df_metadata,df_ANI,merged_with_positions,list_species,list_continent,list_organisms,karyotype_dict_list,dict_list_gene_plus,dict_list_gene_minus,df_matrix = init_dataframes(pathname)
    #df_metadata3 = df_metadata[(df_metadata["Continent"] != "none")]
    #df_metadata5 = df_metadata3[(df_metadata3["Organism"] != "none")]
    
    #if (continent != "all"):
    #    df_metadata2 = df_metadata[(df_metadata["Continent"] == continent) | (df_metadata["Continent"] == "none")]
    #    df_metadata3 = df_metadata[df_metadata["Continent"] == continent]
        
    #if (organism != "all"):
    #    df_metadata4 = df_metadata3[(df_metadata3["Organism"] == organism) | (df_metadata3["Organism"] == "none")]
    #    df_metadata5 = df_metadata3[df_metadata3["Organism"] == organism]
        
    reference_list = []
    if metadata_table:
        wjdata = json.loads(json.dumps(metadata_table, indent=2))
        val = wjdata
        for strain in wjdata:
            strain_name = strain['Strain name']
            reference_list.append(strain_name)
            
    #reference_list=df_metadata3['Strain']
    #reference_list=df_metadata5['Strain name']
    return [{'label': i, 'value': i} for i in reference_list], [{'label': i, 'value': i} for i in reference_list]


@callback(
    Output('reference', 'value'),
    Input('reference', 'options')
)
def set_reference_value(available_options):
    if available_options:
        return available_options[0]['value']
    else:
        return ''

@callback(
        Output('dynamic_network','children'),
        Output('graph_mlva', 'figure'),
        Input('submit-vntr', 'n_clicks'),
        State('mlva_table','selectedRows'),
        State('metadata_table','selectedRows'),
        prevent_initial_call=True
        
)

def update_MLVA(submit_vntr,mlva_table,metadata_table):

    ###########################################################
    # MLVA
    ###########################################################
    list_selected = ['ID','Repeat','Flanking']
    #if submit_samples:
    if metadata_table:
        wjdata = json.loads(json.dumps(metadata_table, indent=2))
        val = wjdata
        for strain in wjdata:
            strain_name = strain['Strain name']
            list_selected.append(strain_name)
                
    else:
        for value in df_metadata2['Strain name']:
            list_selected.append(value)


    session = random.randint(1, 9000000)
    vntr_file = directory+'/vntr_matrix.tsv'

    print("submit vntr button" + str(submit_vntr) + " "+str(session))

    df_vntr = pd.DataFrame(columns=['ID'])
    if os.path.exists(vntr_file):

        # remove lines/markers with missing data
        vntr_file_nomissing = directory+'/vntr_matrix.nomissing.tsv'
        cmd = "grep -v '-' "+vntr_file+ " >"+vntr_file_nomissing
        returned_value = os.system(cmd)

        df_vntr = pd.read_csv(vntr_file_nomissing,sep='\t')
        df_vntr_filtered = df_vntr[list_selected]
        print(df_vntr_filtered.columns)
        df_vntr = df_vntr_filtered


    repeat_names = df_vntr["ID"].astype(str).tolist()
    print("Filtered vntr")
    print(list_selected)
    

    repeats = []
    if mlva_table:
        wjdata1 = json.loads(json.dumps(mlva_table, indent=2))
        for vntr in wjdata1:
            #print(vntr)
            vntr_name = vntr['ID']
            repeats.append(vntr_name) 

    
    #print(repeats)
    mask = df_vntr['ID'].isin(repeats)
    testdf = df_vntr[mask]
    newdf = testdf.drop(["ID","Repeat","Flanking"], axis='columns')
    #print(df_vntr)
    graph_mlva = px.imshow(newdf, 
                           aspect="auto",
                           labels=dict(x="Samples", y="VNTR loci", color="Number of repeats"),
                           #x=list_sp2,
                           y=repeats,
                           text_auto=True
                           )
    mlva_table = df_vntr.to_dict('records')


    
    transposed_newdf = newdf.transpose()

    

    # concatenate numbers of repeats as an haplotype value for each sample
    transposed_newdf['haplotype'] = transposed_newdf.astype(str).agg('_'.join, axis=1)

    # assign metadata to haplotype
    df_metadata_tmp = pd.read_csv(directory+'/metadata.tmp.xls',sep='\t')
    dict_metadata = df_metadata_tmp.set_index('Strain name')['Country'].to_dict()
    dict_haplo = {}
    dict_element_for_colorizing = {}
    for strain, row in transposed_newdf.iterrows():
        country = dict_metadata[strain]
        dict_element_for_colorizing[country]=1
        if row.haplotype in dict_haplo.keys():
            dict_haplo[row.haplotype] = dict_haplo[row.haplotype] + "," + str(country)
        else:
            dict_haplo[row.haplotype] = str(country)

    transposed_newdf.to_csv(tmp_dir+"/"+str(session)+".strain_haplotypes.txt")

    #dictionary_haplotype_of_strain = transposed_newdf.set_index('strains')['haplotype'].to_dict()

    


    # put frequency of haplotypes into a dictionnary 
    dico_freq = transposed_newdf['haplotype'].value_counts().to_dict()
    haplotype_freq_df = pd.DataFrame([dico_freq]).transpose()
    haplotype_freq_df.to_csv(tmp_dir+"/"+str(session)+".haplotype_frequency.txt")


    with open(tmp_dir+"/"+str(session)+".haplotypes.txt", 'a') as f, open("assets/network."+str(session)+".1.json", 'a') as j:
        for i in range(len(newdf)):
            f.write(","+str(i))
        
        j.write("{\n")
        j.write("  \"nodes\": [\n")
        f.write("\n")
        i = 0
        concat = ""
        for row in haplotype_freq_df.itertuples():
            i+=1
            haplotype = row[0]
            size = row[1]
            country = dict_haplo[haplotype]
            list_countries = dict_haplo[haplotype].split(",")
            concat = concat + "{\"id\": \"haplo" + str(i)+"\",\"size\":"+str(10 * size)+","
            color_nb = 0
            concat = concat + "\"pieChart\" : ["
            subconcat = ""
            for country in dict_element_for_colorizing.keys():
                nb_occurence = list_countries.count(country)
                percentage = (nb_occurence / size) * 100
                if nb_occurence > 0:
                    subconcat = subconcat + "{ \"color\": \"" + colors[color_nb] + "\", \"percent\": " + str(percentage) + " },"

                color_nb += 1
            subconcat = subconcat[:len(subconcat)-1]

            concat = concat + subconcat + "]},\n"
            f.write("haplo"+str(i)+","+row[0].replace("_", ",")+"\n")
        
        concat = concat[:len(concat)-2]
        j.write(concat+"\n")
        j.write("],\n")

    # run haplotype network
    cmd = "python haplotype_network.py -i " + tmp_dir+"/"+str(session)+".haplotypes.txt -o " + tmp_dir+"/"+str(session) + " >> " + tmp_dir+"/haplotype_network.log 2>&1"
    returned_value = os.system(cmd)

    with open("assets/network."+str(session)+".2.json", 'a') as j, open(tmp_dir+"/"+str(session)+".haplotype_network.csv",'r') as n:
        j.write("  \"links\": [\n")

        lines = n.readlines()[1:]
        concat = ""
        for line in lines:
            informations = line.split(',')
            concat = concat + "{\"source\": \""+informations[0]+"\", \"target\": \""+ informations[1] +"\", \"value\": "+ informations[2] +"},\n"

        concat = concat[:len(concat)-2]
        j.write(concat+"\n")
        j.write("]\n")
        j.write("}\n")

    cmd = "cat assets/network."+str(session)+".1.json assets/network."+str(session)+".2.json > assets/network."+str(session)+".json"
    returned_value = os.system(cmd)

    # add the prefix haplo to indexes
    #haplotype_freq_df.index = [f"haplo{i+1}" for i in range(len(haplotype_freq_df))]

    cmd = "sed \"s/SESSION/" + str(session) + "/g\" assets/network_template.html >assets/network."+str(session)+".html"
    returned_value = os.system(cmd)

    dynamic_network = html.Iframe(src="assets/network."+str(session)+".html",style={"height": "1000px", "width": "100%"}),

    return dynamic_network, graph_mlva

#################################################
# callback for changing graphes
#################################################
@callback(
    Output("nb_of_pangenes",'children'),
    Output('textarea-example-output', 'children'),
    Output('PAV_graph', 'figure'),
    Output('table_pangenes', 'rowData'),
    
    #Output('datatable-paging','srcDoc'),
    Output('graph_ANI', 'figure'),
    Output('graph_gene', 'figure'),
    Output('graph_pie', 'figure'),
    Output('graph_COG_all', 'figure'),
    Output('graph_COG1', 'figure'),
    Output('graph_COG2', 'figure'),
    Output('rarefaction', 'figure'),
    Output("my-dashbio-default-circos", "layout"),
    Output("my-dashbio-default-circos", "tracks"),
    Output("table_of_search",'rowData'),
    Output("clustersearch",'children'),
    Output("graph_macrosynteny", 'figure'),
    Output('clinker','children'),
    Output('mlva_table', 'rowData'),
    Output('flanking','value'),
    Output('PCA','figure'),
    Output('iframe-content', 'src'),
    Output('results', 'style'),
    Output('sNMF', 'figure'),
    Output('sNMF_cross_entropy', 'figure'),
    Output('geo_map', 'figure'),
    #Output('graph_upset', 'figure'),
    #Input('sp', 'value'),
    #Input('continent', 'value'),
    #Input('organism', 'value'),
    State('reference', 'value'),
    State('ordering', 'value'),
    State('colorizing', 'value'),
    State('highlight', 'value'),
    State('projets', 'value'),
    State('url','hash'),
    Input('submit-val', 'n_clicks'),
    State('specific_to','value'),
    State('cluster_search','value'),
    State('bedfile','value'),
    State('metadata_table','selectedRows'),
    State("my-dashbio-default-circos", "layout"),
    State("my-dashbio-default-circos", "tracks"),
    prevent_initial_call=True
    #Input('datatable-paging', "page_current"),
    #Input('datatable-paging', "page_size"),
     )
def update_graph(reference,ordering,colorizing,highlight,projets,url,submit_button,specific_to,cluster_search,bedfile,metadata_table,current_layout,current_tracks):
    
    print("================ Start Update graphes ===========")

    pathname = "#"+projets
    if url:
        pathname=url
    df,df_metadata,df_ANI,merged_with_positions,list_species,list_continent,list_organisms,karyotype_dict_list,dict_list_gene_plus,dict_list_gene_minus,df_matrix = init_dataframes(pathname)
    
    
    
        
    directory = "data/african_Xo"
    with open("panexplorer_config.yaml", "r") as yaml_file:
        conf = yaml.safe_load(yaml_file)
        directory = conf["directory"]
    
    if len(pathname) > 1:
        directory = conf["data_dir"] + "/" + pathname.replace("#", "")
        if os.path.isdir(directory):
            print("exists")
        else:
            print("dir to be importeddd")
    #5743742574445.Lactococcus_Lactis

    list_of_lists = []
    # with clusterID
    df_metadata2 = df_metadata
    # without clusterID
    df_metadata3 = df_metadata[(df_metadata["Continent"] != "none")]
    
    #if (continent != "all"):
    #    df_metadata2 = df_metadata2[(df_metadata2["Continent"] == continent) | (df_metadata2["Continent"] == "none")]
    #    df_metadata3 = df_metadata3[df_metadata3["Continent"] == continent]
        
    #if (organism != "all"):
    #    df_metadata2 = df_metadata2[(df_metadata2["Organism"] == organism) | (df_metadata2["Organism"] == "none")]
    #    df_metadata3 = df_metadata3[df_metadata3["Organism"] == organism]

    

    list_selected = ['ClutserID']
    #if submit_samples:
    if metadata_table:
        wjdata = json.loads(json.dumps(metadata_table, indent=2))
        val = wjdata
        for strain in wjdata:
            strain_name = strain['Strain name']
            list_selected.append(strain_name)
                
    else:
        for value in df_metadata2['Strain name']:
            list_selected.append(value)
            

    
    ####################################################################
    # intersection between ordered list of samples and selected samples
    ####################################################################
    
    list_sp2 = []
    list_sp = []
    list1 = []
    for value in df.columns:
        list1.append(value)


    for value in list1:
        if value in list_selected:
            list_sp.append(value)
            if value != 'ClutserID':
                list_sp2.append(value)
      
    
    nb_pangenes = 0
    nb_coregenes = 0
    nb_specific_genes = 0
    cluster_names=[]
    cluster_indexes=[]
    
    
    df2 = df[list_sp]

    

    
    # add sum column indicating the number of strains holding the gene
    df2['sum'] = df2.drop('ClutserID', axis=1).sum(axis=1)
    

    # get only if at least one gene is present
    df2 = df2[df2["sum"] > 0]
    
    # remove CLUSTER tag (TODO: to be removed)
    df2['ClutserID']= df2['ClutserID'].astype(str)
    df2['ClutserID'] = df2['ClutserID'].str.replace('CLUSTER000','')
    df2['ClutserID'] = df2['ClutserID'].str.replace('CLUSTER00','')
    df2['ClutserID'] = df2['ClutserID'].str.replace('CLUSTER0','')
    df2['ClutserID'] = df2['ClutserID'].str.replace('CLUSTER','')
    cluster_names = df2["ClutserID"]
    
    
    df2.loc[df2['sum'] == 1, 'type'] = 'Strain-specific'
    df2.loc[df2['sum'] == len(list_sp2), 'type'] = 'Core-gene'
    df2.loc[(df2['sum'] < len(list_sp2)) & (df2['sum'] > 1), 'type'] = 'Dispensable-gene'
    
    df2.to_csv("export_df2.csv")
    
    ##############################################
    # Generate Core-gene and accessory files
    ##############################################
    cmd = "awk {'print $1\"\t\"$2\"\t\"$3'} "+directory+"/cog_of_clusters.txt >"+directory+"/cog_of_clusters.2.txt"
    returned_value = os.system(cmd)

    df_cog_of_clusters = pd.read_csv(directory+'/cog_of_clusters.2.txt',sep='\t')
    
    df_cog_of_clusters.columns = ['Cluster', 'COG', 'COGcat']


    df2[['ClutserID']] = df2[['ClutserID']].apply(pd.to_numeric)

    # get only the first COG assigned to a cluster
    df_cog_of_clusters_grouped_by_cluster = df_cog_of_clusters.groupby('Cluster').first()
    print(df_cog_of_clusters_grouped_by_cluster)

    #df_cog_of_clusters_grouped_by_cluster = df_cog_of_clusters_grouped_by_cluster.astype({"Cluster": int})
    merged_with_cog = pd.merge(df2, df_cog_of_clusters_grouped_by_cluster, how="left", left_on='ClutserID', right_on='Cluster')

    df_cog_terms = pd.read_csv('COG_terms.txt',sep='\t')

    merged_with_cog_term = pd.merge(df_cog_terms, merged_with_cog, how="right", left_on='COG', right_on='COG')

    merged_with_cog = merged_with_cog_term
    merged_with_cog.to_csv(directory+"/merged_with_cog.txt")
    #merged_with_cog_term.to_csv(directory+"/merged_with_cog_term.txt")




    core_df = merged_with_cog[merged_with_cog["sum"] == len(list_sp2)]
    specific_df = merged_with_cog[merged_with_cog["sum"] == 1]
    accessory_df = merged_with_cog[(merged_with_cog["sum"] != 1) & (merged_with_cog["sum"] < len(list_sp2))]
    
    nb_pangenes = len(df2)

    
    
    nb_specific_genes = len(specific_df)
    nb_coregenes = len(core_df)
    nb_accessory = nb_pangenes - nb_specific_genes - nb_coregenes

    print("Nb specific: "+str(nb_specific_genes))

    
    
    #################################################
    # pie chart
    #################################################
    dic = {}
    dic['Type'] = ['Strain-specific','Core genes','Accessory genes']
    dic['Nb'] = [nb_specific_genes,nb_coregenes,nb_accessory]
    df_synthesis = pd.DataFrame.from_dict(dic)
    
    fig_pie = px.pie(df_synthesis, values='Nb', names='Type', title='Distribution of core-genes and accessory genes')
    
    

    ####################################################################
    # Generate rarefaction curve. Takes randomly N columns from dataframe
    # and counts number of pan- and core-genes
    ####################################################################
    strain_index = 0
    df01_only = df[list_sp2]
    
    list1 = []
    list2 = []
    list3 = []
    
    for strain in list_sp2:
        strain_index+=1
        for number in range(3):
            df_random = df01_only.sample(n=strain_index, axis='columns') 
            
            df_random['sum'] = df_random.sum(axis=1)
            # get pangenes: keep only if at least one gene is present
            df_random = df_random[df_random["sum"] > 0]
            n_pangenes = len(df_random)
            df_random = df_random[df_random["sum"] == strain_index]
            n_coregenes = len(df_random)
            list1.append(str(strain_index))
            list1.append(str(strain_index))
            list2.append(str(n_pangenes))
            list2.append(str(n_coregenes))
            list3.append("Pan-genes")
            list3.append("Core-genes")

    data = {'Number strains': list1,'Number genes': list2,"Type": list3}
    df_rarefaction = pd.DataFrame(data)
    df_rarefaction.to_csv(tmp_dir + "/" +"rarefactiontest2.txt",index=False)
    df_rarefaction2 = pd.read_csv(tmp_dir + "/" +'rarefactiontest2.txt',sep=',')
    fig_rarefaction = px.box(df_rarefaction2, title="Rarefaction curve",x="Number strains", y="Number genes",color="Type")

    
    ##########################################################
    # test for changing color for specific genes or strains
    ##########################################################
    search_res2 = []
    if colorizing == "Level of presence":
        for sample in list_sp2:
            proportion = df2["sum"] / len(list_sp2)
            df2[sample] = np.where( (df2[sample] == 1),proportion,df2[sample])
    elif colorizing == "Continent":
        list_organisms = df_metadata3["Continent"].unique().tolist()
        count = 0
        association = {}
        for organism in list_organisms:
            count+=0.1
            association[organism] = count
            
        ordered_list_organisms = df_metadata3["Continent"]
        ordered_list_strains = df_metadata3["Strain name"]
        count = 0
        for sample in ordered_list_strains:
            organism = ordered_list_organisms[count]
            count+=1
            val = association[organism]
            df2[sample] = np.where( (df2[sample] == 1),val,df2[sample])
            
            
            
    elif highlight == "Reference genome":
        for sample in list_sp2:
            proportion = df2["sum"] / len(list_sp2)
            if sample == reference:
                df2[sample] = np.where( (df2[sample] == 1),1,df2[sample])
            else:
                df2[sample] = np.where( (df2[sample] == 1),0.67,df2[sample])
    elif highlight == "Core-genes":
        for sample in list_sp2:
            proportion = df2["sum"] / len(list_sp2)
            df2[sample] = np.where( (df2[sample] == 1) & (proportion != 1),0.67,df2[sample])
    elif highlight == "Strain-specific genes":
        for sample in list_sp2:
            proportion = df2["sum"] / len(list_sp2)
            df2[sample] = np.where( (df2[sample] == 1) & (df2["sum"] > 1),0.67,df2[sample])
            
    ##############################################
    # get clusters specific to a subset of samples
    ##############################################
    elif specific_to is not None and len(specific_to) > 0:
        list_of_clusters = [1000]
        
        # 1) get clusters for which gene is present for these samples
        specific_to.append("ClutserID")
        df_specific_to = df[specific_to]
        df_specific_to['sum'] = df_specific_to.drop('ClutserID', axis=1).sum(axis=1)
        # get only if at least one gene is present
        df_specific_to = df_specific_to[df_specific_to["sum"] == len(specific_to)-1]
        # remove CLUSTER tag (TODO: to be removed)

        #df_specific_to['ClutserID'] = df_specific_to['ClutserID'].str.replace('CLUSTER000','')
        #df_specific_to['ClutserID'] = df_specific_to['ClutserID'].str.replace('CLUSTER00','')
        #df_specific_to['ClutserID'] = df_specific_to['ClutserID'].str.replace('CLUSTER0','')
        #df_specific_to['ClutserID'] = df_specific_to['ClutserID'].str.replace('CLUSTER','')
        df_specific_to.to_csv("df_specific_to.csv")
        list1 = df_specific_to['ClutserID'].tolist()
        #list1bis = [eval(i) for i in list1]
        
        
        # 2) get clusters for which the number of presence correspond to the number of selected samples
        same_number_df = merged_with_cog[merged_with_cog["sum"] == len(specific_to)-1]
        same_number_df.to_csv("df_specific_to2.csv")
        list2 = same_number_df['ClutserID'].tolist()
        
        # 3) get overlapping clusters between the two dataframes
        intersected_list = [value for value in list1 if value in list2]
        print(intersected_list)
        print("Nb specific genes:")
        print(specific_to)
        print(len(intersected_list))

        
        
        df_search = pd.DataFrame(intersected_list, columns=['ClutserID'])
        search_res2 = df_search.to_dict('records')
        #df_specific_final2.to_csv("df_specific_to.csv")
        
        list_of_clusters = intersected_list

        df_search = pd.DataFrame(list_of_clusters, columns=['ClutserID'])

        


        search_res2 = df_search.to_dict('records')
        
        for sample in list_sp2:
            df2[sample] =  np.where( (df2[sample] == 1) & (df2["ClutserID"].isin(list_of_clusters)==False),0.67,df2[sample])
            
        print(len(search_res2))
        print("specific to: "+str(specific_to))
    elif cluster_search != "":
        
        #cmd = "grep -P '"+cluster_search+"' "+directory+"/1.Orthologs_Cluster.txt | awk {'print $1'}"
        #returned_value = os.popen(cmd).read()
        #cluster_search = returned_value
        #df_search = pd.DataFrame([int(returned_value)], columns=['ClutserID'])
        #search_res2 = df_search.to_dict('records')
        
        
        #COG1192
        
        list_of_clusters = []
        list_of_COGs = cluster_search.split(",")
        for cog in list_of_COGs:
            cmd = "grep -P '"+cog+"' "+directory+"/cog_of_clusters.txt | awk {'print $1'}"
            returned_value = os.popen(cmd).read()
            list_of_clusters1 = returned_value.split("\n")
            list_of_clusters.extend(list_of_clusters1)

        
        # remove empty values
        list_of_clusters = list(filter(None, list_of_clusters))
        list_of_clusters = list(map(int, list_of_clusters))
        
        df_search = pd.DataFrame(list_of_clusters, columns=['ClutserID'])
        search_res2 = df_search.to_dict('records')

        

        
        for sample in list_sp2:
            df2[sample] =  np.where( (df2[sample] == 1) & (df2["ClutserID"].isin(list_of_clusters)==False),0.67,df2[sample])

    
    
    

    #################################################
    # manage Circos
    #################################################
    #gene_position_file = 'data/Xo/'+reference+'.ptt'
    gene_position_file = directory+'/genomes/genomes/'+str(reference)+'.ptt'
    gene_position_file2 = directory+'/genomes/genomes/'+str(reference)+'.2.ptt'
    
    
    # Remove lines from ptt
    cmd = "grep -P 'Location|^\d+\.\.' "+ directory+"/genomes/genomes/"+reference+".ptt >"+directory+"/genomes/genomes/"+reference+".2.ptt"
    returned_value = os.system(cmd)
    merged_with_positions2 = []
    if os.path.exists(gene_position_file) & os.path.exists(gene_position_file2):
        #df_gene_positons = pd.read_csv('data/Xo/'+reference+'.ptt',sep='\t')
        df_gene_positons = pd.read_csv(directory+'/genomes/genomes/'+reference+'.2.ptt',sep='\t')

        if 'block_id' not in df_gene_positons.columns:
            df_gene_positons.insert(0, 'block_id', 'chr1')

        # create a simplified matrix, with only the first gene if a list of genes for the reference
        simplified_df_matrix = df_matrix
        simplified_df_matrix[[reference]] = simplified_df_matrix[reference].str.extract('([^,]+),*', expand=True)

        merged_with_positions = pd.merge(simplified_df_matrix, df_gene_positons, left_on=reference, right_on='PID')
        #merged_with_positions = pd.merge(df_matrix, df_gene_positons, left_on=reference, right_on='PID')


        # rename and reorganize columns
        merged_with_positions = merged_with_positions.rename(columns={'ClutserID': 'name'})
        merged_with_positions[['start', 'end']] = merged_with_positions['Location'].str.split('\.\.', expand=True)
        merged_with_positions2 = merged_with_positions
        #merged_with_positions.insert(0, 'block_id', 'chr1')
        merged_with_positions.insert(0, 'color', 'black')
        merged_with_positions = merged_with_positions[['name','block_id','start', 'end','color','Strand']]
        merged_with_positions['start'] = merged_with_positions['start'].astype(int)
        gene_plus_df = merged_with_positions[merged_with_positions["Strand"] == "+"]
        gene_minus_df = merged_with_positions[merged_with_positions["Strand"] == "-"]
        dict_list_gene_plus = gene_plus_df.to_dict('records')
        dict_list_gene_minus = gene_minus_df.to_dict('records')
        karyotype_df = merged_with_positions.groupby('block_id').max().reset_index()
        karyotype_df = karyotype_df.rename(columns={'block_id': 'id'})
        karyotype_df['label'] = karyotype_df.loc[:, 'id']
        karyotype_df = karyotype_df.rename(columns={'start': 'len'})
        karyotype_df = karyotype_df[['id','label','len','color']]
        karyotype_dict_list = karyotype_df.to_dict('records')

    
    core_df['ClutserID'] = core_df['ClutserID'].astype(int)
    
    core_df_merged_with_positions = pd.merge(core_df, merged_with_positions, left_on='ClutserID', right_on='name')
    core_df_merged_with_positions = core_df_merged_with_positions[['name','block_id','start', 'end','color','Strand']]
    core_df_merged_with_positions.to_csv(directory+"/core.txt",index=False,sep='\t')
    core_list_dict = core_df_merged_with_positions.to_dict('records')

    specific_df['ClutserID'] = specific_df['ClutserID'].astype(int)
    specific_df_merged_with_positions = pd.merge(specific_df, merged_with_positions, left_on='ClutserID', right_on='name')
    specific_df_merged_with_positions = specific_df_merged_with_positions[['name','block_id','start', 'end','color','Strand']]
    specific_df_merged_with_positions.to_csv(directory+"/specific.txt",index=False,sep='\t')
    specific_list_dict = specific_df_merged_with_positions.to_dict('records')

    #specific_df_merged_with_positions.to_csv(directory+"/specific.txt",index=False,sep='\t')
    
    fig_gene = px.histogram(df2, x="sum")

    if bedfile is not None:

        print("analysis of bedfile")
        lines_of_bedfile = bedfile.split("\n")

        df_search = pd.DataFrame(merged_with_positions2, columns=['name','Product','start','end'])
        df_search['start'] = df_search['start'].astype(int)
        df_search['end'] = df_search['end'].astype(int)

        list_of_clusters = []
        for line in lines_of_bedfile:
            elements_of_line = line.split("\t")
            start = int(elements_of_line[1])
            end = int(elements_of_line[2])
            df_subset = df_search.loc[(df_search['start']>=start) & (df_search['end']< end)]
            df_subset.rename(columns={'name': 'ClutserID'}, inplace=True)
            list_of_clusters1 = df_subset['ClutserID'].tolist()
            list_of_clusters.extend(list_of_clusters1)

        df_search = pd.DataFrame(list_of_clusters, columns=['ClutserID'])
        search_res2 = df_search.to_dict('records')

        for sample in list_sp2:
            df2[sample] =  np.where( (df2[sample] == 1) & (df2["ClutserID"].isin(list_of_clusters)==False),0.67,df2[sample])



    if ordering == "Hierarchical clustering":
        
        # remove sum and clutserID from the col
        df2 = df2[list_sp2]
        transposed_df = df2.transpose() 
        
    else:
        # to be modified for ordering clusters along pivot genome
        merged_with_positions2 = merged_with_positions2[['start','name']]
        merged_with_positions2['start'] = merged_with_positions2['start'].astype(int)
        df2['ClutserID'] = df2['ClutserID'].astype(int)
        merged_with_positions3 = pd.merge(df2, merged_with_positions2, left_on='ClutserID', right_on='name')
        merged_with_positions3 = merged_with_positions3.sort_values(by=['start'],ascending=True)
        merged_with_positions3.to_csv("export.tsv")
        cluster_names = merged_with_positions3["ClutserID"].astype(str).tolist()
        merged_with_positions3 = merged_with_positions3[list_sp2]

        
    
        transposed_df = merged_with_positions3.transpose() 
    
    
    
    # Nb genes for each strain
    #fig_gene = px.bar(df, x='year', y='Nb_genes')
    
    colorscale = [[0, 'whitesmoke'], [1, 'teal']]
    if highlight != "None" or cluster_search != "" or bedfile is not None or specific_to is not None:
        colorscale = [[0, 'whitesmoke'], [0.67, 'teal'], [1, 'red']]
    elif colorizing == "Continent":
        colorscale = [[0, 'whitesmoke'], [0.1, 'yellow'], [0.2, 'red'], [0.3,'blue'], [0.4,'green'], [0.5,'brown'], [0.6,'pink'], [0.7,'orange']]
    fig = go.FigureWidget(data=go.Heatmap(
                   #z=[[1, 0, 0, 0, 1], [0, 1, 0, 0, 0], [0, 0, 1, 1, 0]],
                   #z=list_of_lists,
                   z=transposed_df,
                   y=list_sp2,
                   x=cluster_names,
                   #colorscale= [[0, 'whitesmoke'], [0.5, 'limegreen'], [0.67, 'tomato'], [1, 'teal']],
                   #colorscale= [[0, 'whitesmoke'], [0.33, 'limegreen'], [0.67, 'tomato'], [1, 'red']],
                   #colorscale= [[0, 'whitesmoke'], [1, 'teal']],
                   colorscale = colorscale,
                   hoverinfo='text+x+y+z',
                   hoverongaps = False))

    text="Number of genomes: " + str(len(list_sp2)) + ", Pangenome size: " + str(nb_pangenes)+" pan-genes and "+str(nb_coregenes)+" core-genes and "+str(nb_specific_genes)+" strain-specific genes"
    #fig.update_traces(showscale=False)
    fig.update_layout(clickmode='event+select')
    
    fig_ANI = None
    if os.path.exists(directory + "/fastani.out.matrix.complete.xls"):
        df_ANI_selected = df_ANI[df_ANI["Genomes"].isin(list_sp2)]
        df_ANI_selected = df_ANI_selected[list_sp2]
        df_ANI_selected.to_csv("export_ani.tsv")
        
        fig_ANI = dash_bio.Clustergram(
            data=df_ANI_selected,
            column_labels=list(df_ANI_selected.columns.values),
            row_labels=list(df_ANI_selected.index),
            #row_labels=list(df_ANI_selected.columns.values),
            height=1200,
            width=1700,
            center_values=False,
            line_width=2,
            color_map= [
                [0.0, 'yellow'],
                [1.0, 'red']
            ]
        )
    #fig_ANI.update_traces(showlegend=False) # does not work

    #df_ANI_selected.to_csv("export2.tsv")

    table_specific = specific_df.to_dict('records')
    table_core = core_df.to_dict('records')
    
    table_pangenes = merged_with_cog.to_dict('records')
    merged_with_cog.to_csv("export_merged_with_cog.csv")
    
    current_layout = karyotype_dict_list
    
    #current[0].update(data=circos_graph_data["cytobands"], type="HIGHLIGHT",config=highlight_config)
    current_tracks[0].update(data=dict_list_gene_plus,type="HIGHLIGHT",config=highlight_config1)
    current_tracks[1].update(data=dict_list_gene_minus,type="HIGHLIGHT",config=highlight_config2)
    current_tracks[2].update(data=core_list_dict,type="HIGHLIGHT",config=highlight_config3)
    current_tracks[3].update(data=specific_list_dict,type="HIGHLIGHT",config=highlight_config4)
    
    
    #########################################
    # Upset plot
    #########################################
    #set_list = ["Set A", "Set B", "Set C","Set D", "Set E", "Set F","Set G", "Set H", "Set I"]
    #df_upset = pd.DataFrame(
    #    np.random.randint(0, 2, size=(10_000, len(set_list))), columns=set_list
    #)
    #example = generate_counts()
    #example.to_csv("data/Xo/df_upset.csv",index=False,sep='\t')

    # Plotting
    #fig_upset = plot_upset(
    #    dataframes=[df_upset],
    #    exclude_zeros=True,
    #    sorted_x="d",
    #    sorted_y="a",
    #    max_y = 10,
    #    legendgroups=["Group X"],
    #    marker_size=16,
    #    height=1200,
    #    width=1700,
    #)
    #fig_upset.update_layout(
    #    #font_family="Jetbrains Mono",
    #)

    ##############################
    # COG graphes
    ##############################
    data_COG1 = pd.read_csv(directory+'/cog_category_counts.txt',sep='\t')
    data_COG1 = data_COG1.rename(columns={'COG': 'Genome'})
    data_COG2 = pd.read_csv(directory+'/cog_category_2_counts.txt',sep='\t')
    data_COG2 = data_COG2.rename(columns={'COG': 'Genome'})
    data_COG1_selected = data_COG1[data_COG1["Genome"].isin(list_sp2)]
    data_COG2_selected = data_COG2[data_COG2["Genome"].isin(list_sp2)]

    df_count = merged_with_cog.groupby(['COGcat']).size().reset_index(name='counts')
    df_count.to_csv("COG.count.txt")

    #dftet = px.data.tips()
    #dftet.to_csv("COG.count.txt")

    fig_COG_all = px.pie(df_count, values='counts', names='COGcat', title='Distribution of COG categories among all clusters')
    
    #data_COG2_selected.to_csv("export_COG.tsv")
    
    fig_COG1 = px.bar(data_COG1_selected, x='Genome', y=data_COG1_selected.columns, title="Distribution of COG functional categories")
    fig_COG2 = px.bar(data_COG2_selected, x='Genome', y=data_COG2_selected.columns, title="Distribution of COG functional categories")
    fig_COG1.update_layout(
        yaxis_title="Number of genes with COG category"
    )
    fig_COG2.update_layout(
        yaxis_title="Number of genes with COG category"
    )
    
    ############################################################
    # accessory-based tree
    ############################################################

    session = random.randint(1, 9000000)
    newick = ""
    
    # get tree in newick format as a variable
    with open(directory+'/heatmap.svg.complete.pdf.distance_matrix.hclust.newick') as fp:
        newick = fp.read()

    df_metadata.to_csv(directory+'/metadata.csv',sep=',',index=False)
    metadata_csv = ""
    with open(directory+'/metadata.csv') as fp:
        metadata_csv = fp.read()

    concat_for_hash = ""
    list_metadata_color = df_metadata['Country'].unique().tolist()
    dict_colors = {}
    i = 0



    legend = ""
    legend += "<style>"
    legend += ".legend div{display:flex;align-items:center;margin:4px 0}"
    legend += ".legend span{width:16px;height:16px;margin-right:6px}"
    legend += "</style>"
    legend += "<div class=\"legend\">"
    for country in list_metadata_color:
        if country != "none" and country != "None" and str(country) != "nan" and country != "":
            dict_colors[country] =  colors[i]
            legend = legend + "<div><span style=\"background:" + str(colors[i]) + "\"></span>" + str(country) + "</div>"
            i += 1
    legend += "</div>"

    for index, row in df_metadata.iterrows():
        color = "black"
        if str(row['Country']) in dict_colors:
            color = dict_colors[str(row['Country'])]
        concat_for_hash = concat_for_hash + "hash_colors['" + str(row['Strain name']) + "'] = '" + color + "';\n"

    # remove last caracter
    newick = newick.rstrip(newick[-1])
    f = open("assets/tree."+str(session)+".html", "w")
    template = open('assets/tree.html', 'r')
    for line in template:
        if re.search(r"NEWICK_TREE", line):
            f.write("var test_string = \""+newick+";\"\n")
        elif re.search(r"HASH_COLORS", line):
            f.write(concat_for_hash+"\n")
        elif re.search(r"LEGEND", line):
            f.write(legend+"\n")
        else:
            f.write(line)
    template.close()
    f.close()





    f = open("assets/taxonium."+str(session)+".html", "w")
    template = open('assets/taxonium.sample.html', 'r')
    for line in template:
        if re.search(r"NEWICK_TREE", line):
            f.write("const nwk = `" + newick + "`;\n")
        elif re.search(r"METADATA", line):
            f.write("const metadata_text = `" + metadata_csv + "`;\n")
        else:
            f.write(line)
    template.close()
    f.close()

    #cmd = "sed \"s/NEWICK_TREE/"+newick+"/g\" assets/tree.html >assets/tree."+str(session)+".html"
    #returned_value = os.system(cmd)


    dynamic_tree = html.Iframe(id='tree',src="../assets/taxonium."+str(session)+".html",style={"height": "1000px", "width": "100%"}),
    #dynamic_tree = cmd

    print("resulats recherche cluster: "+str(len(search_res2)))
    nb_of_pangenes = "Pan-genes (" + str(nb_pangenes) + ")"
    clustersearch = "Cluster Search: " + str(len(search_res2)) + " clusters"


    ############################################################
    # Calculate coordinates of core-genes for macrosynteny
    ############################################################

    print("Number of genes:")
    # remove duplicates from a list
    list_selected = list(dict.fromkeys(list_selected))
    
    df_matrix_filtered = df_matrix[list_selected]
    df_core_genes = pd.merge(df_matrix_filtered, core_df, how='inner', on=['ClutserID', 'ClutserID']) 

    df_core_genes.to_csv(tmp_dir + "/" + str(session) + ".core_genes.txt",sep="\t")

    list_selected.remove("ClutserID")
    max_nb_strains_macrosynteny = 20
    if len(list_selected) < max_nb_strains_macrosynteny:
        max_nb_strains_macrosynteny = len(list_selected)

    print("Max nb for synteny: " + str(max_nb_strains_macrosynteny))
    print(list_selected)

    selection_dir = tmp_dir+"/selection."+str(session)
    print(selection_dir)

    try:
        os.makedirs(selection_dir)
        print(f"Nested directories '{selection_dir}' created successfully.")
    except FileExistsError:
        print(f"One or more directories in '{selection_dir}' already exist.")
    except PermissionError:
        print(f"Permission denied: Unable to create '{selection_dir}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

    c=0
    list_of_species_macrosyneny = []
    for sp in list_selected:
        c+=1
        if (c >=1 and c <=(max_nb_strains_macrosynteny)):
            cmd = "cp -rf "+directory+"/genomes/genomes/"+sp+".ptt "+ selection_dir
            returned_value = os.system(cmd)
            list_of_species_macrosyneny.append(sp)

    cmd = "perl GetSyntenicBlocks.pl "+selection_dir+" " + tmp_dir + "/" + str(session) + ".core_genes.txt " + tmp_dir + "/" + str(session) + ".syntenic_blocks.txt 10"
    returned_value = os.system(cmd)

    # add the prefix haplo to indexes
    #haplotype_freq_df.index = [f"haplo{i+1}" for i in range(len(haplotype_freq_df))]

    cmd = "cat assets/clinker_template.part1.html " + tmp_dir + "/" + str(session) + ".syntenic_blocks.txt.clinker.json assets/clinker_template.part2.html >assets/clinker."+str(session)+".html"
    returned_value = os.system(cmd)

    clinker = html.Iframe(src="assets/clinker."+str(session)+".html",style={"height": "2000px", "width": "100%"}),

    # #df_core_genes2 = df_core_genes[list_species]
    # #print(df_core_genes)
    # genes_coordinates = {}
    # c=0
    # for sp in list_selected:
    #     c+=1
    #     if (c >=1 and c <=(max_nb_strains_macrosynteny)):
    #         cmd = "grep -P 'Location|^\d+\.\.' "+directory+"/genomes/genomes/"+sp+".ptt >"+directory+"/genomes/genomes/"+sp+".2.ptt"
    #         returned_value = os.system(cmd)
    #         df_gene_positons = pd.read_csv(directory+'/genomes/genomes/'+sp+'.2.ptt',sep='\t')
            
    #         for row in df_gene_positons.itertuples():
    #             gene = row[4]
    #             position = row[1]
    #             chrom = row[5]

    #             # case bacteria 
    #             if len(row) > 6:
    #                 chrom='1'

    #             # case eukaryotes
    #             else:
    #                 chrom_number = re.findall(r'\d+', str(chrom))
    #                 if len(chrom_number) > 0:
    #                     chrom = chrom_number[0]  
                    
    #             genes_coordinates[str(gene)]= str(chrom) + ":" + str(position)
        
            



    
            
    # fichier = open('coregenes_coordinates.txt', 'w')
    # c=0
    # #for specie in df_core_genes:
    # for specie in list_selected:
    #     #specie = specie[:-2]
    #     #print("specie:"+specie)
    #     c+=1
    #     if (c >=1 and c <=(max_nb_strains_macrosynteny)):
    #         fichier.write("," + specie)
    #         list_of_species_macrosyneny.append(specie)
 
    # fichier.write('\n')
    # num_cores = 0
    # for row in df_core_genes.itertuples():
    #     num_cores+=1
    #     concat = ''
    #     dict_chrom = {}
    #     for i in range(2,max_nb_strains_macrosynteny+2):
    #         genes = row[i].split(',')
    #         gene = genes[0]
            
    #         if gene in genes_coordinates.keys():
    #             position = genes_coordinates[str(gene)]
    #             chrom = position.split(':')[0]
    #             dict_chrom[chrom] = 1
    #             if int(chrom) == 1:
    #             #if int(chrom) >= 1:
    #                 positions = position.split(':')[1]
    #                 start = int(positions.split('..')[0])
    #                 #start += (int(chrom) * 40000000)
    #                 if concat == '':
    #                     concat = str(num_cores)
    #                 concat = concat + ',' + str(start)
    #     # only print if the chrom is the same for each genome
    #     if concat != '' and len(dict_chrom) == 1:
    #         fichier.write(concat + '\n')


    #df_macrosynteny = px.data.iris()
    #df_macrosynteny.to_csv("iris.txt")
    #df_macrosynteny = pd.read_csv('coregenes_coordinates.txt',sep=',')
    df_macrosynteny = pd.read_csv(tmp_dir + "/" + str(session) + ".syntenic_blocks.txt",sep=',')
    graph_macrosynteny = px.parallel_coordinates(df_macrosynteny,color="num_block",
                              dimensions=list_of_species_macrosyneny,
                              #dimensions = ["Genus_species_CIX5672gb","Genus_species_CIX696gb","Genus_species_CIX767gb","Genus_species_CIX691gb"],
                              #color_continuous_scale=px.colors.diverging.Tealrose,
                              #color_continuous_midpoint=2
                              )

    ##############################################################################################
    # VNTR table / MLVA
    ##############################################################################################
    vntr_file = directory+'/vntr_matrix.tsv'


    df_vntr = pd.DataFrame(columns=['ID','Repeat'])
    flanking_sequences = ""
    if os.path.exists(vntr_file):

        # remove lines/markers with missing data
        vntr_file_nomissing = directory+'/vntr_matrix.nomissing.tsv'
        cmd = "grep -v '-' "+vntr_file+ " >"+vntr_file_nomissing
        returned_value = os.system(cmd)

        df_vntr = pd.read_csv(vntr_file_nomissing,sep='\t')

        df_vntr_filtered = df_vntr.drop(list_selected, axis=1)
        df_vntr = df_vntr_filtered

        for row in df_vntr.itertuples():
            id = row[1]
            flanking = row[3]
            flanking_sequences = flanking_sequences + ">" + str(id) + "\n" + str(flanking) + "\n"
            

    
    repeat_names = df_vntr["ID"].astype(str).tolist()

    

    newdf = df_vntr.drop("ID", axis='columns')
    graph_mlva = px.imshow(newdf, 
                           aspect="auto",
                           labels=dict(x="Samples", y="VNTR loci", color="Number of repeats"),
                           #x=list_sp2,
                           y=repeat_names,
                           text_auto=True
                           )
    mlva_table = df_vntr.to_dict('records')

    ##############################################################################################
    # SNP
    ##############################################################################################
    vcf_file = directory+"/variants.vcf"
    df_pca = pd.DataFrame(columns=['#IID', 'PC1', 'PC2','PC3'])
    df_crossentropy = pd.DataFrame(columns=['K', 'Cross-entropy'])
    dfsnmf = pd.DataFrame(columns=['Individual','Ancestry','Cluster','K'])
    individual_order = []
    individual_order_by_Pop1 = []
    col_names = []
    if os.path.exists(vcf_file):

        #################################################################
        # Phylogenetic tree from SNPs
        #################################################################

        cmd = "plink2 --vcf " + vcf_file +" --max-alleles 2 --min-alleles 2 --make-bed --out "+ tmp_dir + "/" + str(session) + ".dataset"
        returned_value = os.system(cmd)

        cmd = "plink --bfile " + tmp_dir + "/" + str(session) + ".dataset --distance square --allow-extra-chr --out "+ tmp_dir + "/" + str(session) + ".dataset"
        returned_value = os.system(cmd)

        cmd = "grep -v '#FID' " + tmp_dir + "/" + str(session) + ".dataset.dist.id >"+ tmp_dir + "/" + str(session) + ".dataset.dist.id.2"
        returned_value = os.system(cmd)

        from skbio import DistanceMatrix
        from skbio.tree import nj

        # Charger les identifiants
        ids = pd.read_csv(tmp_dir + "/" + str(session) + ".dataset.dist.id.2", delim_whitespace=True, header=None)
        ids = ids[1].tolist()

        # Charger la matrice de distances
        D = np.loadtxt(tmp_dir + "/" + str(session) + ".dataset.dist")

        # Construire la matrice de distances scikit-bio
        dm = DistanceMatrix(D, ids)

        # Construire un arbre neighbor-joining
        tree = nj(dm)

        rooted_tree = tree.root_at_midpoint()

        # Sauvegarder au format Newick
        with open(tmp_dir + "/" + str(session) + ".dataset.tree", "w") as f:
            f.write(str(rooted_tree))

        # Extraire l'ordre des taxons dans l'arbre
        individual_order_by_Pop1 = [tip.name for tip in rooted_tree.tips()]

        #################################################################
        # Population structure with sNMF
        #################################################################
        cmd = "vcf2geno " + vcf_file +" " + tmp_dir + "/" + str(session) + ".variants.geno"
        returned_value = os.system(cmd)

        cmd = "grep '#CHROM' " + vcf_file
        result = os.popen(cmd).read()
        list_sp2 = result.strip().split("\t")[9:]

        with open(directory + "/1.Orthologs_Cluster.txt") as f:
            ordered_ids = f.readline().strip().split("\t")

        ordered_ids.remove("ClutserID")


        results = []
        list_entropy = []
        
        # Launch sNMF for K from 2 to 5
        for K in range(2, 6):
            cmd = "sNMF -x " + tmp_dir + "/" + str(session) + ".variants.geno" + " -c -K " + str(K)
            returned_value = os.popen(cmd).read()
            match = re.search(r"Cross-Entropy \(masked data\):\s*([0-9]+(?:\.[0-9]+)?)", returned_value)
            if match:
                valeur = float(match.group(1))
                list_entropy.append(valeur)

        # get the assignation of individuals to populations
        previous_dict_groups = {}
        previous_qmat = pd.DataFrame(columns=['Individual', 'Assigned_to_pop', 'max_prop'])
        for K in range(2, 6):
            ancestry_cols = [f"Pop_{i+1}" for i in range(K)]
            qmat = pd.read_csv(tmp_dir + "/" + str(session) + ".variants."+str(K)+".Q", sep=" ", header=None, names=ancestry_cols)
            qmat['Individual'] = list_sp2
            qmat['Assigned_to_pop'] = qmat[ancestry_cols].idxmax(axis=1)
            qmat['max_prop'] = qmat[ancestry_cols].max(axis=1)

            #print("\n\n")

            groups = qmat.groupby("Assigned_to_pop")["Individual"].agg(concat=lambda x: ", ".join(sorted(x)),size="count").reset_index().sort_values("size", ascending=False)
            #print(groups)
            #print(str(K))
            dict_groups = {}
            dict_renaming = {}
            dict_renaming2 = {}
            dict_done = {}
            dict_splitted = {}

            
            # first assignment for population with exact same individuals
            for row in groups.itertuples():
                pop_name = row[1]
                individuals = row[2]
                dict_groups[individuals] = pop_name
                #print(pop_name + " : " + individuals)
                # keep the same name of population if it exists in previous dict
                if individuals in previous_dict_groups:
                    previous_pop_name = previous_dict_groups[individuals]
                    dict_renaming[pop_name] = previous_pop_name
                    dict_done[previous_pop_name] = 1
                    #print("same as previous" + previous_pop_name)

            for row in groups.itertuples():
                pop_name = row[1]
                individuals = row[2]
                dict_groups[individuals] = pop_name
                #print(pop_name + " : " + individuals)
                # keep the same name of population if it exists in previous dict
                if individuals in previous_dict_groups:
                    print("do nothing here")
                # else it means that the pop has been splitted into two populations
                else:
                    if len(previous_dict_groups) > 0:
                        individuals_list = individuals.split(", ")
                        dict_of_pop_in_previous = {}
                        for ind in individuals_list:
                            # get the pop in previous qmat
                            pop = previous_qmat.loc[previous_qmat["Individual"] == ind, "Assigned_to_pop"].iloc[0]
                            
                            if pop not in dict_of_pop_in_previous:
                                dict_of_pop_in_previous[pop] = 1
                            else:
                                dict_of_pop_in_previous[pop] += 1
                            if pop not in dict_splitted:
                                dict_splitted[pop] = pop_name
                            else:
                                dict_splitted[pop] += ","+pop_name

                                

                        print("splitted")
                        
                        

                        # renaming for all except the last one
                        if len(dict_of_pop_in_previous) > 1:
                            #dict_renaming[pop_name] = list(dict_of_pop_in_previous)[0]+","+list(dict_of_pop_in_previous)[1]
                            if dict_of_pop_in_previous[list(dict_of_pop_in_previous)[0]] >= dict_of_pop_in_previous[list(dict_of_pop_in_previous)[1]] and list(dict_of_pop_in_previous)[0] not in dict_done:
                                dict_renaming[pop_name] = list(dict_of_pop_in_previous)[0]
                                dict_done[list(dict_of_pop_in_previous)[0]] = 1
                            elif dict_of_pop_in_previous[list(dict_of_pop_in_previous)[1]] >= dict_of_pop_in_previous[list(dict_of_pop_in_previous)[0]] and list(dict_of_pop_in_previous)[1] not in dict_done:
                                dict_renaming[pop_name] = list(dict_of_pop_in_previous)[1]
                                dict_done[list(dict_of_pop_in_previous)[1]] = 1
                            
                        else:
                            if list(dict_of_pop_in_previous)[0] not in dict_done:
                                dict_renaming[pop_name] = list(dict_of_pop_in_previous)[0]
                                dict_done[list(dict_of_pop_in_previous)[0]] = 1
                            else:
                                new_pop_name = "Pop_" + str(K)
                                if len(dict_of_pop_in_previous) > 1:
                                    dict_renaming[list(dict_of_pop_in_previous)[0]+","+list(dict_of_pop_in_previous)[1]] = new_pop_name
                                else:
                                    dict_renaming[pop_name] = new_pop_name
                                    dict_done[new_pop_name] = 1

                        #print(dict_of_pop_in_previous.keys())
                        #print(list(dict_of_pop_in_previous)[0])
                    else:
                        print("do nothing")

            #print("Dict renaming before adjustment")
            #print(dict_renaming)
            #print("Dict renaming after adjustment")
            #print(dict_renaming2)
            #print("Dict splitted")
            for key, value in dict_splitted.items():
                listvalue = value.split(",")
                dict_splitted[key] = list(dict.fromkeys(listvalue))
            
            #print(dict_splitted)
            list_keys_to_removed = []
            for key in dict_renaming.keys():
                value = dict_renaming[key]
                print("key: " + key + " => " + value)
                list_values = value.split(",")
                
                if len(list_values) > 1:
                    has_been_adjusted = 0
                    for val in list_values:
                        print("val: " + val)
                        if val not in dict_done:
                            print("to be adjusted :" + val + "=>" + key)
                            has_been_adjusted = 1
                            dict_renaming[key] = val
                    if has_been_adjusted == 0:
                        new_pop_name = "Pop_" + str(K)
                        dict_renaming[key] = new_pop_name
            

            #print(dict_renaming)
            # rename pop for keeping the same as previously
            #qmat = qmat.rename(columns=dict_renaming)
            #qmat2 = qmat.drop('Assigned_to_pop', axis=1)
            #qmat = qmat
            #qmat["Assigned_to_pop"] = qmat[ancestry_cols].idxmax(axis=1)
            #print(qmat)
            #qmat['Assigned_to_pop'] = qmat[ancestry_cols].idxmax(axis=1)

            previous_dict_groups = dict_groups
            previous_qmat = qmat
            #print(dict_groups)
            #print(previous_dict_groups)

            qmat_sorted = qmat.sort_values(
                by=['Assigned_to_pop', 'max_prop'],
                ascending=[True, False]
            )

            individual_order = qmat_sorted['Individual'].tolist()

            qmat['Individual'] = pd.Categorical(
                qmat['Individual'],
                categories=individual_order,
                ordered=True
            )

            qmat_long = qmat.melt(id_vars=['Individual'],
                          value_vars=ancestry_cols,
                          var_name='Cluster', value_name='Ancestry')


            qmat_long['K'] = K

            #print(qmat_long)

            results.append(qmat_long)

        
        dfsnmf = pd.concat(results)
        print(dfsnmf)

        dict_cross_entropy = {'K': range(2, 6),'Cross-entropy': list_entropy}
        df_crossentropy = pd.DataFrame.from_dict(dict_cross_entropy)



        #################################################################
        # PCA with plink
        #################################################################
        output_basename = tmp_dir+"/"+str(session)+".plink"
        pca_output = output_basename + ".eigenvec"

        cmd = "plink2 --vcf " + vcf_file +" --pca --out " + output_basename
        returned_value = os.system(cmd)

        if os.path.exists(pca_output):
            cmd = "awk {'print $1\"\t\"$2\"\t\"$3\"\t\"$4'} " + pca_output + ">" + pca_output + ".tsv"
            returned_value = os.system(cmd)

        if os.path.exists(pca_output + ".tsv"):
            df_pca = pd.read_csv(pca_output + ".tsv",sep='\t')

        
        

    df_pca_metadata=pd.merge(df_pca,df_metadata, left_on='#IID', right_on='Strain name' )
    fig_scatter = px.scatter_3d(df_pca_metadata, x='PC1', y='PC2', z='PC3', color='Country')

    # Création des barcharts avec facettes
    fig_snmf = px.bar(
        dfsnmf, 
        x="Individual", y="Ancestry", color="Cluster", category_orders={"Individual": individual_order_by_Pop1}, 
        facet_row="K",  # un graphique par valeur de K
        height=800
    )

    fig_snmf.update_layout(
        title="Population structure (by sNMF) for different K",
        barmode='stack',
        showlegend=True
    )

    fig_cross_entropy = px.line(df_crossentropy, x="K", y="Cross-entropy", title='Values of the cross-entropy criterion for 4 sNMF runs (K=2 to K=5)')

    #tree = Phylo.read(directory+"/heatmap.svg.complete.pdf.distance_matrix.hclust.newick", "newick")
    #Phylo.draw(tree)

    # from itolapi import Itol
    # from pathlib import Path
    # itol_uploader = Itol()
    # itol_uploader.add_file(Path(directory+"/heatmap.svg.complete.pdf.distance_matrix.hclust.newick"))
    # itol_uploader.params['treeName'] = 'apple'
    # status = itol_uploader.upload()
    # print("Status itol: " + str(status))
    

    # from phytreeviz import TreeViz, load_example_tree_file
    # tree_file = directory+"/heatmap.svg.complete.pdf.distance_matrix.hclust.newick"
    # tv = TreeViz(tree_file)
    # group1 = ["Genus_species_CIX4232gb"]
    # group2 = ["Genus_species_CIX4476gb"]
    # tv.highlight(group1, "orange")
    # tv.highlight(group2, "lime")
    # tv.annotate(group1, "group1")
    # tv.annotate(group2, "group2")
    # tv.marker(group1, marker="s", color="blue")
    # tv.marker(group2, marker="D", color="purple", descendent=True)
    # #tv.marker(["Genus_species_CIX4232gb"], marker="D", color="purple", descendent=True)
    # tv.set_node_label_props("Genus_species_CIX4232gb", color="green", style="italic")
    # tv.set_node_label_props("Genus_species_CIX4476gb", color="green")
    # tv.show_scale_bar()
    # buf = io.BytesIO() # in-memory files
    # tv.savefig(buf)
    # data = base64.b64encode(buf.getbuffer()).decode("utf8") # encode to html elements
    # buf.close()
    # dynamic_tree="data:image/png;base64,{}".format(data)

    
    ##############################################################################################
    # geographical map of strains
    ##############################################################################################
    print(df_metadata3)

    counts = df_metadata3.groupby(["Country", "Continent"]).size().reset_index(name="number_strains")
    
    
    # Créer la carte choroplèthe
    fig_geomap = px.choropleth(
        counts,
        locations="Country",            # Colonne avec les noms des pays
        locationmode="country names", # On utilise les noms de pays
        color="number_strains",      # Couleur selon le nombre de souches
        color_continuous_scale="Viridis",
        title="Number of strains by country"
    )



    
    ##############################################################################################
    # merge main cluster table and cluster search in order to report the same columns
    ##############################################################################################
    if (len(search_res2) > 1):
        df_search = pd.DataFrame.from_dict(search_res2)
        df_search = pd.merge(df_search,merged_with_cog, left_on='ClutserID', right_on='ClutserID')
        search_res2 = df_search.to_dict('records')


    return nb_of_pangenes,text,fig,table_pangenes,fig_ANI,fig_gene,fig_pie,fig_COG_all,fig_COG1,fig_COG2,fig_rarefaction,current_layout,current_tracks,search_res2,clustersearch, graph_macrosynteny, clinker, mlva_table, flanking_sequences, fig_scatter, "assets/tree."+str(session)+".html", {'display': 'block'}, fig_snmf, fig_cross_entropy, fig_geomap #,fig_upset

def get_directory(pathname):
    directory = "data/african_Xo"
    with open("panexplorer_config.yaml", "r") as yaml_file:
        conf = yaml.safe_load(yaml_file)
        directory = conf["directory"]
    
    if len(pathname) > 1:
        directory = conf["data_dir"] + "/" + pathname.replace("#", "")
        
        
        if os.path.isdir(directory):
            print("exists")
        else:
            ###########################
            # Import remote data files
            ###########################
            os.mkdir(directory)
            os.mkdir(directory+"/genomes")
            os.mkdir(directory+"/genomes/genomes")


            cmd = "wget https://panexplorer.southgreen.fr/tables/"+pathname.replace("#", "")+".pav.xls -O "+directory+"/1.Orthologs_Cluster.txt"
            returned_value = os.system(cmd)
            cmd = "wget https://panexplorer.southgreen.fr/tables/"+pathname.replace("#", "")+".metadata.xls -O "+directory+"/metadata.xls"
            returned_value = os.system(cmd)
            cmd = "wget https://panexplorer.southgreen.fr/tables/"+pathname.replace("#", "")+".ani.xls -O "+directory+"/fastani.out.matrix.complete.xls"
            returned_value = os.system(cmd)
            cmd = "wget https://panexplorer.southgreen.fr/tables/"+pathname.replace("#", "")+".cog_category_counts.txt -O "+directory+"/cog_category_counts.txt"
            returned_value = os.system(cmd)
            cmd = "wget https://panexplorer.southgreen.fr/tables/"+pathname.replace("#", "")+".accessory_based_tree.nwk -O "+directory+"/heatmap.svg.complete.pdf.distance_matrix.hclust.newick"
            returned_value = os.system(cmd)
            cmd = "wget https://panexplorer.southgreen.fr/tables/"+pathname.replace("#", "")+".cog_category_2_counts.txt -O "+directory+"/cog_category_2_counts.txt"
            returned_value = os.system(cmd)
            cmd = "wget https://panexplorer.southgreen.fr/tables/"+pathname.replace("#", "")+".cog_of_clusters.xls -O "+directory+"/cog_of_clusters.txt"
            returned_value = os.system(cmd)

            df_matrix = pd.read_csv(directory+'/1.Orthologs_Cluster.txt',sep='\t')
            df_matrix_modified = df_matrix.replace(to_replace ='[\w\.,:]+', value = 1, regex = True)
            df = df_matrix_modified.replace(to_replace ='-', value = 0, regex = True)
            df.to_csv(directory+"/1.Orthologs_Cluster.2.txt",sep='\t',index=False)
            list_species = []
            for col in df.columns:
                if col != "ClutserID":
                    cmd = "wget https://panexplorer.southgreen.fr/tables/"+col+".ptt -O "+directory+"/genomes/genomes/"+col+".ptt"
                    returned_value = os.system(cmd)
                    cmd = "wget https://panexplorer.southgreen.fr/tables/"+col+".faa -O "+directory+"/genomes/genomes/"+col+".faa"
                    returned_value = os.system(cmd)

    return directory

def init_dataframes(pathname):
    
    directory = get_directory(pathname)

    #https://panexplorer.southgreen.fr/tmp/86740638254871261615/1.Orthologs_Cluster.txt
    myfile = directory+'/1.Orthologs_Cluster.txt'
    print(myfile)
    
    df_matrix = pd.read_csv(myfile, sep='\t')
    #df_matrix = pd.read_csv("https://panexplorer.southgreen.fr/tmp/86740638254871261615/1.Orthologs_Cluster.txt")
    #df_matrix = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/solar.csv")
    
    print("yeahhhh: "+str(df_matrix.size))

    
    df_matrix_modified = df_matrix.replace(to_replace ='[\w\.,:]+', value = 1, regex = True)
    df = df_matrix_modified.replace(to_replace ='-', value = 0, regex = True)

    #df['ClutserID'].replace(to_replace ='\d', value ='CLUSTER',regex = True,inplace=True)
    df.to_csv(directory+"/1.Orthologs_Cluster.2.txt",sep='\t',index=False)
    
    #df.to_csv("sessions/pav_matrix."+str(session)+".txt",sep='\t',index=False)

    #cmd = "sed -i 's/^/CLUSTER/g' " + directory+"/1.Orthologs_Cluster.2.txt"
    #returned_value = os.system(cmd)

    #df = pd.read_csv(directory+'/1.Orthologs_Cluster.2.txt',sep='\t')

    #df = df.rename(columns={'CLUSTERClutserID': 'ClutserID'})
    #df = df.rename(columns={'CLUSTERCLUSTERClutserID': 'ClutserID'})
    #df = df.dropna()

    df_ANI = pd.DataFrame()  
    if os.path.exists(directory + "/fastani.out.matrix.complete.xls"):
        df_ANI = pd.read_csv(directory+'/fastani.out.matrix.complete.xls',sep='\t')

    list_species = []
    for col in df.columns:
        if col != "ClutserID":
            list_species.append(col)


    df_metadata = pd.read_csv(directory+'/metadata.xls',sep='\t')
    df_metadata.loc[len(df_metadata.index)] = ['ClutserID', 'none','none','none'] 
    df_metadata3 = df_metadata[(df_metadata["Continent"] != "none")]
    list_continent = ["all"] + df_metadata3["Continent"].unique().tolist()
    list_organisms = ["all"] + df_metadata3["Organism"].unique().tolist()

    # Remove lines from ptt
    cmd = "grep -P 'Location|^\d+\.\.' "+directory+"/genomes/genomes/"+list_species[0]+".ptt >"+directory+"/genomes/genomes/"+list_species[0]+".2.ptt"
    returned_value = os.system(cmd)
    
    print("Species:"+list_species[0])

    df_gene_positons = pd.read_csv(directory+'/genomes/genomes/'+list_species[0]+'.2.ptt',sep='\t')
    if 'block_id' not in df_gene_positons.columns:
        df_gene_positons.insert(0, 'block_id', 'chr1')
        
    merged_with_positions = pd.merge(df_matrix, df_gene_positons, left_on=list_species[0], right_on='PID')

    # rename and reorganize columns
    merged_with_positions = merged_with_positions.rename(columns={'ClutserID': 'name'})

    merged_with_positions[['start', 'end']] = merged_with_positions['Location'].str.split('\.\.', expand=True)
    #merged_with_positions.insert(0, 'block_id', 'chr1')
    

    merged_with_positions.insert(0, 'color', 'black')
    merged_with_positions = merged_with_positions[['name','block_id','start', 'end','color','Strand']]
    merged_with_positions['start'] = merged_with_positions['start'].astype(int)
    gene_plus_df = merged_with_positions[merged_with_positions["Strand"] == "+"]
    gene_minus_df = merged_with_positions[merged_with_positions["Strand"] == "-"]
    gene_plus_df.to_csv(directory+"/merged_with_positions.csv",index=False,sep='\t')
    dict_list_gene_plus = gene_plus_df.to_dict('records')
    dict_list_gene_minus = gene_minus_df.to_dict('records')
    karyotype_df = merged_with_positions.groupby('block_id').max().reset_index()
    karyotype_df = karyotype_df.rename(columns={'block_id': 'id'})
    karyotype_df['label'] = karyotype_df.loc[:, 'id']
    karyotype_df = karyotype_df.rename(columns={'start': 'len'})
    karyotype_df = karyotype_df[['id','label','len','color']]
    karyotype_df.to_csv(directory+"/karyotype.csv",index=False,sep='\t')
    karyotype_dict_list = karyotype_df.to_dict('records')

    data_summary_filtered_md_template = 'Selected strains'
    data_summary_filtered_md = data_summary_filtered_md_template.format(len(df))


    
    return df,df_metadata,df_ANI,merged_with_positions,list_species,list_continent,list_organisms,karyotype_dict_list,dict_list_gene_plus,dict_list_gene_minus,df_matrix


def generate_html(dataframe: pd.DataFrame):
    # get the table HTML from the dataframe
    table_html = dataframe.to_html(table_id="table")
    # construct the complete HTML with jQuery Data tables
    # You can disable paging or enable y scrolling on lines 20 and 21 respectively
    html = f"""
    <html>
    <header>
        <link href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css" rel="stylesheet">
    </header>
    <body>
    {table_html}
    <script src="https://code.jquery.com/jquery-3.6.0.slim.min.js" integrity="sha256-u7e5khyithlIdTpu22PHhENmPcRdFiHRjhAuHcs05RI=" crossorigin="anonymous"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
    <script>
        $(document).ready( function () {{
            $('#table').DataTable({{
                // paging: false,
                // scrollY: 400,
            }});
        }});
    </script>
    </body>
    </html>
    """
    # return the html
    return html

###############################################
# return list of the same combination as a cluster given as argument
###############################################
def get_combination(cluster,pathname,list_of_strains):
    
    directory = get_directory(pathname)

    df = pd.read_csv(directory+'/1.Orthologs_Cluster.2.txt',sep='\t')

    # convert cluster identifiers into string for filtering
    df = df.astype({'ClutserID': str})
    mini_df = df.loc[df['ClutserID'] == str(cluster)]
    
    # generate a new dataframe from a list of list
    list_of_list = []
    nb_presence = 0
    specific_to = []
    for item in mini_df.columns:
        
        if item != 'ClutserID' and item in list_of_strains:
            
            genes = mini_df[item]
            keep = True

            
            for gene in genes:
                if gene == 0:
                    keep = False
            if keep:
                list_genes = ','.join(map(str,genes)) 
                list = [cluster,item,list_genes]
                list_of_list.append(list)
                nb_presence+=1
                specific_to.append(str(item))

    
    return specific_to

if __name__ == '__main__':
    #app.run_server(debug=True)
    app.run_server(host= '0.0.0.0',debug=True)
