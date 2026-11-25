import framebuf
import time


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


def update_display(oled, freq, step_size, volume, rds_station="", rds_song="", scroll_pos=0):
    oled.fill(0)

    # 1. a 2. řádek: Zobrazení olvádaných parametrů (frekvence, krok, hlasitost)
    oled.fill_rect(0, 0, 128, 21, 1)
    oled.text(f"F: {freq:.1f} MHz", 2, 2, 0)
    oled.text(f"K:{step_size:.1f} | H:{volume:.0f}", 2, 12, 0)

    # 3. řádek: Název stanice
    station = (rds_station.strip() or "---")[:16]
    oled.text(station, (128 - len(station) * 8) // 2, 28)
    oled.hline(0, 43, 128, 1)

    # 4. řádek: Název písničky (s posuvem)
    song = rds_song.strip()
    if len(song) > 16:
        padded = song + "   "
        pause = 6  # Počet kroků pauzy na začátku
        cycle = len(padded) + pause
        step = scroll_pos % cycle
        idx = 0 if step < pause else (step - pause)
        visible = (padded + padded)[idx : idx + 16]
    else:
        visible = song

    oled.text(visible, 0, 52)
    oled.show()

    
