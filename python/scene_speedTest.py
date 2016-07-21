from __future__ import print_function, division
from glob import glob
from random import random
from numpy import array
from geojson import load
from shapely.geometry import Polygon
import numpy as np
import os
import time

def polygonize(feature):


    if feature:

        if feature['geometry']:

            if feature['geometry']['coordinates']:

                if feature['geometry']['coordinates']:

                    test = feature['geometry']['coordinates'][0]

                    if test:
                        if len(test)>3:
                            return Polygon(test)
                        else:
                            return []
                    else:
                        return []
                else:
                    return []

            else:
                return []
        else:
            return []
    else:
        return []

    
def load_sorted_polygons(test_geojson_path, truth_geojson_path):

    # Define internal functions
    #polygonize = lambda feature: Polygon(feature['geometry']['coordinates'][0])

    # Convert geojson files of features/geometries to arrays of polygons
    test_features = load(open(test_geojson_path), encoding='latin-1')
    truth_features = load(open(truth_geojson_path), encoding='latin-1')
    test_polys = []
    for f in test_features['features']:
        test = polygonize(f)
        if test:
            test_polys.append(test)
    truth_polys=[]
    for f in test_features['features']:
        test = polygonize(f)
        if test:
            truth_polys.append(test)


    #test_polys = [polygonize(f) for f in test_features['features']]
    #truth_polys = [polygonize(f) for f in truth_features['features']]

    # Generate artifical confidences and sort [condidences should be user
    # supplied or presorted]
    test_polys =  [[random(), test_poly] for test_poly in test_polys]
    test_polys = sorted(test_polys, key=lambda l:l[0], reverse=True)

    return test_polys, truth_polys

def score(test_polys, truth_polys):

    # Define internal functions
    IoU = lambda p1, p2: p1.intersection(p2).area/p1.union(p2).area
    argmax = lambda iterable, func: max(iterable, key=func)

    # Find detections using threshold/argmax/IoU for test polygons
    true_pos_count = 0
    false_pos_count = 0
    B = len(truth_polys)
    M = len(test_polys)
    for test_poly in test_polys:
        IoUs = map(lambda x:IoU(test_poly[1],x),truth_polys)
        maxIoU = max(IoUs)
        threshold = 0.5
        if maxIoU >= threshold:
            true_pos_count += 1
            del truth_polys[np.argmax(IoUs)]
        else:
            false_pos_count += 1
    false_neg_count = B - true_pos_count
    print('Num truths: ', B)
    print('Num proposals: ', M)
    print('True pos count: ', true_pos_count)
    print('False pos count: ', false_pos_count)
    print('False neg count: ', false_neg_count)
    if true_pos_count+false_pos_count>0:
        precision = true_pos_count/(true_pos_count+false_pos_count)
    else:
        precision = 0

    if true_pos_count+false_neg_count>0:
        recall = true_pos_count/(true_pos_count+false_neg_count)
    else:
        recall = 0

    return precision, recall, true_pos_count, false_pos_count, false_neg_count


if __name__ == "__main__":

    start = time.time()
    precisions = []
    recalls = []
    true_pos_counts = []
    false_pos_counts = []
    false_neg_counts = []

    geoJsonList = glob('/usr/local/share/spacenet/combinedClipTest/*.geojson')

    for geoJsonFile in geoJsonList:
        truth_fp = geoJsonFile
        test_fp = geoJsonFile
        print('truth_fp=%s' % truth_fp)
        print('test_fp=%s' % test_fp)
        test_polys, truth_polys = load_sorted_polygons(test_fp, truth_fp)
        precision, recall, true_pos_count, false_pos_count, false_neg_count= score(test_polys, truth_polys)
        precisions.append(precision)
        recalls.append(recall)
        true_pos_counts.append(true_pos_count)
        false_pos_counts.append(false_pos_count)
        false_neg_counts.append(false_neg_count)


    precision_avg = sum(precisions)/len(precisions)
    recall_avg = sum(precisions)/len(precisions)
    F1score_avg  = precision_avg*recall_avg/(precision_avg+recall_avg)
    precision_all = sum(true_pos_counts)/(sum(true_pos_counts)+sum(false_pos_counts))
    recall_all = sum(true_pos_counts)/(sum(true_pos_counts)+sum(false_neg_counts))
    F1score_all  = precision_all*recall_all/(precision_all+recall_all)
    print('Average precision: ', precision_avg)
    print('Average recall: ', recall_avg)
    print('Average F1 Score: ', F1score_avg)
    print('All precision: ', precision_all)
    print('All recall: ', recall_all)
    print('All F1 Score: ', F1score_all)

    stop = time.time()

    print('Total Time to Process = {}'.format(stop-start))
    print('Time per a guess  = {}'.format((stop-start)/len(geoJsonList)))
