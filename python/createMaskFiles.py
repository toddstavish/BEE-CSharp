from osgeo import gdal
from osgeo import osr
from osgeo import ogr
import numpy as np
import subprocess
import os
import time
import json
import glob


rastList = ['013022223130.tif',
            '013022223132.tif',
            '013022232020.tif',
            '013022232023.tif',
            '013022232033.tif',
            '013022232122.tif',
            '013022232210.tif',
            '013022223131.tif',
            '013022223133.tif',
            '013022232022.tif',
            '013022232032.tif',
            '013022232120.tif',
            '013022232200.tif']

mosaic3BandLocation = '/Users/dlindenbaum/dataStorage/spacenet/mosaic/'
mosaic8BandLocation = '/Users/dlindenbaum/dataStorage/spacenet/mosaic_8band'
shpOutline = '/Users/dlindenbaum/dataStorage/spacenet/rioBuildings_08022016/Rio_AOI_OutLine_Combined/Rio_Outline_Combined.shp'
for rast in rastList:

    #gdalwarp -q -cutline /Users/dlindenbaum/dataStorage/spacenet/rioBuildings_08022016/Rio_AOI_OutLine_Combined/Rio_Outline_Combined.shp -dstalpha -tr 4.48787913603e-06 4.48787913603e-06
    ## -of GTiff /Users/dlindenbaum/dataStorage/spacenet/mosaic/013022223132.tif /Users/dlindenbaum/dataStorage/spacenet/mosaic/013022223132_mask.tif


    # process3Band
    inputRaster = os.path.join(mosaic3BandLocation,rast)
    outputRaster = os.path.join(mosaic3BandLocation, rast.replace('.tif', '_mask.tif'))
    subprocess.call(["gdalwarp", "-q", "-cutline", shpOutline, "-dstalpha",
                     "-of", "GTiff", inputRaster, outputRaster])

    print("complete 3band {}".format(rast))
    #process8band
    inputRaster = os.path.join(mosaic8BandLocation, rast)
    outputRaster = os.path.join(mosaic8BandLocation, rast.replace('.tif', '_mask.tif'))

    subprocess.call(["gdalwarp", "-q", "-cutline", shpOutline, "-dstalpha",
                     "-of", "GTiff", inputRaster, outputRaster])

    print("complete 8band {}".format(rast))