import sys
import select
import time
from machine import I2C, Pin, ADC
from Si4703Library import Si4703

# ==========================================
# HLAVNÍ PROGRAM
# ==========================================

# Nastavení pinů pro Raspberry Pi Pico
RESET_PIN = 13
SDA_PIN = 4
SCL_PIN = 5
I2C_BUS = 0
adc = ADC(26)

# Fyzický start I2C a hardwarový reset (SDIO na chvíli LOW)
sda = Pin(SDA_PIN, Pin.OUT, value=0)
reset = Pin(RESET_PIN, Pin.OUT, value=0)
time.sleep_ms(10)
reset.value(1)
time.sleep_ms(10)

# Inicializace sběrnice
i2c = I2C(I2C_BUS, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=100000)

# Start rádia
radio = Si4703(i2c, reset)
radio.set_volume(0)

frekvence = 0
hlasitost = 0

print("\n\nSi4703 Radio (MicroPython - Sjednocena verze)")
print("===========================")
print("a b     Oblibene stanice nastavene v programu")
print("+ -     hlasitost (max 15)")
print("n d     Zmena frekvence nahoru/dolu")
print("r       Nacteni RDS dat (15 sekund timeout)\n")

# Sledování vstupů z REPL konzole
poll_obj = select.poll()
poll_obj.register(sys.stdin, select.POLLIN)

def zobraz_info():
    print(f"Frekvence: {frekvence} | Hlasitost: {trans_hlasitost}")

def transformace_hlasitosti(value, from_low, from_high, to_low, to_high):
    return (value - from_low) * (to_high - to_low) / (from_high - from_low) + to_low
    

while True:

    #Nastavení hlasitosti potenciometrem
    raw = adc.read_u16()
    trans_hlasitost = transformace_hlasitosti(raw, 300, 65535, 0, 15)
    print(f"Hlasitost: {round(trans_hlasitost,1)}")
    time.sleep_ms(50)

    radio.set_volume(int(trans_hlasitost))


    if poll_obj.poll(0):
        ch = sys.stdin.read(1).lower()
        
        if ch == 'n':
            frekvence = radio.seek_up()
            zobraz_info()

        elif ch == 'd':
            frekvence = radio.seek_down()
            zobraz_info()

        elif ch == 'a':
            frekvence = 910
            radio.set_channel(frekvence)
            zobraz_info()

        elif ch == 'b':
            frekvence = 1055
            radio.set_channel(frekvence)
            zobraz_info()

        elif ch == 'r':
            print("Nacteni RDS dat...")
            rds_data = radio.read_rds(15000)
            print(f"RDS data: {rds_data}")


##################################################

        #elif ch == '+':
        #    hlasitost += 1
        #    if hlasitost > 15: hlasitost = 15
        #    radio.set_volume(hlasitost)
        #    zobraz_info()

        #elif ch == '-':
        #    hlasitost -= 1
        #    if hlasitost < 0: hlasitost = 0
        #    radio.set_volume(hlasitost)
        #    zobraz_info()
