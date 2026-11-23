from machine import Pin, SoftI2C
import time
import rotary_encoder
from display_oled import SH1106_I2C, update_display


def main():
    # Inicializace displeje a enkodéru
    i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400000)
    oled = SH1106_I2C(i2c)

    rotary_encoder.setup()

    freq = 87.5
    step_size = 0.1
    print("Rádio spuštěno. Naladěno:", freq, "MHz")
    update_display(oled, freq, step_size)

    try:
        while True:
            step = rotary_encoder.get_step()

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

            if rotary_encoder.is_button_pressed():
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
