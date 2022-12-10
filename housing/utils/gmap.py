import json
import requests
import pandas as pd


def fetch_gmap_data(nearby_type, coords, res, API_token, city_name, distance=5000,  maximun_page=5):
    '''
    fetch data from gmap about princeton nearby facilities
    nearby_type = schools,shopping_mall
    response may overlap, so the return type is dictionary with name as key
    '''
    
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={}%2C{}&radius={}&type={}&key={}".format(
    coords[0],coords[1], distance, nearby_type, API_token)
    response = requests.request("GET", url, headers={}, data={})
    next_page = json.loads(response.text).get('next_page_token', None)
    rsp_lst = json.loads(response.text).get("results")
    for dic in rsp_lst:
        res[dic['name']] = (nearby_type, dic['geometry']['location']['lat'], dic['geometry']['location']['lng'], dic.get('rating', 0.0), city_name)

    page = 1
    while page < maximun_page:
        page += 1
        if next_page is None:
            break
        else:
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={}%2C{}&radius={}&type={}&key={}&next_page_token={}".format(
    coords[0], coords[1], distance, nearby_type, API_token, next_page)
            response = requests.request("GET", url, headers={}, data={})
            next_page = json.loads(response.text).get('next_page_token', None)
            response_lst = json.loads(response.text)['results']
            for dic in response_lst:
                res[dic['name']] = (nearby_type, dic['geometry']['location']['lat'], dic['geometry']['location']['lng'], dic.get('rating', 0.0), city_name)
    return res


if __name__ == "__main__":
    princeton_coordinates = (40.3573, -74.6672)
    ww_coordinates = (40.2983, -74.6186)
    lawrence_coordinates = (40.2778, -74.7294)
    gmap_token = open('gmap.txt').read()
    res = dict()
    res = fetch_gmap_data('school', princeton_coordinates, res, gmap_token)
    res = fetch_gmap_data('school', ww_coordinates, res, gmap_token)
    res = fetch_gmap_data('school', lawrence_coordinates, res, gmap_token)
    res = fetch_gmap_data('shopping_mall', princeton_coordinates, res, gmap_token)
    res = fetch_gmap_data('shopping_mall', ww_coordinates, res, gmap_token)
    res = fetch_gmap_data('supermarket', lawrence_coordinates, res, gmap_token)
    res = fetch_gmap_data('supermarket', princeton_coordinates, res, gmap_token)
    res = fetch_gmap_data('supermarket', ww_coordinates, res, gmap_token)
    res = fetch_gmap_data('supermarket', lawrence_coordinates, res, gmap_token)
    res = fetch_gmap_data('train_station', princeton_coordinates, res, gmap_token)
    res = fetch_gmap_data('train_station', ww_coordinates, res, gmap_token)
    res = fetch_gmap_data('train_station', lawrence_coordinates, res, gmap_token)
    res = fetch_gmap_data('hospital', princeton_coordinates, res, gmap_token)
    res = fetch_gmap_data('hospital', ww_coordinates, res, gmap_token)
    res = fetch_gmap_data('hospital', lawrence_coordinates, res, gmap_token)
    
    res_lst = []
    for k,v in res.items():
        res_lst.append([k,v[0], v[1], v[2], v[3]])

    df = pd.DataFrame(res_lst, columns=['Name', 'Lat', 'Lng', 'Rating', 'Type'])
    df.to_csv('princeton_layout.csv')
    

