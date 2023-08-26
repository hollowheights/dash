# Imports
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load data - random data just for testing out Dash
df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv')

# Initialize the app
app = Dash(__name__)

# App layout
app.layout = html.Div([
    html.H2('Population stats', style={'text-align': 'center'}),
    html.H4('- in development', style={'text-align': 'center'}),
    html.Div(html.Hr() ),
    html.Div(
        [html.Div(
                [dcc.Slider(1_000_000, 500_000_000, 50_000_000, value=10, id='Slider_pop'),
                dcc.Slider(70, 85, 1, value=10, id='Slider_life_exp')],
                style = {'width' : '50%'}) ],
        style={
            'display': 'flex',
            'justify-content': 'center'} ),

    html.Div([
        dcc.RadioItems(options=['pop', 'lifeExp', 'gdpPercap'], value='lifeExp', id='controls-and-radio-item', inline=True),
        dash_table.DataTable(data=df.to_dict('records'), page_size=8, style_table={'width' : '100vh'},
                            style_cell_conditional= [{'if':{'column_id':'country'}, 'textAlign':'left'}] ),

        html.Div(children='Chart'),
        #dcc.Graph(figure=px.histogram(df, x='continent', y='lifeExp', histfunc='avg')),
        dcc.Graph(figure={}, id='output-figure', style={'width' : '100vh'}, config = {'displaylogo' : False}) ],
            style = {
            'width': '100%',
            'margin': '0 auto',
            'display': 'flex',
            'flex-direction': 'column',
            'justify-content': 'center',
            'align-items': 'center',
            'height': '100vh',
            'overflow': 'hidden'} )
                    ]
    )


# Add controls to build the interaction
@callback(
    Output(component_id='output-figure', component_property='figure'),
    Input(component_id='Slider_life_exp', component_property='value'),
    Input(component_id='Slider_pop', component_property='value') )

def update_graph(life_exp, pop):
    df_f = df[(df['lifeExp'] > life_exp) & (df['pop'] > pop) ]

    table = go.Figure(data=[go.Table(
        header=dict(values=list(df_f.columns)),
        cells=dict(values=[df_f[col] for col in df_f.columns])) ])

    return table

# Run the app
if __name__ == '__main__':
    app.run(debug=True)