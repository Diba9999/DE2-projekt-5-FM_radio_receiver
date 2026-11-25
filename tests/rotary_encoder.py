from machine import Pin
import time

# ==========================================
# DEFINICE PRO ROTAČNÍ ENKODÉR
# ==========================================
steps = 0
button_pressed = False
last_press = 0
last_step = 0
previous_state = 0

clk = Pin(12, Pin.IN, Pin.PULL_UP)
dt = Pin(13, Pin.IN, Pin.PULL_UP)
button = Pin(14, Pin.IN, Pin.PULL_UP)

def encoder_handler(pin):
    global steps, previous_state, last_step
    clk_state = clk.value()
    now = time.ticks_ms()

    if clk_state != previous_state and time.ticks_diff(now, last_step) > 2:
        if clk_state == 0:
            if clk_state != dt.value():
                steps -= 1
            else:
                steps += 1
        last_step = now
        previous_state = clk_state

def button_handler(pin):
    global button_pressed, last_press
    now = time.ticks_ms()

    if time.ticks_diff(now, last_press) > 200:
        button_pressed = True
        last_press = now

def encoder_setup():
    global previous_state
    previous_state = clk.value()
    clk.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_handler, hard=True)
    button.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)

def get_step():
    global steps
    change = steps
    steps = 0
    return change

def is_button_pressed():
    global button_pressed
    if button_pressed:
        button_pressed = False
        return True
    return False

# ==========================================
# TESTOVACÍ SMYČKA
# ==========================================
encoder_setup()
hodnota = 0
print("Test enkoderu spusten...")

while True:
    krok = get_step()
    if krok != 0:
        hodnota += krok
        smer = "VPRAVO" if krok > 0 else "VLEVO"
        print(f"Smer: {smer} ({krok:+d}) | Celkem: {hodnota}")

    if is_button_pressed():
        hodnota = 0
        print("Tlacitko STISKNUTO -> nulovani")

    time.sleep_ms(20)
