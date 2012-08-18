'''
A translation file for City of Surrey GIS data

See https://github.com/pnorman/SurreyCombinedAuto for related scripts

Copyright (c) 2011-2012 Paul Norman


Layer information
trnTrafficSignalsSHP: http://cosmosbeta.surrey.ca/COSREST/rest/services/Public/MapServer/58
wtrHydrantsSHP: http://cosmosbeta.surrey.ca/COSREST/rest/services/Public/MapServer/29

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
    
    index = ogrfeature.GetFieldIndex('STATUS')
    if index >= 0:
        if ogrfeature.GetField(index) in ('History', 'For Construction', 'Proposed'):
            return None

    index = ogrfeature.GetFieldIndex('__LAYER')
    if index >= 0:
        layer = ogrfeature.GetField(index)
        
    if layer == 'trnTrafficSignalsSHP':
        index = ogrfeature.GetFieldIndex('CONSTATUS')
        if index >= 0:
            if ogrfeature.GetField(index) == 'Proposed':
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
    if 'GIS_ES' in attrs:
        del attrs['GIS_ES']     
    if 'PROJ_NO' in attrs:
        del attrs['PROJ_NO']

    if '__LAYER' in attrs and attrs['__LAYER'] == 'trnTrafficSignalsSHP':  
        if 'YR' in attrs:
            if attrs['YR'].strip() != '':
                tags['start_date'] = attrs['YR'].strip()
            del attrs['YR']
        
    if '__LAYER' in attrs and attrs['__LAYER'] == 'trnTrafficSignalsSHP':  
        if 'CONSTATUS' in attrs:
            del attrs['CONSTATUS']
        if 'LOCATION' in attrs:
            del attrs['LOCATION']
        if 'OPTICOM' in attrs: # No suitable existing tags and not verifible
            del attrs['OPTICOM']
        if 'RCONTROL' in attrs: # Radio Control
            del attrs['RCONTROL']
        if 'STATUS' in attrs:
            del attrs['STATUS']
        
        if 'OWNER' in attrs:
            if attrs['OWNER'] == 'Provincial':
                tags['owner'] = 'Ministry of Transport'
            else:
                tags['owner'] = attrs['OWNER']
                
            del attrs['OWNER']
            
        if 'SIGNAL_ID' in attrs:
            tags['ref'] = attrs['SIGNAL_ID'].strip()
            del attrs['SIGNAL_ID']
            
        if 'SIGTYPE' in attrs:
            if attrs['SIGTYPE'].strip() == '0':
                tags['highway'] = 'traffic_signals'
                tags['traffic_signals'] = 'beacon'
                if 'COMMENTS' in attrs:
                    if attrs['COMMENTS'] == 'Red Beacon':
                        tags['beacon'] = 'stop'
                    elif attrs['COMMENTS'] == 'Yellow Beacon':
                        tags['beacon'] = 'yield'
                    else:
                        l.error("Unknown COMMENTS=%s in %s" % (attrs['COMMENTS'].strip(), attrs['__LAYER']))
                        tags['fixme'] = 'yes'
                    del attrs['COMMENTS']
            elif attrs['SIGTYPE'].strip() == '1':
                tags['highway'] = 'traffic_signals'
                tags['traffic_signals'] = 'emergency'
            elif attrs['SIGTYPE'].strip() == '2':
                tags['highway'] = 'traffic_signals'
                tags['traffic_signals'] = 'pedestrian_only'                
            elif attrs['SIGTYPE'].strip() == '3':
                tags['highway'] = 'crossing'
                tags['crossing'] = 'traffic_signals'
            elif attrs['SIGTYPE'].strip() == '4':
                tags['highway'] = 'traffic_signals'
        
            else:
                l.error("Unknown SIGTYPE=%s in %s" % (attrs['SIGTYPE'].strip(), attrs['__LAYER']))
                tags['fixme'] = 'yes'
                if 'SIGTYPE2' in attrs:
                    tags['surrey:SIGTYPE'] = attrs['SIGTYPE2'].strip()
                else:
                    tags['surrey:SIGTYPE'] = attrs['SIGTYPE'].strip()

            del attrs['SIGTYPE']
            if 'SIGTYPE2' in attrs:
                del attrs['SIGTYPE2']
            
        if 'YR' in attrs:
            if attrs['YR'].strip() != '':
                tags['start_date'] = attrs['YR'].strip()
            del attrs['YR']
                
    if '__LAYER' in attrs and attrs['__LAYER'] == 'wtrHydrantsSHP':
        if 'ANC_YRROLE' in attrs:
            del attrs['ANC_YRROLE']
        if 'BV_MANUFAC' in attrs:
            del attrs['BV_MANUFAC']
        if 'BV_MODEL' in attrs:
            del attrs['BV_MODEL']
        if 'COMMENTS' in attrs:
            del attrs['COMMENTS']
        if 'COND_DATE' in attrs:
            del attrs['COND_DATE']
        if 'CONDITION' in attrs:
            del attrs['CONDITION']
        if 'DIS2VALVE' in attrs: # Distance to valve
            del attrs['DIS2VALVE']
        if 'FACILITYID' in attrs:
            del attrs['FACILITYID']
        if 'ENABLED' in attrs:
            del attrs['ENABLED']
        if 'LAST_MAINT' in attrs:
            del attrs['LAST_MAINT']
        if 'LC_COST' in attrs:
            del attrs['LC_COST']
        if 'LEGACYID' in attrs:
            del attrs['LEGACYID']
        if 'LOCATION' in attrs:
            del attrs['LOCATION']
        if 'NODE_NO' in attrs:
            del attrs['NODE_NO']
        if 'OP_STATUS' in attrs: # Although the operating status is important if you want water, it's likely to change too often and be unmappable
            del attrs['OP_STATUS']
        if 'PROJECT_NO' in attrs:
            del attrs['PROJECT_NO']
        if 'STATUS' in attrs:
            del attrs['STATUS']
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
        
        if 'HYDRANT_NO' in attrs:
            tags['ref'] = attrs['HYDRANT_NO']
            del attrs['HYDRANT_NO']
        
        if 'MAKE' in attrs:
            tags['manufacturer'] = attrs['MAKE']
            del attrs['MAKE']
                
        if 'OWNER' in attrs:
            tags['owner'] = attrs['OWNER']
            del attrs['OWNER']
        
        if 'YR' in attrs:
            tags['start_date'] = attrs['YR']
            del attrs['YR']
        
    for k,v in attrs.iteritems():
        if v.strip() != '' and not k in tags:
            tags[k]=v
    
    return tags
