'''
A translation function for TIGER 2012 counties
'''

def filterTags(attrs):
    if not attrs:
        return
    tags = {}
    tags['boundary'] = 'administrative'
    tags['admin_level'] = '6'
    # Names
    if 'NAME' in attrs:
        tags['name'] = attrs['NAME']
    if 'NAMELSAD' in attrs:
        tags['official_name'] = attrs['NAMELSAD']

    # FIPS codes
    if 'STATEFP' in attrs:
        tags['nist:state_fips'] = attrs['STATEFP']
        if 'COUNTYFP' in attrs:
            tags['nist:fips_code'] = attrs['STATEFP'] + attrs['COUNTYFP']

    return tags