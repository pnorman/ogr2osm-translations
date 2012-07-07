'''
A translation function for DataBC TA_MUNICIP city data. 

'''

    
def filterTags(attrs):
    if not attrs:
        return
    if 'CODE' in attrs and attrs['CODE'] == 'MU':
        if 'MUN_NAME' in attrs:
            return { 'boundary':'administrative', 'admin_level':'8', 'source':'DataBC TA_MUNICIP', 'name':attrs['MUN_NAME'].title() }
        else:
            return { 'boundary':'administrative', 'admin_level':'8', 'source':'DataBC TA_MUNICIP' }
    
    return tags