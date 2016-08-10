from __future__ import print_function, division
from glob import glob
from random import random
import os
from numpy import array
from geojson import load
from shapely.geometry import Polygon
from shapely import wkt
import pandas as pd
import time
import cPickle as pickle
import math
import numpy as np
from multiprocessing import Pool, Process
import multiprocessing
import csv
import itertools
def polygonize(csv_path):
    polys = []
    polys_df = pd.read_csv(csv_path)
    image_ids = set(polys_df['ImageId'].tolist())
    for image_id in image_ids:
        img_df = polys_df.loc[polys_df['ImageId'] == image_id]
        building_ids = set(img_df['BuildingId'].tolist())
        for building_id in building_ids:
            if building_id != 0:
                building_df = img_df.loc[img_df['BuildingId'] == building_id]
                poly = zip(building_df['X'].astype(int), building_df['Y'].astype(int))
                polys.append({'ImageId': image_id, 'BuildingId': building_id, 'poly': Polygon(poly)})
    return polys

def get_image_ids(csv_path):
    polys_df = pd.read_csv(csv_path)
    return set(polys_df['ImageId'].tolist())

def load_sorted_polygons(test_csv_path, truth_csv_path):
    # Assumes -
    # 1. Polygons are presorted for descending confindence.
    # 2. Chips with no buildings assign zero for the BuildingId
    return importFromGeoJson(test_csv_path), polygonize(truth_csv_path)

def IoU2(test_poly, truth_polys):
    iouList = []
    for idx, truth_poly in enumerate(truth_polys):
        #truth_poly=truth_poly.buffer(0.0)
        #test_poly = test_poly.buffer(0.0)
        #print(idx)
        #if idx == 74:
        #    pass
        intersectionResult = test_poly.intersection(truth_poly)
        if intersectionResult.geom_type == 'Polygon' or intersectionResult.geom_type == 'MultiPolygon':
            intersectionArea = intersectionResult.area
        else:
            intersectionArea = 0
        #print(intersectionArea)
        unionArea = test_poly.union(truth_poly).area
        #print(unionArea)

        iouList.append(intersectionArea/unionArea)


    return iouList


def score(test_polys, truth_polys):

    # Define internal functions

    IoU = lambda p1, p2: (p1.intersection(p2).area/p1.union(p2).area)
    argmax = lambda iterable, func: max(iterable, key=func)

    # Find detections using threshold/argmax/IoU for test polygons
    true_pos_count = 0
    false_pos_count = 0
    B = len(truth_polys)
    M = len(test_polys)
    idx = 0
    for test_poly in test_polys:
        #print(idx)
        idx = idx +1
        #if idx == 25:
        #    pass
        IoUs = IoU2(test_poly, truth_polys)
        #IoUs = map(lambda x:IoU(test_poly,x),truth_polys)
        if not IoUs:
            maxIoU = 0
        else:
            maxIoU = max(IoUs)

        threshold = 0.5
        if maxIoU >= threshold:
            true_pos_count += 1
            del truth_polys[np.argmax(IoUs)]
        else:
            false_pos_count += 1
    false_neg_count = B - true_pos_count
    precision = true_pos_count/(true_pos_count+false_pos_count)
    recall = true_pos_count/(true_pos_count+false_neg_count)
    return true_pos_count, false_pos_count, false_neg_count


def addbuffer(polys):
    polysNewList = []
    for poly in polys:
        polyNew=poly
        polyNew['poly'] = poly['poly'].buffer(0.0)
        polysNewList.append(polyNew)

    return polysNewList


from osgeo import ogr
def writeToGeoJson(polysList, geoJsonName):
        driver = ogr.GetDriverByName('geojson')
        if os.path.exists(geoJsonName):
            driver.DeleteDataSource(geoJsonName)
        dataSource = driver.CreateDataSource(geoJsonName)
        layer = dataSource.CreateLayer('buildings', geom_type=ogr.wkbPolygon)
        layer.CreateField(ogr.FieldDefn("ImageId", ogr.OFTInteger))
        layer.CreateField(ogr.FieldDefn("ContainsBuildings", ogr.OFTInteger))
        layer.CreateField(ogr.FieldDefn("BuildingId", ogr.OFTInteger))
        emptyCount = 0

        for poly in polysList:
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetField("ImageId", poly['ImageId'])
            feature.SetField("BuildingId", poly['BuildingId'])

            if poly['poly'].is_empty:
                emptyCount = emptyCount + 1
                print(emptyCount)
                feature.SetField("ContainsBuildings", 0)
            else:
                feature.SetField("ContainsBuildings", 1)
            polygonImport = ogr.CreateGeometryFromWkt(poly['poly'].wkt)
            feature.SetGeometry(polygonImport)
            # Create the feature in the layer (shapefile)
            layer.CreateFeature(feature)
            # Destroy the feature to free resources
            feature.Destroy()

        dataSource.Destroy()

def readWKTCSV(csv_path):

    polys = []
    polys_df = pd.read_csv(csv_path)
    image_ids = set(polys_df['ImageId'].tolist())
    for image_id in image_ids:
        img_df = polys_df.loc[polys_df['ImageId'] == image_id]
        building_ids = set(img_df['BuildingId'].tolist())
        for building_id in building_ids:
            if building_id != 0:
                building_df = img_df.loc[img_df['BuildingId'] == building_id]
                poly = wkt.loads(building_df.iloc[0,2])
                polys.append({'ImageId': image_id, 'BuildingId': building_id, 'poly': poly})
    return polys




def writeToCSV_Polygon(polysList, csvFileName):
    with open(csvFileName, 'wb') as csvFileName:
        fileWriter = csv.writer(csvFileName, delimiter=';')
        fileWriter.writerow(['ImageId', 'BuildingId', 'PolygonWKT'])
        idx = 0
        for poly in polysList:
            print(idx)
            idx = idx + 1
            #if poly['poly'].is_empty:
            fileWriter.writerow([poly['ImageId'], poly['BuildingId'], poly['poly'].wkt])
            #else:
            #    if poly['poly'].geom_type == 'MultiPolygon':
            #        for polyPart in poly['poly']:
            #            xList,yList = polyPart.exterior.coords.xy

            #            for x,y in zip(xList,yList):
            #                fileWriter.writerow([poly['ImageId'], poly['BuildingId'], '{}'.format(int(x)), '{}'.format(int(y))])
            #    else:
            #        xList, yList = poly['poly'].exterior.coords.xy
            #        for x, y in zip(xList, yList):
            #            fileWriter.writerow([poly['ImageId'], poly['BuildingId'], '{}'.format(int(x)), '{}'.format(int(y))])





def doublePolysList(polysList):
    newPolysList = []
    buildingId = 0
    for poly in polysList:
        buildingId = buildingId+1
        poly['buildingId']=buildingId
        newPolysList.append(poly)
        buildingId = buildingId+1
        poly['buildingId']=buildingId
        newPolysList.append(poly)

    return newPolysList


def importFromGeoJson(geoJsonName):

    #driver = ogr.GetDriverByName('geojson')
    dataSource = ogr.Open(geoJsonName, 0)

    layer = dataSource.GetLayer()
    print(layer.GetFeatureCount())

    polys =  []
    image_id = 1
    building_id = 0
    for feature in layer:
        building_id = building_id + 1
        polys.append({'ImageId': feature.GetField('ImageId'), 'BuildingId': feature.GetField('BuildingId'), 'poly': wkt.loads(feature.GetGeometryRef().ExportToWkt())})

    return polys

import math
import numpy as np
def evalFunction2((image_id, (prop_polysIdList, prop_polysPoly), (sol_polysIdsList, sol_polysPoly))):

    #test_polys = []
    #truth_polys = []
    #true_pos_count = 0
    #false_pos_count = 0
    #false_neg_count = 0
    #image_test_polys = [item for item in prop_polys if item["ImageId"] == image_id]
    #for poly in image_test_polys:
    #    test_polys.append(poly['poly'])
    test_polys = prop_polysPoly[np.argwhere(prop_polysIdList == image_id).flatten()]
    truth_polys = sol_polysPoly[np.argwhere(sol_polysIdsList == image_id).flatten()]


    #image_truth_polys = [item for item in sol_polys if item["ImageId"] == image_id]
    if truth_polys == []:
        true_pos_count = 0
        false_pos_count = len(truth_polys)
        false_neg_count = 0
    else:
        true_pos_count, false_pos_count, false_neg_count = score(test_polys, truth_polys.tolist())


    if (true_pos_count > 0) or ((false_neg_count > 0) and (false_pos_count > 0)):

        precision = float(true_pos_count) / (float(true_pos_count) + float(false_pos_count))
        recall = float(true_pos_count) / (float(true_pos_count) + float(false_neg_count))
        F1score = 2.0 * precision * recall / (precision + recall)
    else:
        F1score = 0
    return (F1score, true_pos_count, false_pos_count, false_neg_count)
        # print('F1 Score: ', F1score)
        # print('bad count: ', bad_count)



def evalFunction((image_id, prop_polys, sol_polys)):

    test_polys = []
    truth_polys = []
    true_pos_count = 0
    false_pos_count = 0
    false_neg_count = 0
    image_test_polys = [item for item in prop_polys if item["ImageId"] == image_id]
    for poly in image_test_polys:
        test_polys.append(poly['poly'])

    image_truth_polys = [item for item in sol_polys if item["ImageId"] == image_id]
    if image_truth_polys == []:
        true_pos_count = 0
        false_pos_count = len(image_test_polys)
        false_neg_count = 0
    else:
        for poly in image_truth_polys:
            truth_polys.append(poly['poly'])

        true_pos_count, false_pos_count, false_neg_count = score(test_polys, truth_polys)


    if (true_pos_count > 0) or ((false_neg_count > 0) and (false_pos_count > 0)):

        precision = float(true_pos_count) / (float(true_pos_count) + float(false_pos_count))
        recall = float(true_pos_count) / (float(true_pos_count) + float(false_neg_count))
        F1score = 2.0 * precision * recall / (precision + recall)
    else:
        F1score = 0
    return (F1score, true_pos_count, false_pos_count, false_neg_count)
        # print('F1 Score: ', F1score)
        # print('bad count: ', bad_count)





if __name__ == "__main__":
    true_pos_counts = []
    false_pos_counts = []
    false_neg_counts = []


    #test_fp = '../solution2xSubmission.geojson'
    test_fp  = '../solution_v4Buffer.geojson'
    truth_fp = '../solution_v4Buffer.geojson'


    pickleLocation = 'solution_v4.p'
    t0 = time.time()
    #sol_polys = pickle.load(open(pickleLocation, "rb"))
    sol_polys = importFromGeoJson(truth_fp)

    #prop_polys = importFromGeoJson(test_fp)
    prop_polys = sol_polys
    #prop_polys, sol_polys = load_sorted_polygons(test_fp, truth_fp)
    t1 = time.time()
    total = t1-t0
    print('time of ingest: ', total)

    #t0 = time.time()
    test_image_ids = set([item['ImageId'] for item in prop_polys if item['ImageId']>0])
    prop_polysIdList = np.asarray([item['ImageId'] for item in prop_polys if item["ImageId"] >0])
    prop_polysPoly   = np.asarray([item['poly'] for item in prop_polys if item["ImageId"] >0])
    sol_polysIdsList = np.asarray([item['ImageId'] for item in sol_polys if item["ImageId"] >0])
    sol_polysPoly    = np.asarray([item['poly'] for item in sol_polys if item["ImageId"] >0])

    bad_count = 0
    F1ScoreList=[]
    print('{}'.format(multiprocessing.cpu_count()))
    p = Pool(processes=multiprocessing.cpu_count())
    ResultList=[]
    # timeList = []
    # for image_id in test_image_ids:
    #     t1 = time.time()
    #     ResultList.append(evalFunction2(((image_id),  (prop_polysIdList, prop_polysPoly), (sol_polysIdsList, sol_polysPoly))))
    #     t2 = time.time()
    #     timeList.append(t2-t1)
    #     print("{}s per imageID".format(t2-t1))
    #     print("{}sAvg out of {}".format(np.mean(timeList), len(timeList)))
    ResultList = p.map(evalFunction2, zip(test_image_ids, itertools.repeat((prop_polysIdList, prop_polysPoly), times=len(test_image_ids)),
                                         itertools.repeat((sol_polysIdsList, sol_polysPoly), times=len(test_image_ids))))
    ResultSum = np.sum(ResultList, axis=0)
    True_Pos_Total = ResultSum[1]
    False_Pos_Total = ResultSum[2]
    False_Neg_Total = ResultSum[3]
    print('True_Pos_Total', True_Pos_Total)
    print('False_Pos_Total', False_Pos_Total)
    print('False_Neg_Total', False_Neg_Total)
    precision = float(True_Pos_Total) / (float(True_Pos_Total) + (False_Pos_Total))
    recall = float(True_Pos_Total) / (float(True_Pos_Total)+ (False_Neg_Total))
    F1ScoreTotal = 2.0*precision*recall/(precision+recall)
    print('F1Total', ResultSum[3])



        #p.map(evalFunction, )
        # print('Imaged ID: ', image_id)
        # test_polys = []
        # truth_polys = []
        # image_test_polys = [item for item in prop_polys if item["ImageId"] == image_id]
        # for poly in image_test_polys:
        #     test_polys.append(poly['poly'])
        # image_truth_polys = [item for item in sol_polys if item["ImageId"] == image_id]
        # if image_truth_polys == []:
        #     true_pos_count = 0
        #     false_pos_count = len(image_test_polys)
        #     false_neg_count = 0
        # else:
        #     for poly in image_truth_polys:
        #         truth_polys.append(poly['poly'])
        #     true_pos_count, false_pos_count, false_neg_count = score(test_polys, truth_polys)
        # true_pos_counts.append(true_pos_count)
        # false_pos_counts.append(false_pos_count)
        # false_neg_counts.append(false_neg_count)
        # if (sum(true_pos_counts) > 0 ) and ((sum( false_neg_counts ) > 0 ) and (sum(false_pos_counts) > 0)):
        #     precision = float(sum(true_pos_counts))/float(sum(true_pos_counts)+sum(false_pos_counts))
        #     recall = float(sum(true_pos_counts))/float(sum(true_pos_counts)+sum(false_neg_counts))
        #     F1score  = 2.0*precision*recall/(precision+recall)
        #     F1ScoreList.append(F1score)
        #     #print('F1 Score: ', F1score)
        #     #print('bad count: ', bad_count)
    t2 = time.time()
    total = t2-t0
    print('time of evaluation: {}'.format(t2-t1))
    print('time of evaluation {}s/imageId'.format((t2-t1)/len(ResultList)))
    print('Total Time {}s'.format(total))
    print(ResultList)
    print(np.mean(ResultList))



#    t5 =time.time()

    #readWKTCSV('/Users/dlindenbaum/Documents/CosmiQCode_09282015/BEE-CSharp/wktSubmission.csv')


    #t6 = time.time()
    #print(t6-t5)


    #t5 = time.time()
#    newTest = []
#    for example in test:
#        example['poly'] = wkt.loads(example['PolygonWKT'])



#    t6 = time.time()