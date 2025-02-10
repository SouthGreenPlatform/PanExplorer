import dash
from dash import Dash, html, dcc, Input, Output, State, callback, dash_table
from IPython.display import HTML
import plotly.express as px

import urllib.request as urlreq
from urllib.request import Request, urlopen

import numpy as np
import json
import subprocess

import dash_ag_grid as dag

import os
import random
import re

import plotly.graph_objects as go

import dash_table as dt
import dash_html_components as html

from dash.dependencies import Output, Input
from dash.exceptions import PreventUpdate

import pandas as pd
import folium
import folium.plugins


import dash_bio as dash_bio

#from plotly_upset.plotting import plot_upset
#from upsetplot import plot
#from upsetplot import generate_counts
from matplotlib import pyplot

#import dash_datatables as ddt

import plotly.figure_factory as ff

import yaml

directory = "data/african_Xo"
with open("panexplorer_config.yaml", "r") as yaml_file:
    conf = yaml.safe_load(yaml_file)
    directory = conf["directory"]




#dftest = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')
#column_defs = [{"title": i, "data": i} for i in dftest.columns]


filtering = 'Continent'

app = Dash(__name__)

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

#df_metadata = pd.read_csv(directory+'/metadata.xls',sep='\t')
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


data = ""



PAGE_SIZE = 5
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    
    
    html.H1('PanExplorer: Pangene Atlas'),
    html.Div(id='sample_selection',children=[
        
        dag.AgGrid(
            id="metadata_table",
            style={'width': '100vh','margin-left': '15px'},
            columnDefs=columnDefs,
            rowData=[],
            columnSize="sizeToFit",
            selectAll=True,
            defaultColDef={"filter": True},
            dashGridOptions={
                "rowSelection": "multiple",
                "animateRows": False
            },
        ),
        html.Br(),
        html.Button('Apply the selection of samples', id='submit-samples', n_clicks=0),  
        html.Br(),
        html.Br(),
        
        #html.Div([
        #    "Continent",dcc.Dropdown(
        #        id='continent',
        #        multi=False
        #    )
        #], style={'width': '300px', 'display': 'inline-block'}),
        #html.Div(style={'width': '10px', 'display': 'inline-block'}),
        #html.Div([
        #    "Organism",dcc.Dropdown(
        #        id='organism',
        #        multi=False
        #    )
        #], style={'width': '300px', 'display': 'inline-block'}),
        html.Div(style={'width': '10px', 'display': 'inline-block'}),
        html.Div([
            "Reference Genome for projection",dcc.Dropdown(
                id='reference',
                multi=False
            )
        ], style={'width': '500px', 'display': 'inline-block'}),
        html.Div(style={'width': '10px', 'display': 'inline-block'}),
    ]),

    html.H5("PAV configuration"),        
    html.Div(id='PAV_config',children=[
        
        html.Div([
            "Colors",dcc.Dropdown(
                ['Presence/absence','Level of presence','Organism','Continent'],
                id='colorizing',
                value = 'Presence/absence',
                multi=False
            )
        ], style={'width': '300px', 'display': 'inline-block'}),
        html.Div(style={'width': '10px', 'display': 'inline-block'}),
        html.Div([
            "Highlight",dcc.Dropdown(
                ['None','Reference genome','Core-genes','Strain-specific genes'],
                id='highlight',
                value = 'None',
                multi=False
            )
        ], style={'width': '300px', 'display': 'inline-block'}),
        
        html.Div(style={'width': '10px', 'display': 'inline-block'}),
        html.Div([
            "Cluster ordering",dcc.Dropdown(
                ['Hierarchical clustering','Position in genome used for projection'],
                value = 'Hierarchical clustering',
                id='ordering',
                multi=False
            )
        ], style={'width': '300px', 'display': 'inline-block'}),

        html.Div(style={'width': '10px', 'display': 'inline-block'}),



        

    ]),
    html.H5("Search for a cluster"),
    html.Div([
            "Search for cluster by keyword:",
            dcc.Input(
                id='cluster_search',
                value = '',
            )
        ], style={'width': '400px', 'display': 'inline-block'}),

    html.Br(),
    html.Div([
            "Search for clusters specific to these genomes",dcc.Dropdown(
                id='specific_to',
                multi=True
            )
        ], style={'width': '500px', 'display': 'inline-block'}),
    html.Br(),
    html.Br(),
    html.Button('Submit', id='submit-val', n_clicks=0),  

    html.Br(),
    html.Br(),
    

    # The Visuals
    dcc.Tabs(id='tab', style=tabs_styles, children=[
        dcc.Tab(label='Stats and Overview', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            html.Div(className="row", id='stats', children=[
                
                dcc.Loading(dcc.Graph(id='graph_gene',style={'width': '50vh', 'height': '50vh','margin-left': '15px'})),
                dcc.Loading(dcc.Graph(id='graph_pie',style={'width': '50vh', 'height': '50vh','margin-left': '15px'})),
                dcc.Loading(dcc.Graph(id='rarefaction',style={'width': '50vh', 'height': '50vh','margin-left': '15px'})),
            ]),
        ]),
        dcc.Tab(label='Presence/absence matrix', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            
            html.Div(id='textarea-example-output', style={'whiteSpace': 'pre-line'}),
            dcc.Loading(html.Div(id='test', style={'whiteSpace': 'pre-line'})),
            html.Div(id='test2'),
            dcc.Loading(dcc.Graph(id='PAV_graph')),
            html.Br(),
            html.Div(className="row", id='tables', children=[
                html.Div(children=[
                    html.H3("Pan-genes"),
                    dcc.Loading(
                        dag.AgGrid(
                                id="table_pangenes",
                                style={'width': '50vh', 'height': '50vh','margin-left': '15px'},
                                rowData=[],
                                columnDefs=[{"field": i} for i in ["ClutserID","COG","COGcat","type"]],
                                #defaultColDef={"filter": True},
                                columnSize="sizeToFit",
                                #getRowId="params.data.State",
                                dashGridOptions={"pagination": True, "animateRows": False}
                        ),
                    ),
                ]),
                
                
                html.Div(style={'marginLeft': 50}, children=[
                    html.H3("Selected cluster"),
                    #html.Div(id="cluster_info"),
                    dcc.Loading(
                        dag.AgGrid(
                                    id="genes_cluster",
                                    style={'width': '80vh', 'height': '50vh','margin-left': '15px'},
                                    rowData=[],
                                    columnDefs=[{"field": i} for i in ["Cluster","Species","Genes"] ],
                                    #defaultColDef={"filter": True},
                                    columnSize="sizeToFit",
                                    #getRowId="params.data.State",
                                    dashGridOptions={"pagination": True, "animateRows": False}
                            )
                    ),
                ]),

                html.Div(style={'marginLeft': 50}, children=[
                    html.H3("Cluster Search"),
                    dcc.Loading(
                        dag.AgGrid(
                                id="table_of_search",
                                style={'width': '20vh', 'height': '50vh','margin-left': '15px'},
                                rowData=[],
                                columnDefs=[{"field": i} for i in ["ClutserID"]],
                                #defaultColDef={"filter": True},
                                columnSize="sizeToFit",
                                #getRowId="params.data.State",
                                dashGridOptions={"pagination": True, "animateRows": False}
                        ),
                    ),
                ]),
            ]),
           
            html.Br(),
            dcc.Loading(dash_bio.AlignmentChart(
                id='my-default-alignment-viewer',
                data=data,
                width=1000,
                height=600,
            ),
            ),
            
            html.Div(id='tbl_out'),
            
        ]),

        dcc.Tab(label='COG', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            dcc.Loading(dcc.Graph(id='graph_COG1')),
            html.Br(),
            dcc.Loading(dcc.Graph(id='graph_COG2')),
            ]),
        dcc.Tab(label='Accessory-based tree', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            #html.Iframe(id='tree',src="https://panexplorer.southgreen.fr/phylotree/38070424888018112151183211213515.html",style={"height": "600px", "width": "100%"}),
            #html.Iframe(id='tree',src="assets/tree.html",style={"height": "600px", "width": "100%"}),
            html.Div("Dynamic tree",id='dynamic_tree'),
            html.Br(),
            ]),
        
        dcc.Tab(label='ANI', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            dcc.Loading(dcc.Graph(id='graph_ANI')),
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
        ]),
    #html.Div(id='cluster_info', style={'whiteSpace': 'pre-line'}),
])

@app.callback(
    Output('sample_selection', 'children'), 
    Input('url', 'hash')
)

def display_sample_selection(pathname):
    df,df_metadata,df_ANI,merged_with_positions,list_species,list_continent,list_organisms,karyotype_dict_list,dict_list_gene_plus,dict_list_gene_minus,df_matrix = init_dataframes(pathname)
    
    
    df_metadata = df_metadata[df_metadata['Strain name'] != 'ClutserID']
    
    return html.Div([
        
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
        html.Button('Apply the selection of samples', id='submit-samples', n_clicks=0),  
        html.Br(),
        html.Br(),
        
        
        html.Div([
            "Reference Genome for projection",dcc.Dropdown(
                options = list_species,
                value = list_species[0],
                id='reference',
                multi=False
            )
        ], style={'width': '500px', 'display': 'inline-block'}),
        
    ])

    

#############################################################
# Callback for cluster selection from heatmap or from table
#############################################################
@app.callback(
    #Output('cluster_info', 'children'),
    Output('genes_cluster', 'rowData'),
    Output('my-default-alignment-viewer', 'data'),
    Input('PAV_graph', 'clickData'),
    Input('url', 'hash'),
    Input('metadata_table','selectedRows'),
    #Input('table_core', 'cellClicked'),
    #Input('url', 'hash')
)

def display_click_data(clickData,pathname,metadata_table):
         
    cluster = 1
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
    return dictionary,data

@app.callback(
    Output('genes_cluster', 'rowData', allow_duplicate=True),
    Output('my-default-alignment-viewer', 'data', allow_duplicate=True),
    Input('table_pangenes', 'cellClicked'),
    Input('url', 'hash'),
    Input('metadata_table','selectedRows'),
    prevent_initial_call=True
    #Input('url', 'hash')
)

def display_click_data(cell,pathname,metadata_table):
         
    cluster = 1
    list_of_strains = []
    if metadata_table:
        wjdata1 = json.loads(json.dumps(metadata_table, indent=2))
        for strain in wjdata1:
            strain_name = strain['Strain name']
            list_of_strains.append(strain_name)  
    if cell:
        wjdata = json.loads(json.dumps(cell, indent=2))
        cluster = wjdata['value']
        nb_presence,dictionary,data = get_cluster_details(cluster,pathname,list_of_strains)
        return dictionary,data
    else:
        return [],""

@app.callback(
    Output('genes_cluster', 'rowData', allow_duplicate=True),
    Output('my-default-alignment-viewer', 'data', allow_duplicate=True),
    Input('table_of_search', 'cellClicked'),
    Input('url', 'hash'),
    Input('metadata_table','selectedRows'),
    prevent_initial_call=True
    #Input('url', 'hash')
)

def display_click_data(cell,pathname,metadata_table):
         
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
        return dictionary,data
    else:
        return [],""
        


        
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
    print(data)
    #data = ">test\nP\t>test2\nP"
    mydf.to_csv('export_cluster_details.txt')
    dictionary = mydf.to_dict('records')

    return nb_presence,dictionary,data


#################################################
# callback for changing list of strains for pivot
#################################################
@app.callback(
    Output('reference', 'options'),
    Output('specific_to','options'),
    #Input('sp', 'value'),
    #Input('continent', 'value'),
    #Input('organism', 'value'),
    Input('metadata_table','selectedRows'),
    Input('url', 'hash'),
    
    #Input('datatable-paging', "page_current"),
    #Input('datatable-paging', "page_size"),
     )
def update_pivot(metadata_table,pathname):
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


@app.callback(
    Output('reference', 'value'),
    Input('reference', 'options')
)
def set_reference_value(available_options):
    return available_options[-1]['value']

#################################################
# callback for changing graphes
#################################################
@app.callback(
    Output('textarea-example-output', 'children'),
    Output('PAV_graph', 'figure'),
    Output('table_pangenes', 'rowData'),
    Output("dynamic_tree","children"),
    
    #Output('datatable-paging','srcDoc'),
    Output('graph_ANI', 'figure'),
    Output('graph_gene', 'figure'),
    Output('graph_pie', 'figure'),
    Output('graph_COG1', 'figure'),
    Output('graph_COG2', 'figure'),
    Output('rarefaction', 'figure'),
    Output("my-dashbio-default-circos", "layout"),
    Output("my-dashbio-default-circos", "tracks"),
    Output("table_of_search",'rowData'),
    
    
    #Output('graph_upset', 'figure'),
    #Input('sp', 'value'),
    #Input('continent', 'value'),
    #Input('organism', 'value'),
    State('reference', 'value'),
    State('ordering', 'value'),
    State('colorizing', 'value'),
    State('highlight', 'value'),
    Input('url', 'hash'),
    Input('submit-val', 'n_clicks'),
    Input('submit-samples','n_clicks'),
    State('specific_to','value'),
    State('cluster_search','value'),
    State('metadata_table','selectedRows'),
    
    
    State("my-dashbio-default-circos", "layout"),
    State("my-dashbio-default-circos", "tracks"),
    #Input('datatable-paging', "page_current"),
    #Input('datatable-paging', "page_size"),
     )
def update_graph(reference,ordering,colorizing,highlight,pathname,submit_button,submit_samples,specific_to,cluster_search,metadata_table,current_layout,current_tracks):
    
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
    cmd = "echo 'Cluster\tCOG\tCOGcat' >"+directory+"/cog_of_clusters.2.txt; awk {'print $1\"\t\"$2\"\t\"$3'} "+directory+"/cog_of_clusters.txt >>"+directory+"/cog_of_clusters.2.txt"
    returned_value = os.system(cmd)
    
    df_cog_of_clusters = pd.read_csv(directory+'/cog_of_clusters.2.txt',sep='\t')
    df2 = df2.astype({"ClutserID": int})
    df_cog_of_clusters = df_cog_of_clusters.astype({"Cluster": int})
    merged_with_cog = pd.merge(df2, df_cog_of_clusters, how="left", left_on='ClutserID', right_on='Cluster')
    merged_with_cog.to_csv(directory+"/merged_with_cog.txt")
    core_df = merged_with_cog[merged_with_cog["sum"] == len(list_sp2)]
    specific_df = merged_with_cog[merged_with_cog["sum"] == 1]
    accessory_df = merged_with_cog[(merged_with_cog["sum"] != 1) & (merged_with_cog["sum"] < len(list_sp2))]
    
    nb_pangenes = len(df2)
    
    nb_specific_genes = len(specific_df)
    nb_coregenes = len(core_df)
    nb_accessory = nb_pangenes - nb_specific_genes - nb_coregenes
    
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
    df_rarefaction.to_csv("rarefactiontest2.txt",index=False)
    df_rarefaction2 = pd.read_csv('rarefactiontest2.txt',sep=',')
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
    elif specific_to is not None:
        list_of_clusters = [1000]
        
        # 1) get clusters for which gene is present for these samples
        specific_to.append("ClutserID")
        df_specific_to = df[specific_to]
        df_specific_to['sum'] = df_specific_to.drop('ClutserID', axis=1).sum(axis=1)
        # get only if at least one gene is present
        df_specific_to = df_specific_to[df_specific_to["sum"] == len(specific_to)-1]
        # remove CLUSTER tag (TODO: to be removed)
        df_specific_to['ClutserID'] = df_specific_to['ClutserID'].str.replace('CLUSTER000','')
        df_specific_to['ClutserID'] = df_specific_to['ClutserID'].str.replace('CLUSTER00','')
        df_specific_to['ClutserID'] = df_specific_to['ClutserID'].str.replace('CLUSTER0','')
        df_specific_to['ClutserID'] = df_specific_to['ClutserID'].str.replace('CLUSTER','')
        df_specific_to.to_csv("df_specific_to.csv")
        list1 = df_specific_to['ClutserID'].tolist()
        list1bis = [eval(i) for i in list1]
        
        
        # 2) get clusters for which the number of presence correspond to the number of selected samples
        same_number_df = merged_with_cog[merged_with_cog["sum"] == len(specific_to)-1]
        same_number_df.to_csv("df_specific_to2.csv")
        list2 = same_number_df['ClutserID'].tolist()
        
        # 3) get overlapping clusters between the two dataframes
        intersected_list = [value for value in list1bis if value in list2]
        print(intersected_list)
        print(len(intersected_list))
        
        df_search = pd.DataFrame(intersected_list, columns=['ClutserID'])
        search_res2 = df_search.to_dict('records')
        #df_specific_final2.to_csv("df_specific_to.csv")
        
        list_of_clusters = intersected_list

        df_search = pd.DataFrame(list_of_clusters, columns=['ClutserID'])
        search_res2 = df_search.to_dict('records')
        
        for sample in list_sp2:
            df2[sample] =  np.where( (df2[sample] == 1) & (df2["ClutserID"].isin(list_of_clusters)==False),0.67,df2[sample])
            
        print("specific to: "+str(specific_to))
    elif cluster_search != "":
        
        #cmd = "grep -P '"+cluster_search+"' "+directory+"/1.Orthologs_Cluster.txt | awk {'print $1'}"
        #returned_value = os.popen(cmd).read()
        #cluster_search = returned_value
        #df_search = pd.DataFrame([int(returned_value)], columns=['ClutserID'])
        #search_res2 = df_search.to_dict('records')
        
        
        #COG1192
        
        cmd = "grep -P '"+cluster_search+"' "+directory+"/cog_of_clusters.txt | awk {'print $1'}"
        returned_value = os.popen(cmd).read()
        cluster_search = returned_value
        list_of_clusters = returned_value.split("\n")
        
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
    gene_position_file = directory+'/genomes/genomes/'+reference+'.ptt'
    gene_position_file2 = directory+'/genomes/genomes/'+reference+'.2.ptt'
    
    
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

    
    
    
    #html = generate_html(df2)
    #open("data/table.html", "w").write(html)
    
    
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
    if highlight != "None" or cluster_search != "" or specific_to is not None:
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

    # remove last caracter
    newick = newick.rstrip(newick[-1])
    f = open("assets/tree."+str(session)+".html", "w")
    template = open('assets/tree.html', 'r')
    for line in template:
        if re.search(r"NEWICK_TREE", line):
            f.write("var test_string = \""+newick+";\"\n")
            #f.write("var test_string\n")
        else:
            f.write(line)
    template.close()
    f.close()
    #cmd = "sed \"s/NEWICK_TREE/"+newick+"/g\" assets/tree.html >assets/tree."+str(session)+".html"
    #returned_value = os.system(cmd)


    dynamic_tree = html.Iframe(id='tree',src="assets/tree."+str(session)+".html",style={"height": "600px", "width": "100%"}),
    #dynamic_tree = cmd

    return text,fig,table_pangenes,dynamic_tree,fig_ANI,fig_gene,fig_pie,fig_COG1,fig_COG2,fig_rarefaction,current_layout,current_tracks,search_res2#,fig_upset



def init_dataframes(pathname):
    
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
            cmd = "wget https://panexplorer.southgreen.fr/tables/"+pathname.replace("#", "")+".cog_category_2_counts.txt -O "+directory+"/cog_category_2_counts.txt"
            returned_value = os.system(cmd)
            cmd = "wget https://panexplorer.southgreen.fr/tables/"+pathname.replace("#", "")+".cog_of_clusters.xls -O "+directory+"/cog_of_clusters.txt"
            returned_value = os.system(cmd)
            
            
            df_matrix = pd.read_csv(directory+'/1.Orthologs_Cluster.txt',sep='\t')
            df_matrix_modified = df_matrix.replace(to_replace ='[\w\.,:]+', value = 1, regex = True)
            df = df_matrix_modified.replace(to_replace ='-', value = 0, regex = True)
            list_species = []
            for col in df.columns:
                if col != "ClutserID":
                    cmd = "wget https://panexplorer.southgreen.fr/tables/"+col+".ptt -O "+directory+"/genomes/genomes/"+col+".ptt"
                    returned_value = os.system(cmd)
                    cmd = "wget https://panexplorer.southgreen.fr/tables/"+col+".faa -O "+directory+"/genomes/genomes/"+col+".faa"
                    returned_value = os.system(cmd)

            #directory = "https://panexplorer.southgreen.fr/tmp/" + pathname.replace("#", "")

    #https://panexplorer.southgreen.fr/tmp/86740638254871261615/1.Orthologs_Cluster.txt
    myfile = directory+'/1.Orthologs_Cluster.txt'
    print(myfile)
    
    df_matrix = pd.read_csv(myfile, sep='\t')
    #df_matrix = pd.read_csv("https://panexplorer.southgreen.fr/tmp/86740638254871261615/1.Orthologs_Cluster.txt")
    #df_matrix = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/solar.csv")
    
    print("yeahhhh: "+str(df_matrix.size))

    
    df_matrix_modified = df_matrix.replace(to_replace ='[\w\.,:]+', value = 1, regex = True)
    df = df_matrix_modified.replace(to_replace ='-', value = 0, regex = True)

    df['ClutserID'].replace(to_replace ='\d', value ='CLUSTER',regex = True,inplace=True)
    df.to_csv(directory+"/1.Orthologs_Cluster.2.txt",sep='\t',index=False)
    cmd = "sed -i 's/^/CLUSTER/g' "+directory+"/1.Orthologs_Cluster.2.txt"
    returned_value = os.system(cmd)

    df = pd.read_csv(directory+'/1.Orthologs_Cluster.2.txt',sep='\t')
    df = df.rename(columns={'CLUSTERClutserID': 'ClutserID'})
    df = df.rename(columns={'CLUSTERCLUSTERClutserID': 'ClutserID'})
    #df = df.dropna()



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



if __name__ == '__main__':
    #app.run_server(debug=True)
    app.run_server(host= '0.0.0.0',debug=True)
