# Imports
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
pd.options.display.float_format = '{:.2f}'.format
import plotly.express as px
import datetime
from datetime import date
import plotly.graph_objects as go
import numpy as np

# Load data
# Loads as timestamp (technically datetime64) - no need for explicit parsing
df = pd.read_excel('FadeFinderOutput_AGGS_23_08_2023.xlsx')
df.Date = df.Date.dt.date

# Adjust data - units and number of decimals
df.PreVolume = (df.PreVolume / 1_000_000).round(2)
df.Volume = (df.Volume / 1_000_000).round(2)
df.GapSize = df.GapSize.round(2)
df.MarketCap = (df.MarketCap / 1_000_000).round(2)

# Initialize the app
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP]) #COSMO
app.title = "FadeFinder"
server = app.server

# --- Elements for the layout ---

# output sections for the layout
#output_datatable = dcc.Graph(figure={}, id='output-figure', config={'displaylogo': False})
output_datatable = dbc.Container(id='output-figure', style={"padding-left" : "0%"})
output_frontpage_chart = dcc.Graph(figure={}, id='output-figure2', config={'displaylogo': False})
output_basic_stats = dbc.Container(id='output_basic_stats', style={'margin-top' : "30px"})

output_backtest = dcc.Graph(figure={}, id='output_backtest', config={'displaylogo': False})

# Sliders section
slider_section = html.Div(
            [html.Div(
                [dbc.Label("GapSize (%)", style={'margin-top': '20px'}),
                 dcc.RangeSlider(10, 200, 10, value=[20, 199], id='Slider_GapSize', tooltip={"placement": "bottom"}),
                 dbc.Label("PreVolume (M.)", style={'margin-top': '20px'}),
                 dcc.RangeSlider(0.5, 30, value=[1,5], id='Slider_PreVolume', tooltip={"placement": "bottom"}),
                 dbc.Label("Open Price ($ unadjusted)", style={'margin-top': '20px'}),
                 dcc.RangeSlider(0, 50, value=[0,6], id='Slider_OpenUnadjusted', tooltip={"placement": "bottom"}),
                 dbc.Label("MarketCap (M.)", style={'margin-top': '20px'}),
                 dcc.RangeSlider(0, 200, value=[10, 100], id='Slider_MarketCap', tooltip={"placement": "bottom"}),
                 dbc.Label("Open/PreHigh (Percentile)", style={'margin-top': '20px'}),
                 dcc.RangeSlider(0, 1, 0.1, value=[0.4, 1], id='Slider_Open/PreHigh', tooltip={"placement": "bottom"}),
                 dbc.Label("Time period", style={'margin-top': '20px'}),
                 html.Br(),
                 dcc.DatePickerRange(id="picker_DateRange", start_date=date(2018, 1, 1), end_date=date(2023, 7, 1), display_format='DD-MMM-YYYY')
                 ],
                style={'width': '95%'}
            )],
            style={
                'display': 'flex',
                'justify-content': 'center'})


# information box - definitions of measures
accordion_section = html.Div(
    dbc.Accordion(
        [dbc.AccordionItem([
            html.B("GapSize"),
            html.P("The percentage difference from prior days' close to next day opening price."),
            html.B("PreVolume"),
            html.P("The total volume traded from 4AM EST to 9:30 EST across exchanges."),
            html.B("Opening price (unadjusted)"),
            html.P("The unadjusted price is the price the stock was trading at on a given day and avoids hindsight bias.")],
        title="Definitions of stats" )],
            style={"margin-top": "8%"}
                    ))

right_side_overview = dbc.Container([
                            output_datatable,
                            output_frontpage_chart
                            ], style={"margin-top": "3%", "margin-left" : "0%", "padding-left" : "0%"})

right_side_backtest = dbc.Container([
                        output_backtest
])

# tabs section
tabs_section = dbc.Tabs([
                    dbc.Tab(right_side_overview, label="Overview"),
                    dbc.Tab([output_basic_stats, right_side_backtest], label="Backtest"),
                    dbc.Tab(html.P("tab2 text"), label="Deep dive"),
                    dbc.Tab(html.P("tab2 text"), label="Heatmap")
])


# App layout
app.layout = dbc.Container(
        [
        dbc.Row([html.Div([
                    html.H2("FadeFinder"), #, className="text-center bg-primary text-white p-2" ),
                    html.H6('- A gapper stats tool in development') ],
                    className="text-center bg-primary text-white p-2",
                    style={'marginBottom': '3em'})
        ]),
        dbc.Row([
            dbc.Col(dbc.Card(
                        html.Div([
                            html.H3('Parameter settings for testing', style={"margin": "10px"} ),
                            #html.Div(html.Hr()),  # Maybe use this later to divide two categories of sliders
                            slider_section,
                            accordion_section ],
                            style={"background-color": "Gainsboro"}),
                    style={"margin-left" : "2%"},

                ), #"border":"2px grey solid",
                width=4
            ),
            dbc.Col([], width=1),  # Empty column for whitespace,
            dbc.Col([
                #html.H3('Data section'),
                tabs_section,
                ], width=7)

        ], justify="start")
    ],
    fluid=True
)

# --- Custom functions ---

def generate_basic_stats(df_f):

    table_header = [html.Thead(
                        html.Tr(
                            html.Th("Basic statistics", colSpan=2, style={'text-align': 'center'}))
    )]

    setups_count = df_f.shape[0]
    red_close_count = df_f[df_f['Day1/Gap'] < 0].shape[0]
    green_close_count = df_f[df_f['Day1/Gap'] > 0].shape[0]
    red_close_percentage = (red_close_count / setups_count ) * 100
    green_close_percentage = (green_close_count / setups_count ) * 100
    largest_fade = df_f['Day1/Gap'].min()
    largest_fade_name = df[df['Day1'] == df['Day1'].min()]['Stock']
    largest_fade_date = df[df['Day1'] == df['Day1'].min()]['Date']

    percentage_break_PM_high = (df_f.loc[df_f['PreBreakTime'].notna(), 'PreBreakTime'].count() / setups_count) * 100


    table_body = [html.Tbody([
        html.Tr([html.Td("Number of setups"), html.Td(setups_count)]),
        html.Tr([html.Td("Number of days closing red"), html.Td(red_close_count)]),
        html.Tr([html.Td("Number of days closing green"), html.Td(green_close_count)]),
        html.Tr([html.Td("Percentage of days closing red"), html.Td(round(red_close_percentage, 2))]),
        html.Tr([html.Td("Percentage of days closing green"), html.Td(round(green_close_percentage, 2))]),

        html.Tr([html.Td("Percentage of days breaking PM-high"), html.Td(round(percentage_break_PM_high, 2))]),

        html.Tr([html.Td("Largest fade (Gap multiples)"), html.Td(round(largest_fade, 2))]),
        html.Tr([html.Td("Largest fade ticker"), html.Td(largest_fade_name)]),
        html.Tr([html.Td("Largest fade ticker"), html.Td(largest_fade_date)]),

        html.Tr([html.Td("Trading days in test period"), html.Td("Trading days in test period")])
    ])
    ]

    table = dbc.Table(table_header + table_body, bordered=False, striped=True, hover=True)

    return table

def Plotter_Stats(df_f, long_short='Short', FeeWin=0.01, FeeLoss=0.02):  # now in percentage
    '''Fees need to be calculated dynamically for each stop_size as long as we are using percentage size - could switch to absolute values'''
    # not sure if thats necessarily true though....

    winrate_dict = {}  # Dictionary to store winrate values
    EV_dict = {}  # Dictionary_ to store EV values
    PF_dict = {}  # Dict to store PF

    list_stopsizes = [0.3, 0.5, 0.6, 0.7, 1]

    for stopsize in list_stopsizes:

        result_column_title = 'SL' + str(stopsize) + 'Gap'

        # define columns for trade results in R-multiples
        risk = stopsize * df_f['GapSizeAbs']
        if long_short == 'Short':
            profit = ((df_f["OpenUnadjusted"] - df_f["CloseUnadjusted"]) - (df_f["OpenUnadjusted"] * FeeWin)) / risk
            loss = (-risk - (df_f["OpenUnadjusted"] * FeeLoss)) / risk
            df_f[result_column_title] = np.where(df_f['MaxGain/Gap'] < stopsize, profit, loss)

        elif long_short == 'Long':
            profit = ((df_f["CloseUnadjusted"] - df_f["OpenUnadjusted"]) - (df_f["OpenUnadjusted"] * FeeWin)) / risk
            loss = (-risk - (df_f["OpenUnadjusted"] * FeeLoss)) / risk
            df_f[result_column_title] = np.where(abs(df_f['Open_to_low/Gap'] < stopsize), profit, loss)

        # define a dictionary entry for each winrate + replace the decimal with an underscore
        winrate_variable_title = 'WR' + str(stopsize).replace('.', '_') + 'Gap'
        winrate_dict[winrate_variable_title] = (df_f[result_column_title] > 0).mean() * 100
        # https://stackoverflow.com/questions/63422081/python-dataframe-calculate-percentage-of-occurrences-rows-when-value-is-greater

        # define a variable for each expected value
        EV_variable_title = "EV" + str(stopsize) + "Gap"
        EV_dict[EV_variable_title] = df_f[result_column_title].mean()

        # define ... for each profitfactor
        PF_variable_title = "PF" + str(stopsize) + "Gap"
        Sum_wins = df_f.loc[df_f[result_column_title] > 0, result_column_title].sum()
        Sum_losses = df_f.loc[df_f[result_column_title] < 0, result_column_title].sum()
        PF_dict[PF_variable_title] = abs(Sum_wins) / abs(Sum_losses)

        # measure for % trades closing -1

        # measure for % trades closing +1 R


    # calculate profitfactor + sums
    Sum_wins_r = df_f[(df_f['SL0.5Gap'] > 0)]['SL0.5Gap'].sum()
    Sum_losses_r = df_f[(df_f['SL0.5Gap'] < 0)]['SL0.5Gap'].sum()
    Profit_factor = abs(Sum_wins_r) / abs(Sum_losses_r)

    # --- Show the data in a table ---

    data = [
        ["Profit factor:", Profit_factor],
        ["Total wins R:", Sum_wins_r],
        ["Total losses R:", Sum_losses_r]]

    #table = tabulate(data, headers=['Measure', 'Value'], tablefmt='html')

    #display(table)

    # Define lists to present in a table
    list_winrates = [list(winrate_dict.values())[x].round(2) for x in range(len(list_stopsizes))]
    list_EV = [list(EV_dict.values())[x].round(2) for x in range(len(list_stopsizes))]
    title_col = [x for x in list_stopsizes]
    list_PF = [list(PF_dict.values())[x].round(2) for x in range(len(list_stopsizes))]

    values = [title_col, list_winrates, list_EV, list_PF]

    fig = go.Figure(
        data=[go.Table(
            # columnorder = [0,1],
            columnwidth=[100, 200],
            header=dict(
                values=[['<b>Basic metrics</b><br>As of: June 1st 2023'],
                        ['<b>Winrate (%)</b>'], ['<b>EV (R)</b>'], ['<b>PF (R)</b>']],
                line_color='darkslategray',
                fill_color='royalblue',
                align=['left', 'center'],
                font=dict(color='white', size=12),
                height=40),
            cells=dict(
                values=values,
                line_color='darkslategray',
                fill=dict(color=['paleturquoise', 'white']),
                align=['left', 'center'],
                font_size=12,
                height=30))
        ])

    return fig

# Define the callback controlling the interactive features
@app.callback(
    Output(component_id='output-figure', component_property='children'),
    Output(component_id='output-figure2', component_property='figure'),
    Output(component_id='output_backtest', component_property='figure'),
    Output(component_id='output_basic_stats', component_property='children'),

    Input(component_id='Slider_GapSize', component_property='value'),
    Input(component_id='Slider_PreVolume', component_property='value'),
    Input(component_id='Slider_OpenUnadjusted', component_property='value'),
    Input(component_id='Slider_MarketCap', component_property='value'),
    Input(component_id='Slider_Open/PreHigh', component_property='value'),
    Input(component_id='picker_DateRange', component_property='start_date'),
    Input(component_id='picker_DateRange', component_property='end_date')
    #Input(component_id='Slider_Weekday', component_property='value'),
)

def update_graph(gapsize, PreVolume, Price, MarketCap, Open_PreHigh, start_date, end_date):

    #DateRange values need parsing - comes in as string format
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()

    df_f = df[
          ( (df['GapSize'] >= gapsize[0]) & (df['GapSize'] <= gapsize[1])) &
          ( (df['PreVolume'] > PreVolume[0]) & (df['PreVolume'] < PreVolume[1])) &
          ( (df['OpenUnadjusted'] > Price[0]) & (df['OpenUnadjusted'] < Price[1])) &
          ( (df['MarketCap'] >= MarketCap[0]) & (df['MarketCap'] <= MarketCap[1])) &
          ( (df['Open/PreHigh'] >= Open_PreHigh[0]) & (df['Open/PreHigh'] <= Open_PreHigh[1])) &
          #(df['Weekday'].isin(Weekday)) &
          ( (df['Date'] >= start_date) & (df['Date'] <= end_date) )
          ]

    df_f = df_f[['Date','Stock','MarketCap','GapSize','PreVolume','Weekday','Volume', 'Day1/Gap', 'MaxGain/Gap', 'PreBreakTime', 'GapSizeAbs', 'OpenUnadjusted', 'CloseUnadjusted']]

    df_to_present = df_f[['Date', 'Stock', 'GapSize', 'PreVolume', 'MarketCap', 'Day1/Gap']]

    #table = dbc.Table.from_dataframe(df_f, striped=True, bordered=True, hover=True, size ='md')

    overview_table = dash_table.DataTable(df_to_present.to_dict('records'), [{"name": i, "id": i, "format" :  {'specifier': '.2f'}} for i in df_to_present.columns],

                                 page_size=10,
                                 style_table={'margin': 0, 'padding': 0},
                                 style_cell={'textAlign' : 'left'},
                                 style_data_conditional=[{
                                         'if': {'row_index': 'odd'},
                                         'backgroundColor': 'rgb(220, 220, 220)',
                                         }],
                                 style_header={'fontWeight': 'bold', 'backgroundColor': 'white'}
                                 )


    chart_temp = px.scatter(df_f, df_f.Date, df_f['Day1/Gap'])

    #output_backtest = px.scatter(df_f, df_f.Date, df_f['Day1/Gap'])
    output_backtest = Plotter_Stats(df_f)

    output_basic_stats = generate_basic_stats(df_f)

    return overview_table, chart_temp, output_backtest, output_basic_stats


# Run the app
if __name__ == '__main__':
    app.run(debug=True)




# output_datatable2 = html.Div([
#         #html.Div(children='Chart'),
#         dcc.Graph(figure={}, id='output-figure', style={'width': '90vw'}, config={'displaylogo': False})],
#         style={
#             #'width': '100%',
#             'margin': '0 auto',
#             'display': 'flex',
#             'flex-direction': 'column',
#             'justify-content': 'center',
#             'align-items': 'center',
#             'height': '100vh',
#             'overflow': 'hidden'})