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

if __name__ == "__main__":

    with open('all_polygons_solution.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',lineterminator='\n')
        writer.writerow(['ImageId','ContainsBuildings', 'BuildingId', 'X', 'Y','Usage'])
        max_buildings = 0
        num_imgs_no_buildings = 0

        imagefiles = sorted(os.listdir('image_chips_filtered/3band'))
        geojsonfiles = sorted(os.listdir('image_chips_filtered/geojsons/'))

        np.random.seed(1234)
        rand_list = np.random.random_sample((len(imagefiles),))

        errors = []
        #truthJsonFp = '/Users/dlindenbaum/dataStorage/spacenet/testing/clip2_013022223130_mask_-43.6824092745_-22.9569020838.geojson'
        #inputRaster = '/Users/dlindenbaum/dataStorage/spacenet/testing/clip2_013022223130_mask_-43.6824092745_-22.9569020838_other.tif'
        for image_id in range(1,len(imagefiles)+1):
            
            rand_number = rand_list[image_id-1]
            if rand_number < 0.18 :
                usage = 'Public'
            elif rand_number < 0.6:
                usage = 'Private'
            else:
                usage = 'Train'

            truthJsonFp = ''.join(['image_chips_filtered/geojsons/',geojsonfiles[image_id-1]])
            inputRaster = ''.join(['image_chips_filtered/3band/',imagefiles[image_id-1]])
            eightbandRaster = ''.join(['image_chips_filtered/8band/',imagefiles[image_id-1]])

            print('reading truthJsonFp=%s' % truthJsonFp)
            # load GeoJSON file
            f = open(truthJsonFp)
            truthFeatures = load(f,encoding='latin-1')

            # Convert
            xOriginPx, yOriginPx = latLonToPixel(-22.8930035, -43.6125347, inputRaster)

            building_id = 1

            if truthFeatures['features'] != []:
                srcRaster = gdal.Open(inputRaster)
                targetSR = osr.SpatialReference()
                targetSR.ImportFromWkt(srcRaster.GetProjectionRef())
                geomTransform = srcRaster.GetGeoTransform()

                for truthFeature in truthFeatures['features']:
                    try:
                        truthPoly = Polygon(truthFeature['geometry']['coordinates'][0])
                    except:
                        try:
                            truthPoly = Polygon(truthFeature['geometry']['coordinates'][0][0])
                        except:
                            print truthFeature

                    for coord in list(truthPoly.exterior.coords):
                        lat1, lon1 = coord[1], coord[0]
                        # print 'Original lat/long: ', lat1, '/', lon1
                        xPix, yPix = latLonToPixel(coord[1], coord[0], inputRaster, targetSR, geomTransform)
                        # coord_arr.append((int(xPix), int(yPix)))
                        # print 'Pixel x/y: ', xPix, '/', yPix
                        # print 'Transformed Pixel x/y', xPix - xOriginPx, xPix - yOriginPx
                        # print 'Alternative Pixel x/y', latLonToPixel2(inputRaster, [[coord[1], coord[0]]])
                        # coord_arr.append([int(image_id), int(building_id), int(xPix), int(yPix)])
                        writer.writerow([int(image_id), 1, int(building_id), int(xPix), int(yPix), usage])
                        # print 'Pixel x/y: ', xPix, '/', yPix
                        # lat2, lon2 = pixelToLatLon(xPix, yPix, inputRaster)
                
                    building_id += 1
            else:
                writer.writerow([int(image_id), 0, 0, 0, 0, usage])


            print('number of buildings = %d, images processed = %d' % (building_id - 1, image_id))
            if building_id > max_buildings:
                max_buildings = building_id -1
            if (building_id-1) == 0:
                num_imgs_no_buildings += 1

            print('number of buildings = %d, num_imgs_no_buildings = %d' % (building_id - 1, num_imgs_no_buildings))

            # do the copying
            copyfile(truthJsonFp, ''.join(['final_data/geojsons/',str(image_id),'.geojson']))
            copyfile(inputRaster, ''.join(['final_data/3band/',str(image_id),'.tif']))
            copyfile(eightbandRaster, ''.join(['final_data/8band/',str(image_id),'.tif']))


        print('max num buildings = %d' % max_buildings)
        print('number of images with no buildings = %d' % num_imgs_no_buildings)
        print(errors)

            # print latLonToPixel2(inputRaster, [[-22.9557932591, -43.3411151695]])
            # print 'Origin in pixels: ', xOriginPx, yOriginPx
