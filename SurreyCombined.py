'''
A translation file for City of Surrey GIS data

See https://github.com/pnorman/SurreyCombinedAuto for related scripts

Copyright (c) 2011-2012 Paul Norman

This translation deletes attributes from attrs as it uses them then looks at the end result. This allows easier detection of tagging changes in the source data.

Layer information
trnPolesSHP: http://cosmosbeta.surrey.ca/COSREST/rest/services/Public/MapServer/56
trnRoadCentrelinesSHP: http://cosmosbeta.surrey.ca/COSREST/rest/services/Public/MapServer/106
trnSidewalksSHP: http://cosmosbeta.surrey.ca/COSREST/rest/services/Public/MapServer/105
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
    'Fg':'Frontage Road'
}
directionlookup = {
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

def filterFeature(ogrfeature, fieldNames, reproject):
    if not ogrfeature: return
    
    index = ogrfeature.GetFieldIndex('STATUS')
    if index >= 0:
        if ogrfeature.GetField(index) in ('History', 'For Construction', 'Proposed'):
            return None

    index = ogrfeature.GetFieldIndex('__LAYER')
    if index >= 0:
        layer = ogrfeature.GetField(index)

    if layer == 'trnPolesSHP':
        POLE_TYPE2 = ogrfeature.GetField(ogrfeature.GetFieldIndex('POLE_TYPE2'))
        LUM_STYLE = ogrfeature.GetField(ogrfeature.GetFieldIndex('LUM_STYLE'))
        if POLE_TYPE2 == 'Overhead Sign Pole':
            '''
            These are poles letting you know stuff like turn right for highway 15
            '''
            if LUM_STYLE is None or LUM_STYLE == 'Specialty':
                return None
            
        elif POLE_TYPE2 == 'Push Button':
            '''
            Poles with signal buttons without lights or power lines on them.
            '''
            return None
        elif POLE_TYPE2 == 'Secondary Signal Pole':
            '''
            Poles with signal buttons without lights or power lines on them.
            '''
            if LUM_STYLE is None:
                return None
        elif POLE_TYPE2 == 'Primary Signal Pole':
            '''
            Poles with signal buttons without lights or power lines on them.
            '''
            if LUM_STYLE is None or LUM_STYLE == 'Traditionaire':
                return None
        elif POLE_TYPE2 == 'Sign Bridge':
            '''
            The sign bridges on King George 
            '''
            return None
        elif POLE_TYPE2 == 'Stand Alone Service Base':
            '''
            Not a pole at all
            '''
            return None

    
    if layer == 'trnTrafficSignalsSHP':
        index = ogrfeature.GetFieldIndex('CONSTATUS')
        if index >= 0:
            if ogrfeature.GetField(index) == 'Proposed':
                return None

        
    if layer == 'trnSidewalksSHP':
        index = ogrfeature.GetFieldIndex('DESIGNTN')
        if index >= 0 and ogrfeature.GetField(index) is None:
            index = ogrfeature.GetFieldIndex('GREENWAY')
            if index >= 0:
                if ogrfeature.GetField(index) == 'No':
                    return None
                

                
    return ogrfeature

'''
Map Surrey -> OSM
'''
def filterTags(attrs):
    if not attrs: return
    tags = {}

    ''' Delete common useless tags '''
    if 'YTD_COST' in attrs: del attrs['YTD_COST']
    if 'GIS_ES' in attrs: del attrs['GIS_ES']     
    if 'LC_COST' in attrs: del attrs['LC_COST']
    if 'LEGACYID' in attrs: del attrs['LEGACYID']
    if 'PROJ_NO' in attrs: del attrs['PROJ_NO']

    if '__LAYER' in attrs and attrs['__LAYER'] == 'trnPolesSHP': 
        if 'CP_ANTEN' in attrs: del attrs['CP_ANTEN']       # Cell phone antenna. never Yes
        if 'LOCATION' in attrs: del attrs['LOCATION']
        if 'MAP_NO' in attrs: del attrs['MAP_NO']
        if 'PAINTDATE' in attrs: del attrs['PAINTDATE']     # Unverifible
        if 'PHASE' in attrs: del attrs['PHASE']             # Unverifible
        if 'POLE_INST' in attrs: del attrs['POLE_INST']     # Unverifible
        if 'RL_ZONE' in attrs: del attrs['RL_ZONE']         # Relamp zone
        if 'SL_STATUS' in attrs: del attrs['SL_STATUS']     # relamp information
        if 'SPACING' in attrs: del attrs['SPACING']         # Spacing, duplicates geodata
        if 'SPAC_TYPE' in attrs: del attrs['SPAC_TYPE']     # Spacing type, duplicates geodata
        if 'SUR_ID_AVE' in attrs: del attrs['SUR_ID_AVE']   # Geodata
        if 'SUR_ID_ST' in attrs: del attrs['SUR_ID_ST']     # Geodata
        if 'SURREYID' in attrs: del attrs['SURREYID']       # Geodata

        if 'COLOUR' in attrs and attrs['COLOUR'].strip() != '':
            tags['colour'] = attrs['COLOUR'].lower()
            del attrs['COLOUR']
            
        if 'POLE_HT' in attrs:
            if attrs['POLE_HT'].strip().strip('0').rstrip('.') != '': 
                ''' Reject blank heights and heights of 0 '''
                tags['height'] = str(round(float(attrs['POLE_HT'].strip()),3))
            del attrs['POLE_HT']

        if 'POLE_NO' in attrs and attrs['POLE_NO'].strip() != '':
            tags['ref'] = attrs['POLE_NO']
            del attrs['POLE_NO']
        
        if 'YR' in attrs and attrs['YR'].strip() != '':
            tags['start_date'] = attrs['YR'].strip()
            del attrs['YR']        
        
        if 'LAMP_TYPE' in attrs and attrs['LAMP_TYPE'] != '':
            if attrs['LAMP_TYPE'] == 'High Pressure Sodium':
                tags['lamp_type'] = 'sodium'
                del attrs['LAMP_TYPE']
            elif attrs['LAMP_TYPE'] == 'LED':
                tags['lamp_type'] = 'led'
                del attrs['LAMP_TYPE']
            elif attrs['LAMP_TYPE'] == 'Metal Halide':
                tags['lamp_type'] = 'metal_halide'
                del attrs['LAMP_TYPE']
            elif attrs['LAMP_TYPE'] == 'Special Lighting (Other)':
                del attrs['LAMP_TYPE']
            else:
                l.error("trnPolesSHP LAMP_TYPE logic fell through")
                tags['fixme'] = 'yes'
                
        if 'MATERIAL' in attrs and attrs['MATERIAL'] != '':    
            tags['material'] = attrs['MATERIAL'].lower()
            del attrs['MATERIAL']
            
        if 'POLE_SHAPE' in attrs and attrs['POLE_SHAPE'] != '':
            tags['pole:shape'] = attrs['POLE_SHAPE']
            del attrs['POLE_SHAPE']
            
        if 'POLE_TYPE2' in attrs:
            if attrs['POLE_TYPE2'] == 'Hydro with Lights':
                '''
                Type 0
                The poles with the wrong numerical value set are still hydro with lights
                '''
                tags['highway'] = 'street_lamp'
                tags['power'] = 'pole'
                del attrs['POLE_TYPE2']
            elif attrs['POLE_TYPE2'] == 'Overhead Sign Pole':
                '''
                Type 1
                OSPs without lights have been filtered out already
                '''
                tags['highway'] = 'street_lamp'
                del attrs['POLE_TYPE2']
            elif attrs['POLE_TYPE2'] == 'Primary Signal Pole':
                '''
                Type 2
                Poles without lights have been filtered
                '''
                tags['highway'] = 'street_lamp'
                del attrs['POLE_TYPE2']
            elif attrs['POLE_TYPE2'] == 'Private Property Light':
                '''
                Type 3
                On private property normally
                '''
                tags['highway'] = 'street_lamp'
                del attrs['POLE_TYPE2']
            elif attrs['POLE_TYPE2'] == 'Secondary Signal Pole':
                '''
                Type 5
                '''
                tags['highway'] = 'street_lamp'
                del attrs['POLE_TYPE2']
            elif attrs['POLE_TYPE2'] == 'Streetlight':
                '''
                Type 8
                '''
                tags['highway'] = 'street_lamp'
            elif attrs['POLE_TYPE2'] == 'Streetlight with Service Base':
                '''
                Type 9
                '''
                tags['highway'] = 'street_lamp'
                
            
            
    elif '__LAYER' in attrs and attrs['__LAYER'] == 'trnRoadCentrelinesSHP': 
        if 'COMMENTS' in attrs: del attrs['COMMENTS']
        if 'DATECLOSED' in attrs: del attrs['DATECLOSED']
        if 'DATECONST' in attrs: del attrs['DATECONST']
        if 'DESIGNTN' in attrs: del attrs['DESIGNTN']
        if 'DISR_ROUTE' in attrs: del attrs['DISR_ROUTE']
        if 'GCROADS' in attrs: del attrs['GCROADS']
        if 'GREENWAY' in attrs: del attrs['GREENWAY']
        if 'LEFTFROM' in attrs: del attrs['LEFTFROM']
        if 'LEFTTO' in attrs: del attrs['LEFTTO']
        if 'RIGHTFROM' in attrs: del attrs['RIGHTFROM']
        if 'RIGHTTO' in attrs: del attrs['RIGHTTO']
        if 'ROW_WIDTH' in attrs: del attrs['ROW_WIDTH']
        if 'ROADCODE' in attrs: del attrs['ROADCODE']
        if 'SNW_RTEZON' in attrs: del attrs['SNW_RTEZON']
        if 'STATUS' in attrs: del attrs['STATUS']
        if 'WTR_VEHCL' in attrs: del attrs['WTR_VEHCL'] #Not really relevant
        
        if 'GCNAME' in attrs:
        
            '''
            Build the name of the road from the name, road type and direction.
            Frontage roads need to be special-cased
            '''
            if 'GCTYPE' in attrs and attrs['GCTYPE'].upper() == 'FG' and 'ROAD_NAME' in attrs:
                tags['name'] = ''
                for part in attrs['ROAD_NAME'].title().split():
                    tags['name'] += ' ' + suffixlookup.get(directionlookup.get(part,part),directionlookup.get(part,part))
            else:
                tags['name'] =  (attrs['GCNAME'].title() + 
                            (' ' + suffixlookup.get(attrs['GCTYPE'].strip().title(),attrs['GCTYPE'].strip().title()) 
                            if 'GCTYPE' in attrs and attrs['GCTYPE'].strip() != '' else '') +
                            (' ' + directionlookup.get(attrs['GCSUFDIR'].strip(), attrs['GCSUFDIR'].strip()) 
                            if 'GCSUFDIR' in attrs and attrs['GCSUFDIR'].strip() != '' else ''))
            
        if 'NO_LANE' in attrs:
            tags['lanes'] = attrs['NO_LANE'].strip()
            del attrs['NO_LANE']
            
        if 'SPEED' in attrs:
            tags['maxspeed'] = attrs['SPEED'].strip()
            del attrs['SPEED']
            
        if 'YR' in attrs:
            if attrs['YR'].strip() != '':
                tags['start_date'] = attrs['YR'].strip()
            del attrs['YR']
        
        if 'RC_TYPE' in attrs:
            if attrs['RC_TYPE'].strip() == '0': # Normal roads
                del attrs['RC_TYPE']
                if 'RC_TYPE2' in attrs: del attrs['RC_TYPE2']
                if 'MATERIAL' in attrs:
                    tags['surface'] = attrs['MATERIAL'].lower()
                    del attrs['MATERIAL']
                if 'RD_CLASS' in attrs and attrs['RD_CLASS'] == 'Local':
                    tags['highway'] = 'residential'
                    del attrs['RD_CLASS']
                elif 'RD_CLASS' in attrs and attrs['RD_CLASS'] == 'Major Collector':
                    tags['highway'] = 'tertiary'
                    del attrs['RD_CLASS']
                elif 'RD_CLASS' in attrs and attrs['RD_CLASS'] == 'Arterial':
                    if 'ROAD_NAME' in attrs and attrs['ROAD_NAME'] in ('King George Blvd', 'Fraser Hwy'):
                        tags['highway'] = 'primary'
                    else:
                        if 'MRN' in attrs and attrs['MRN'] == 'Yes':
                            tags['highway'] = 'secondary'
                        else:
                            tags['highway'] = 'tertiary'
                    del attrs['RD_CLASS']
                elif 'RD_CLASS' in attrs and attrs['RD_CLASS'] == 'Provincial Highway':
                    # Special-case motorways
                    if 'ROAD_NAME' in attrs and attrs['ROAD_NAME'] in ('No 1 Hwy', 'No 99 Hwy'):
                        tags['highway'] = 'motorway'
                    else:
                        tags['highway'] = 'primary'
                    del attrs['RD_CLASS']
                elif 'RD_CLASS' in attrs and attrs['RD_CLASS'] == 'Translink':
                    tags['highway'] = 'unclassified'
                    del attrs['RD_CLASS']
                else:
                    l.error("trnRoadCentrelinesSHP RC_TYPE=0 logic fell through")
                    tags['fixme'] = 'yes'
                    tags['highway'] = 'road'
            elif attrs['RC_TYPE'].strip() == '1': # Frontage roads
                del attrs['RC_TYPE']
                if 'RC_TYPE2' in attrs: del attrs['RC_TYPE2']
                if 'MATERIAL' in attrs:
                    tags['surface'] = attrs['MATERIAL'].lower()
                    del attrs['MATERIAL']
                tags['highway'] = 'residential'
            elif attrs['RC_TYPE'].strip() == '2': # Highway Interchange
                del attrs['RC_TYPE']
                if 'RC_TYPE2' in attrs: del attrs['RC_TYPE2']
                if 'MATERIAL' in attrs:
                    tags['surface'] = attrs['MATERIAL'].lower()
                    del attrs['MATERIAL']
                tags['highway'] = 'motorway_link'
            elif attrs['RC_TYPE'].strip() == '3': # Street Lane
                del attrs['RC_TYPE']
                if 'RC_TYPE2' in attrs: del attrs['RC_TYPE2']
                if 'MATERIAL' in attrs:
                    tags['surface'] = attrs['MATERIAL'].lower()
                    del attrs['MATERIAL']
                tags['highway'] = 'service'
            elif attrs['RC_TYPE'].strip() == '4': # Access lane
                del attrs['RC_TYPE']
                if 'RC_TYPE2' in attrs: del attrs['RC_TYPE2']
                if 'MATERIAL' in attrs:
                    tags['surface'] = attrs['MATERIAL'].lower()
                    del attrs['MATERIAL']
                if 'OWNER' in attrs and attrs['OWNER'] == 'Private':
                    tags['highway'] = 'residential'
                else:
                    tags['highway'] = 'service'
            elif attrs['RC_TYPE'].strip() == '5': # Railway
                del attrs['RC_TYPE']
                if 'RC_TYPE2' in attrs: del attrs['RC_TYPE2']        
                tags['railway'] = 'rail'
                if 'MATERIAL' in attrs: del attrs['MATERIAL']
        
        ''' Gritting '''
        if 'WTR_PRIOR' in attrs and attrs['WTR_PRIOR'].strip() != '':
            if 'First' in attrs['WTR_PRIOR']:
                tags['maintenance'] = 'gritting'
                tags['gritting'] = 'priority_1'
            elif 'Second' in attrs['WTR_PRIOR']:
                tags['maintenance'] = 'gritting'
                tags['gritting'] = 'priority_2'
            else:
                l.error("trnRoadCentrelinesSHP WTR_PRIOR logic fell through")
                tags['fixme'] = 'yes'
            del attrs['WTR_PRIOR']
            
        if 'TRK_ROUTE' in attrs and attrs['TRK_ROUTE'].strip() != '':
            if attrs['TRK_ROUTE'] == 'Dangerous Goods Routes':
                tags['hgv'] = 'designated'
                tags['hazmat'] = 'designated'
                del attrs['TRK_ROUTE']
            elif attrs['TRK_ROUTE'] == 'Truck Routes Restrictions':
                tags['hgv'] = 'no'
                del attrs['TRK_ROUTE']
            elif attrs['TRK_ROUTE'] == 'No Heavy Truck Routes':
                tags['hgv'] = 'no'
                tags['goods'] = 'yes'
                del attrs['TRK_ROUTE']
            elif attrs['TRK_ROUTE'] == 'Truck Routes':
                tags['hgv'] = 'designated'
                del attrs['TRK_ROUTE']
            else:
                l.error("trnRoadCentrelinesSHP TRK_ROUTE logic fell through")
                tags['fixme'] = 'yes'
                
            
        '''
        Clean up attributes used above
        '''
        if 'GCNAME' in attrs: del attrs['GCNAME']
        if 'GCTYPE' in attrs: del attrs['GCTYPE']
        if 'GCSUFDIR' in attrs: del attrs['GCSUFDIR']
        if 'OWNER' in attrs: del attrs['OWNER']
        if 'ROAD_NAME' in attrs: del attrs['ROAD_NAME']
        if 'RD_CLASS' in attrs: del attrs['RD_CLASS']
        if 'MRN' in attrs: del attrs['MRN']

        
    elif '__LAYER' in attrs and attrs['__LAYER'] == 'trnSidewalksSHP':  
        if 'COMMENTS' in attrs: del attrs['COMMENTS']
        if 'STATUS' in attrs: del attrs['STATUS']
        if 'LOCATION' in attrs: del attrs['LOCATION']
        
        if 'MATERIAL' in attrs and attrs['MATERIAL'].strip() != '':
            if attrs['MATERIAL'] == 'Asphalt':
                tags['surface'] = 'asphalt'
            elif attrs['MATERIAL'] == 'Concrete':
                tags['surface'] = 'concrete'
            elif attrs['MATERIAL'] == 'Limestone':
                tags['surface'] = 'gravel'
                tags['gravel'] = 'limestone'
            else:
                l.error("Unknown MATERIAL=%s in %s" % (attrs['MATERIAL'].strip(), attrs['__LAYER']))
                tags['fixme'] = 'yes'
            del attrs['MATERIAL']
            
        if 'WIDTH' in attrs:
            if attrs['WIDTH'].strip().rstrip('0').rstrip('.') != '':
                tags['width'] = attrs['WIDTH'].strip().rstrip('0').rstrip('.')
            del attrs['WIDTH']
        if 'YR' in attrs:
            if attrs['YR'].strip() != '':
                tags['start_date'] = attrs['YR'].strip()
            del attrs['YR']
            
        if 'GREENWAY' in attrs and attrs['GREENWAY'].strip() == 'Yes':
            
            if 'DESIGNTN' in attrs and attrs['DESIGNTN'].strip() == 'Commercial':
                tags['highway'] = 'footway'
                tags['footway'] = 'sidewalk'
            elif 'DESIGNTN' in attrs and attrs['DESIGNTN'].strip() == 'Land Development':
                tags['highway'] = 'footway'
                tags['footway'] = 'sidewalk'
            elif 'DESIGNTN' in attrs and attrs['DESIGNTN'].strip() == 'Residential':
                tags['highway'] = 'footway'
            else:
                l.error("trnSidewalksSHP GREENWAY=Yes logic fell through")
                tags['fixme'] = 'yes'
                
            del attrs['GREENWAY']
            if 'DESIGNTN' in attrs: del attrs['DESIGNTN']
            if 'OWNER' in attrs: del attrs['OWNER']
        else:
            if 'GREENWAY' in attrs: del attrs['GREENWAY']
                
            if 'OWNER' in attrs and attrs['OWNER'].strip() == 'Private':
                if 'DESIGNTN' in attrs and attrs['DESIGNTN'] == 'Commercial':
                    tags['highway'] = 'footway'
                    tags['footway'] = 'sidewalk'
                elif 'DESIGNTN' in attrs and attrs['DESIGNTN'] == 'Residential':
                    tags['highway'] = 'footway'
                else:
                    l.error("trnSidewalksSHP OWNER=Private logic fell through")
                    tags['fixme'] = 'yes'
            else:
                tags['highway'] = 'footway'
                tags['footway'] = 'sidewalk'
            if 'OWNER' in attrs: del attrs['OWNER']
            if 'DESIGNTN' in attrs: del attrs['DESIGNTN']

    elif '__LAYER' in attrs and attrs['__LAYER'] == 'trnTrafficSignalsSHP':  
        if 'CONSTATUS' in attrs: del attrs['CONSTATUS']
        if 'LOCATION' in attrs: del attrs['LOCATION']
        if 'OPTICOM' in attrs: del attrs['OPTICOM'] # No suitable existing tags and not verifible
        if 'RCONTROL' in attrs: del attrs['RCONTROL'] # Radio Control
        if 'STATUS' in attrs: del attrs['STATUS']
        
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
    
    elif '__LAYER' in attrs and attrs['__LAYER'] == 'wtrHydrantsSHP':
        if 'ANC_YRROLE' in attrs: del attrs['ANC_YRROLE']
        if 'COMMENTS' in attrs: del attrs['COMMENTS']
        if 'COND_DATE' in attrs: del attrs['COND_DATE']
        if 'CONDITION' in attrs: del attrs['CONDITION']
        if 'DIS2VALVE' in attrs: del attrs['DIS2VALVE'] # Distance to valve
        if 'FACILITYID' in attrs: del attrs['FACILITYID']
        if 'ENABLED' in attrs: del attrs['ENABLED']
        if 'LAST_MAINT' in attrs: del attrs['LAST_MAINT']
        if 'LOCATION' in attrs: del attrs['LOCATION']
        if 'NODE_NO' in attrs: del attrs['NODE_NO']
        if 'OP_STATUS' in attrs: del attrs['OP_STATUS']# Although the operating status is important if you want water, it's likely to change too often and be unmappable
        if 'PROJECT_NO' in attrs: del attrs['PROJECT_NO']
        if 'STATUS' in attrs: del attrs['STATUS']
        if 'WARR_DATE' in attrs: del attrs['WARR_DATE']

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
            if 'HYD_TYPE2' in attrs: del attrs['HYD_TYPE2']
        
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
