import requests
import yaml
import smtplib

from slack import WebClient
from slack.errors import SlackApiError

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class MailAlertsClass:
    def __init__(self, config):
        self.senderAddress = config['EMAILADDRESS']
        self.senderPass = config['EMAILPASS']
        self.receiverAddress = config['MAILRECIPIENT']

    def sendMail(self, mailContent):

        message = MIMEMultipart()
        message['From'] = self.senderAddress
        message['To'] = self.receiverAddress
        message['Subject'] = 'IBM Cloud CPAT Account Cluster deletion list'
        message.attach(MIMEText(mailContent, 'plain'))

        session = smtplib.SMTP('smtp.gmail.com', 587)
        session.starttls()
        session.login(self.senderAddress, self.senderPass)
        text = message.as_string()

        session.sendmail(self.senderAddress, self.receiverAddress, text)

        session.quit()

        print('Mail Sent')

class SlackAlertsClass:
    def __init__(self, config):
        self.token= config['SLACKBOTTOKEN']
        self.client = WebClient(token=self.token)
        self.channel='#' + config['SLACKBOTCHANNEL']

    def postSlack(self, postContent):
        response = self.client.chat_postMessage(channel=self.channel, text=postContent)
        assert response["message"]["text"] == postContent 

        print('slack message posted')

class IBMApiCallingClass:
    def __init__(self):
        with open(r'config.yaml') as configFile:
            config = yaml.load(configFile, Loader=yaml.FullLoader)

        ibm_api_key = config['IBMAPIKEY']

        self.iam_api_url = 'https://iam.cloud.ibm.com/identity/token'
        self.ks_api_url = 'https://containers.cloud.ibm.com/global/v1/clusters'
        self.tags_api_url = 'https://tags.global-search-tagging.cloud.ibm.com/v3/tags?attached_to='

        self.iam_api_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        self.iam_payload = {'grant_type': 'urn:ibm:params:oauth:grant-type:apikey', 'apikey': ibm_api_key}

    #retrieves OAUTH token from IBM IAM API
    def __getToken__(self):
        return requests.post(self.iam_api_url, headers=self.iam_api_headers, data=self.iam_payload).json()
    
    def __getAuthHeaders__(self):
        token = self.__getToken__()

        return {"authorization": ' '.join([token['token_type'], token['access_token']])}

    def getClusterList(self):
        authHeaders = self.__getAuthHeaders__()

        #gets list of clusters and information about those clusters in json format
        clusterJson = requests.get(self.ks_api_url, headers=authHeaders).json()

        #creates a list of Dicts where each entry represents all needed data about a single cluster
        clusterList = [{'name': cluster['name'], 'id': cluster['id'], 'crn': cluster['crn'], 'createdDate': cluster['createdDate'], 'resourceGroup': cluster['resourceGroup']} for cluster in clusterJson]

        #adds tags
        for cluster in clusterList:
            cluster['tags'] = requests.get(self.tags_api_url + cluster['crn'], headers=authHeaders).json()

        return  clusterList

    def deleteClusters(self, clusterList):
        with open(r'config.yaml') as configFile:
            config = yaml.load(configFile, Loader=yaml.FullLoader)

        auth_headers = self.__getAuthHeaders__()
           
        #if IBMDELETE is true, delete all clusters
        if config['IBMDELETE']:
            #delete all clusters and add response to list
            responses = []
            for cluster in clusterList:
                resource_group_header = {'X-Auth-Resource-Group': cluster['resourceGroup']}
                deleteResponse = requests.delete(''.join([self.ks_api_url, '/', cluster['id'], '?deleteResources=true']), headers={**auth_headers, **resource_group_header})
                responses.append(f'{cluster["name"]}: {deleteResponse}')
            return '\n'.join(responses)
        else:
            return 'IBMDELETE wasnt set to TRUE, todays deletion CANCELLED'


class Messenger:
    def __init__(self):
        #load config from yaml
        with open(r'config.yaml') as configFile:
            config = yaml.load(configFile, Loader=yaml.FullLoader)

        #build a list of functions that want to receive messages
        self.messageFuncs = [print]
        if config['IBMMAILALERT']:
            self.messageFuncs.append(MailAlertsClass(config).sendMail)
        if config['IBMSLACKALERT']:
            self.messageFuncs.append(SlackAlertsClass(config).postSlack)
            
    def postMessages(self, messageContent):
        #send message to all functions listed in messageFuncs
        for func in self.messageFuncs:
            func(messageContent)
