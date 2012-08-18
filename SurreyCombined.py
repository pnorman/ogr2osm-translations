'''
A translation file for City of Surrey GIS data

See https://github.com/pnorman/SurreyCombinedAuto for related scripts

Copyright (c) 2012 Paul Norman
'''

from osgeo import ogr

def filterLayer(layer):
    if not layer:
        return
    
    layername = layer.GetName()
    
    '''
    Add a new field indicating the current layer
    '''
    field = ogr.FieldDefn('__LAYER', ogr.OFTString)
    field.SetWidth(len(layername))
    layer.CreateField(field)
    
    for j in range(layer.GetFeatureCount()):
        ogrfeature = layer.GetNextFeature()
        ogrfeature.SetField('__LAYER', layername)
        layer.SetFeature(ogrfeature)
    
    layer.ResetReading()
    return layer
