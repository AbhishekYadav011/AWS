import requests


def project_details(accountId, apiKey):
    api_url = 'https://endpoint_url/c0030_log_hyperscaler_accounts/_search'
    my_headers = {'Authorization': apiKey, 'Content-Type': 'application/json'}
    get_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "accountID.keyword": accountId
                            }
                        }
                    ]
                }
            }
        }
    response = requests.get(api_url, headers=my_headers, json=get_query).json()
    if response['hits']['hits']:
        return response['hits']['hits'][0]['_source']['name'], response['hits']['hits'][0]['_source']['lob'], response['hits']['hits'][0]['_source']['environment']
    else:
        return "None", "None", "None"
