# TX_TRANSMISOR.py
from machine import Pin, ADC, I2C, SPI
from nrf24l01 import NRF24L01, POWER_3, SPEED_250K
import utime, math, struct
# Driver SSD1306 (asegúrate de tener ssd1306.py en la placa)
from ssd1306 import SSD1306_I2C

# --- SPI / NRF24L01 ---
spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4))
csn = Pin(15, Pin.OUT)
ce = Pin(14, Pin.OUT)

nrf = NRF24L01(spi, csn, ce, channel=100, payload_size=32)
nrf.set_power_speed(POWER_3, SPEED_250K)
nrf.set_crc(2)
num_reintentos = 10
tiempo_espera = 5
nrf.reg_write(0x04, (num_reintentos << 4) | tiempo_espera)

# Direcciones (coinciden con RX)
nrf.open_tx_pipe(b'\xd2\xf0\xf0\xf0\xf0')   # enviar control al RX
nrf.open_rx_pipe(1, b'\xe1\xf0\xf0\xf0\xf0') # recibir telemetría del RX

# --- I2C + OLED ---
# Ajusta pines I2C si hace falta. Ejemplo usa I2C(0, sda=GP0, scl=GP1)
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

# --- Joystick ---
xAxis = ADC(Pin(27))
yAxis = ADC(Pin(26))
button = Pin(16, Pin.IN, Pin.PULL_UP)

# --- Inicializar escucha para telemetría ---
nrf.start_listening()

# Escalas (para mostrar en unidades humanas)
ACCEL_SCALE = 16384.0
GYRO_SCALE = 131.0

# --- Variables ---
seq = 0
t_inicio = utime.ticks_ms()
contador_envios = 0

# Para mostrar datos recibidos
last_tele_time = 0
tele_data = None  # (seq, ax,ay,az,gx,gy,gz)

print("🚀 TX listo. Enviando control (joystick) y mostrando telemetría en OLED...")

while True:
    try:
        # --- Leer joystick y calcular ángulo 0-180 ---
        xValue = xAxis.read_u16()
        yValue = yAxis.read_u16()

        grados = math.degrees(math.atan2(yValue - 32768, xValue - 32768))
        if grados < 0:
            grados += 360
        servo_angle = grados / 2
        angle_byte = int((servo_angle / 180) * 255) & 0xFF

        # Enviar paquete control: seq + angle
        try:
            nrf.stop_listening()
            paquete = struct.pack('BB', seq & 0xFF, angle_byte)
            nrf.send(paquete)
            nrf.start_listening()
        except OSError:
            # intentar reanudar escucha si falla
            try:
                nrf.start_listening()
            except:
                pass

        seq = (seq + 1) % 256
        contador_envios += 1

        # --- Revisar si hay telemetría entrante ---
        while nrf.any():
            msg = nrf.recv()
            # Esperamos telemetría empaquetada como '<B6h>' (13 bytes)
            if len(msg) >= 13:
                try:
                    unpacked = struct.unpack('<B6h', msg[:13])
                    t_seq = unpacked[0]
                    ax, ay, az, gx, gy, gz = unpacked[1:]
                    tele_data = (t_seq, ax, ay, az, gx, gy, gz)
                    last_tele_time = utime.ticks_ms()
                except Exception as e:
                    # mensaje con formato inesperado
                    tele_data = None
            else:
                # mensaje pequeño (posible paquete antiguo o debug), ignorar o manejar aquí
                pass

        # --- Actualizar OLED ---
        oled.fill(0)
        oled.text("Joystick -> Servo", 0, 0)
        oled.text("Seq: {}".format(seq), 0, 10)
        oled.text("Ang: {:3.0f}°".format(servo_angle), 0, 20)

        if tele_data:
            t_seq, ax, ay, az, gx, gy, gz = tele_data
            # convertir a unidades humanas
            ax_g = ax / ACCEL_SCALE
            ay_g = ay / ACCEL_SCALE
            az_g = az / ACCEL_SCALE
            gx_dps = gx / GYRO_SCALE
            gy_dps = gy / GYRO_SCALE
            gz_dps = gz / GYRO_SCALE

            oled.text("Tseq:{}".format(t_seq), 0, 32)
            # mostrar dos líneas con valores redondeados
            oled.text("A:{:.2f},{:.2f}".format(ax_g, ay_g), 0, 42)
            oled.text("{:.2f}g G:{:.1f},{:.1f}".format(az_g, gx_dps, gy_dps), 0, 52)
            # (Nota: espacio en 128x64 es limitado — ajusta formato a gusto)
        else:
            oled.text("Telemetria: --", 0, 32)

        oled.show()

    except OSError:
        print("⚠️ Error lectura o envió")

    # Estadísticas cada segundo
    if utime.ticks_diff(utime.ticks_ms(), t_inicio) > 1000:
        print(f"📤 {contador_envios} paquetes enviados/seg")
        contador_envios = 0
        t_inicio = utime.ticks_ms()

    utime.sleep_ms(20)  # ajuste para no saturar bus / RF
