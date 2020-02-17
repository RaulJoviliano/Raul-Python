# Step one for every Python app that talks over the web
import requests
import sys
import time

resp = requests.get('https://jsonplaceholder.typicode.com/todos/')

if resp.status_code != 200:
    #It means something went wrong
        raise ApiError('GET /todos/ {}'.format(resp.status_code))

dados = open("dados.txt", "a")
consulta = open("consulta.txt", "a")
num_consulta = 0
data_e_hora_em_texto = time.strftime('%d/%m/%Y %H:%M')

for user in resp.json():
    if (user['userId'] == 10 and user['completed'] == True):
        print("{\"userId\": \""+str(user['userId'])+"\"}")
        dados.write("{\"userId\": \""+str(user["userId"])+"\"}" + " {\"completed\": \""+str(user["completed"])+"\"}"+"\n")
        num_consulta = num_consulta + 1

consulta.write("{Data: "+ data_e_hora_em_texto +"}" + " {Resposta da consulta: " + str(resp.status_code) + "}"+ " {Numero de consulta: "+ str(num_consulta) +"}"+ "\n")

dados.close()