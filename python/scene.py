from __future__ import print_function, division
from glob import glob
from random import random
from numpy import array
from geojson import load
from shapely.geometry import Polygon
import numpy as np
import os


def load_sorted_polygons(test_geojson_path, truth_geojson_path):

    # Define internal functions
    polygonize = lambda feature: Polygon(feature['geometry']['coordinates'][0])

    # Convert geojson files of features/geometries to arrays of polygons
    test_features = load(open(test_geojson_path), encoding='latin-1')
    truth_features = load(open(truth_geojson_path), encoding='latin-1')
    test_polys = [polygonize(f) for f in test_features['features']]
    truth_polys = [polygonize(f) for f in truth_features['features']]

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
    precision = true_pos_count/(true_pos_count+false_pos_count)
    recall = true_pos_count/(true_pos_count+false_neg_count)
    return precision, recall


if __name__ == "__main__":
    precisions = []
    recalls = []
    # DG sample submissions
    for image_id in range(1,6):
        truth_fp = ''.join(['Rio/rio_test_aoi',str(image_id),'.geojson'])
        test_fp = ''.join(['Rio_Submission_Testing/Rio_sample_challenge_submission',str(image_id),'.geojson'])
        print('truth_fp=%s' % truth_fp)
        print('test_fp=%s' % test_fp)
        test_polys, truth_polys = load_sorted_polygons(test_fp, truth_fp)
        precision, recall = score(test_polys, truth_polys)
        print('Score Precision = ', precision)
        print('Score Recall = ', recall)
        precisions.append(precision)
        recalls.append(recall)

    # CosmiQ sample submissions 1
    path = 'Rio_Hand_Truth_AOI1/*.geojson'
    for test_fp in glob(path):
        truth_fp = 'Rio/rio_test_aoi1.geojson'
        print('truth_fp=%s' % truth_fp)
        print('test_fp=%s' % test_fp)
        test_polys, truth_polys = load_sorted_polygons(test_fp, truth_fp)
        precision, recall = score(test_polys, truth_polys)
        print('Score Precision = ', precision)
        print('Score Recall = ', recall)
        precisions.append(precision)
        recalls.append(recall)

    # CosmiQ sample submissions 2
    path = 'Rio_Submission_Testing_CQWUnit/rio_test_aoi2*'
    for test_fp in glob(path):
        truth_fp = 'Rio/rio_test_aoi2.geojson'
        print('truth_fp=%s' % truth_fp)
        print('test_fp=%s' % test_fp)
        test_polys, truth_polys = load_sorted_polygons(test_fp, truth_fp)
        precision, recall = score(test_polys, truth_polys)
        print('Score Precision = ', precision)
        print('Score Recall = ', recall)
        precisions.append(precision)
        recalls.append(recall)

    precision_avg = sum(precisions)/len(precisions)
    recall_avg = sum(precisions)/len(precisions)
    F1score  = precision_avg*recall_avg/(precision_avg+recall_avg)
    print('Average precision: ', precision_avg)
    print('Average recall: ', recall_avg)
    print('F1 Score: ', F1score)
