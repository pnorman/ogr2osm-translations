'''
A translation function for NHD data. 

The shapefiles are availble as PD from the USGS 
at ftp://nhdftp.usgs.gov/DataSets/Staged/SubRegions/PersonalGDB/HighResolution/
or ftp://nhdftp.usgs.gov/DataSets/Staged/SubRegions/FileGDB/HighResolution/

PersonalGDB files can be converted to shapefiles with a default Windows build of QGIS or gdal.

These files are very large and it may be desirable to cut them down to size first

http://nhd.usgs.gov/NHDDataDictionary_model2.0.pdf helps explain the definitions of some fields

The following fields are dropped from the source shapefile:

Field           Definition                  Reason
AreaSqKm        Area of feature             Duplicates geodata    
ComID           Unique ID of feature        Metadata
FDate           Date of last modification   Metadata
FType           Feature type                Duplication of FCode
OBJECTID        Object ID                   Metadata
Permanent_      40 character GUID           Metadata
Resolution      Resolution                  Metadata    
Shape_Area      Area of feature             Duplicates geodata
Shape_Leng      Length of feature           Duplicates geodata

The following fields are used:    

Field           Used for            Reason
Elevation       Elevation
FCode           Mapping to OSM tags
GNIS_Name       
GNIS_ID         
ReachCode       combining ways?

Internal mappings:

OSM Mappings
Source value                            OSM value                           Shortcomings

'''

def filterTags(attrs):
    if not attrs:
        return
    tags = {}
    
    for k,v in attrs.iteritems():
        if k not in ('AreaSqKm', 'ComID', 'FDate', 'FType', 'OBJECTID', 'Permanent_', 'Resolution', 'Shape_Area', 'Shape_Leng', 'Elevation'):
            tags['nhd:'+k]=v
            
    try:
        if 'Elevation' in attrs and float(attrs['Elevation'].strip()) != 0.:
            tags['ele'] =  float(attrs['Elevation'].strip())
    except ValueError:
        pass
        
        
    return tags
    