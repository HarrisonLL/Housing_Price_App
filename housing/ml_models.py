from sklearn.cluster import KMeans
import numpy as np
import statistics

'''
remove null values
takes a list of list [query1_result, query2_result, ...]
returns a list of list with null value removed
'''
def remove_null_values(lst_lst):
    transpose = np.array(lst_lst).T
    filtered = []
    for i in range(len(transpose)):
        is_not_null = True
        for j in range(len(transpose[0])):
            if transpose[i][j] is None:
                is_not_null = False
                break
        if is_not_null:
            filtered.append(transpose[i])
    return np.array(filtered).T.tolist()


'''
takes coords and price, run kmeans (k is selected by rule of thumbs)
returns a dictionary
{   
    lats: [],          # filtered null value
    lngs: [],          # filted null value
    prices: [],        # filtered null value
    urls: [],          # filtered null value
    labels: [],     
    medium_prices: [] 

}
'''
def run_KMeans (lats, lngs, price, urls, max_cluster_size = 10):
    [lats, lngs, price, urls] = remove_null_values([lats, lngs, price, urls])
    coords = np.array([lats, lngs]).T
    best_k = int(np.sqrt(len(price)/2))
    kmeans = KMeans(n_clusters=best_k, max_iter=1000, init ='k-means++').fit(coords, sample_weight=price)
    labels = kmeans.labels_
    label_prices = dict()

    for i in range(best_k):
        group = []
        for j,label in enumerate(labels):
            if label == i:
                group.append(price[j])
        label_prices[i] = statistics.median(group)
    
    print(label_prices)
    
    medium_prices = []
    for label in labels:
        medium_prices.append(label_prices[label])
    
    return {"lats": lats, "lngs": lngs,  "price": price, "urls": urls, "labels": labels,  "medium_prices": medium_prices,}


