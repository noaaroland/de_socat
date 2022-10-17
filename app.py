from dash import Dash, dcc, html, Input, Output, exceptions
import dash_design_kit as ddk
import plotly.graph_objects as go
import plotly.express as px
import vaex
import os
import colorcet as cc
import dask.dataframe as dd
import pandas as pd
import datashader as ds
import datashader.transfer_functions as tf
import PIL
import sdig.erddap.util as util
import dask

# Load Parquet file as vaex DataFrame
parquet_path = "./data/socat_2022_decimated.parquet"
vdf = dd.read_parquet(parquet_path, npartitions=8)
full_path = "./data/socat_2022.parquet"
fdf = dd.read_parquet(full_path)
ESRI_API_KEY = os.environ.get('ESRI_API_KEY')
variables = vdf.columns.to_list()
variables.sort()
variable_options = []
for var in variables:   
    if var != 'lat_meters' and var != 'lon_meters':
        variable_options.append({'label':var, 'value': var})

center = {'lon': 0.0, 'lat': 0.0}
zoom = .5
map_height = 520
map_width = 1040
map_title_base = 'Trajectory from the SOCAT v2022 Decimated Data Set '

# Define Dash application structure
app = Dash(__name__)
server = app.server  # expose server variable for Procfile

app.layout = ddk.App(children=[
    ddk.Header([
        ddk.Logo(src='https://www.socat.info/wp-content/uploads/2017/06/cropped-socat_cat.png'),
        ddk.Title('Surface Ocean CO\u2082 Atlas'),
    ]),
    html.Div(id='kick'),
    ddk.ControlCard(width=.3, children=[
        ddk.ControlItem(label='Expocode', children=[
            dcc.Dropdown(id='expocode', placeholder='Select Cruises by Expocode', multi=True)
        ]),
        ddk.ControlItem(label='Color by', children=[
            dcc.Dropdown(id='map-variable', value='fCO2_recommended', multi=False, options=variable_options)
        ])
    ]),
    ddk.Card(width=.7,
        children=[
            dcc.Loading(
                ddk.CardHeader(
                    modal=True, 
                    modal_config={'height': 90, 'width': 95}, 
                    fullscreen=True,
                    id='map-graph-header',
                    title=map_title_base,
                ),
            ),
            ddk.Graph(
                id='map-graph',
            ),
        ]
    ),
        ddk.ControlCard(width=.3, children=[
        ddk.ControlItem(label='Plot type', children=[
            dcc.Dropdown(id='plot-type',
            value='timeseries',
            multi=False,
            options=[
                {'label': 'Timeseries', 'value': 'timeseries'},
                {'label': 'Property-Property', 'value': 'prop-prop'}
            ])
        ]),
        ddk.ControlItem(id='prop-prop-x-item', style={'display':'none'}, label='Property-property X-axis', children=[
            dcc.Dropdown(id='prop-prop-x',
            value='fCO2_recommended',
            multi=False,
            disabled=False,
            options=variable_options)
        ]),
        ddk.ControlItem(id='prop-prop-y-item', style={'display':'none'}, label='Property-property Y-axis', children=[
            dcc.Dropdown(id='prop-prop-y',
            value='latitude',
            multi=False,
            disabled=False,
            options=variable_options)
        ]),
        ddk.ControlItem(id='prop-prop-colorby-item', style={'display':'none'}, label='Property-property Color-by', children=[
            dcc.Dropdown(id='prop-prop-colorby',
            value='expocode',
            multi=False,
            disabled=False,
            options=variable_options)
        ]),
    ]),
    ddk.Card(width=.7,
        children=[
            dcc.Loading(
                ddk.CardHeader(
                    modal=True, 
                    modal_config={'height': 90, 'width': 95}, 
                    fullscreen=True,
                    id='graph-header',
                ),
            ),
            dcc.Loading(
                ddk.Graph(id='graph',),
            )
        ]
    ),
])


@app.callback(
    [
        Output('expocode', 'options')
    ],
    [
        Input('kick', 'n_clicks')
    ]
)
def set_expocode_options(click):
    deci_df = vdf
    expos = deci_df['expocode'].unique()
    options = []
    for expo in expos:
        options.append({'label': expo, 'value': expo})
    return [options]


@app.callback(
    [
        Output('map-graph', 'figure'),
        Output('map-graph-header', 'title'),
    ],
    [
        Input('kick', 'n_clicks'),
        Input('expocode', 'value'),
        Input('map-variable', 'value'),
        Input("map-graph", "relayoutData"),
    ]
)
def update_map(clicky, map_in_expocode, map_in_variable, map_state):
    title = 'joe'
    if map_state is not None and 'mapbox.zoom' in map_state:
        my_zoom = map_state['mapbox.zoom']
    else:
        my_zoom = zoom
    if map_state is not None and 'mapbox.center' in map_state:
        my_center = map_state['mapbox.center']
    else:
        my_center = center
    deci_df = vdf
    if map_state is not None and 'mapbox._derived' in map_state:
        derived = map_state['mapbox._derived']
        if 'coordinates' in derived:
            map_coords = derived['coordinates']
            print('incoming map coords')
            print(map_coords)
            lon_min = map_coords[0][0]
            lon_max = map_coords[1][0]
            lat_min = map_coords[2][1]
            lat_max = map_coords[0][1]
            print('lon_min=',lon_min,'lon_max=',lon_max,'lat_min=',lat_min,'lat_max=',lat_max)
            deci_df = util.getLonConstraint(lon_min, lon_max, True, True, 'longitude', vdf)
            deci_df = deci_df.loc[(deci_df['latitude']<=lat_max) & (deci_df['latitude']>=lat_min)]
            # deci_df = vdf.loc[(vdf['latitude']<=lat_max) & (vdf['latitude']>=lat_min) & (vdf['longitude']>=lon_min) & (vdf['longitude']<=lon_max)]            

    map_variable = 'fCO2_recommended'
    if map_in_variable is not None and len(map_in_variable) > 0:
        map_variable = map_in_variable
    
    if map_in_expocode is not None:
        if isinstance(map_in_expocode, str):
            deci_df = vdf[vdf.expocode == map_in_expocode]
        elif isinstance(map_in_expocode, list) and len(map_in_expocode) > 0:
            for ei, expo in enumerate(map_in_expocode):
                if ei == 0:
                    deci_df = vdf.filter(deci_df.expocode==expo)
                else:
                    deci_df = deci_df.filter(deci_df.expocode==expo, mode="or")


    # Build graph title
    title ='Mean of ' + map_variable + " from ( {nrows:,} cruise tracks shown )".format(nrows=len(deci_df['expocode'].unique()))

    # if map_variable != 'expocode' and map_variable != 'dataset_name' and map_variable != 'platform_name' and map_variable != 'platform_type' and map_variable != 'organization':
    #     deci_df['map_text'] = deci_df['text'] + '<br>' + map_variable + "=" + deci_df[map_variable].astype('str')
    # else:
    #     deci_df['map_text'] = deci_df['text']
    # if deci_df[map_variable].dtype == 'string':
    #     for cati, category in enumerate(deci_df[map_variable].unique()):
    #         cat_df = deci_df[deci_df[map_variable] == category]
    #         map = go.Scattermapbox(lat=cat_df['latitude'].values, 
    #                     lon=cat_df['longitude'].values,
    #                     marker=dict(color=cc_color_set(cati, cc.glasbey_bw_minc_20)),
    #                     hoverlabel = {'namelength': 0,},
    #                     hovertext=cat_df['map_text'].values,name=category, customdata=cat_df['expocode'].values)
    #         figure.add_trace(map)
    # else:
    #     map = go.Scattermapbox(lat=deci_df['latitude'].values, 
    #                         lon=deci_df['longitude'].values,
    #                         hovertext=deci_df['map_text'].values,
    #                         hoverlabel = {'namelength': 0,},
    #                         marker=dict(color=deci_df[map_variable].values,
    #                                     # autocolorscale=True,
    #                                     colorscale='Viridis',
    #                                     showscale=True), customdata=deci_df['expocode'].values)
    #     figure.add_trace(map)
    #
    ######################################
    #
    # For now, assume we're working with the entire data frame and compute using datashader
    #
    lon_min = deci_df['longitude'].min(numeric_only=True).compute()
    lon_max = deci_df['longitude'].max(numeric_only=True).compute()
    lat_min = deci_df['latitude'].min(numeric_only=True).compute()
    lat_max = deci_df['latitude'].max(numeric_only=True).compute()
    coordinates = [[lon_min, lat_min],
                   [lon_max, lat_min],
                   [lon_max, lat_max],
                   [lon_min, lat_max]]
    print('coordinates=')
    print(coordinates)
    cvs = ds.Canvas(plot_width=map_width, plot_height=map_height)
    print('canvas set')
    agg = cvs.points(deci_df, 'lon_meters', 'lat_meters', ds.mean(map_variable))
    print('agg created')
    img = ds.tf.shade(agg, cmap=cc.bgy).to_pil()
    print('shading complete')
    img = img.transpose(PIL.Image.Transpose.FLIP_TOP_BOTTOM)
    figure = go.Figure()
    map = go.Scattermapbox()
    figure.add_trace(map)
    print('map built')
    figure.update_layout(
        height=map_height,
        width=map_width,
        mapbox_style="white-bg",
        mapbox_layers=[
            {
                "below": 'traces',
                "sourcetype": "raster",
                "sourceattribution": "Powered by Esri",
                "source": [
                    "https://ibasemaps-api.arcgis.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}?token=" + ESRI_API_KEY
                ]
            },
            {"sourcetype": "image", "source": img, "coordinates": coordinates}
        ],
        mapbox_zoom=my_zoom,
        mapbox_center=my_center,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend=dict(
            orientation="v",
            x=-.01,
        ),
        modebar_orientation='v',
    )
    print('returning figure')
    return figure, title


@app.callback(
    [
        Output('expocode', 'value')
    ],
    [
        Input('map-graph', 'clickData')
    ], prevent_initial_call=True
)
def set_platform_code_from_map(state_in_click):
    out_expocode = None
    if state_in_click is not None:
        fst_point = state_in_click['points'][0]
        out_expocode = fst_point['customdata']
    return [out_expocode]


@app.callback(
    [
        Output('graph', 'figure'),
        Output('graph-header', 'title')
    ],
    [
        Input('kick', 'n_clicks'),
        Input('expocode', 'value'),
        Input('plot-type', 'value'),
        Input('map-variable', 'value'),
        Input('prop-prop-x', 'value'),
        Input('prop-prop-y', 'value'),
        Input('prop-prop-colorby', 'value'),
    ]
)
def update_plots(clicky, plot_in_expocode, in_plot_type, in_map_variable, in_prop_prop_x, in_prop_prop_y, in_prop_prop_colorby):
    if plot_in_expocode is None:
        raise exceptions.PreventUpdate
    if len(plot_in_expocode) < 1:
        raise exceptions.PreventUpdate
    deci_df = fdf
    figure = go.Figure()
    x_label = None
    y_label = None
    legend_title = None
    if plot_in_expocode is not None and len(plot_in_expocode) > 0:
        if isinstance(plot_in_expocode, str):
            plot_in_expocode = [plot_in_expocode]
            
        for ei, expo in enumerate(plot_in_expocode):
            deci_df = vdf.filter(deci_df.expocode==expo)
            if in_plot_type == 'timeseries':
                deci_df = deci_df.sort('time')
                x_values = deci_df['time'].values
                y_values = deci_df[in_map_variable].values
                marker = None
                mode='lines'
                if ei == 0:
                    card_title = in_map_variable + ' for ' + str(expo)
                else:
                    card_title = card_title + ', ' + str(expo)
                x_label = 'Time'
                y_label = in_map_variable
                if in_map_variable != 'expocode' and in_map_variable != 'dataset_name' and in_map_variable != 'platform_name' and in_map_variable != 'platform_type' and in_map_variable != 'organization':
                    deci_df['plot_text'] = deci_df['text'] + '<br>' + in_map_variable + "=" + deci_df[in_map_variable].astype('str')
            elif in_plot_type == 'prop-prop':
                if ei == 0: 
                    card_title = in_prop_prop_y + ' vs ' + in_prop_prop_x + ' colored by ' + in_prop_prop_colorby + ' for ' + str(expo)
                else:
                    card_title = card_title + ', ' + str(expo)
                x_values = deci_df[in_prop_prop_x].values
                y_values = deci_df[in_prop_prop_y].values
                color_by = deci_df[in_prop_prop_colorby].values
                x_label = in_prop_prop_x
                y_label = in_prop_prop_y
                legend_title = in_prop_prop_colorby
                mode='markers'
                deci_df['plot_text'] = deci_df['text']
                if deci_df[in_prop_prop_colorby].dtype == 'string':
                    marker = dict(color=px.colors.qualitative.Light24[ei])
                else:
                    marker = dict(color=color_by,autocolorscale=True,showscale=True)
            plot = go.Scatter(x=x_values, y=y_values, marker=marker, name=expo, mode=mode, hovertext=deci_df['plot_text'].values, hoverlabel = {'namelength': 0,},)
            figure.add_trace(plot)
        figure.update_xaxes(title_text=x_label, showticklabels=True)
        figure.update_yaxes(title_text=y_label, showticklabels=True)
        if legend_title is not None:
            figure.update_layout(legend_title=legend_title)
    return[figure, card_title]


@app.callback(
    [
        Output('prop-prop-x-item', 'style'),
        Output('prop-prop-y-item', 'style'),
        Output('prop-prop-colorby-item', 'style')
    ],
    [
        Input('plot-type', 'value')
    ]
)
def set_expocode_options(in_plot_type):
    if in_plot_type is not None and in_plot_type == "prop-prop":
        return [{'display': 'block'}, {'display': 'block'}, {'display':'block'}]
    return [{'display':'none'}, {'display':'none'}, {'display':'none'}]


def cc_color_set(index, palette):
    rgb = px.colors.convert_to_RGB_255(palette[index])
    hexi = '#%02x%02x%02x' % rgb
    return hexi


if __name__ == '__main__':
    app.run_server(debug=True)
