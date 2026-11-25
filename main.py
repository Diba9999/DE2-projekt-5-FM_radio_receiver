from machine import Pin, SoftI2C, ADC
import time
import rotary_encoder
from display_oled import SH1106_I2C, update_display


def read_volume(pot, samples=8):
    """Přečte průměr z ADC a převede ho na rozsah 0–15."""
    total = 0
    for _ in range(samples):
        total += pot.read_u16()
    avg = total // samples
    return min(15, (avg * 16) // 65536)


def main():
    i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400000)
    oled = SH1106_I2C(i2c)
    rotary_encoder.setup()

    # Potenciometr pro hlasitost na GP26 (ADC0)
    pot = ADC(Pin(26))

    freq = 87.6
    step_size = 0.1
    volume = read_volume(pot)
    stanice = "Impuls"
    pisnicka = "Never Gonna Give You Up"

    scroll_pos = 0
    last_scroll = time.ticks_ms()

    update_display(oled, freq, step_size, volume, stanice, pisnicka, scroll_pos)

    while True:
        changed = False
        step = rotary_encoder.get_step()

        if step != 0:
            freq += step * step_size
            if freq > 108.0:
                freq = 87.5
            elif freq < 87.5:
                freq = 108.0
            freq = round(freq, 1)
            scroll_pos = 0
            changed = True

        if rotary_encoder.is_button_pressed():
            step_size = 1.0 if step_size == 0.1 else 0.1
            changed = True

        # Čtení hlasitosti z potenciometru
        new_volume = read_volume(pot)
        if new_volume != volume:
            volume = new_volume
            changed = True

        # Posun textu každých 300 ms
        if time.ticks_diff(time.ticks_ms(), last_scroll) >= 300:
            scroll_pos += 1
            last_scroll = time.ticks_ms()
            changed = True

        if changed:
            update_display(oled, freq, step_size, volume, stanice, pisnicka, scroll_pos)

        time.sleep_ms(20)


if __name__ == "__main__":
    main()
