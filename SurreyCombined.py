'''
A translation file for City of Surrey GIS data

See https://github.com/pnorman/SurreyCombinedAuto for related scripts

Copyright (c) 2011-2012 Paul Norman
'''

from osgeo import ogr
import logging as l

'''
 Some common name conversion functions
'''

suffixlookup = {
    'Ave':'Avenue',
    'Rd':'Road',
    'St':'Street',
    'Pl':'Place',
    'Cr':'Crescent',
    'Blvd':'Boulevard',
    'Dr':'Drive',
    'Lane':'Lane',
    'Crt':'Court',
    'Gr':'Grove',
    'Cl':'Close',
    'Rwy':'Railway',
    'Div':'Diversion',
    'Hwy':'Highway',
    'Hwy':'Highway',
    'E':'East',
    'S':'South',
    'N':'North',
    'W':'West'
}

def translateName(rawname):

	newName = ''
	for partName in rawname.split():
		newName = newName + ' ' + suffixlookup.get(partName,partName)
	
	return newName.strip()

def filterFeature(ogrfeature, fieldNames, reproject):
    if not ogrfeature: return
    index = ogrfeature.GetFieldIndex('__LAYER')
    if index >= 0:
        layer = ogrfeature.GetField(index)
        
    if layer == 'wtrHydrantsSHP':
        index = ogrfeature.GetFieldIndex('STATUS')
        if index >= 0:
            if ogrfeature.GetField(index) in ('History', 'For Construction', 'Proposed'):
                return None
        
    return ogrfeature


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
