from flask import Flask, render_template, request, Blueprint
from housing.db import get_db
import pandas as pd
import numpy as np
import json
from housing.queries import get_layout_from_db, get_housing_from_db, analysis_query, get_census_data, get_monthly_price, digit_to_dollar_string
from housing.ml_models import run_KMeans
from housing.perference import Perference
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils as pu
from datetime import date


views = Blueprint('views', __name__)
plotly_go_token = open('./housing/access_token/mapbox.txt').read()
today = date.today()
month = today.strftime("%Y-%m")
perference = Perference()


@views.route('/<location>/customize', methods=['POST'])
def update_custom_settings(location):
    perference.bedroom_from = request.form.get('bedroomFrom')
    perference.bedroom_to = request.form.get('bedroomTo')
    perference.bathroom_from = request.form.get('bathroomFrom')
    perference.bathroom_to = request.form.get('bathroomTo')
    perference.aggregated_type = request.form.get('aggregatedType')
    perference.max_posted_days = request.form.get('maxPostedDays')
    return city_map(location)


@views.route('/', defaults={'location': 'princeton'})
@views.route('/<location>', methods=['GET'])
def city_map(location):
    city_name =  []
    city_coords = tuple()

    if location == 'nyc':
        city_name = ['NYC,NY']
        city_coords = (40.7128, -74.0060)
    elif location == 'seattle':
        city_name = ['Seattle,WA']
        city_coords = (47.6062, -122.3321)
    elif location == 'princeton':
        city_name = ['Princeton,NJ', 'West Windsor,NJ', 'Lawrence,NJ']
        city_coords = (40.3573, -74.6672)

    additional_args = {
        "bedroom_from": perference.bedroom_from, 
        "bedroom_to": perference.bedroom_to,
        "bathroom_from": perference.bathroom_from,
        "bathroom_to": perference.bathroom_to,
        "aggregated_type": perference.aggregated_type,
        "max_posted_days": perference.max_posted_days
    }
   
    cursor = get_db()
    summarize = analysis_query(cursor, city_name, month, kwargs=additional_args)
    month_prices = get_monthly_price(cursor, city_name, month, kwargs=additional_args)
    urls, lons, lats, price = get_housing_from_db(cursor, city_name, month, kwargs=additional_args)
    
    # table and graph on the right
    prices = month_prices['price']
    months = month_prices['month']
    fig_right = go.Figure()
    fig_right.add_trace(go.Box(y=prices,x=months, boxpoints=False))
    fig_right.update_layout(height=400, width=400)
    graphJSON_right = json.dumps(fig_right, cls=pu.PlotlyJSONEncoder)

    # graph on the left
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
    
    graphJSON_left = json.dumps(fig, cls=pu.PlotlyJSONEncoder)

    return render_template('map.html', graphJSON=[graphJSON_left, graphJSON_right], tables=[summarize.to_html(classes='data', header="true")])



@views.route('/<location>/graph', methods=['POST'])
def rerender_graph(location):
    graphing_type = request.form.get('graphing')
    if location == 'nyc':
        city_name = ['NYC,NY']
        city_coords = (40.7128, -74.0060)
    elif location == 'seattle':
        city_name = ['Seattle,WA']
        city_coords = (47.6062, -122.3321)
    elif location == 'princeton':
        city_name = ['Princeton,NJ', 'West Windsor,NJ', 'Lawrence,NJ']
        city_coords = (40.3573, -74.6672)
    
    additional_args = {
        "bedroom_from": perference.bedroom_from, 
        "bedroom_to": perference.bedroom_to,
        "bathroom_from": perference.bathroom_from,
        "bathroom_to": perference.bathroom_to,
        "aggregated_type": perference.aggregated_type,
        "max_posted_days": perference.max_posted_days
    }
    cursor = get_db()
    urls, lons, lats, price = get_housing_from_db(cursor, city_name, month, kwargs=additional_args)
    if graphing_type == "heatmap":
        hovertemplate = 'Price: %{z} <br> More Info on: <a href="%{customdata}">Zillow Link</a>'
        fig = go.Figure(go.Densitymapbox(lat=lats, 
                                        lon=lons, 
                                        z=price, 
                                        customdata=urls,
                                        hovertemplate=hovertemplate,
                                        radius=30, 
                                        opacity=1))
    elif graphing_type == "scatter":
        fig = go.Figure(px.scatter_mapbox(lat=lats, 
                        lon=lons,
                        color=price,
                        size=price,
                        opacity=0.6,
                        custom_data=[digit_to_dollar_string(price), urls]
                        ))
        fig.update_traces(
            hovertemplate="<br>".join([
                "Price: %{customdata[0]}",
                'URL: More Info on: <a href="%{customdata[1]}">Zillow Link</a>',
            ])
        )
    elif graphing_type == "clustering":
        kmeans_result = run_KMeans(lats, lons, price, urls)
        fig = go.Figure(px.scatter_mapbox(lat=kmeans_result["lats"], 
                                lon=kmeans_result["lngs"], 
                                color=kmeans_result["medium_prices"],
                                custom_data=[digit_to_dollar_string(kmeans_result["price"]), digit_to_dollar_string(kmeans_result["medium_prices"]), kmeans_result["urls"]]
                        ))
        fig.update_traces(
            hovertemplate="<br>".join([
                "Price: %{customdata[0]}",
                "Cluster Medium Price: %{customdata[1]}",
                'URL: More Info on: <a href="%{customdata[2]}">Zillow Link</a>',
            ])
        )
    fig.update_layout(mapbox = {
        'accesstoken': plotly_go_token,
        },
        mapbox_style="outdoors",
        mapbox_zoom=11,
        mapbox_center_lat=city_coords[0],
        mapbox_center_lon=city_coords[1],
        height=800, width=1000,
    )
    graphJSON = json.dumps(fig, cls=pu.PlotlyJSONEncoder)
    return graphJSON

@views.route('/city-stats', methods=['POST', 'GET'])
def city_stats():
    census = get_census_data('./housing/census_data')
    return render_template('city-stats.html', tables=[census.to_html(classes='data', header="true")])


