'''
A translation function for NHD data. 

The shapefiles are availble as PD from the USGS 
at ftp://nhdftp.usgs.gov/DataSets/Staged/SubRegions/PersonalGDB/HighResolution/
or ftp://nhdftp.usgs.gov/DataSets/Staged/SubRegions/FileGDB/HighResolution/

PersonalGDB files can be converted to shapefiles with a default Windows build of QGIS or gdal.

See http://www.gdal.org/ogr/drv_mdb.html or http://www.gdal.org/ogr/drv_pgeo.html

These files are very large and it may be desirable to cut them down to size first

http://nhd.usgs.gov/NHDDataDictionary_model2.0.pdf helps explain the definitions of some fields

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
Shape_Leng      Length of feature           Duplicates geodata
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

OSM Mappings
Source value                            OSM value                           Shortcomings

'''

from osgeo import ogr

def filterLayer(layer):
    if not layer:
        return
    if layer.GetName() in ('NHDArea', 'NHDAreaEventFC', 'NHDFlowline', 'NHDLine', 
                    'NHDLineEventFC', 'NHDPoint', 'NHDPointEventFC', 'NHDWaterbody'):
        return layer
    elif layer.GetName() in ('WBD_HU10', 'WBD_HU12', 'WBD_HU14', 'WBD_HU16', 'WBD_HU2', 'WBD_HU4', 'WBD_HU6', 'WBD_HU8', 'HYDRO_NET_Junctions'):
        return
    else:
        print 'Unknown layer ' + layer.GetName()
        return layer

def filterTags(attrs):
    if not attrs:
        return
    tags = {}
    

    for k,v in attrs.iteritems():
        if k not in ('AreaSqKm', 'ComID', 'FDate', 'FType', 'OBJECTID', 'Permanent_', 'Resolution', 
        'Shape_Area', 'Shape_Leng', 'Elevation', 'LengthKM', 'GNIS_Name', 'WBAreaComI', 'WBArea_Per', 
        'FeatureDet', 'Source_Fea', 'Enabled', 'FCode'):
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
        
    if 'FCode' in attrs and attrs['FCode'] != '':
        tags['gnis:fcode'] = attrs['FCode']
        if attrs['FCode'] == '55800':
            if 'name' in tags and 'river'.upper() in tags['name'].upper():
                tags['waterway'] = 'river'
            else:
                tags['waterway'] = 'stream'
        else:
            tags['fixme'] = 'Unknown FCode ' + attrs['FCode']
            
    return tags
    