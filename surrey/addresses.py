'''
Translation rules for the Surrey Addresses.

Copyright 2010-2012 Paul Norman. 

'''

affixlookup = {
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
    'Fg':'Frontage Road',

    'E':'East',
    'S':'South',
    'N':'North',
    'W':'West'
}

def filterFeature(ogrfeature, fieldNames, reproject):
    if not ogrfeature: return

    index = ogrfeature.GetFieldIndex('STATUS')
    if index >= 0:
        if ogrfeature.GetField(index) in ('History', 'For Construction', 'Proposed'):
            return None
    return ogrfeature

def filterTags(attrs):
    if not attrs: return

    tags = {}

    if 'HOUSE_NO' in attrs:
        tags['addr:housenumber'] = attrs['HOUSE_NO'].strip(' ')

    # This assumes every address will have a road name
    tags['addr:street'] = ' '.join([affixlookup.get(part.title(), part) for part in attrs['ROAD_NAME'].split()])

    #Add city-wide addressing info
    tags['addr:city'] = 'Surrey'

    # BLDG_PRMT, if > about 1986, should indicate when the address was assigned and the house built. 
    # It isn't reliable enough to blindly copy to start_date even when >1986
    if 'BLDG_PRMT' in attrs:
        tags['surrey:permit_date'] = attrs['BLDG_PRMT'].strip(' ')

    if tags['addr:housenumber'].strip() == '' or  tags['addr:street'].strip() == '':
        raise Exception('Invalid address found with ' + str(attrs))

    return tags
