from flask import Flask, render_template, request, Blueprint
from housing.db import get_db
import pandas as pd
import numpy as np
import json
from housing.queries import get_layout_from_db, get_housing_from_db, analysis_query, get_census_data, get_monthly_price
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils as pu
from datetime import date


views = Blueprint('views', __name__)
plotly_go_token = open('./housing/access_token/mapbox.txt').read()
today = date.today()
month = today.strftime("%Y-%m")



@views.route('/', defaults={'location': 'princeton'})
@views.route('/<location>', methods=['POST', 'GET'])
def city_map(location):
    #grouping_type = request.args.get("groupingType", "price")
    if location == 'nyc':
        city_name = ['NYC,NY']
        city_coords = (40.7128, -74.0060)
    if location == 'seattle':
        city_name = ['Seattle,WA']
        city_coords = (47.6062, -122.3321)
    if location == 'princeton':
        city_name = ['Princeton,NJ', 'West Windsor,NJ', 'Lawrence,NJ']
        city_coords = (40.3573, -74.6672)

    cursor = get_db()
    summarize = analysis_query(cursor, city_name, month)
    urls, lons, lats, price = get_housing_from_db(cursor, city_name, month)
    hovertemplate = 'Price: %{z} <br> More Info on: <a href="%{customdata}">Zillow Link</a>'
    fig = go.Figure(go.Densitymapbox(lat=lats, 
                                     lon=lons, 
                                     z=price, 
                                     customdata=urls,
                                     hovertemplate=hovertemplate,
                                     radius=30, 
                                     opacity=1))
    
    fig.update_layout(mapbox = {
        'accesstoken': plotly_go_token,
        },
        mapbox_style="outdoors",
        mapbox_zoom=11,
        mapbox_center_lat=city_coords[0],
        mapbox_center_lon=city_coords[1],
        height=800, width=1000,
    )

    lons, lats, names = get_layout_from_db(cursor, 'school', city_name)
    fig.add_trace(go.Scattermapbox(
                name='School',
                mode = 'markers+text',
                lon = lons,
                lat = lats,
                hovertext = names,
                marker=go.scattermapbox.Marker(
                    size=10,
                    opacity=1,
                    symbol="school"
                ),
                showlegend=True
            ))

    lons, lats, names = get_layout_from_db(cursor, 'train_station', city_name)
    fig.add_trace(go.Scattermapbox(
                name='Train',
                mode = 'markers+text',
                lon = lons, 
                lat = lats,
                hovertext = names,
                marker=go.scattermapbox.Marker(
                    size=20,
                    opacity=1,
                    symbol="rail"
                ),
                showlegend=True
            ))

    lons, lats, names = get_layout_from_db(cursor, 'supermarket', city_name)
    lons2, lats2, names2 = get_layout_from_db(cursor, 'shopping_malls', city_name)
    lons += lons2
    lats += lats2
    names += names2
    fig.add_trace(go.Scattermapbox(
                name='Shop',
                mode = 'markers+text',
                lon = lons, 
                lat = lats,
                hovertext = names,
                marker=go.scattermapbox.Marker(
                    size=10,
                    opacity=1,
                    symbol="shop"
                ),
                showlegend=True
            ))


    lons, lats, names = get_layout_from_db(cursor, 'hospital', city_name)
    fig.add_trace(go.Scattermapbox(
                name='Hospital',
                mode = 'markers+text',
                lon = lons, 
                lat = lats,
                hovertext = names,
                marker=go.scattermapbox.Marker(
                    size=10,
                    opacity=1,
                    symbol="hospital"
                ),
                showlegend=True
            ))
    
    graphJSON = json.dumps(fig, cls=pu.PlotlyJSONEncoder)
    
    month_prices = get_monthly_price(cursor, city_name, month)
    prices = month_prices['price']
    months = month_prices['month']
    fig2 = go.Figure()
    fig2.add_trace(go.Box(y=prices,x=months, boxpoints=False))
    graphJSON2 = json.dumps(fig2, cls=pu.PlotlyJSONEncoder)

    return render_template('map.html', graphJSON=[graphJSON, graphJSON2], tables=[summarize.to_html(classes='data', header="true")])


@views.route('/city-stats', methods=['POST', 'GET'])
def city_stats():
    census = get_census_data('./housing/census_data')
    return render_template('city-stats.html', tables=[census.to_html(classes='data', header="true")])


