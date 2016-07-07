from __future__ import print_function, division
from glob import glob
from random import random
from geojson import load
from shapely.geometry import Polygon
from skimage import draw
from rtree import index
import numpy as np


def remove_dupes(test_polys):
    unique = []
    for test_poly in test_polys:
        if test_poly not in unique:
            unique.append(test_poly)
        else:
            print('Removed duplicate.')
    return unique


def score_rtree(test_geojson_path, truth_geojson_path):

    # Define internal functions
    IoU = lambda p1, p2: p1.intersection(p2).area/p1.union(p2).area
    polygonize = lambda feature: Polygon(feature['geometry']['coordinates'][0])

    # Convert geojson files of features/geometries to arrays of polygons
    test_features = load(open(test_geojson_path), encoding='latin-1')
    truth_features = load(open(truth_geojson_path), encoding='latin-1')
    test_polys = remove_dupes([polygonize(f) for f in test_features['features']])
    test_polys = [(i, p.bounds, p) for i, p in enumerate(test_polys)]
    truth_polys = [polygonize(f) for f in truth_features['features']]

    # Use a geospatial index to compare the polygons
    idx = index.Index(interleaved=False)
    for i, bounds, test_poly in test_polys:
        idx.insert(i, bounds, obj=test_poly)

    threshold = 0.5
    true_pos_count = 0
    false_pos_count = 0
    B = len(truth_polys)
    for truth_poly in truth_polys:
        maxIoU = 0
        for test_poly in idx.intersection(truth_poly.bounds, objects=True):
            iou = IoU(test_poly.object, truth_poly)
            if iou >= threshold:
                maxIoU = iou
                print('Max: ', iou)
            elif iou != 0:
                print('False positive: ', iou)
                false_pos_count += 1
        if maxIoU != 0:
            true_pos_count += 1
    false_neg_count = B - true_pos_count
    print('rtree: True pos count: ', true_pos_count)
    print('rtree: False pos count: ', false_pos_count)
    print('rtree: False neg count: ', false_neg_count)
    precision = true_pos_count/(true_pos_count+false_pos_count)
    recall = true_pos_count/(true_pos_count+false_neg_count)
    return (precision, recall)


def score_max(test_geojson_path, truth_geojson_path):

    # Define internal functions
    IoU = lambda p1, p2: p1.intersection(p2).area/p1.union(p2).area
    polygonize = lambda feature: Polygon(feature['geometry']['coordinates'][0])

    # Convert geojson files of features/geometries to arrays of polygons
    test_features = load(open(test_geojson_path), encoding='latin-1')
    truth_features = load(open(truth_geojson_path), encoding='latin-1')
    test_polys = [polygonize(f) for f in test_features['features']]
    truth_polys = [polygonize(f) for f in truth_features['features']]

    # Generate artifical confidences and sort
    test_polys =  [[random(), test_poly] for test_poly in test_polys]
    test_polys = sorted(test_polys, key=lambda l:l[0], reverse=True)

    # Compare polygons using threshold/argmax/IoU
    threshold = 0.5
    true_pos_count = 0
    false_pos_count = 0
    B = len(truth_polys)
    for test_poly in test_polys:
        IoUs = map(lambda x:IoU(test_poly[1],x),truth_polys)
        maxIoU = max(IoUs)
        if maxIoU >= threshold:
            true_pos_count += 1
            del truth_polys[np.argmax(IoUs)]
        else:
            false_pos_count += 1
    false_neg_count = B - true_pos_count
    print('Max: True pos count: ', true_pos_count)
    print('Max: False pos count: ', false_pos_count)
    print('Max: False neg count: ', false_neg_count)
    precision = true_pos_count/(true_pos_count+false_pos_count)
    recall = true_pos_count/(true_pos_count+false_neg_count)
    return (precision, recall)


if __name__ == "__main__":
    # DG sample submissions
    for image_id in range(1,6):
        truth_fp = ''.join(['Rio/rio_test_aoi',str(image_id),'.geojson'])
        test_fp = ''.join(['Rio_Submission_Testing/Rio_sample_challenge_submission',str(image_id),'.geojson'])
        print('truth_fp=%s' % truth_fp)
        print('test_fp=%s' % test_fp)
        precision, recall = score_max(test_fp, truth_fp)
        print('Max: Precision = ', precision)
        print('Max: Recall = ', recall)
        precision, recall = score_rtree(test_fp, truth_fp)
        print('Rtree: Precision = ', precision)
        print('Rtree: Recall = ', recall)

    # CosmiQ sample submissions
    path = 'Rio_Hand_Truth_AOI1/*.geojson'
    for test_fp in glob(path):
        truth_fp = 'Rio/rio_test_aoi1.geojson'
        print('truth_fp=%s' % truth_fp)
        print('test_fp=%s' % test_fp)
        precision, recall = score_max(test_fp, truth_fp)
        print('Max: Precision = ', precision)
        print('Max: Recall = ', recall)
