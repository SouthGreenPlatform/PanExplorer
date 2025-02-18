import dash
from dash import Dash, html, dcc

import dash_auth

# Keep this out of source code repository - save in a file or a database
VALID_USERNAME_PASSWORD_PAIRS = {
    'hello': 'world'
}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets,use_pages=True)
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)


app.layout = html.Div([
    html.Div([

        dcc.Link(html.Button("Access PanExplorer"), href="app-pav"),
    ]),
    html.Br(),
    dash.page_container
])

if __name__ == '__main__':
    app.run_server(host= '0.0.0.0',debug=True)
