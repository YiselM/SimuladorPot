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

Pred = 0
Ppanel = 0
Pbat = 0
Pcarga = 0 
Pem = 0

def SendData(mycursor, mydb):
     global Pred, Ppanel, Pbat, Pcarga, Pem
     now = datetime.now()
     fecha = now.strftime('%Y-%m-%d')
     hora = time.strftime("%H:%M")
     #Se obtiene los datos de radiación y viento de las estaciones meteorologicas
     rv = requests.get('https://api.weather.com/v2/pws/observations/current?stationId=IATLNTIC4&format=json&units=m&apiKey=2538e347f5254da8b8e347f5258da83d')
     resultadov = rv.json()
     viento = (resultadov['observations'][0]['metric']['windSpeed'])*(10/36) #Se obtiene el viento   
     rr = requests.get('https://api.weather.com/v2/pws/observations/current?stationId=IPUERTOC4&format=json&units=m&apiKey=2538e347f5254da8b8e347f5258da83d')
     resultador = rr.json()
     radiacion = resultador['observations'][0]['solarRadiation'] #Se obtiene la radiacion 
     
     #Definicion de la carga
     Pesenciales = 15
     Pnoesenciales = 68

     #Perfil de carga
     if ((hora >= "00:00") and (hora <= "05:00")):
        Pcarga = 15
     if ((hora >= "05:00") and (hora <= "23:20")):
        Pcarga = 83
     if ((hora >= "23:20") and (hora <= "00:00")):
        Pcarga = 15

     #Calculo de la potencia maxima del panel
     eficienciap = 0.13
     area = 1.31
     Ppanel = radiacion*eficienciap*area
     Ppanel = round(Ppanel, 2)
     
     #Calculo de la potencia del emulador eolico
     if (viento < 4 or viento > 14):
        Pem = 0 
     else:
        Pem = (0.001723483*((viento)**6) - 0.04935507*((viento)**5) + 0.01124858*((viento)**4) + 12.34628*((viento)**3) - 144.3604*((viento)**2) + 657.3997*viento - 1038.827)*(5 / 60)
     Pem = Pem/10
     Pem = round(Pem, 2)

     #Eficiencias
     ng = 0.554
     nred = 0.448
     nbat = 0.8
     np = 0.652
     nwt = 0.56

     #Calculo de la red
     Pred = (Pcarga - Ppanel*np - Pem*ng)/nred
     Pred = round(Pred, 2)
     Pbat = 0

     def Estado1():
        global Pred
        if(Pred < 0):
           Pred = 0

     def Estado2():
        global Pred, Ppanel, Pcarga
        Pred = 0
        if(Ppanel >= Pcarga/np):
           Ppanel = Pcarga/np

     def Estado3():
        global Pcarga, Ppanel, Pem, Pbat
        if (Pcarga > Ppanel*np + Pem*nwt):
            Pcarga = Pesenciales
            if(Pesenciales > Ppanel*np + Pem*nwt):
               Pbat = (Pesenciales - Ppanel*np - Pem*nwt)/nbat
            
     def Estado4():
        global Pred, Ppanel, Pem
        Pred1 = (Pesenciales - Ppanel*np - Pem*ng)/nred
        Pred1 = round(Pred1, 2)
        if(Pred1 < 0):
           Pred1 = 0
           Ppanel = Pesenciales/np
        Pred = Pred1 + Pnoesenciales
        

     #Logica para los estados
     Estado = 1
     if (Pred < Pcarga):
        Estado = 1
        Estado1()
     if (Pred <= 0):
        Estado = 2
        Estado2()
     if (Pred > 0 and Pred < Pcarga):
        Estado = 1
        Estado1()
     if(Pred == 0 and Estado == 1):
        Estado = 3
        Estado3()
     if (Pred > Pcarga):
        Estado = 4
        Estado4()

     #Envío de datos a la base de datos
     sql = "INSERT INTO datos (P1, P2, P3, P4, P5, fecha, hora, estado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
     val = (Pred, Ppanel, Pbat, Pcarga, Pem, fecha, hora, Estado)
     #print(val)
     mycursor.execute(sql, val)
     mydb.commit()
     print("Subido")



#Main
inicio = time.time()
while True: 
     tiempo = (time.time() - inicio)
     tiempo = round(tiempo,2)
     if (tiempo >= 300): #Cada 5 minutos se envía un dato a la BD
        print("Sending")   
        SendData(mycursor,mydb)
        inicio = time.time()

