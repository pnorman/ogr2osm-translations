'''
A translation function for NHD data. 

The shapefiles are availble as PD from the USGS 
at ftp://nhdftp.usgs.gov/DataSets/Staged/SubRegions/PersonalGDB/HighResolution/
or ftp://nhdftp.usgs.gov/DataSets/Staged/SubRegions/FileGDB/HighResolution/

PersonalGDB files can be converted to shapefiles with a default Windows build of QGIS or gdal.

See http://www.gdal.org/ogr/drv_mdb.html or http://www.gdal.org/ogr/drv_pgeo.html

These files are very large and it may be desirable to cut them down to size first

http://nhd.usgs.gov/NHDDataDictionary_model2.0.pdf helps explain the definitions of some fields

It may be desirable to post-process with https://trac.openstreetmap.org/browser/applications/utils/filter/merge-ways/merge-ways.pl (maybe)

The following fields are dropped from the source shapefile:

Field           Definition                  Reason
AreaSqKm        Area of feature             Duplicates geodata    
ComID           Unique ID of feature        Metadata
FDate           Date of last modification   Metadata
FType           Feature type                Duplication of FCode
LengthKM        Feature length              Duplicates geodata
OBJECTID        Object ID                   Metadata
Permanent_      40 character GUID           Metadata
Resolution      Resolution                  Metadata    
Shape_Area      Area of feature             Duplicates geodata
Shape_Length    Length of feature           Duplicates geodata
Source_Fea      Way that event is on        Duplicates geodata
WBAreaComI          
WBArea_Per
Measure         Location along stream       Duplicates geodata
Enabled


The following fields are used:    

Field           Used for            Reason
Elevation       Elevation
FCode           Mapping to OSM tags
FeatureDet      Website of stream gage
GNIS_Name       
GNIS_ID         
ReachCode       combining ways?

Internal mappings:
n is short for natural
ww is short for waterway
OSM Mappings
NHDFlowline
Source FCode            OSM value                             Shortcomings
55800   ARTIFICIAL PATH ww=stream/river                 stream/river may need adjusting
33600   CANAL/DITCH     ww=ditch                        Check if any waterway=canal have this
33601
33603
56600   COASTLINE       n=coastline
33400   CONNECTOR       delete these
428__
42803   PIPELINE        man_made=pipeline type=water location=underground
42807   PIPELINE        man_made=pipeline type=water location=underground   is it always water?
46000   STREAM/RIVER    ww=stream/river                 stream/river may need adjusting.
46003   STREAM/RIVER    ww=stream intermittent=yes      stream/river may need adjusting
46006   STREAM/RIVER    ww=stream/river                 stream/river may need adjusting
46007
420__

NHDLine
31800
34300   DAM/WEIR        ww=dam area=yes    
30305   DAM/WEIR        ww=dam area=yes dam=earth
34306   DAM/WEIR        ww=dam area=yes dam=artificial        
36200   FLUME           delete
36200
36900
56800   LEVEE           man_made=dyke
41100   NONEARTHERN SHORE   delete        
43100   RAPIDS          
50302   SOUNDING DATUM LINE delete

NHDPoint
36700   GAGING STATION  delete
44101   ROCK            n=rock
45000   SINK/RISE       delete      
45800   SPRING/SEEP     n=spring
48700   WATERFALL       ww=waterfall
48800   WELL            man_made=water_well             Are these all water wells?

NHDWaterbody
49300   ESTUARY         n=water tidal=yes               Should these be subtracted from the ocean?
37800   ICE MASS        n=glacier
39000   LAKE/POND       n=water [water=lake]
39001   LAKE/POND       n=water [water=lake] intermittent=yes
39004   LAKE/POND       n=water [water=lake]
39005
39006
39009   LAKE/POND       n=water [water=lake] ele=*
39010
39011
39012
36100   PLAYA           n=wetland wetland=dry_lake      http://www.pljv.org/
43600   RESERVOIR       n=water water=pond              Not otherwise specified.
43601   RESERVOIR       n=water water=pond pond=aquaculture
436__
43603   RESERVOIR       n=water water=pool              decorative pool?
43609   RESERVOIR       n=water water=pond pond=cooling
43610   RESERVOIR       n=water water=pond pond=filtration
43611   RESERVOIR       n=water water=pond pond=settling
43612   RESERVOIR       n=water water=pond pond=sewage
43613   RESERVOIR       n=water water=pond pond=storage
43613   RESERVOIR       n=water water=pond pond=storage
43614   RESERVOIR       n=water water=pond              in 0310 these are used for all ponds not just storage ponds?
43617   RESERVOIR       n=water water=pond              as in 43614
46600   SWAMP/MARSH     n=wetland 
46601   SWAMP/MARSH     n=wetland intermittent=yes
46602   SWAMP/MARSH     n=wetland

NHDArea
53700
30700
31200   BAY/INLET       natural=bay
31800
33600   CANAL/DITCH     natural=water
33601   CANAL/DITCH     delete?
33603
34300   DAM/WEIR        ww=dam area=yes    
30305   DAM/WEIR        ww=dam area=yes dam=earth
34306   DAM/WEIR        ww=dam area=yes dam=artificial        
36200   FLUME
36400   FORESHORE       n=beach
37300
34300
40307   INUNDATION      n=water intermittent=uncontrolled
40308   INUNDATION      n=water intermittent=controlled
40309   INUNDATION      n=water intermittent=flood
56800
39800
43100   RAPIDS          ww=rapids area=yes
44500   SEA/OCEAN       Condense to a point? Delete for now
454__
45500
46000   STREAM/RIVER    ww=riverbank
46003   STREAM/RIVER    n=water intermittent=yes        Maybe add water=river/stream based on reachcode and feature inside?
46006   STREAM/RIVER    ww=riverbank
46007   See WASH
48400   WASH            n=water intermittent=yes        Can't tell apart from 46003
'''

from osgeo import ogr

def filterLayer(layer):
    if not layer:
        return

    '''
    Check for layers that should not be processed
    '''
    layername = layer.GetName()
    if layername in ('WBD_HU10', 'WBD_HU12', 'WBD_HU14', 'WBD_HU16', 'WBD_HU2', 'WBD_HU4', 'WBD_HU6', 'WBD_HU8', 'HYDRO_NET_Junctions'):
        return
    
    '''
    Process unknown layers, but warn about them
    '''
    if layername not in ('NHDArea', 'NHDAreaEventFC', 'NHDFlowline', 'NHDLine', 
                    'NHDLineEventFC', 'NHDPoint', 'NHDPointEventFC', 'NHDWaterbody'):
        print 'Unknown layer ' + layer.GetName()
    
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
    if not ogrfeature:
        return
    index = ogrfeature.GetFieldIndex('FCode')
    if index >= 0:
        if ogrfeature.GetField(index) in (33400, 44500, 33601, 36200, 36700, 41100, 50301, 50302, 45000):
            return None
        
    return ogrfeature

def filterTags(attrs):
    if not attrs:
        return
    tags = {}
    for k,v in attrs.iteritems():
        if k[0:10] not in ('AreaSqKm', 'ComID', 'FType', 'OBJECTID', 'Permanent_', 'Resolution', 
        'Shape_Area', 'Shape_Leng', 'Elevation', 'LengthKM', 'GNIS_Name', 'WBAreaComI', 'WBArea_Per', 
        'FeatureDet', 'Source_Fea', 'Enabled', 'FCode', 'FlowDir', '__LAYER'):
            if v != '':
                tags['nhd:'+k]=v
            
    try:
        if 'Elevation' in attrs and float(attrs['Elevation'].strip()) != 0.:
            tags['ele'] =  str(float(attrs['Elevation'].strip()))
    except ValueError:
        pass

    if 'GNIS_Name' in attrs and attrs['GNIS_Name'] != '':
        tags['name'] = attrs['GNIS_Name']
     
    if 'FeatureDet' in attrs and attrs['FeatureDet'] != '':
        tags['website'] = attrs['FeatureDet']
        
    if 'FeatureDetailURL' in attrs and attrs['FeatureDetailURL'] != '':
        tags['website'] = attrs['FeatureDetailURL']
    
    if 'FlowDir' in attrs and attrs['FlowDir'] == '0':
        tags['directional'] = 'no'
    
    if 'FCode' in attrs and attrs['FCode'] != '':
        tags['gnis:fcode'] = attrs['FCode'] # Remove for production
        
        if attrs['__LAYER'] == 'NHDFlowline':
            '''
            NHDFlowline Features
            '''
            if attrs['FCode'] == '55800':
                if 'name' in tags and 'river'.upper() in tags['name'].upper():
                    tags['waterway'] = 'river'
                else:
                    tags['waterway'] = 'stream'
            elif attrs['FCode'] == '33600':
                tags['waterway'] = 'ditch'
                if 'FlowDir' in attrs and attrs['FlowDir'] == '1':
                    tags['directional'] = 'yes'        
            elif attrs['FCode'] == '56600':
                tags['natural'] = 'coastline'
            elif attrs['FCode'] == '42803':
                tags['man_made'] = 'pipeline'
                tags['location'] = 'underground'
                tags['type'] = 'water'
            elif attrs['FCode'] == '42807':
                tags['man_made'] = 'pipeline'
                tags['location'] = 'underground'
                tags['type'] = 'water'
            elif attrs['FCode'] == '46000' or attrs['FCode'] == '46006':
                if 'name' in tags and 'river'.upper() in tags['name'].upper():
                    tags['waterway'] = 'river'
                else:
                    tags['waterway'] = 'stream'
          
            elif attrs['FCode'] == '46003':
                tags['waterway'] = 'stream'
                tags['intermittent'] = 'yes'
            else:
                tags['fixme'] = 'Unknown FCode in NHDFlowline: ' + attrs['FCode']
        elif attrs['__LAYER'] == 'NHDWaterbody':
            '''
            NHDWaterbody Features
            '''
            if attrs['FCode'] == '49300':
                tags['natural'] = 'water'
                tags['tidal'] = 'yes'
            elif attrs['FCode'] == '37800':
                tags['natural'] = 'glacier'
            elif attrs['FCode'] == '39000':
                tags['natural'] = 'water'
            elif attrs['FCode'] == '39001':
                tags['natural'] = 'water'
                tags['intermittent'] = 'yes'
                if 'name' in tags and 'lake'.upper() in tags['name'].upper():
                    tags['water'] = 'lake'
            elif attrs['FCode'] == '39004':
                tags['natural'] = 'water'
                tags['water'] = 'lake'
                if 'name' in tags and 'lake'.upper() in tags['name'].upper():
                    tags['water'] = 'lake'
            elif attrs['FCode'] == '39009':
                tags['natural'] = 'water'
                if 'name' in tags and 'lake'.upper() in tags['name'].upper():
                    tags['water'] = 'lake'
            elif attrs['FCode'] == '39010':
                tags['natural'] = 'water'
                if 'name' in tags and 'lake'.upper() in tags['name'].upper():
                    tags['water'] = 'lake'
            elif attrs['FCode'] == '36100':
                tags['natural'] = 'wetland'
                tags['wetland'] = 'dry_lake'
            elif attrs['FCode'] == '43600':
                tags['natural'] = 'water'
                tags['water'] = 'pond'
            elif attrs['FCode'] == '43601':
                tags['natural'] = 'water'
                tags['water'] = 'pond'
                tags['pond'] = 'aquaculture'
            elif attrs['FCode'] == '43603':
                tags['natural'] = 'water'
                tags['water'] = 'pool'
            elif attrs['FCode'] == '43609':
                tags['natural'] = 'water'
                tags['water'] = 'pond'
                tags['pond'] = 'cooling'
            elif attrs['FCode'] == '43610':
                tags['natural'] = 'water'
                tags['water'] = 'pond'
                tags['pond'] = 'filtration'
            elif attrs['FCode'] == '43611':
                tags['natural'] = 'water'
                tags['water'] = 'pond'
                tags['pond'] = 'settling'
            elif attrs['FCode'] == '43612':
                tags['natural'] = 'water'
                tags['water'] = 'pond'
                tags['pond'] = 'sewage'
            elif attrs['FCode'] == '43613':
                tags['natural'] = 'water'
                tags['water'] = 'pond'
                tags['pond'] = 'storage'
            elif attrs['FCode'] == '43614':
                tags['natural'] = 'water'
                tags['water'] = 'pond'
            elif attrs['FCode'] == '43617':
                tags['natural'] = 'water'
                tags['water'] = 'pond'
            elif attrs['FCode'] == '46600':
                tags['natural'] = 'wetland'
            elif attrs['FCode'] == '46601':
                tags['natural'] = 'wetland'
                tags['intermittent'] = 'yes'
            elif attrs['FCode'] == '46602':
                tags['natural'] = 'wetland'
            else:
                tags['fixme'] = 'Unknown FCode in NHDWaterbody: ' + attrs['FCode']
        elif attrs['__LAYER'] == 'NHDLine':
            if attrs['FCode'] == '34300':
                tags['waterway'] = 'dam'
            elif attrs['FCode'] == '34305':
                tags['waterway'] = 'dam'
                tags['dam'] = 'earth'
            elif attrs['FCode'] == '34306':
                tags['waterway'] = 'dam'
                tags['dam'] = 'artificial'
            elif attrs['FCode'] == '56800':
                tags['man_made'] = 'dyke'
            else:
                tags['fixme'] = 'Unknown FCode in NHDLine: ' + attrs['FCode']
        elif attrs['__LAYER'] == 'NHDPoint':
            if attrs['FCode'] == '44101':
                tags['natural'] = 'rock'
            elif attrs['FCode'] == '45800':
                tags['natural'] = 'spring'
            elif attrs['FCode'] == '48700':
                tags['waterway'] = 'waterfall'
            elif attrs['FCode'] == '48800':
                tags['man_made'] = 'water_well'
            else:
                tags['fixme'] = 'Unknown FCode in NHDPoint: ' + attrs['FCode']
        elif attrs['__LAYER'] == 'NHDArea':
            if attrs['FCode'] == '31200':
                tags['natural'] = 'bay'
            elif attrs['FCode'] == '33600':
                tags['natural'] = 'water'
            elif attrs['FCode'] == '34300':
                tags['waterway'] = 'dam'
                tags['area'] = 'yes'
            elif attrs['FCode'] == '34305':
                tags['waterway'] = 'dam'
                tags['area'] = 'yes'
                tags['dam'] = 'earth'
            elif attrs['FCode'] == '34306':
                tags['waterway'] = 'dam'
                tags['area'] = 'yes'
                tags['dam'] = 'artificial'
            elif attrs['FCode'] == '36400':
                tags['natural'] = 'beach'
            elif attrs['FCode'] == '40307':
                tags['natural'] = 'water'
                tags['intermittent'] = 'uncontrolled'
            elif attrs['FCode'] == '40308':
                tags['natural'] = 'water'
                tags['intermittent'] = 'controlled'
            elif attrs['FCode'] == '40309':
                tags['natural'] = 'water'
                tags['intermittent'] = 'flood'
            elif attrs['FCode'] == '43100':
                tags['waterway'] = 'rapids'
                tags['area'] = 'yes'
            elif attrs['FCode'] == '46000' or attrs['FCode'] == '46006':
                tags['waterway'] = 'riverbank'
            elif attrs['FCode'] == '46003':
                tags['natural'] = 'water'
                tags['intermittent'] = 'yes'
            elif attrs['FCode'] == '48400':
                tags['natural'] = 'water'
                tags['intermittent'] = 'yes'
                
            else:
                tags['fixme'] = 'Unknown FCode in NHDArea: ' + attrs['FCode']
        else:
            tags['fixme'] = 'Unknown FCode in ' + attrs['__LAYER'] + ': ' + attrs['FCode']
            
    '''
    Code is required to handle monitoring stations 
    '''
    return tags
    
