from __future__ import print_function, division
from glob import glob
from numpy import array
from geojson import load
from shapely.geometry import Polygon


def average_precision(truth_fp, test_fp):
    f = open(truth_fp)
    truth_features = load(f, encoding='latin-1')
    f = open(test_fp)
    test_features = load(f, encoding='latin-1')
    pos_det = 0
    for truth_feature in truth_features['features']:
        truth_poly = Polygon(truth_feature['geometry']['coordinates'][0])
        for test_feature in test_features['features']:
            test_poly = Polygon(test_feature['geometry']['coordinates'][0])
            if test_poly.intersects(truth_poly):
                pos_det += 1
    return pos_det/len(test_features['features'])

def average_localization_error(truth_fp, test_fp):
    f = open(truth_fp)
    truth_features = load(f, encoding='latin-1')
    f = open(test_fp)
    test_features = load(f, encoding='latin-1')
    pos_det = 0
    for truth_feature in truth_features['features']:
        truth_poly = Polygon(truth_feature['geometry']['coordinates'][0])
        for test_feature in test_features['features']:
            test_poly = Polygon(test_feature['geometry']['coordinates'][0])
            if 0 < IoU(test_poly, truth_poly) < 0.5:
                pos_det += 1
    return pos_det/len(test_features['features'])

def score(test_geojson_path, truth_geojson_path):

    # Define internal functions
    IoU = lambda p1, p2: p1.intersection(p2).area/p1.union(p2).area
    argmax = lambda iterable, func: max(iterable, key=func)
    polygonize = lambda feature: Polygon(feature['geometry']['coordinates'][0])

    # Convert geojson files of features/geometries to arrays of polygons
    test_features = load(open(test_geojson_path), encoding='latin-1')
    truth_features = load(open(truth_geojson_path), encoding='latin-1')
    test_polys = [polygonize(f) for f in test_features['features']]
    truth_polys = [polygonize(f) for f in truth_features['features']]

    # Find detections using threshold/argmax for test polygons
    detections = []
    false_pos_count = 0
    if len(test_polys) >= len(truth_polys):
        for test_poly in test_polys:
            detect = None
            threshold = 0.5
            for truth_poly in truth_polys:
                iou = IoU(test_poly, truth_poly)
                if iou >= threshold:
                    detect = (test_poly, truth_poly, iou)
                    threshold = iou
                elif iou != 0:
                    false_pos_count += 1
            if detect:
                detections.append(detect)
    else:
        for test_poly in test_polys:
            detect = None
            threshold = 0.5
            for truth_poly in truth_polys:
                iou = IoU(test_poly, truth_poly)
                if iou >= threshold:
                    detections.append((test_poly, truth_poly, iou))
                elif iou != 0:
                    false_pos_count += 1
    false_neg_count = len(truth_polys) - len(detections)
    print('Precision = ', len(detections)/(len(detections)+false_pos_count))
    print('Recall = ', len(detections)/(len(detections)+false_neg_count))

if __name__ == "__main__":
    # DG sample submissions
    for image_id in range(1,6):
        truth_fp = ''.join(['Rio/rio_test_aoi',str(image_id),'.geojson'])
        test_fp = ''.join(['Rio_Submission_Testing/Rio_sample_challenge_submission',str(image_id),'.geojson'])
        print('truth_fp=%s' % truth_fp)
        print('test_fp=%s' % test_fp)
        #print('Average precision: ', average_precision(truth_fp, test_fp))
        #print('Average localization error: ', average_localization_error(truth_fp, test_fp))
        score(test_fp, truth_fp)

    # CosmiQ sample submissions
    path = 'Rio_Hand_Truth_AOI1/*.geojson'
    for test_fp in glob(path):
        truth_fp = 'Rio/rio_test_aoi1.geojson'
        print('truth_fp=%s' % truth_fp)
        print('test_fp=%s' % test_fp)
        #print('Average precision: ', average_precision(truth_fp, test_fp))
        #print('Average localization error: ', average_localization_error(truth_fp, test_fp))
        score(test_fp, truth_fp)
