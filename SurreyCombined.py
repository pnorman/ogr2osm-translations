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
    if not layer: return
    
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

'''
Map Surrey -> OSM
'''
def filterTags(attrs):
    if not attrs: return
    tags = {}

    ''' Delete common useless tags '''
    if 'YTD_COST' in attrs:
            del attrs['YTD_COST']
    if '__LAYER' in attrs and attrs['__LAYER'] == 'wtrHydrantsSHP':
        if 'BV_MANUFAC' in attrs:
            del attrs['BV_MANUFAC']
        if 'BV_MODEL' in attrs:
            del attrs['BV_MODEL']
        if 'COMMENTS' in attrs:
            del attrs['COMMENTS']
        if 'DIS2VALVE' in attrs: # Distance to valve
            del attrs['DIS2VALVE']
        if 'PROJECT_NO' in attrs:
            del attrs['PROJECT_NO']
        if 'WARR_DATE' in attrs:
            del attrs['WARR_DATE']

        tags['emergency'] = 'fire_hydrant'

        if 'HYD_TYPE' in attrs:
            if attrs['HYD_TYPE'].strip() == '0':
                tags['fire_hydrant:type'] = 'pillar'
            elif attrs['HYD_TYPE'].strip() == '1':
                tags['fire_hydrant:type'] = 'underground'
            else:
                l.error("Unknown HYD_TYPE=%s in %s" % (attrs['HYD_TYPE'].strip(), attrs['__LAYER']))
                tags['fixme'] = 'yes'
                if 'HYD_TYPE2' in attrs:
                    tags['surrey:HYD_TYPE'] = attrs['HYD_TYPE2'].strip()
                else:
                    tags['surrey:HYD_TYPE'] = attrs['HYD_TYPE'].strip()
            del attrs['HYD_TYPE']
            if 'HYD_TYPE2' in attrs:
                del attrs['HYD_TYPE2']

        if 'MAKE' in attrs:
            tags['manufacturer'] = attrs['MAKE']
            del attrs['MAKE']
                
        if 'OWNER' in attrs:
            tags['owner'] = attrs['OWNER']
            del attrs['OWNER']
        
        if 'YR' in attrs:
            tags['start_date'] = attrs['YR']
            del attrs['YR']
        
    tags.update(attrs)
    
    return tags
