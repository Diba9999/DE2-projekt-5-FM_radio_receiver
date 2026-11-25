from machine import ADC, Pin
import time

# ==========================================
# DEFINICE PRO POTENCIOMETR (GP26 / ADC0)
# ==========================================

pot = ADC(Pin(26))

def read_raw(vzorky=10):
    # Prumerovani potlaci bezny sum ADC prevodniku na Pico
    soucet = 0
    for _ in range(vzorky):
        soucet += pot.read_u16()
    return soucet // vzorky

def get_volume():
    # Prevod na rozsah 0 az 15 pro FM modul Si4703
    raw = read_raw()
    return max(0, min(15, round(raw * 15 / 65535)))

def get_percent():
    raw = read_raw()
    return max(0, min(100, round(raw * 100 / 65535)))

# ==========================================
# TESTOVÁNÍ
# ==========================================

print("Test potenciometru na GP26 spusten. Otacej od dorazu k dorazu...")

while True:
    raw = read_raw()
    napeti = raw * 3.3 / 65535
    procenta = max(0, min(100, round(raw * 100 / 65535)))
    hlasitost = max(0, min(15, round(raw * 15 / 65535)))
    graf = "#" * hlasitost + "-" * (15 - hlasitost)

    print(f"RAW: {raw:5d} | {napeti:.2f} V | {procenta:3d} % | Hlasitost: {hlasitost:2d}/15 [{graf}]")
    time.sleep_ms(200)
