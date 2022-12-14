import pandas as pd
import numpy as np
import glob
import logging

def get_census_data(file_path):
    csv_files = glob.glob(file_path + '/*.csv')
    dfs = []
    for file in csv_files:
        df = pd.read_csv(file).T
        df.rename(columns={i:elem for i,elem in enumerate(df.iloc[0].to_numpy())}, inplace=True)
        columns_shown = [
            "Population Estimates, July 1 2021, (V2021)",
            "Foreign born persons, percent, 2016-2020",
            "Owner-occupied housing unit rate, 2016-2020",
            "Median value of owner-occupied housing units, 2016-2020",
            "Median selected monthly owner costs -with a mortgage, 2016-2020",
            "Median selected monthly owner costs -without a mortgage, 2016-2020",
            "Bachelor's degree or higher, percent of persons age 25 years+, 2016-2020",
            "Median household income (in 2020 dollars), 2016-2020"
        ]
        df = df[columns_shown]
        dfs.append(df)
    
    dfs = pd.concat(dfs).T[["Princeton, New Jersey",  "New York city, New York", "Seattle city, Washington", "United States",]]
    return dfs


def query_add_kwargs(query, kwargs):
    bedroom_from = kwargs.get('bedroom_from')
    bedroom_to = kwargs.get('bedroom_to')
    bathroom_from = kwargs.get('bathroom_from')
    bathroom_to = kwargs.get('bathroom_to')
    aggregated_type = kwargs.get('aggregated_type')
    max_posted_days = kwargs.get('max_posted_days')
    if bedroom_from:
        query += " and num_bedroom >= {}".format(bedroom_from)
    if bedroom_to:
        query += " and num_bedroom <= {}".format(bedroom_to)
    if bathroom_from:
        query += " and num_bathroom >= {}".format(bathroom_from)
    if bathroom_to:
        query += " and num_bathroom <= {}".format(bathroom_to)
    if max_posted_days:
        query += " and num_days_posted <= {}".format(max_posted_days)
    if aggregated_type and aggregated_type == "unitPrice":
        query = query.replace("select price,", "select (price/area) as price,")
        query += " and area > 0"
    return query


def get_layout_from_db(cursor, landmark_type, cities):
    if len(cities) not in {1, 3}:
        logging.exception('Numbers of cities passed is not correct')
        return
    if len(cities) == 1:
        query = cursor.execute(
        """
        select landmark_lng,landmark_lat,landmark_name from city_layout join city on city_layout.city_id = city.id
        where landmark_type = ? and city.city_name = ?
        """, (landmark_type, cities[0])).fetchall()

    else:
        query = cursor.execute(
        """
        select landmark_lng,landmark_lat,landmark_name from city_layout join city on city_layout.city_id = city.id
        where landmark_type = ? and city.city_name in (?, ?, ?)
        """, (landmark_type, cities[0], cities[1], cities[2])).fetchall()

    lons = []
    lats = []
    names = []
    for item in query:
        lons.append(item['landmark_lng'])
        lats.append(item['landmark_lat'])
        names.append(item['landmark_name'])
    return lons, lats, names


def get_housing_from_db(cursor, cities, month, kwargs={}):
    if len(cities) not in {1, 3}:
        logging.exception('Numbers of cities passed is not correct')
        return
    
    if len(cities) == 1:
        base_query = """
                    select price,zillow_url,house_lat,house_lng from city_housing join city on city_housing.city_id = city.id
                    where city.city_name = ? and crawled_date = ?
                    """
        base_query = query_add_kwargs(base_query, kwargs)
        query = cursor.execute(base_query, (cities[0], month, )).fetchall()

    else:
        base_query = """
                    select price,zillow_url,house_lat,house_lng from city_housing join city on city_housing.city_id = city.id
                    where city.city_name in (?, ?, ?) and crawled_date = ? 
                    """
        base_query = query_add_kwargs(base_query, kwargs)
        query = cursor.execute(base_query, (cities[0], cities[1], cities[2], month, )).fetchall()
    
    urls = []
    lons = []
    lats = []
    price = []
    for item in query:
        urls.append(item['zillow_url'])
        lons.append(item['house_lng'])
        lats.append(item['house_lat'])
        price.append(item['price'])
    print('line76 price list length',len(price))
    return urls, lons, lats, price


'''
retrieve data from db
use pandas to calculate min, max, medium
return summary stats after grouping and price list
'''
def analysis_query(cursor, cities, month, kwargs={}):
    if len(cities) not in {1, 3}:
        logging.exception('Numbers of cities passed is not correct')
        return
    
    if len(cities) == 1:
        base_query = """
                    select price,num_bathroom, num_bedroom from city_housing join city on city_housing.city_id = city.id
                    where city.city_name = ? and crawled_date = ?
                    """
        base_query = query_add_kwargs(base_query, kwargs)
        query = cursor.execute(base_query, (cities[0], month, )).fetchall()
    else:
        base_query = """
                    select price,num_bathroom, num_bedroom from city_housing join city on city_housing.city_id = city.id
                    where city.city_name in (?,?,?) and crawled_date = ?
                    """
        base_query = query_add_kwargs(base_query, kwargs)
        query = cursor.execute(base_query, (cities[0], cities[1], cities[2], month)).fetchall()

    df_data = {'Bathrooms': [], 'Bedrooms':[], 'price':[]}
    for record in query:
        df_data['Bathrooms'].append(record['num_bathroom'])
        df_data['Bedrooms'].append(record['num_bedroom'])
        df_data['price'].append(record['price'])

    summarize = pd.DataFrame(df_data).dropna()
    summarize = summarize[(summarize.Bathrooms > 0) & (summarize.Bedrooms > 0)]
    summarize.Bathrooms = summarize.Bathrooms.astype(int)
    summarize.Bedrooms = summarize.Bedrooms.astype(int)
    summarize = summarize.groupby(['Bedrooms', 'Bathrooms'])['price'].agg(['min', 'max', 'median'])
    summarize['min'] = summarize['min'].apply(lambda x: "${:.1f}k".format((x/1000)))
    summarize['max'] = summarize['max'].apply(lambda x: "${:.1f}k".format((x/1000)))
    summarize['median'] = summarize['median'].apply(lambda x: "${:.1f}k".format((x/1000)))

    return summarize


'''
return monthly price data from DB
If set remove_outliers to true,
then use IQR (Inter Quartile Range) to remove outliers
'''
def get_monthly_price(cursor, cities, end_month, kwargs={}, remove_outliers=True):
    if len(cities) not in {1, 3}:
        logging.exception('Numbers of cities passed is not correct')
        return
    
    if len(cities) == 1:
        base_query = """
                        select price,crawled_date from city_housing join city on city_housing.city_id = city.id
                        where city.city_name = ? and crawled_date <= ?
                    """
        base_query = query_add_kwargs(base_query, kwargs)
        query = cursor.execute(base_query, (cities[0], end_month, )).fetchall()
    else:
        base_query = """
                        select price,crawled_date from city_housing join city on city_housing.city_id = city.id
                        where city.city_name in (?, ?, ?) and crawled_date <= ?
                     """
        base_query = query_add_kwargs(base_query, kwargs)
        query = cursor.execute(base_query, (cities[0], cities[1], cities[2], end_month,)).fetchall()
    
    df_data = {'month': [], 'price':[]}
    for record in query:
        df_data['month'].append(record['crawled_date'])
        df_data['price'].append(record['price'])
    res = pd.DataFrame(df_data).dropna()

    if remove_outliers:
        Q1 = np.percentile(res['price'], 25,
                   interpolation = 'midpoint')
 
        Q3 = np.percentile(res['price'], 75,
                    interpolation = 'midpoint')
        IQR = Q3 - Q1
        upper = np.where(res['price'] >= (Q3+1.5*IQR))
        lower = np.where(res['price'] <= (Q1-1.5*IQR))
        res.drop(upper[0], inplace = True)
        res.drop(lower[0], inplace = True)

    return res


def digit_to_dollar_string(lst):
    res = []
    for i in range(len(lst)):
        res.append("${:,}".format(int(lst[i])))
    return res