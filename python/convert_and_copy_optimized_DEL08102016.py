# -*- coding: latin-1 -*-


import sys
import os
import csv
import numpy as np
import ogr
import osr
import gdal
from shutil import copyfile
from geojson import load
from shapely.geometry import box, Polygon


def latLonToPixel(lat, lon, inputRaster='', targetSR='', geomTransform=''):
    sourceSR = osr.SpatialReference()
    sourceSR.ImportFromEPSG(4326)

    geom = ogr.Geometry(ogr.wkbPoint)
    geom.AddPoint(lon, lat)

    if targetSR == '':
        srcRaster = gdal.Open(inputRaster)
        targetSR = osr.SpatialReference()
        targetSR.ImportFromWkt(srcRaster.GetProjectionRef())
    coordTrans = osr.CoordinateTransformation(sourceSR,targetSR)
    if geomTransform == '':
        srcRaster = gdal.Open(inputRaster)
        transform = srcRaster.GetGeoTransform()
    else:
        transform = geomTransform

    xOrigin = transform[0]
    # print xOrigin
    yOrigin = transform[3]
    # print yOrigin
    pixelWidth = transform[1]
    # print pixelWidth
    pixelHeight = transform[5]
    # print pixelHeight
    geom.Transform(coordTrans)
    # print geom.GetPoint()
    xPix = (geom.GetPoint()[0]-xOrigin)/pixelWidth
    yPix = (geom.GetPoint()[1]-yOrigin)/pixelHeight

    return (xPix, yPix)

# The following method translates given latitude/longitude pairs into pixel locations on a given GEOTIF
# INPUTS: geotifAddr - The file location of the GEOTIF
#      latLonPairs - The decimal lat/lon pairings to be translated in the form [[lat1,lon1],[lat2,lon2]]
# OUTPUT: The pixel translation of the lat/lon pairings in the form [[x1,y1],[x2,y2]]
# NOTE:   This method does not take into account pixel size and assumes a high enough
#     image resolution for pixel size to be insignificant
def latLonToPixel2(geotifAddr, latLonPairs):
    # Load the image dataset
    ds = gdal.Open(geotifAddr)
    # Get a geo-transform of the dataset
    gt = ds.GetGeoTransform()
    # Create a spatial reference object for the dataset
    srs = osr.SpatialReference()
    srs.ImportFromWkt(ds.GetProjection())
    # Set up the coordinate transformation object
    srsLatLong = srs.CloneGeogCS()
    ct = osr.CoordinateTransformation(srsLatLong,srs)
    # Go through all the point pairs and translate them to latitude/longitude pairings
    pixelPairs = []
    for point in latLonPairs:
        # Change the point locations into the GeoTransform space
        (point[1],point[0],holder) = ct.TransformPoint(point[1],point[0])
        # Translate the x and y coordinates into pixel values
        x = (point[1]-gt[0])/gt[1]
        y = (point[0]-gt[3])/gt[5]
        # Add the point to our return array
        pixelPairs.append([int(x),int(y)])
    return pixelPairs

def pixelToLatLon(xPix, yPix, inputRaster, targetSR=''):
    if targetSR == '':
        targetSR = osr.SpatialReference()
        targetSR.ImportFromEPSG(4326)

    geom = ogr.Geometry(ogr.wkbPoint)
    srcRaster = gdal.Open(inputRaster)
    sourceSR = osr.SpatialReference()
    sourceSR.ImportFromWkt(srcRaster.GetProjectionRef())
    coordTrans = osr.CoordinateTransformation(sourceSR,targetSR)

    transform = srcRaster.GetGeoTransform()
    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = transform[5]

    xCoord = (xPix*pixelWidth)+xOrigin
    yCoord = (yPix*pixelHeight)+yOrigin
    geom.AddPoint(xCoord, yCoord)
    geom.Transform(coordTrans)
    return (geom.GetX(), geom.GetY())

# The following method translates given pixel locations into latitude/longitude locations on a given GEOTIF
# INPUTS: geotifAddr - The file location of the GEOTIF
#      pixelPairs - The pixel pairings to be translated in the form [[x1,y1],[x2,y2]]
# OUTPUT: The lat/lon translation of the pixel pairings in the form [[lat1,lon1],[lat2,lon2]]
# NOTE:   This method does not take into account pixel size and assumes a high enough
#     image resolution for pixel size to be insignificant
def pixelToLatLon2(geotifAddr,pixelPairs):
    # Load the image dataset
    ds = gdal.Open(geotifAddr)
    # Get a geo-transform of the dataset
    gt = ds.GetGeoTransform()
    # Create a spatial reference object for the dataset
    srs = osr.SpatialReference()
    srs.ImportFromWkt(ds.GetProjection())
    # Set up the coordinate transformation object
    srsLatLong = srs.CloneGeogCS()
    ct = osr.CoordinateTransformation(srs,srsLatLong)
    # Go through all the point pairs and translate them to pixel pairings
    latLonPairs = []
    for point in pixelPairs:
        # Translate the pixel pairs into untranslated points
        ulon = point[0]*gt[1]+gt[0]
        ulat = point[1]*gt[5]+gt[3]
        # Transform the points to the space
        (lon,lat,holder) = ct.TransformPoint(ulon,ulat)
        # Add the point to our return array
        latLonPairs.append([lat,lon])

    return latLonPairs

def geoPolygonToPixelPolygonWKT(geom, inputRaster, targetSR, geomTransform):
    polygonPixBufferList = []
    polygonPixBufferWKTList = []
    if geom.GetGeometryName()=='POLYGON':
        polygonPix = ogr.Geometry(ogr.wkbPolygon)
        for ring in geom:
            # GetPoint returns a tuple not a Geometry
            ringPix = ogr.Geometry(ogr.wkbLinearRing)

            for pIdx in xrange(ring.GetPointCount()):
                    lon, lat, z = ring.GetPoint(pIdx)
                    xPix, yPix = latLonToPixel(lat, lon, inputRaster, targetSR, geomTransform)
                    ringPix.AddPoint(xPix, yPix)

            polygonPix.AddGeometry(ringPix)
            polygonPixBuffer  = polygonPix.Buffer(0.0)
            polygonPixBufferList.append(polygonPixBuffer)
    elif geom.GetGeometryName() == 'MULTIPOLYGON':


        for poly in geom:
            polygonPix = ogr.Geometry(ogr.wkbPolygon)
            for ring in geom:
                # GetPoint returns a tuple not a Geometry
                ringPix = ogr.Geometry(ogr.wkbLinearRing)

                for pIdx in xrange(ring.GetPointCount()):
                    lon, lat, z = ring.GetPoint(pIdx)
                    xPix, yPix = latLonToPixel(lat, lon, inputRaster, targetSR, geomTransform)
                    ringPix.AddPoint(xPix, yPix)

                polygonPix.AddGeometry(ringPix)
                polygonPixBuffer = polygonPix.Buffer(0.0)
                polygonPixBufferList.append(polygonPixBuffer)


    for polygonTest in polygonPixBufferList:
        if polygonTest.GetGeometryName() == 'POLYGON':
            polygonPixBufferWKTList.append(polygonTest.ExportToWkt())
        elif polygonTest.GetGeometryName() == 'MULTIPOLYGON':
            for polygonTest2 in polygonTest:
                polygonPixBufferWKTList.append(polygonTest2.ExportToWkt())





    return polygonPixBufferWKTList











if __name__ == "__main__":

    csvFileTotalName_3Band = '../data/all_polygons_solution_3Band.csv'

    csvFileTrainName_3Band = '../data/train_polygons_solution_3Band.csv'
    csvFilePublicName_3Band = '../data/public_polygons_solution_3Band.csv'
    csvFilePrivateName_3Band = '../data/private_polygons_solution_3Band.csv'

    csvFileTotalName_8Band = '../data/all_polygons_solution_8Band.csv'
    csvFileTrainName_8Band = '../data/train_polygons_solution_8Band.csv'
    csvFilePublicName_8Band = '../data/public_polygons_solution_8Band.csv'
    csvFilePrivateName_8Band = '../data/private_polygons_solution_8Band.csv'

    csvFileImageKeyIndexName = '../data/imageKeyIndex.csv'
    aoiFile = '../data/chipNames_inAOI.txt'
    imageFileList = []
    with open(aoiFile, 'rb') as csvfile:
        fileReader = csv.reader(csvfile, delimiter=' ', quotechar='|')
        for row in fileReader:
            imageFileList.append(row[0])


    with open(csvFileTotalName_3Band, 'wb') as csvfileTotal, \
            open(csvFileTotalName_8Band, 'wb') as csvfileTotal_8Band, \
            open(csvFileImageKeyIndexName, 'wb') as csvfileImageKey:


        # instantiate writers
        writerTotal         = csv.writer(csvfileTotal, delimiter=',',lineterminator='\n')
        writerTotal_8Band   = csv.writer(csvfileTotal_8Band, delimiter=',',lineterminator='\n')
        writerImageKey      = csv.writer(csvfileImageKey, delimiter=',', lineterminator='\n')

        writerTotal.writerow(['ImageId','BuildingId', 'BuildingId', 'PolygonWKT', 'Usage'])
        writerTotal_8Band.writerow(['ImageId','BuildingId', 'BuildingId', 'PolygonWKT', 'Usage'])
        writerImageKey.writerow(['ImageID', 'Usage', 'geoJsonSrc', '3BandSrc', '8BandSrc'])


        max_buildings = 0
        num_imgs_no_buildings = 0

        #imagefiles = sorted(os.listdir('image_chips_filtered/3band'))
        #geojsonfiles = sorted(os.listdir('image_chips_filtered/geojsons/'))

        np.random.seed(1234)
        rand_list = np.random.random_sample((len(imageFileList),))

        errors = []
        for image_id in range(1,len(imageFileList)+1):
            
            rand_number = rand_list[image_id-1]
            if rand_number < 0.18 :
                usage = 'Public'
            elif rand_number < 0.6:
                usage = 'Private'
            else:
                usage = 'Train'
            writerImageKey.writerow([image_id, usage, imageFileList[image_id-1].replace('.tif', '.geojson'),
                                     imageFileList[image_id-1], imageFileList[image_id-1]])


            truthJsonFp = ''.join(['../data/chipsBuildings/',imageFileList[image_id-1].replace('.tif', '.geojson')])
            inputRaster = ''.join(['../data/image_chips/3band/',imageFileList[image_id-1]])
            eightbandRaster = ''.join(['../data/image_chips/8band/',imageFileList[image_id-1]])

            print('reading truthJsonFp=%s' % truthJsonFp)
            # load GeoJSON file

            dataSource = ogr.Open(truthJsonFp, 0)
            layer = dataSource.GetLayer()
            print(layer.GetFeatureCount())
            building_id = 0
            # check if geoJsonisEmpty
            if layer.GetFeatureCount()>0:
                srcRaster = gdal.Open(inputRaster)
                targetSR = osr.SpatialReference()
                targetSR.ImportFromWkt(srcRaster.GetProjectionRef())
                geomTransform = srcRaster.GetGeoTransform()

                srcRaster_8band = gdal.Open(eightbandRaster)
                targetSR_8band = osr.SpatialReference()
                targetSR_8band.ImportFromWkt(srcRaster_8band.GetProjectionRef())
                geomTransform_8band = srcRaster_8band.GetGeoTransform()


                for feature in layer:
                    building_id = building_id+1
                    geom = feature.GetGeometryRef()

                    ## Calculate 3 band
                    polygonWKTList = geoPolygonToPixelPolygonWKT(geom, inputRaster, targetSR, geomTransform)

                    for polygonWKT in polygonWKTList:
                        outputList = [image_id, building_id, polygonWKT, usage]
                        writerTotal.writerow(outputList)
                    ## Calculate 3 band
                    polygonWKTList_8Band = geoPolygonToPixelPolygonWKT(geom, eightbandRaster, targetSR_8band, geomTransform_8band)

                    for polygonWKT in polygonWKTList_8Band:
                        outputList = [image_id, building_id, polygonWKT, usage]
                        writerTotal_8Band.writerow(outputList)




            else:
                outputList = [image_id, -1, Polygon([(0, 0), (0, 0), (0, 0)]).wkt, usage]
                writerTotal.writerow(outputList)
                writerTotal_8Band.writerow(outputList)







