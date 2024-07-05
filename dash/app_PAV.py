import dash
from dash import Dash, dcc, html, Input, Output, dash_table, State
from IPython.display import HTML
import plotly.express as px

import urllib.request as urlreq

import numpy as np
import json
import subprocess

import os

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
        "size": 18,
        "color": "#4d4d4d",
    },
    "ticks": {
        "color": "#4d4d4d",
        "labelColor": "#4d4d4d",
        "spacing": 100000,
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
  


PAGE_SIZE = 5
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    

    html.Div(id='sample_selection',children=[
        
        html.Div([
            "Continent",dcc.Dropdown(
                id='pathovar',
                multi=False
            )
        ], style={'width': '300px', 'display': 'inline-block'}),
        html.Div(style={'width': '10px', 'display': 'inline-block'}),
        html.Div([
            "Reference Genome for projection",dcc.Dropdown(
                id='reference',
                multi=False
            )
        ], style={'width': '500px', 'display': 'inline-block'}),
        html.Div(style={'width': '10px', 'display': 'inline-block'}),
        html.Div([
            "Colors",dcc.Dropdown(
                ['presence/absence','level of presence'],
                id='colorizing',
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
        
    ]),
    
    html.Br(),
    

    # The Visuals
    dcc.Tabs(id='tab', style=tabs_styles, children=[
        dcc.Tab(label='Presence/absence matrix', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            html.Div(id='textarea-example-output', style={'whiteSpace': 'pre-line'}),
            dcc.Loading(dcc.Graph(id='graph')),
            "Selected cluster:",html.Div(id="cluster_info"),
            html.Br(),
            html.Div(className="row", id='stats', children=[
                dcc.Loading(dcc.Graph(id='graph_gene',style={'width': '50vh', 'height': '50vh','margin-left': '15px'})),
                dcc.Loading(dcc.Graph(id='graph_pie',style={'width': '50vh', 'height': '50vh','margin-left': '15px'})),
            ]),
            
        ]),
        dcc.Tab(label='Core-genes', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            #html.Iframe(id='table',src="https://localhost/data/table.html",style={"height": "600px", "width": "100%"}),
            dcc.Loading(dash_table.DataTable(
                id='table_core',
                columns=[
                    {"name": i, "id": i, "deletable": True, "selectable": True} for i in ["ClutserID","COG","COGcat"] #df.columns
                ],
                style_data={
                    'font-size' : 22,
                    'color': 'black',
                    'backgroundColor': 'white'
                },
                style_header={
                    'font-size' : 22,
                    'backgroundColor': 'rgb(210, 210, 210)',
                    'color': 'black',
                    'fontWeight': 'bold'
                },
                filter_action="custom",
                filter_query='',
                sort_action="native",
                sort_mode="multi",
                page_action="native",
                page_current= 0,
                page_size= 10,
            )),
        ]),
        dcc.Tab(label='Dispensable genes', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            #html.Iframe(id='table',src="https://localhost/data/table.html",style={"height": "600px", "width": "100%"}),
            dcc.Loading(dash_table.DataTable(
                id='table_dispensable',
                columns=[
                    {"name": i, "id": i, "deletable": True, "selectable": True} for i in ["ClutserID","COG","COGcat"] #df.columns
                ],
                style_data={
                    'font-size' : 22,
                    'color': 'black',
                    'backgroundColor': 'white'
                },
                style_header={
                    'font-size' : 22,
                    'backgroundColor': 'rgb(210, 210, 210)',
                    'color': 'black',
                    'fontWeight': 'bold'
                },
                filter_action="custom",
                filter_query='',
                sort_action="native",
                sort_mode="multi",
                page_action="native",
                page_current= 0,
                page_size= 10,
            )),
        ]),
        dcc.Tab(label='Strain-specific genes', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            #html.Iframe(id='table',src="https://localhost/data/table.html",style={"height": "600px", "width": "100%"}),
            dcc.Loading(dash_table.DataTable(
                id='table_specific',
                columns=[
                    {"name": i, "id": i, "deletable": True, "selectable": True} for i in ["ClutserID","COG","COGcat"] #df.columns
                ],
                style_data={
                    'font-size' : 22,
                    'color': 'black',
                    'backgroundColor': 'white'
                },
                style_header={
                    'font-size' : 22,
                    'backgroundColor': 'rgb(210, 210, 210)',
                    'color': 'black',
                    'fontWeight': 'bold'
                },
                filter_action="custom",
                filter_query='',
                sort_action="native",
                sort_mode="multi",
                page_action="native",
                page_current= 0,
                page_size= 10,
            )),
        ]),
        dcc.Tab(label='COG', style=tab_style, selected_style=tab_selected_style, children=[
            html.Br(),
            dcc.Loading(dcc.Graph(id='graph_COG1')),
            html.Br(),
            dcc.Loading(dcc.Graph(id='graph_COG2')),
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
    Input('url', 'hash'))

def display_sample_selection(pathname):
    df,df_metadata,df_ANI,merged_with_positions,list_species,list_pathovar,karyotype_dict_list,dict_list_gene_plus,dict_list_gene_minus,df_matrix = init_dataframes(pathname)
    
    
    return html.Div([
        
        
        html.Div([
            "Continent",dcc.Dropdown(
                list_pathovar,
                'all',
                id='pathovar',
                multi=False
            )
        ], style={'width': '300px', 'display': 'inline-block'}),
        html.Div(style={'width': '10px', 'display': 'inline-block'}),
        html.Div([
            "Reference Genome for projection",dcc.Dropdown(
                options = list_species,
                value = list_species[0],
                id='reference',
                multi=False
            )
        ], style={'width': '500px', 'display': 'inline-block'}),
        html.Div(style={'width': '10px', 'display': 'inline-block'}),
        html.Div([
            "Colors",dcc.Dropdown(
                ['presence/absence','level of presence'],
                id='colorizing',
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
    ])

    


@app.callback(
    Output('cluster_info', 'children'),
    Input('graph', 'clickData'))

def display_click_data(clickData):
    
    cmd = "date"
    returned_output = subprocess.check_output(cmd)
    #return returned_output.decode("utf-8")

    wjdata = json.loads(json.dumps(clickData, indent=2))
    #print wjdata['data']['current_condition'][0]['temp_C']
    #return wjdata['points']
    return json.dumps(clickData, indent=2)

#################################################
# callback for changing list of strains for pivot
#################################################
@app.callback(
    Output('reference', 'options'),
    #Input('sp', 'value'),
    Input('pathovar', 'value'),
    Input('url', 'hash')
    #Input('datatable-paging', "page_current"),
    #Input('datatable-paging', "page_size"),
     )
def update_pivot(pathovar,pathname):
    df,df_metadata,df_ANI,merged_with_positions,list_species,list_pathovar,karyotype_dict_list,dict_list_gene_plus,dict_list_gene_minus,df_matrix = init_dataframes(pathname)
    df_metadata3 = df_metadata[(df_metadata[filtering] != "none")]
    
    if (pathovar != "all"):
        df_metadata2 = df_metadata[(df_metadata[filtering] == pathovar) | (df_metadata[filtering] == "none")]
        df_metadata3 = df_metadata[df_metadata[filtering] == pathovar]
        
    #reference_list=df_metadata3['Strain']
    reference_list=df_metadata3['Strain name']
    return [{'label': i, 'value': i} for i in reference_list]


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
    Output('graph', 'figure'),
    Output('table_core', 'data'),
    Output('table_dispensable', 'data'),
    Output('table_specific', 'data'),
    
    #Output('datatable-paging','srcDoc'),
    Output('graph_ANI', 'figure'),
    Output('graph_gene', 'figure'),
    Output('graph_pie', 'figure'),
    Output('graph_COG1', 'figure'),
    Output('graph_COG2', 'figure'),
    Output("my-dashbio-default-circos", "layout"),
    Output("my-dashbio-default-circos", "tracks"),
    
    #Output('graph_upset', 'figure'),
    #Input('sp', 'value'),
    Input('pathovar', 'value'),
    Input('reference', 'value'),
    Input('ordering', 'value'),
    Input('url', 'hash'),
    State("my-dashbio-default-circos", "layout"),
    State("my-dashbio-default-circos", "tracks"),
    #Input('datatable-paging', "page_current"),
    #Input('datatable-paging', "page_size"),
     )
def update_graph(pathovar,reference,ordering,pathname,current_layout,current_tracks):
    
    df,df_metadata,df_ANI,merged_with_positions,list_species,list_pathovar,karyotype_dict_list,dict_list_gene_plus,dict_list_gene_minus,df_matrix = init_dataframes(pathname)
    
    directory = "data/african_Xo"
    with open("panexplorer_config.yaml", "r") as yaml_file:
        conf = yaml.safe_load(yaml_file)
        directory = conf["directory"]
    
    if len(pathname) > 1:
        directory = 'data/'+ pathname.replace("#", "")

    list_of_lists = []
    # with clusterID
    df_metadata2 = df_metadata
    # without clusterID
    df_metadata3 = df_metadata[(df_metadata[filtering] != "none")]
    
    if (pathovar != "all"):
        df_metadata2 = df_metadata[(df_metadata[filtering] == pathovar) | (df_metadata[filtering] == "none")]
        df_metadata3 = df_metadata[df_metadata[filtering] == pathovar]
  
    list_sp = df_metadata2['Strain name']
    list_sp2 = df_metadata3['Strain name']
    
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
    
    
    
    
    
    ##############################################
    # Generate Core-gene and accessory files
    ##############################################
    cmd = "echo 'Cluster\tCOG\tCOGcat' >"+directory+"/cog_of_clusters.2.txt; awk {'print $1\"\t\"$2\"\t\"$3'} "+directory+"/cog_of_clusters.txt >>"+directory+"/cog_of_clusters.2.txt"
    returned_value = os.system(cmd)
    
    df_cog_of_clusters = pd.read_csv(directory+'/cog_of_clusters.2.txt',sep='\t')
    df2 = df2.astype({"ClutserID": int})
    df_cog_of_clusters = df_cog_of_clusters.astype({"Cluster": int})
    merged_with_cog = pd.merge(df2, df_cog_of_clusters, left_on='ClutserID', right_on='Cluster')
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
    
    
    
    # test for changing color for specific genes
    #for sample in list_sp2:
    #    proportion = df2["sum"] / len(list_sp2)
    #    df2[sample] = np.where( (df2[sample] == 1),proportion,df2[sample])
 
    #################################################
    # manage Circos
    #################################################
    #gene_position_file = 'data/Xo/'+reference+'.ptt'
    gene_position_file = directory+'/genomes/genomes/'+reference+'.ptt'
    
    # Remove lines from ptt
    cmd = "grep -P 'Location|^\d+\.\.' "+ directory+"/genomes/genomes/"+reference+".ptt >"+directory+"/genomes/genomes/"+reference+".2.ptt"
    returned_value = os.system(cmd)
    merged_with_positions2 = []
    if os.path.exists(gene_position_file):
        #df_gene_positons = pd.read_csv('data/Xo/'+reference+'.ptt',sep='\t')
        df_gene_positons = pd.read_csv(directory+'/genomes/genomes/'+reference+'.2.ptt',sep='\t')
        merged_with_positions = pd.merge(df_matrix, df_gene_positons, left_on=reference, right_on='PID')
        # rename and reorganize columns
        merged_with_positions = merged_with_positions.rename(columns={'ClutserID': 'name'})
        merged_with_positions[['start', 'end']] = merged_with_positions['Location'].str.split('\.\.', expand=True)
        merged_with_positions2 = merged_with_positions
        merged_with_positions.insert(0, 'block_id', 'chr1')
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
    

    fig = go.FigureWidget(data=go.Heatmap(
                   #z=[[1, 0, 0, 0, 1], [0, 1, 0, 0, 0], [0, 0, 1, 1, 0]],
                   #z=list_of_lists,
                   z=transposed_df,
                   y=list_sp2,
                   x=cluster_names,
                   #colorscale= [[0, 'whitesmoke'], [0.5, 'limegreen'], [0.67, 'tomato'], [1, 'teal']],
                   #colorscale= [[0, 'whitesmoke'], [0.33, 'limegreen'], [0.67, 'tomato'], [1, 'red']],
                   colorscale= [[0, 'whitesmoke'], [1, 'teal']],
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
    table_dispensable = accessory_df.to_dict('records')


    
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


    return text,fig,table_core,table_dispensable,table_specific,fig_ANI,fig_gene,fig_pie,fig_COG1,fig_COG2,current_layout,current_tracks #,fig_upset
            
def init_dataframes(pathname):
    
    directory = "data/african_Xo"
    with open("panexplorer_config.yaml", "r") as yaml_file:
        conf = yaml.safe_load(yaml_file)
        directory = conf["directory"]
    
    if len(pathname) > 1:
        directory = 'data/'+ pathname.replace("#", "")
        
    print(directory)

    df_matrix = pd.read_csv(directory+'/1.Orthologs_Cluster.txt',sep='\t')

    df_matrix_modified = df_matrix.replace(to_replace ='[\w\.,:]+', value = 1, regex = True)
    df = df_matrix_modified.replace(to_replace ='-', value = 0, regex = True)

    df['ClutserID'].replace(to_replace ='\d', value ='CLUSTER',regex = True,inplace=True)

    df.to_csv(directory+"/1.Orthologs_Cluster.2.txt",sep='\t',index=False)
    cmd = "sed -i 's/^/CLUSTER/g' "+directory+"/1.Orthologs_Cluster.2.txt"
    returned_value = os.system(cmd)


    df = pd.read_csv(directory+'/1.Orthologs_Cluster.2.txt',sep='\t')
    df = df.rename(columns={'CLUSTERClutserID': 'ClutserID'})
    df = df.dropna()

    df_ANI = pd.read_csv(directory+'/fastani.out.matrix.complete.xls',sep='\t')


    list_species = []
    for col in df.columns:
        if col != "ClutserID":
            list_species.append(col)





    df_metadata = pd.read_csv(directory+'/metadata.xls',sep='\t')
    df_metadata.loc[len(df_metadata.index)] = ['ClutserID', 'none','none','none'] 
    df_metadata3 = df_metadata[(df_metadata[filtering] != "none")]
    list_pathovar = ["all"] + df_metadata3[filtering].unique().tolist()

    # Remove lines from ptt
    cmd = "grep -P 'Location|^\d+\.\.' "+directory+"/genomes/genomes/"+list_species[0]+".ptt >"+directory+"/genomes/genomes/"+list_species[0]+".2.ptt"
    returned_value = os.system(cmd)
    


    df_gene_positons = pd.read_csv(directory+'/genomes/genomes/'+list_species[0]+'.2.ptt',sep='\t')
    merged_with_positions = pd.merge(df_matrix, df_gene_positons, left_on=list_species[0], right_on='PID')
    # rename and reorganize columns
    merged_with_positions = merged_with_positions.rename(columns={'ClutserID': 'name'})
    merged_with_positions[['start', 'end']] = merged_with_positions['Location'].str.split('\.\.', expand=True)
    merged_with_positions.insert(0, 'block_id', 'chr1')
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
    
    return df,df_metadata,df_ANI,merged_with_positions,list_species,list_pathovar,karyotype_dict_list,dict_list_gene_plus,dict_list_gene_minus,df_matrix


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