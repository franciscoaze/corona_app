import requests
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import plotly.express as px

url = "https://pomber.github.io/covid19/timeseries.json"
resp = requests.get(url)
countries_json = resp.json()
country_names = [i for i in countries_json.keys()]


class Analyze:

    def __init__(self):

        self.IT = Country('Italy',0)
        self.PT = Country('Portugal',0)


class Country:

    def __init__(self,name,start):
        try:
            s = int(start)
        except:
            s = 0

        self.name = name
        self.raw_df = pd.DataFrame(countries_json[name])
        self.active_df = self.raw_df.loc[self.raw_df['confirmed']>s].reset_index(drop=True)
        self.started = self.active_df.loc[0].date
        self.days = self.active_df.__len__()


class Graphics:

    def __init__(self,data):
        external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

        self.app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=data.IT.active_df.index, y=data.IT.active_df['confirmed'],
                                 mode='lines+markers',
                                 name='Italy',
                                 customdata = data.IT.active_df['date'],
                                 hovertemplate = "Day %{x} <br>"
                                                 "%{customdata} <br>"
                                                 "%{y} cases confirmed"))
        fig.add_trace(go.Scatter(x=data.PT.active_df.index, y=data.PT.active_df['confirmed'],
                                 mode='lines+markers',
                                 name='Portugal',
                                 customdata=data.PT.active_df['date'],
                                 hovertemplate="Day %{x} <br>"
                                               "%{customdata} <br>"
                                               "%{y} cases confirmed"))

        fig.update_layout(xaxis_title='Dias',
                          yaxis_title='Casos Confirmados')

        country_dict = [{'label':c, 'value': c} for c in country_names]
        self.app.layout = html.Div(children=[
            html.H1(children='Dashboard'),
            html.Div([
            dcc.Graph(
                id='confirmados',
                figure= fig
            ),
            dcc.RangeSlider(
                id='days_from',
                min=0,
                max=100,
                step=1,
                value=[0,100],
            )]),
            html.Div([
                html.Label('Start counting from ... confirmed cases'),
                dcc.Input(id='start_from', value='0', type='text')]),
            html.Br(),
            html.Div([dcc.Dropdown(
                options= country_dict,
                multi=True,
                value=["Portugal","Italy"],
                id = 'dropdown'
            )])
        ])

        @ self.app.callback(
        dash.dependencies.Output('confirmados', 'figure'),
        [dash.dependencies.Input('dropdown', 'value'),
         dash.dependencies.Input('start_from', 'value'),
         dash.dependencies.Input('days_from', 'value')])
        def update_graph(ctry,start,lim):
            fig = go.Figure()
            maxi = []
            for country_name in ctry:
                c = Country(country_name,start)

                fig.add_trace(go.Scatter(x=c.active_df.index, y=c.active_df['confirmed'],
                                         mode='lines+markers',
                                         name=country_name,
                                         customdata=c.active_df['date'],
                                         hovertemplate="Day %{x} <br>"
                                                       "%{customdata} <br>"
                                                       "%{y} cases confirmed"))
                maxi.append(c.days)
            xlimit = round(max(maxi)*lim[1]/100)
            fig.update_layout(xaxis_range = [lim[0],xlimit],
                              xaxis_title='Dias',
                              yaxis_title='Casos Confirmados')
            return fig

if __name__ == '__main__':
    data = Analyze()
    pltly = Graphics(data)
    pltly.app.run_server(debug=True)
