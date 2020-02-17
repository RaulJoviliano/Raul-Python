import requests
import os
import slack
import sys
import json
import time
import calendar
from datetime import datetime
import base64
from pymongo import *
import smtplib

###Raul changes####

def sending_email(escalated_count, ticket_id, sev):
    smtp_server = "us.relay.ibm.com"
    source_email = "EMAIL@BLA.COM" # From
    destination_emails = [email_contact , escalate_contact_1 , escalate_contact_2]  # Enter receiver address


    if int(sev) < 2:
        message = f"""\
Subject: [EMERGENCY - SEV 1] {ticket_id} 
Oncall {oncall_person}\nBackup {backup_person}\n\n{ticket_id} has been escalated {escalated_count} times and no action was done in the ticket so far. 
Its a SEV-1, please work on it ASAP as priority. """

    if int(sev) > 1:
        message = f"""\
Subject: [Action Required] {ticket_id} 
Oncall {oncall_person}\nBackup {backup_person}\n\n{ticket_id} is escalated now, this ticket has been on DevOps queue for a while. Please check it ASAP."""

    server = smtplib.SMTP(smtp_server)
    server.starttls()
    server.sendmail(source_email, destination_emails, message,)
    server.quit()

def db_connection(row):
    try:
        mc = MongoClient()
        t = mc.fila
        c = t.bios
        already_exist = False
        escalated_count = 0
        print("Connected Succesfully")
    except:
        print("Could not connect to MongoDB")

    for docfound in c.find ( {} ):
        if  row == docfound['ticket_id']:
            already_exist = True
            c.replace_one({"ticket_id" : row}, { 'ticket_id': docfound['ticket_id'],
                            'date_time':  docfound['date_time'], 
                            'owner': docfound['owner'],
                            'sev': docfound['sev'],
                            'escalated': docfound['escalated'] + 1 } )  
            ##Return Escalated Number
            return(docfound['escalated'] + 1)  

    if already_exist == False:
        c.insert_many( [ { 'ticket_id': ticket_id,
                            'date_time': data_e_hora_em_texto, 
                            'owner': contact_name,
                            'sev': sev,
                            'escalated': escalated_count } ] )
        return 0

### Creating string for the date and time
data_e_hora_em_texto = time.strftime('%d/%m/%Y %H:%M')

### Opening JsonFile and saving it into obj data
with open('oncall_file.json') as json_file:
    data = json.load(json_file) 

### Getting the name of the current day
day_name = datetime.today().strftime('%A')

### Getting the country working right now
now = datetime.now()
today4_30 = now.replace(hour=4,minute=30,second=0, microsecond=0)
today10_30 = now.replace(hour=10, minute=30, second=0, microsecond=0)
today16_30 = now.replace(hour=16, minute=30, second=0, microsecond=0)
today22_30 = now.replace(hour=22, minute=30, second=0, microsecond=0)
country = ""

if now < today4_30:
    country="China"
elif today4_30 < now < today10_30:
    country="Romania"
elif today10_30 < now < today16_30:
    country="Brazil"
elif today16_30 < now < today22_30:
    country="Mexico"
elif now > today22_30:
    country="China"

### Checking if its lunch time to contact the backup
start_lunch_brazil = now.replace(hour=12, minute=0, second=0, microsecond=0)
end_lunch_brazil = now.replace(hour=13, minute=0, second=0, microsecond=0)
start_lunch_mexico = now.replace(hour=18, minute=0, second=0, microsecond=0)
end_lunch_mexico = now.replace(hour=19, minute=0, second=0, microsecond=0)
start_lunch_romania = now.replace(hour=6, minute=0, second=0, microsecond=0)
end_lunch_romania = now.replace(hour=7, minute=0, second=0, microsecond=0)
start_lunch_china = now.replace(hour=0, minute=0, second=0, microsecond=0)
end_lunch_china = now.replace(hour=1, minute=0, second=0, microsecond=0)
backup=False
contact_name=""

if start_lunch_china < now < end_lunch_china:
    backup=True
elif start_lunch_romania < now < end_lunch_romania:
    backup=True
elif start_lunch_brazil < now < end_lunch_brazil:
    backup=True
elif start_lunch_mexico < now < end_lunch_mexico:
    backup=True

### Getting the oncall person or backup
oncall_person = ""
backup_person = ""
oncall_email = ""
backup_email = ""
escalate_contact_1=""
escalate_contact_2=""
for people in data['fila']:
    ### Getting escalated people
    if (escalate_contact_1 == "" or escalate_contact_2 == ""):
        for escalate in people['email_to_escalate']:
            escalate_contact_1=escalate['email_contact']
            escalate_contact_2=escalate['email_backup']

    for info in people['infos']:
        if people['country']==country and info['day_of_week']==day_name:
            for oncall in info['oncall']:
                oncall_person=str(oncall['name'])
                oncall_email=str(oncall['email'])
            for oncall in info['backup']:
                backup_person=str(oncall['name'])
                back_email=str(oncall['email'])        

if backup==False:
    contact_name=oncall_person
    email_contact=oncall_email
else:
    contact_name=backup_person
    email_contact=backup_email

client = slack.WebClient(token=os.environ['slack_token'])
resp = requests.get('https://icdha.edst.ibm.com/maxrest/rest/os/mxproblem/?OWNER=devopsru@mx1.ibm.com&STATUS=QUEUED&_format=json', auth=('EMAIL DE ENTRADA', os.environ['icd_password']))

print ("[PROBLEM] -> " + str (resp.json()['QueryMXPROBLEMResponse']['rsCount']))
if (resp.json()['QueryMXPROBLEMResponse']['rsCount']) >= 1:
    aux = resp.json()['QueryMXPROBLEMResponse']['MXPROBLEMSet']['PROBLEM']
    for row in aux:
        ticket_id = str(row['Attributes']['TICKETID']['content'])
        sev = str(row['Attributes']['INTERNALPRIORITY']['content'])

        ##Calling db_connection()
        escalated_count = db_connection(ticket_id)

        if (escalated_count == None):
            escalated_count = 0

        if escalated_count == 0:
            ### Applying Sev changes
            if int(sev) < 2:
                client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@here @"+ contact_name +" [PROBLEM " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
                client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@here @"+ contact_name +" [PROBLEM " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
            else:
                client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@"+ contact_name + "[PROBLEM " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
        elif escalated_count == 2 and sev > str(1):
            client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@"+ contact_name + "[PROBLEM " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
        elif escalated_count == 4 and sev > str(1):
            sending_email(escalated_count, ticket_id, sev)
        elif escalated_count > 3 and sev < str(2):
            sending_email(escalated_count, ticket_id, sev)


resp2 = requests.get('https://icdha.edst.ibm.com/maxrest/rest/os/mxsr/?OWNER=devopsru@mx1.ibm.com&STATUS=QUEUED&_format=json', auth=('EMAIL DE ENTRADA', os.environ['icd_password']))
print ("[SR] -> " +  str (resp2.json()['QueryMXSRResponse']['rsCount']))
if (resp2.json()['QueryMXSRResponse']['rsCount']) >= 1:
    aux = resp2.json()['QueryMXSRResponse']['MXSRSet']['SR']
    for row in aux:
        ticket_id = str(row['Attributes']['TICKETID']['content'])
        sev = str(row['Attributes']['INTERNALPRIORITY']['content'])
        
        ##Calling db_connection()
        escalated_count = db_connection(ticket_id)

        if (escalated_count == None):
            escalated_count = 0

        if escalated_count == 0:
            ### Applying Sev Changes
            if int(sev) < 2:
                client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@here @" + contact_name +"[SR " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
                client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@here @" + contact_name + "[SR " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
            else:
                client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@" + contact_name + " [SR " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
        elif escalated_count == 2 and sev > str(1):
            client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@" + contact_name + "[SR " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
        elif escalated_count == 4 and sev > str(1):
            sending_email(escalated_count, ticket_id, sev)
        elif escalated_count > 3 and sev < str(2):
            sending_email(escalated_count, ticket_id, sev)
            
resp3 = requests.get('https://icdha.edst.ibm.com/maxrest/rest/os/mxincident/?OWNER=devopsru@mx1.ibm.com&STATUS=QUEUED&_format=json', auth=('EMAIL DE ENTRADA', os.environ['icd_password']))
print ("[INCIDENT] -> " + str (resp3.json()['QueryMXINCIDENTResponse']['rsCount']))
if (resp3.json()['QueryMXINCIDENTResponse']['rsCount']) >= 1:
    aux = resp3.json()['QueryMXINCIDENTResponse']['MXINCIDENTSet']['INCIDENT']
    for row in aux:
        ticket_id = str(row['Attributes']['TICKETID']['content'])
        sev = str(row['Attributes']['INTERNALPRIORITY']['content'])
        
        ##Calling db_connection()
        escalated_count = db_connection(ticket_id)

        if (escalated_count == None):
            escalated_count = 0

        if escalated_count == 0:
            ### Applying Sev Changes
            if int(sev) < 2:
                client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@here @" + contact_name + " [INCIDENT " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
                client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@here @" + contact_name + " [INCIDENT " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
            else:
                client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@" + contact_name + " [INCIDENT " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
        elif escalated_count == 2 and sev > str(1):
            client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@" + contact_name + " [INCIDENT " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
        elif escalated_count == 4 and sev > str(1):
            sending_email(escalated_count, ticket_id, sev)
        elif escalated_count > 3 and sev < str(2):
            sending_email(escalated_count, ticket_id, sev)

resp4 = requests.get('https://icdha.edst.ibm.com/maxrest/rest/os/mxoschange/?OWNER=devopsru@mx1.ibm.com&STATUS=QUEUED&_format=json', auth=('EMAIL DE ENTRADA', os.environ['icd_password']))

print ("[CHANGE] -> " + str (resp4.json()['QueryMXOSCHANGEResponse']['rsCount']))
if (resp4.json()['QueryMXOSCHANGEResponse']['rsCount']) >= 1:
    aux = resp4.json()['QueryMXOSCHANGEResponse']['MXOSCHANGESet']['OSCHANGE']
    for row in aux:
        ticket_id = str(row['Attributes']['TICKETID']['content'])
        sev = str(row['Attributes']['INTERNALPRIORITY']['content'])
        
        ##Calling db_connection()
        escalated_count = db_connection(ticket_id)

        if (escalated_count == None):
            escalated_count = 0

        if escalated_count == 0:
            ### Applying Sev Changes
            if int(sev) < 2:
                client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@here @" + contact_name + " [CHANGE " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
                client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@here @" + contact_name + " [CHANGE " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
            else:           
                client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@" + contact_name + " [CHANGE " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
        elif escalated_count == 2 and sev > str(1):
            client.chat_postMessage(
                link_names=1,
                channel="CHANNEL NAME",
                text="@" + contact_name + " [CHANGE " + ticket_id + " SEV " + sev + "] found on DevOps Queue, please check!"
                )
        elif escalated_count == 4 and sev > str(1):
            sending_email(escalated_count, ticket_id, sev)
        elif escalated_count > 3 and sev < str(2):
            sending_email(escalated_count, ticket_id, sev)