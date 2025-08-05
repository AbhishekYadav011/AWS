import requests


def datacenter_name(region, secret):
    if region == 'us-east-1':
        longitude, latitude = get_geo_data('AWS US East N. Virginia', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS US East N. Virginia', geo_location
    if region == 'us-east-2':
        longitude, latitude = get_geo_data('AWS US East Ohio', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS US East Ohio', geo_location
    if region == 'us-west-1':
        longitude, latitude = get_geo_data('AWS US West N. California', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS US West N. California', geo_location
    if region == 'us-west-2':
        longitude, latitude = get_geo_data('AWS US West Oregon', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS US West Oregon', geo_location
    if region == 'ap-east-1':
        longitude, latitude = get_geo_data('AWS: Asia Pacific Hong Kong', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS: Asia Pacific Hong Kong', geo_location
    if region == 'ap-south-1':
        longitude, latitude = get_geo_data('AWS Asia Pacific Mumbai', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS Asia Pacific Mumbai', geo_location
    if region == 'ap-northeast-3':
        longitude, latitude = get_geo_data('AWS Asia Pacific Osaka-Local', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS Asia Pacific Osaka-Local', geo_location
    if region == 'ap-northeast-2':
        longitude, latitude = get_geo_data('AWS Asia Pacific Seoul', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS Asia Pacific Seoul', geo_location
    if region == 'ap-southeast-1':
        longitude, latitude = get_geo_data('AWS Asia Pacific Singapore', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS Asia Pacific Singapore', geo_location
    if region == 'ap-southeast-2':
        longitude, latitude = get_geo_data('AWS Asia Pacific Sydney', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS Asia Pacific Sydney', geo_location
    if region == 'ap-northeast-1':
        longitude, latitude = get_geo_data('AWS Asia Pacific Tokyo', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS Asia Pacific Tokyo', geo_location
    if region == 'ca-central-1':
        longitude, latitude = get_geo_data('AWS Canada Central', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS Canada Central', geo_location
    if region == 'eu-central-1':
        longitude, latitude = get_geo_data('AWS EU Frankfurt', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS EU Frankfurt', geo_location
    if region == 'eu-west-1':
        longitude, latitude = get_geo_data('AWS EU Ireland', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS EU Ireland', geo_location
    if region == 'eu-west-2':
        longitude, latitude = get_geo_data('AWS EU London', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS EU London', geo_location
    if region == 'eu-west-3':
        longitude, latitude = get_geo_data('AWS EU Paris', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS EU Paris', geo_location
    if region == 'eu-north-1':
        longitude, latitude = get_geo_data('AWS: EU Stockholm', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS: EU Stockholm', geo_location
    if region == 'sa-east-1':
        longitude, latitude = get_geo_data('AWS South America Sao Paulo', secret)
        geolist = [latitude,longitude]
        geo_location = ",".join([str(i) for i in geolist])
        return 'AWS South America Sao Paulo', geo_location
    return region, '0,0'



def get_geo_data(region, secret):
    apikey = secret.get('elkapikey_euw4')
    api_url = 'https://endpoint_url/c_log_hyperscaler_geolocations/_search'
    my_headers = {'Authorization': apikey, 'Content-Type': 'application/json'}
    get_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "dc_name.keyword": region
                        }
                    }

                ]

            }
        }
    }
    response = requests.get(api_url, headers=my_headers, json=get_query).json()
    return response["hits"]["hits"][0]['_source']['longitude'], response["hits"]["hits"][0]['_source']['latitude']