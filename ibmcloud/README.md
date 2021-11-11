Requires python version > 3.8

This folder contains our automation for cleaning up IBM cloud clusters.

This is a tag-based cleaner, which requires tagging at the cluster level only. All clusters that aren't production need to be tagged with a time-to-live tag, or TTL for short. A valid tag is formatted like this- "ttl:{x}d", where {x} is some number of days. a common example- "ttl:30d"

All production clusters should be tagged with 'env:production', and do not require a ttl tag.

I've scheduled this as a cronjob on our machine to run M-F at 8AM using the following crontab entry-

0 8 * * 1-5 cd /root/cloud-platforms-admin/ibmcloud && /usr/local/bin/python3.8 cleanExpiredClusters.py > /root/logs/ibm/cleanlog.txt 2>&1

There is a config.yaml file that needs to be set up in order to run this script. You only have to set up what you will use- meaning if you don't set mailalerts or slackalerts to TRUE you don't have to bother setting up those config entries.

currently, only Gmail addresses have been tested. Your gmail account will need to be configured to allow SMTP access. SLACKBOTCHANNEL needs to be set to the name of a slack channel, WITHOUT a '#'.

This repo also contains a folder that allows you to clean up orphaned storage volumes. This should be ran every time a cluster is deleted using terraform. The instructions are located in a README in the folder

CANCEL DELETIONS

Deletions are set to happen 3 hours after the script starts and posts the list to slack. This is supposed to give admins time to see the list, and cancel deletions if there are clusters that you would like to save.

To cancel a pending deletion- log onto the machine running the scripts, and edit the config.yaml file. Set IBMDELETE to FALSE.
