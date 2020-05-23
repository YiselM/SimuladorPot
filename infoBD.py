import time
from datetime import datetime
import json
import mysql.connector
import requests

mydb = mysql.connector.connect(
   host="database-1.cbelsi1ervaq.us-east-1.rds.amazonaws.com",
   user="adminpardo",
   passwd="Pfestacion123!",
   database="nodo"
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
     Pesenciales = 15
     Pnoesenciales = 68

     if ((hora >= "00:00") and (hora <= "05:00")):
        Pcarga = 15
     if ((hora >= "05:00") and (hora <= "23:20")):
        Pcarga = 83
     if ((hora >= "23:20") and (hora <= "00:00")):
        Pcarga = 15

     #Para el panel
     eficienciap = 0.13
     area = 1.31
     Ppanel = radiacion*eficienciap*area
     Ppanel = round(Ppanel, 2)
     
     #Para el generador
     if (viento < 4 or viento > 14):
        Pem = 0 
     else:
        Pem = (0.001723483*((viento)**6) - 0.04935507*((viento)**5) + 0.01124858*((viento)**4) + 12.34628*((viento)**3) - 144.3604*((viento)**2) + 657.3997*viento - 1038.827)*(5 / 60)
     Pem = Pem/10
     Pem = round(Pem, 2)

     #Para la red
     ng = 0.554
     nred = 0.448
     nbat = 0.8
     np = 0.652
     nwt = 0.56
     Pred = (Pcarga - Ppanel*np - Pem*ng)/nred
     Pred = round(Pred, 2)
     Pbat = 0

     #------------------------------//----------------------------//----------------------------

     #Los estados
     if (Pred < Pcarga):
        Estado = 1
        if(Pred < 0):
           Pred = 0

     if (Pred <= 0):
        Estado = 2
        Pred = 0
        if (Ppanel >= Pcarga/np):
           Ppanel = Pcarga/np
        #en S1 y S2 tanto esenciales como no esenciales las alimenta el sistema
        
     if(Estado == 1 and Pred == 0):
        if (Pcarga > Ppanel*np + Pem*nwt):
           #Pesenciales <= Ppanel*np + Pem*nwt
           Pcarga = Pesenciales
           Estado = 3
        if(Pesenciales > Ppanel*np + Pem*nwt):
           Estado = 3
           Pbat = (Pesenciales - Ppanel*np - Pem*nwt)/nbat

     if (Pred > 0 and Pred < Pcarga):
        Estado = 1

     if (Pred > Pcarga):
        Estado = 4
        #Si da negativa, el panel tiene potencia suficiente para alimentar a las esenciales
        Pred1 = (Pesenciales - Ppanel*np - Pem*ng)/nred
        Pred1 = round(Pred1, 2)
        if(Pred1 < 0):
           Pred1 = 0
           Ppanel = Pesenciales/np
        Pred = Pred1 + Pnoesenciales

      

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
     #print(tiempo)
     if (tiempo >= 300): # cada 300 segundos que actualice la lectura del json
        print("Sending")   
        SendData(mycursor,mydb)
        inicio = time.time()

