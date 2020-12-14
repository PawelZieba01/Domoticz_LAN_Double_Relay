from machine import Pin, PWM, deepsleep
import urequests
import network
import socket
import ujson
import gc
#import select
from time import sleep

gc.collect()

f = open("config.json", "r")
config_json = f.read()                         #pobranie danych konfiguracyjnych z pliku config.json
config_dict = ujson.loads(config_json)         #zdekodowanie danych json - zamiana na dictionary

f.close()
del config_json

#---------------------------------------   KONFIGURACJA URZĄDZENIA   ---------------------------------------
static_ip = config_dict["static_ip"]
mask_ip = config_dict["mask_ip"]
gate_ip = config_dict["gate_ip"]
dns_ip = config_dict["dns_ip"]
ssid = config_dict["ssid"]
password = config_dict["password"]

server_ip = config_dict["server_ip"]
server_port = config_dict["server_port"]

device1_idx = config_dict["device1_idx"]
device2_idx = config_dict["device2_idx"]

relay1_pin = int(config_dict["relay1_pin"])
relay2_pin = int(config_dict["relay2_pin"])

request_period = float(config_dict["request_period"])
relay_pins_invert = config_dict["relay_pins_invert"]
#cmd_on = config_dict["cmd_on"]
#cmd_off = config_dict["cmd_off"]

del config_dict
#------------------------------------------------------------------------------------------------------------



#-------------------------------------------   ZMIENNE GLOBALNE   -------------------------------------------

#------------------------------------------------------------------------------------------------------------



#------------------------------------------   KONFIGURACJA PINÓW   ------------------------------------------
led = Pin(2, Pin.OUT)    #wbudowana dioda led

relay1 = Pin(relay1_pin, Pin.OUT)    #przekaźnik 1
relay2 = Pin(relay2_pin, Pin.OUT)    #przekaźnik 2


#wyłączenie przekaźników
if(relay_pins_invert == "False"):
    relay1.value(0)
    relay2.value(0)
else:
    relay1.value(1)
    relay2.value(1)

#------------------------------------------------------------------------------------------------------------



#-----------------------------------   KONFIGURACJA POŁĄCZEŃ SIECIOWYCH   -----------------------------------
#utworzenie socketu do komunikacji 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#inicjalizacja WLAN
wlan = network.WLAN(network.STA_IF)

wlan.active(True)
wlan.ifconfig((static_ip, mask_ip, gate_ip, dns_ip))
wlan.connect(ssid, password)
#------------------------------------------------------------------------------------------------------------



#-----------------------------------------   PODŁĄCZENIE DO SIECI   -----------------------------------------
#oczekiwanie na podłączenie urządzenia Wi-Fi
print("Oczekiwanie na podłączenie do sieci Wi-Fi")

while wlan.isconnected() == False:
    led.value(1)
    sleep(0.2)
    led.value(0)
    sleep(0.2)
    print(".", end =" ")
    
print("")
print("Połączenie udane")
print("Konfigurajca Wi-Fi:  ", end =" ")
print(wlan.ifconfig())

#sygnalizacja podłączenia do sieci - LED
led.value(1)
sleep(2)
led.value(0)
for i in range(5):
    led.value(1)
    sleep(0.1)
    led.value(0)
    sleep(0.1)

#nasłuchiwanie na porcie 80 
s.bind(('', 80))
s.listen(3)
#------------------------------------------------------------------------------------------------------------



#-----------------------------------------------   FUNKCJE   ------------------------------------------------

#funkcja pobierająca i konwertująca dane z serwera domoticz
def get_data_from_domoticz(device_idx):
    global server_ip, server_port
    
    status = ""
    
    try:
        response = urequests.get('http://' + server_ip + ':' + server_port + '/json.htm?type=devices&rid=' + device_idx)     #odpowiedź serwera
    except:
        response = "Request error"
    print(response)
    
    if(response != "Request error"):
        parsed_result = ujson.loads(response.text)                                            #konwersja json do dictionary

        status = parsed_result["result"][0]["Status"]                                         #status ("On"  lub  "Off")

        
        print(status)

        if(status.find("On") == 0):                                             #jeżeli urządzenie włączone zwróć True
            return True
        
        elif(status.find("Off") == 0):                                          #jeżeli urządzenie wyłączone zwróć False
            return False
    else:
        print(response)
    
    
#funkcja sterująca diodami rgb    
def set_outputs(status1, status2):
    global relay_pins_invert
     
    if(relay_pins_invert == "False"):                                                #jeżeli relay_pins_invert = 0  ->  nie odwracaj polaryzacji wyjść
        relay1.value(status1)
        relay2.value(status2)
        print("relay1 = " + str(status1) + "    relay2 = " + str(status2))

    elif(relay_pins_invert == "True"):                                               #jeżeli relay_pins_invert = 1  ->  odwróć polaryzacje wyjść
        relay1.value(not status1)
        relay2.value(not status2)
        print("relay1 = " + str(not status1) + "    relay2 = " + str(not status2))

#------------------------------------------------------------------------------------------------------------






#----------------------------------------   GŁÓWNA PĘTLA PROGRAMU   -----------------------------------------
while True:
    device1_status = get_data_from_domoticz(device1_idx)                                #pobranie informacji o stanie urządzenia z serwera domoticz
    device2_status = get_data_from_domoticz(device2_idx)                                #pobranie informacji o stanie urządzenia z serwera domoticz
    set_outputs(device1_status, device2_status)                                         #wysterowanie przekaźników
    sleep(request_period)                                                               #opóźnienie
#------------------------------------------------------------------------------------------------------------    
