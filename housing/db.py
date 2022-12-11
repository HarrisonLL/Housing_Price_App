import sqlite3
import click
import pandas as pd
import numpy as np
import json
import os
import glob
from datetime import date
from flask import current_app, g
from housing.utils.gmap import fetch_gmap_data
from housing.utils.zillow import zillow_request
import logging


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
    layout_types = ['school', 'shopping_malls', 'supermarket', 'train_station', 'hospital', 'subway_station']
    citiesLoc = {'Princeton,NJ': (40.3573, -74.6672), 'West Windsor,NJ': (40.2983, -74.6186), 
                'Lawrence,NJ':(40.2778, -74.7294), 'Seattle,WA':(47.6062, -122.3321), 'NYC,NY':(40.7128, -74.0060)}
    cities2idx = {'Princeton,NJ': 1, 'West Windsor,NJ': 2, 
                  'Lawrence,NJ': 3, 'Seattle,WA': 4, 'NYC,NY':5}
    with open('./housing/access_token/gmap.txt') as f:
        gmap_token = f.read()

    logging.critical('========= Initializing tables and city data =========')
    with current_app.open_resource('./sql/schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    with current_app.open_resource('./sql/initial_data.sql') as f:
        db.executescript(f.read().decode('utf8'))

    logging.critical('========= Starting API call to get layout data =========')
    response = dict()
    for city, location in citiesLoc.items():
        for layout in layout_types:
            if layout == 'subway_station' and city in {'Princeton,NJ', 'West Windsor,NJ', 'Lawrence,NJ'}:
                continue
            response = fetch_gmap_data(layout, location, response, gmap_token, city)

    logging.critical('========= API call was done, storing data to DB =========')
    for k,v in response.items():
        db.execute(
            """
            INSERT INTO city_layout (landmark_name, landmark_type, landmark_lat, landmark_lng, landmark_rating, city_id)
            VALUES
            (?, ?, ?, ?, ?, ?)
            """, (k, v[0], v[1], v[2], v[3], cities2idx[v[4]])
        )
    db.commit()


def update_db_monthly(month):
    data_dir = os.path.join('./housing/utils/crawled_data', month)
    if not os.path.exists(data_dir):
        msg = 'Data folder does not exits. Please create a directory and start crawling first \n'
        msg += 'Directory Tree \n'
        msg += './housing/utils/crawled_data/<some-crawler>.py \n'
        msg += './housing/utils/crawled_data/2022-11/<data>.csv \n'
        msg += './housing/utils/crawled_data/2022-12/<data>.csv \n'
        msg += '...'
        logging.exception(msg)
        return

    db = get_db()
    result = db.execute("""
    select * from city_housing where crawled_date = ?
    """, (month, ))
    record_cnt = 0
    for record in result: record_cnt += 1
    if record_cnt > 0:
        logging.exception('Entered month data already added')
        return

    city2idx = {'princeton': 1, 'west-windsor-township-nj': 2, 
            'lawrence-township-nj': 3, 'seattle': 4, 'nyc':5}
    columns = ['crawled_month','addressStreet', 'unformattedPrice', 'area', 'baths','beds', 'days', 'detailUrl', 'lat', 'lng']
    
    for file in glob.glob(data_dir+'/*.csv'):
        city_name = os.path.basename(file).split(month)[0]
        city_idx = city2idx[city_name]
        df = pd.read_csv(file)
        df['lat'] = [json.loads(string.replace("'", '"')).get('latitude')  for string in df.latLong.tolist()]
        df['lng'] = [json.loads(string.replace("'", '"')).get('longitude')  for string in df.latLong.tolist()]
        days = []
        for string in df.variableData.tolist():
            day = None
            if "DAYS_ON" in string:
                idx = string.index('text')
                day = int(string[idx:].split()[1][1:])
            days.append(day)
        df['days'] = days
        df = df[columns]
        records = df.to_numpy()
        logging.critical('========= Start sync DB for city: {} ========='.format(city_name))
        logging.critical('{} records crawled'.format(df.shape[0]))
        for record in records:
            db.execute(
            """
            INSERT INTO city_housing (crawled_date, house_address, price, area, num_bathroom, num_bedroom, num_days_posted, zillow_url, house_lat, house_lng, city_id)
            VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (record[0], record[1], record[2], record[3], record[4], record[5], record[6], record[7], record[8], record[9], city_idx))
        logging.critical('========= DB sync is done for city: {} ========='.format(city_name))
    db.commit()



@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

@click.command('update-db-monthly')
@click.argument('month')
def update_db_monthly_command(month):
    update_db_monthly(month)
    click.echo('Updated the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(update_db_monthly_command)

