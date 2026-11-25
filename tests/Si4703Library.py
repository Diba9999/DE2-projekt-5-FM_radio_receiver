import time

# ==========================================
# KNIHOVNA PRO OVLÁDÁNÍ MODULU SI4703
# ==========================================

class Si4703:
    POWERCFG = 0x02
    CHANNEL = 0x03
    SYSCONFIG1 = 0x04
    SYSCONFIG2 = 0x05
    STATUSRSSI = 0x0A
    READCHAN = 0x0B
    RDSB = 0x0D
    RDSD = 0x0F

    def transformace_hlasitosti(self, value, from_low, from_high, to_low, to_high):
        return (value - from_low) * (to_high - to_low) / (from_high - from_low) + to_low
    
    def __init__(self, i2c, reset_pin):
        self.i2c = i2c
        self.reset = reset_pin
        self.registers = [0] * 16
        self._init_radio()

    def _init_radio(self):
        self.read_registers()
        self.registers[0x07] = 0x8100 # Povolení oscilátoru
        self.update_registers()
        time.sleep_ms(500)
        
        self.read_registers()
        self.registers[self.POWERCFG] = 0x4001 # Zapnutí IC
        self.registers[self.SYSCONFIG1] |= (1 << 12) # Povolení RDS
        self.registers[self.SYSCONFIG1] |= (1 << 11) # 50kHz Europe setup (DE)
        self.registers[self.SYSCONFIG2] |= (1 << 4)  # 100kHz spacing pro Evropu (SPACE0)
        self.registers[self.SYSCONFIG2] &= 0xFFF0    # Vynulování hlasitosti
        self.registers[self.SYSCONFIG2] |= 0x0001    # Nastavení minimální hlasitosti
        self.update_registers()
        time.sleep_ms(110)

    def read_registers(self):
        data = self.i2c.readfrom(0x10, 32)
        for i in range(16):
            reg_index = (0x0A + i) % 16
            self.registers[reg_index] = (data[i*2] << 8) | data[i*2+1]

    def update_registers(self):
        buf = bytearray(12)
        for i in range(6):
            val = self.registers[0x02 + i]
            buf[i*2] = (val >> 8) & 0xFF
            buf[i*2+1] = val & 0xFF
        self.i2c.writeto(0x10, buf)

    def set_volume(self, volume):
        self.read_registers()
        volume = max(0, min(15, volume))
        self.registers[self.SYSCONFIG2] &= 0xFFF0
        self.registers[self.SYSCONFIG2] |= volume
        self.update_registers()

    def set_channel(self, channel):
        new_channel = int((channel * 10 - 8750) / 10)
        self.read_registers()
        self.registers[self.CHANNEL] &= 0xFE00
        self.registers[self.CHANNEL] |= new_channel
        self.registers[self.CHANNEL] |= (1 << 15) # TUNE bit
        self.update_registers()

        while True:
            self.read_registers()
            if (self.registers[self.STATUSRSSI] & (1 << 14)) != 0:
                break
        
        self.read_registers()
        self.registers[self.CHANNEL] &= ~(1 << 15)
        self.update_registers()
        
        while True:
            self.read_registers()
            if (self.registers[self.STATUSRSSI] & (1 << 14)) == 0:
                break

    def _seek(self, seek_up):
        self.read_registers()
        self.registers[self.POWERCFG] |= (1 << 10) 
        if seek_up:
            self.registers[self.POWERCFG] |= (1 << 9)  
        else:
            self.registers[self.POWERCFG] &= ~(1 << 9) 
        
        self.registers[self.POWERCFG] |= (1 << 8) 
        self.update_registers()
        
        while True:
            self.read_registers()
            if (self.registers[self.STATUSRSSI] & (1 << 14)) != 0:
                break
                
        sfbl = self.registers[self.STATUSRSSI] & (1 << 13)
        self.registers[self.POWERCFG] &= ~(1 << 8)
        self.update_registers()
        
        while True:
            self.read_registers()
            if (self.registers[self.STATUSRSSI] & (1 << 14)) == 0:
                break
                
        if sfbl: return 0
        return self.get_channel()

    def seek_up(self): return self._seek(True)
    def seek_down(self): return self._seek(False)

    def get_channel(self):
        self.read_registers()
        return (self.registers[self.READCHAN] & 0x03FF) + 875

    def read_rds(self, timeout_ms):
        end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
        completed = [False] * 4
        buffer = [" "] * 8
        completed_count = 0
        
        while completed_count < 4 and time.ticks_diff(end_time, time.ticks_ms()) > 0:
            self.read_registers()
            if self.registers[self.STATUSRSSI] & (1 << 15):
                b = self.registers[self.RDSB]
                index = b & 0x03
                if not completed[index] and b < 500:
                    completed[index] = True
                    completed_count += 1
                    dh = chr((self.registers[self.RDSD] & 0xFF00) >> 8)
                    dl = chr(self.registers[self.RDSD] & 0x00FF)
                    buffer[index * 2] = dh
                    buffer[index * 2 + 1] = dl
                time.sleep_ms(40)
            else:
                time.sleep_ms(30)
                
        if time.ticks_diff(end_time, time.ticks_ms()) <= 0:
            return ""
        return "".join(buffer).strip()

#  TESTOVÁNÍ

from machine import Pin, I2C

SDA_PIN = 4
SCL_PIN = 5
RST_PIN = 15

# Reset sekvence pro prepnuti Si4703 do I2C rezimu
rst = Pin(RST_PIN, Pin.OUT, value=0)
sda = Pin(SDA_PIN, Pin.OUT, value=0)
time.sleep_ms(10)
rst.value(1)
time.sleep_ms(10)

i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=100000)
print("I2C:", [hex(a) for a in i2c.scan()])

radio = Si4703(i2c, rst)
radio.set_volume(5)
radio.set_channel(951)  # 95.1 MHz

while True:
    aktualni = radio.get_channel() / 10
    rds = radio.read_rds(2000)
    print(f"Frekvence: {aktualni:.1f} MHz | RDS: {rds if rds else '---'}")
    time.sleep(1)
