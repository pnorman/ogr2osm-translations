#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
This translation file adds a __LAYER field to a datasource before translating it

Copyright (c) 2012 Paul Norman
<penorman@mac.com>
Released under the MIT license: http://opensource.org/licenses/mit-license.php

'''

from osgeo import ogr

def filterLayer(layer):
    if not layer:
        return
    
    layername = layer.GetName()
    
    # Add a __LAYER field
    field = ogr.FieldDefn('__LAYER', ogr.OFTString)
    field.SetWidth(len(layername))
    layer.CreateField(field)

    # Set the __LAYER field to the name of the current layer
    for j in range(layer.GetFeatureCount()):
        ogrfeature = layer.GetNextFeature()
        ogrfeature.SetField('__LAYER', layername)
        layer.SetFeature(ogrfeature)
    
    # Reset the layer's read position so features are read later on
    layer.ResetReading()
    
    return layer
