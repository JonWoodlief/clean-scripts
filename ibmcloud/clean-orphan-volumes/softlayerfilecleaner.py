import SoftLayer
import json
import os
import requests

apikey = input('Please enter IBM Cloud classic infrastructure api key: ')
print('loading...')

iam_api_url = 'https://iam.cloud.ibm.com/identity/token'
iam_api_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
iam_payload = {'grant_type': 'urn:ibm:params:oauth:grant-type:apikey', 'apikey': apikey}

token = requests.post(iam_api_url, headers=iam_api_headers, data=iam_payload).json()
auth_headers = {"authorization": ' '.join([token['token_type'], token['access_token']])}

client = SoftLayer.create_client_from_env(username='apikey', api_key=apikey)

fileman = SoftLayer.FileStorageManager(client)

ids = [volume['id'] for volume in fileman.list_file_volumes()]

ks_api_url = 'https://containers.cloud.ibm.com/global/v1/clusters'
cluster_json = requests.get(ks_api_url, headers=auth_headers).json()

cluster_volume_ids = [cluster['id'] for cluster in cluster_json]
cluster_id_name_map = {cluster['id']: cluster['name'] for cluster in cluster_json}

volumes_to_delete = []
for volume_id in ids:
    name = client.call('SoftLayer_Network_Storage', 'getObject', id=volume_id)['username']
    try:
        cluster_id = json.loads(client.call('SoftLayer_Network_Storage', 'getObject', id=volume_id)['notes'])['cluster']
        if cluster_id not in cluster_volume_ids:
            #print(f'volume "{name}" belongs to deleted cluster "{cluster_id}"')
            volumes_to_delete.append(volume_id)
        else:
            cluster_name = cluster_id_name_map[cluster_id]
            #print(f'volume "{name}" belongs to live cluster "{cluster_id}" with name {cluster_name}')
    except KeyError as e:
        #print(f'Key Error (volume "{name}" doesnt have key {e}')
        pass
    except ValueError as e:
        #print(f'Value Error volume {name} - {e})
        pass

print('These are all volume IDs to be deleted: ')
[print(id) for id in volumes_to_delete]
print('enter "delete" to delete all listed volumes: ')
if input() == 'delete':
    for id in volumes_to_delete:
        try:
            fileman.cancel_file_volume(id, f'automated cleanup for cluster {cluster_id}', immediate=True)
        except SoftLayer.exceptions.SoftLayerError as e:
            print(f'volume id: {id} failed to delete, error: {e}')
