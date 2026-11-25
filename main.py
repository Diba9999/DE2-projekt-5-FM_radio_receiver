import sys
import select
import time
from machine import I2C, Pin, ADC
from Si4703Library import Si4703
import rotary_encoder
from display_oled import SH1106_I2C, update_display

# ==========================================
# INICIALIZACE PERIFERIÍ
# ==========================================

# Nastavení pinů pro Raspberry Pi Pico
RESET_PIN = 15
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
frekvence = 0
trans_hlasitost = 0

# Sledování vstupů z REPL konzole
poll_obj = select.poll()
poll_obj.register(sys.stdin, select.POLLIN)

i2c = I2C(sda=Pin(4), scl=Pin(5), freq=400000)
oled = SH1106_I2C(i2c)
rotary_encoder.setup()

# Potenciometr pro hlasitost na GP26 (ADC0)
pot = ADC(Pin(26))

freq = 876
step_size = 0.1
stanice = "Impuls"
pisnicka = "Never Gonna Give You Up"

scroll_pos = 0
last_scroll = time.ticks_ms()

print("\n\nSi4703 Radio (MicroPython - Sjednocena verze)")
print("===========================")
print("a b     Oblibene stanice nastavene v programu")
print("n d     Zmena frekvence nahoru/dolu")
print("r       Nacteni RDS dat (15 sekund timeout)\n")



# ==========================================
# DEFINICE FUNKCÍ
# ==========================================

def zobraz_info():
    print(f"Frekvence: {frekvence} | Hlasitost: {trans_hlasitost}")

def transformace_hlasitosti(value, from_low, from_high, to_low, to_high):
    return (value - from_low) * (to_high - to_low) / (from_high - from_low) + to_low

def read_volume(pot, samples=8):
    """Přečte průměr z ADC a převede ho na rozsah 0–15."""
    total = 0
    for _ in range(samples):
        total += pot.read_u16()
    avg = total // samples
    return min(15, (avg * 16) // 65536)


# ==========================================
# HLAVNÍ PROGRAM
# ==========================================

def main():
    global freq, step_size, scroll_pos, last_scroll
    
    radio = Si4703(i2c, reset)
    radio.set_volume(0)


    while True:
        # Potenciometr a nastavení hlasitosti
        raw = adc.read_u16()
        trans_hlasitost = transformace_hlasitosti(raw, 300, 65535, 0, 15)
        radio.set_volume(int(trans_hlasitost))

        changed = False
        
        # Čtení enkóderu
        step = rotary_encoder.get_step()
        if rotary_encoder.is_button_pressed():
            step_size = 10 if step_size == 1 else 1
            changed = True

        if step != 0:
            freq += step * step_size
            if freq > 1080:
                freq = 875

            elif freq < 875:
                freq = 1080

            #freq = round(freq, 1)
            radio.set_channel(freq)
            scroll_pos = 0
            changed = True
            

        if poll_obj.poll(0):
            ch = sys.stdin.read(1).lower()
    
            if ch == 'a':
                frekvence = 910
                radio.set_channel(frekvence)
                zobraz_info()

            elif ch == 'b':
                frekvence = 1055
                radio.set_channel(frekvence)
                zobraz_info()

            elif ch == 'r':
                print("Nacteni RDS dat...")
                rds_text = radio.read_rds(15000)
                print("RDS: ", rds_text if rds_text else "Nenalezeno")

        # Posun textu každých 300 ms
        if time.ticks_diff(time.ticks_ms(), last_scroll) >= 300:
            scroll_pos += 1
            last_scroll = time.ticks_ms()
            changed = True

        if changed:
            update_display(oled, freq/10, step_size/10, round(trans_hlasitost,1), stanice, pisnicka, scroll_pos)

            time.sleep_ms(50)
            
            print(f"Hlasitost: {round(trans_hlasitost,1)}")
            print(f"Frekvence: {round(freq,1)}")



if __name__ == "__main__":
    main()
    
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

        # Čtení hlasitosti z potenciometru
        #new_volume = read_volume(pot)
        #if new_volume != volume:
        #    volume = new_volume
        #    changed = True

        #if ch == 'n':
        #    frekvence = radio.seek_up()
        #    zobraz_info()
    
        #elif ch == 'd':
        #    frekvence = radio.seek_down()
        #    zobraz_info()
