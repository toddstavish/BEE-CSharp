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
        polys.append({'ImageId': feature.GetField('ImageId'), 'BuildingId': feature.GetField('BuildingId'), 'poly': feature.GetGeometryRef()})

    return polys