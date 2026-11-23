from machine import Pin, SoftI2C
import framebuf
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
    
    # Ignorujeme zákmity kratší než 2 ms při sepnutí (1->0) i rozepnutí (0->1)
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
# DEFINICE PRO DISPLEJ OLED (SH1106)
# ==========================================
class SH1106_I2C(framebuf.FrameBuffer):
    DEV_ADDR = 0x3c
    WIDTH = 128
    HEIGHT = 64
    PAGES = HEIGHT // 8
    LOW_COLUMN_ADDR = 0x00
    HIGH_COLUMN_ADDR = 0x10
    PAGE_ADDRESS = 0xb0

    def __init__(self, i2c, width=WIDTH, height=HEIGHT, addr=DEV_ADDR):
        self.i2c = i2c
        self.addr = addr
        self.buffer = bytearray(self.PAGES * self.WIDTH)
        super().__init__(self.buffer, width, height, framebuf.MONO_VLSB)
        self._sh1106_init()

    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytearray([0x00, cmd]))

    def write_data(self, data):
        self.i2c.writeto(self.addr, b"\x40" + data)

    def poweron(self):
        self.write_cmd(0xaf)

    def poweroff(self):
        self.write_cmd(0xae)

    def sleep(self, value):
        self.write_cmd(0xae | (not value))

    def contrast(self, val):
        self.write_cmd(0x81)
        self.write_cmd(val)

    def show(self):
        (w, p, buf) = (self.WIDTH, self.PAGES, self.buffer)
        for page in range(0, p):
            self.write_cmd(self.PAGE_ADDRESS | page)
            self.write_cmd(self.LOW_COLUMN_ADDR | 2)
            self.write_cmd(self.HIGH_COLUMN_ADDR | 0)
            self.write_data(buf[(w * page):(w * page + w)])

    def show_logo(
        self,
        logo_x=0,
        logo_y=0,
        text_x=35,
        text_y=1,
        line1="MicroPython",
        line2="Raspberry",
        line3="Brno",
    ):
        self.fill_rect(logo_x, logo_y, 32, 32, 1)
        self.fill_rect(logo_x + 5, logo_y + 5, 10, 4, 0)
        self.fill_rect(logo_x + 15, logo_y + 9, 12, 3, 0)
        self.fill_rect(logo_x + 15, logo_y + 12, 4, 15, 0)
        self.pixel(logo_x + 19, logo_y + 12, 0)
        self.text(line1, text_x, text_y)
        self.text(line2, text_x, text_y + 12)
        self.text(line3, text_x, text_y + 23)
        self.show()

    def _sh1106_init(self):
        INIT_SEQ = (
            0xae,        # Turn off oled panel
            0x00,        # Set low column address
            0x10,        # Set high column address
            0x40,        # Set start line address
            0x20, 0x02,  # Page addressing mode
            0xc8,        # Top-down segment (4th segment)
            0x81,        # Set contrast control register
            0xcf, 0xa1,  # Set segment re-map 95 to 0
            0xa6,        # Set normal display
            0xa8,        # Set multiplex ratio(1 to 64)
            0x3f,        # 1/64 duty
            0xd3, 0x00,  # Set display offset: none
            0xd5, 0x80,
            0xd9, 0xf1,
            0xda, 0x12,
            0xdb, 0x40,
            0x8d, 0x14,
            0xaf         # Turn on oled panel
        )
        time.sleep_ms(100)

        for cmd in INIT_SEQ:
            self.write_cmd(cmd)


# ==========================================
# VYKRESLENÍ A HLAVNÍ SMYČKA
# ==========================================
def update_display(oled, freq, step_size):
    oled.fill(0)
    oled.text(f"Freq: {freq:.1f} MHz", 0, 10)
    oled.text(f"Krok: {step_size:.1f} MHz", 0, 30)
    oled.show()

def main():
    # SoftI2C na 400 kHz spolehlivě funguje s tímto SH1106 modulem bez chyby EIO
    i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400000)
    oled = SH1106_I2C(i2c)
    
    encoder_setup()
    
    freq = 87.5
    step_size = 0.1
    print("Rádio spuštěno. Naladěno:", freq, "MHz")
    update_display(oled, freq, step_size)

    try:
        while True:
            step = get_step()
            
            if step != 0:
                freq += step * step_size
                
                # Hlídání rozsahu FM pásma (87.5 - 108.0 MHz)
                if freq > 108.0:
                    freq = 87.5
                elif freq < 87.5:
                    freq = 108.0
                    
                freq = round(freq, 1)
                print("Frekvence:", freq, "MHz")
                update_display(oled, freq, step_size)

            if is_button_pressed():
                if step_size == 0.1:
                    step_size = 1.0
                    print("Tlačítko stisknuto! (Aktuální krok: 1.0)")
                else:
                    step_size = 0.1
                    print("Tlačítko stisknuto! (Aktuální krok: 0.1)")
                
                update_display(oled, freq, step_size)

            time.sleep_ms(20)

    except KeyboardInterrupt:
        print("\nProgram ukončen.")

if __name__ == "__main__":
    main()
