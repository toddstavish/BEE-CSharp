
from osgeo import gdal
from osgeo import osr
from osgeo import ogr
import numpy as np
import subprocess
import os
import time
import glob
def utm_getZone(longitude):
    return (int(1+(longitude+180.0)/6.0))

def utm_isNorthern(latitude):
    if (latitude < 0.0):
        return 0
    else:
        return 1

def createUTMTransform(polyGeom):
    # pt = polyGeom.Boundary().GetPoint()
    utm_zone = utm_getZone(polyGeom.GetEnvelope()[0])
    is_northern = utm_isNorthern(polyGeom.GetEnvelope()[2])
    utm_cs = osr.SpatialReference()
    utm_cs.SetWellKnownGeogCS('WGS84')
    utm_cs.SetUTM(utm_zone, is_northern);
    wgs84_cs = osr.SpatialReference()
    wgs84_cs.ImportFromEPSG(4326)

    transform_WGS84_To_UTM = osr.CoordinateTransformation(wgs84_cs, utm_cs)
    transform_UTM_To_WGS84 = osr.CoordinateTransformation(utm_cs, wgs84_cs)

    return transform_WGS84_To_UTM, transform_UTM_To_WGS84, utm_cs




def converWGS2UTM():
    pass



def convertUTM2WGS():
    pass







def getRasterExtent(srcImage):
    geoTrans = srcImage.GetGeoTransform()
    ulX = geoTrans[0]
    ulY = geoTrans[3]
    xDist = geoTrans[1]
    yDist = geoTrans[5]
    rtnX = geoTrans[2]
    rtnY = geoTrans[4]

    cols = srcImage.RasterXSize
    rows = srcImage.RasterYSize

    lrX = ulX + xDist * cols
    lrY = ulY + yDist * rows

    # Create ring
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(lrX, lrY)
    ring.AddPoint(lrX, ulY)
    ring.AddPoint(ulX, ulY)
    ring.AddPoint(ulX, lrY)
    ring.AddPoint(lrX, lrY)

    # Create polygon
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)




    return geoTrans, poly, ulX, ulY, lrX, lrY

def createPolygonFromCorners(lrX,lrY,ulX, ulY):
    # Create ring
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(lrX, lrY)
    ring.AddPoint(lrX, ulY)
    ring.AddPoint(ulX, ulY)
    ring.AddPoint(ulX, lrY)
    ring.AddPoint(lrX, lrY)

    # Create polygon
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)

    return poly



def clipShapeFile(shapeSrc, outputFileName, polyToCut):

    source_layer = shapeSrc.GetLayer()
    source_srs = source_layer.GetSpatialRef()
    # Create the output Layer
    outGeoJSon = outputFileName.replace('.tif', '.geojson')
    outDriver = ogr.GetDriverByName("geojson")
    if os.path.exists(outGeoJSon):
        outDriver.DeleteDataSource(outGeoJSon)

    outDataSource = outDriver.CreateDataSource(outGeoJSon)
    outLayer = outDataSource.CreateLayer("groundTruth", source_srs, geom_type=ogr.wkbPolygon)
    # Add input Layer Fields to the output Layer
    inLayerDefn = source_layer.GetLayerDefn()
    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLayer.CreateField(fieldDefn)
    outLayer.CreateField(ogr.FieldDefn("partialBuilding", ogr.OFTInteger))
    outLayerDefn = outLayer.GetLayerDefn()
    source_layer.SetSpatialFilter(polyToCut)
    for inFeature in source_layer:

        outFeature = ogr.Feature(outLayerDefn)

        for i in range (0, inLayerDefn.GetFieldCount()):
            outFeature.SetField(inLayerDefn.GetFieldDefn(i).GetNameRef(), inFeature.GetField(i))

        geom = inFeature.GetGeometryRef()
        geomNew = geom.Intersection(polyToCut)
        if geomNew:
            if geom.GetArea() == geomNew.GetArea():
                outFeature.SetField("partialBuilding", 0)
            else:
                outFeature.SetField("partialBuilding", 1)
        else:
            outFeature.SetField("partialBuilding", 1)


        outFeature.SetGeometry(geomNew)
        outLayer.CreateFeature(outFeature)





def cutChipFromMosaic(rasterFile, shapeFileSrc, outputDirectory='', outputPrefix='clip_',
                      clipSizeMX=100, clipSizeMY=100, numBands=8):
    #rasterFile = '/Users/dlindenbaum/dataStorage/spacenet/mosaic_8band/013022223103.tif'
    srcImage = gdal.Open(rasterFile)
    geoTrans, poly, ulX, ulY, lrX, lrY = getRasterExtent(srcImage)
    rasterFileBase = os.path.basename(rasterFile)
    if outputDirectory=="":
        outputDirectory=os.path.dirname(rasterFile)
    if not os.path.exists(outputDirectory):
        os.makedirs(outputDirectory)

    transform_WGS84_To_UTM, transform_UTM_To_WGS84, utm_cs = createUTMTransform(poly)
    poly.Transform(transform_WGS84_To_UTM)
    env = poly.GetEnvelope()
    minX = env[0]
    minY = env[2]
    maxX = env[1]
    maxY = env[3]

    shapeSrc = ogr.Open(shapeFileSrc)


    for llX in np.arange(minX, maxX, clipSizeMX):
        for llY in np.arange(minY, maxY, clipSizeMY):
            uRX = llX+clipSizeMX
            uRY = llY+clipSizeMY

            polyCut = createPolygonFromCorners(llX, llY, uRX, uRY)
            polyCut.Transform(transform_UTM_To_WGS84)
            envCut = polyCut.GetEnvelope()
            minXCut = envCut[0]
            minYCut = envCut[2]
            maxXCut = envCut[1]
            maxYCut = envCut[3]
            outputFileName = os.path.join(outputDirectory, outputPrefix+rasterFileBase.replace('.tif', "_{}_{}.tif".format(minXCut,minYCut)))

            ## Clip Image
            subprocess.call(["gdalwarp", "-te", "{}".format(minXCut), "{}".format(minYCut),
                             "{}".format(maxXCut),  "{}".format(maxYCut), rasterFile, outputFileName])
            outGeoJSon = outputFileName.replace('.tif', '.geojson')

            clipShapeFile(shapeSrc, outputFileName, polyCut)
            #subprocess.call(["ogr2ogr", "-f", "ESRI Shapefile",
            #                 "-spat", "{}".format(minXCut), "{}".format(minYCut),
            #                 "{}".format(maxXCut),  "{}".format(maxYCut), "-clipsrc", outGeoJSon, shapeFileSrc])
                ## ClipShapeFile





if __name__ == '__main__':
    start = time.time()

    #rasterDirectory = '/Users/dlindenbaum/dataStorage/spacenet/mosaic_8Band/'
    rasterDirectory = '/usr/local/share/spacenet/mosaic/'
    rasterFile = '/Users/dlindenbaum/dataStorage/spacenet/mosaic_8band/013022232122.tif'
    shapeFileSrc = '/usr/local/share/spacenet/AOI_Eastv1.geojson'
    outputDirectoryBase = '/Users/dlindenbaum/dataStorage/spacenet/clipv5Test/v1/'
    outputDirectoryBase = '/usr/local/share/spacenet/clipsTestAOIEast/mosiac'

    rasterFileList = glob.glob(os.path.join(rasterDirectory, '*.tif'))
    print rasterFileList
    for rasterFile in rasterFileList:
        print rasterFile
        outputDirectory = os.path.join(outputDirectoryBase, os.path.basename(rasterFile).replace(".tif", ''))
        cutChipFromMosaic(rasterFile, shapeFileSrc, outputDirectory=outputDirectory, outputPrefix='clip2_',
                      clipSizeMX=1000, clipSizeMY=1000, numBands=8)


    stop = time.time()
    print stop-start

























