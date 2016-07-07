#%% Import Calls
import os
import ogr
import osr
import subprocess
import gdal
import csv
import cv2
import math
import datetime
from pixel import geoUtils
import numpy as np
import random
from guessGenerator import createTranslateMeters



def createBoxFromPoint(xCenter, yCenter, xLength, yLength):

    minX = xCenter - xLength/2
    minY = yCenter - yLength/2
    maxX = xCenter + xLength/2
    maxY = yCenter + yLength/2

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(minX, minY)
    ring.AddPoint(minX, maxY)
    ring.AddPoint(maxX, maxY)
    ring.AddPoint(maxX, minY)
    ring.AddPoint(minX, minY)
    polyEnvelope = ogr.Geometry(ogr.wkbPolygon)
    polyEnvelope.AddGeometry(ring)

    return polyEnvelope


def createIoUTest(dstFileName, xCenter=1000, yCenter=1000, xLength=10, yLength=10, translateRange=np.arange(50)):

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    # Create the output shapefile
    geoJSONdriver = ogr.GetDriverByName("GeoJson")
    if os.path.exists(dstFileName):
        geoJSONdriver.DeleteDataSource(dstFileName)
    outDataSource = geoJSONdriver.CreateDataSource(dstFileName)
    outLayer = outDataSource.CreateLayer(dstFileName, srs, geom_type=ogr.wkbPolygon)
    # Create the feature and set values

    # add Intersection Field
    idField = ogr.FieldDefn("Intersection", ogr.OFTReal)
    outLayer.CreateField(idField)
    # add Union Field
    idField = ogr.FieldDefn("Union", ogr.OFTReal)
    outLayer.CreateField(idField)
    # add Area Field
    idField = ogr.FieldDefn("Area", ogr.OFTReal)
    outLayer.CreateField(idField)
    # add IOU Field
    idField = ogr.FieldDefn("IOU", ogr.OFTReal)
    outLayer.CreateField(idField)
    # add transX Field
    idField = ogr.FieldDefn("transX", ogr.OFTReal)
    outLayer.CreateField(idField)
    # add transY
    idField = ogr.FieldDefn("transY", ogr.OFTReal)
    outLayer.CreateField(idField)

    featureDefn = outLayer.GetLayerDefn()

    # create InitialPolygon
    polyBaseTruth = createBoxFromPoint(xCenter, yCenter, xLength, yLength)
    feature = ogr.Feature(featureDefn)
    feature.SetGeometry(polyBaseTruth)
    calcIntersection = polyBaseTruth.Intersection(polyBaseTruth).GetArea()
    calcUnion        = polyBaseTruth.Union(polyBaseTruth).GetArea()
    calcArea         = polyBaseTruth.GetArea()
    calcIOU          = calcIntersection/calcUnion
    feature.SetField('Intersection', calcIntersection)
    feature.SetField('Union', calcUnion)
    feature.SetField('Area', calcArea)
    feature.SetField('IOU', calcIOU)
    feature.SetField('transX', 0)
    feature.SetField('transY', 0)
    outLayer.CreateFeature(feature)

    for translateDistanceMetersX in translateRange:
        for translateDistanceMetersY in translateRange:
            print translateDistanceMetersX
            print translateDistanceMetersY
            polyGuess = createTranslateMeters(polyBaseTruth, translateDistanceMetersX,
                          translateDistanceMetersY, wgs84Input=False)
            print polyGuess.ExportToJson()
            feature = ogr.Feature(featureDefn)
            feature.SetGeometry(polyGuess)
            calcIntersection = polyBaseTruth.Intersection(polyGuess).GetArea()
            calcUnion = polyBaseTruth.Union(polyGuess).GetArea()
            calcArea = polyGuess.GetArea()
            calcIOU = calcIntersection / calcUnion
            feature.SetField('Intersection', calcIntersection)
            feature.SetField('Union', calcUnion)
            feature.SetField('Area', calcArea)
            feature.SetField('IOU', calcIOU)
            feature.SetField('transX', translateDistanceMetersX)
            feature.SetField('transY', translateDistanceMetersY)

            outLayer.CreateFeature(feature)






    outDataSource.Destroy()




if __name__ == '__main__':
    dstFileName = '/Users/dlindenbaum/Documents/CosmiQCode_09282015/BEE-CSharp/data/Rio_Submission_Testing_CQW/iouTest_50x50.geojson'
    createIoUTest(dstFileName, xCenter=1000, yCenter=1000, xLength=50, yLength=50, translateRange=np.arange(50))


