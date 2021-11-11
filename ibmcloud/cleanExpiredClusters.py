import datetime
import re
import time

from cleanHelper import IBMApiCallingClass, Messenger

ibmApiCaller = IBMApiCallingClass()

#list of clusters that have TTL tags
clusterTtlList = []
#lists of clusters that will be deleted soon
clusterDeletionList = []
clustersDeletingTomorrow = []
#all clusters that don't have a valid TTL tag need to be on a list
invalidTtlList = []

#checks all clusters to see if they have a valid TTL
for cluster in ibmApiCaller.getClusterList():
    has_ttl = False
    prod = False

    #if cluster has a tag which contains the string 'production', it will never be flagged for deletion
    for item in cluster['tags']['items']:
        if 'production' in item['name']:
            prod = True

    #all clusters not in production are checked for a TTL tag
    if not prod:
        for item in cluster['tags']['items']:
            #if cluster has a 'ttl' tag, add it to list
            if 'ttl:' in item['name']:
                cluster['ttl'] = item['name'].split(':')[1]
                clusterTtlList.append(cluster)
                has_ttl = True
                break
        #all clusters that don't have any TTL tag and aren't in production will be deleted after one day
        if not has_ttl:
            #this calculation returns a timedelta object that tells us how long ago the cluster was created
            delta = datetime.datetime.now() - datetime.datetime.fromisoformat(cluster['createdDate'][:-5])
            #if cluster is at least a day old, put in deletion list
            if delta.days >= 1:
                clusterDeletionList.append(cluster)
            else:
                clustersDeletingTomorrow.append(cluster)

#regex pattern that determines if a ttl tag is valid
#a valid TTL tag has the format "ttl:{x}d" where {x} is a number of days
#a space in between is optional
pattern = re.compile("\s?\d+\s?d")

#check to see if clusters with a TTL tag are due for deletion, or that the TTL tag is valid
for cluster in clusterTtlList:
    #this calculation returns a timedelta object that tells us how long ago the cluster was created
    delta = datetime.datetime.now() - datetime.datetime.fromisoformat(cluster['createdDate'][:-5])

    #get the days to live from ttl tag
    if pattern.match(cluster['ttl']):
        daysToLive = int(cluster['ttl'][:-1])
    else:
        print("invalid ttl on cluster: " + cluster['name'])
        #if a cluster has an invalid ttl tag, give it 3 days to be fixed
        invalidTtlList.append(cluster)
        daysToLive = 3

    #if a cluster will be deleted today or tommorow, add it to the appropriate list
    if delta.days == daysToLive:
        clustersDeletingTomorrow.append(cluster)
    elif delta.days > daysToLive:
        clusterDeletionList.append(cluster)

#if any of the lists are populated, send messages through appropriate channels, and potentially delete
if clustersDeletingTomorrow or clusterDeletionList or invalidTtlList:
    messenger = Messenger()

    #format a message with all clusters flagged for action
    now = datetime.datetime.now()
    messageContent = '\n'.join(['-----------------------------------------------------------------',
        f'{now}',
        'clusters to delete tomorrow:',
        '\n'.join([cluster['name'] for cluster in clustersDeletingTomorrow]),
        'clusters being deleted today:',
        '\n'.join([cluster['name'] for cluster in clusterDeletionList]),
        'clusters with an invalid TTL tag:',
        '\n'.join([cluster['name'] for cluster in invalidTtlList]),
        'todays deletions, if applicable, are now SCHEDULED to take place in 3 hours. To cancel, please log into the cleaner VM and set (in ibmcloud/config.yaml)- "IBMDELETE" to "FALSE". Changing tags on cluster alone WILL NOT cancel deletion',
        'If you dont have access to this VM, please get in contact with cloud platform admins at #cpat-cloud-platforms-admin on slack'])

    messenger.postMessages(messageContent)

    #if cluster_deletion_list has any clusters listed, delete all of them.
    if clusterDeletionList:
        #sleep 3 hours. This gives an admin time to change IBMDELETE and cancel deletions if they want to save a cluster
        time.sleep(10800)

        #deletes clusters, and posts list of responses to messaging channels
        messageContent = ibmApiCaller.deleteClusters(clusterDeletionList)
        messenger.postMessages(messageContent)

else:
    print(datetime.datetime.now())
    print('no deletions scheduled')
