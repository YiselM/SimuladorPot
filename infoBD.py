import time
from datetime import datetime
import json
import mysql.connector
import requests

mydb = mysql.connector.connect(
   host="db4free.net",
   user="baenav",
   passwd="qwertyuiop",
   database="proyecto_diseno"
)

mycursor = mydb.cursor()

def SendData(mycursor,mydb):     
     now = datetime.now()
     fecha = now.strftime('%Y-%m-%d')
     hora = time.strftime("%H:%M")
     rv = requests.get('https://api.weather.com/v2/pws/observations/current?stationId=IATLNTIC4&format=json&units=m&apiKey=2538e347f5254da8b8e347f5258da83d')
     resultadov = rv.json()
     viento = (resultadov['observations'][0]['metric']['windSpeed'])*(10/36) #obtengo el viento   
     rr = requests.get('https://api.weather.com/v2/pws/observations/current?stationId=IPUERTOC4&format=json&units=m&apiKey=2538e347f5254da8b8e347f5258da83d')
     resultador = rr.json()
     radiacion = resultador['observations'][0]['solarRadiation'] #obtengo la radiacion 
     
     #Para la carga
     if (hora > "%0:%00" and hora <= "%5:%00"):
        Pcarga = 15
        #print(Pcarga) 
     if ((hora >= "%5:%00") and (hora <= "23:%20")):
        Pcarga = 83
        #print(Pcarga)
     if (hora > "23:%20" and hora <= "%0:%00"):
        Pcarga = 15
        #print(Pcarga) 
     #Para el panel
     np = 0.13
     area = 1.31
     Ppanel = radiacion*np*area
     Ppanel = round(Ppanel, 2)
     #print(Ppanel)
     #Para el generador
     if (viento < 4 or viento > 14):
        Pem = 0 
     else:
        Pem = (0.001723483*((viento)**6) - 0.04935507*((viento)**5) + 0.01124858*((viento)**4) + 12.34628*((viento)**3) - 144.3604*((viento)**2) + 657.3997*viento - 1038.827)*(5 / 60)
     Pem = Pem/10
     Pem = round(Pem, 2)
     #print(Pem)
     #Para la red
     ng = 0.554
     nred = 0.448
     nbat = 0.8
     Pred = (Pcarga - Ppanel*np - Pem*ng)/nred
     Pred = round(Pred, 2)
     #print(Pred)
     #Para la bateria y el estado
     if (Pred < Pcarga):
        Estado = 1
        Pbat = 0
     if (Pred <= 0):
        Estado = 2
        Pbat = 0
     if (Pred > 0 and Pred < Pcarga):
        Estado = 1
        Pbat = 0
     if (Pred > Pcarga):
        Pbat = 15/nbat
        Pbat = round(Pbat, 2)
        Estado = 4

     #print(Pbat)
     #print(Estado)
     sql = "INSERT INTO datos (P1, P2, P3, P4, P5, fecha, hora, estado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
     val = (Pred, Ppanel, Pbat, Pcarga, Pem, fecha, hora, Estado)
    #print(val)
     mycursor.execute(sql, val)
     mydb.commit()
     print("Subido")
#    time.sleep(1) 



inicio = time.time()
while True: 
     tiempo = (time.time() - inicio)
     tiempo = round(tiempo,2)
     if (tiempo >= 300): # cada 300 segundos que actualice la lectura del json
        print("Sending")   
        SendData(mycursor,mydb)
        inicio = time.time()

