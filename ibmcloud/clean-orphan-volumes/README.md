#How to use

run this script using python 3

input your IBM classic infrastructure API key

the script can take a while to run (5-10 minutes).

It works by making a request against IBM Cloud's api to get a list of all clusters on the account. Next, it gets a list of all storage volumes in 'classic infrastructure'. This is where volumes from standard ROKS storage classes are provisioned.

It then checks all of the storage volumes for a tagged cluster id. If the volume has a clusterID that isn't on the list of active clusters, it's put into a list to suggest for deletion. The script only tracks volumes that DO have a a cluster ID, if there isn't one listed it will skip the VM.

The script will print a list of all orphan storage volume IDs it found. You can look up these IDs in the classic infrastructure view online. If it doesn't print a list, it didn't find any. It will prompt you to enter 'delete'- if you don't type 'delete' exactly the deletion will be canceleled and the script will exit.
