# RX_RECEPTOR.py
from machine import Pin, SPI, I2C
from nrf24l01 import NRF24L01, POWER_3, SPEED_250K
from servo import Servo
import utime, struct

# --- SPI / NRF24L01 ---
spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4))
csn = Pin(15, Pin.OUT)
ce = Pin(14, Pin.OUT)

# Usamos payload_size=32 para enviar telemetría completa
nrf = NRF24L01(spi, csn, ce, channel=100, payload_size=32)
nrf.set_power_speed(POWER_3, SPEED_250K)
nrf.set_crc(2)
# Auto-reintentos
num_reintentos = 10
tiempo_espera = 5
nrf.reg_write(0x04, (num_reintentos << 4) | tiempo_espera)

# Direcciones (coinciden con TX)
nrf.open_tx_pipe(b'\xe1\xf0\xf0\xf0\xf0')   # para enviar telemetría al TX
nrf.open_rx_pipe(1, b'\xd2\xf0\xf0\xf0\xf0') # para recibir controles (joystick -> servo)
nrf.start_listening()

# --- Servo ---
s1 = Servo(11)  # ajustar pin si hace falta

def servo_Map(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def servo_Angle(angle):
    angle = max(0, min(180, angle))
    pwm_value = round(servo_Map(angle, 0, 180, 0, 1024))
    s1.goto(pwm_value)

# --- I2C + MPU6050 (lectura directa de registros) ---
# Ajusta los pines I2C según tu placa. Aquí se usa I2C(1, sda=GP2, scl=GP3) como ejemplo.
i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400000)
MPU_ADDR = 0x68

# Inicializar MPU6050 (despierta)
try:
    i2c.writeto_mem(MPU_ADDR, 0x6B, bytes([0]))  # PWR_MGMT_1 = 0
except OSError:
    print("⚠️ No se detectó MPU6050 en la dirección 0x68. Verifica conexión I2C.")

def read_mpu_raw(i2c, addr=MPU_ADDR):
    # Lee 14 bytes desde ACCEL_XOUT_H (0x3B): ax,ay,az,temp,gx,gy,gz
    try:
        data = i2c.readfrom_mem(addr, 0x3B, 14)
    except OSError:
        return None
    def s16(h, l):
        v = (h << 8) | l
        if v >= 32768:
            v -= 65536
        return v
    ax = s16(data[0], data[1])
    ay = s16(data[2], data[3])
    az = s16(data[4], data[5])
    # temp = s16(data[6], data[7])  # si quisieras temperatura
    gx = s16(data[8], data[9])
    gy = s16(data[10], data[11])
    gz = s16(data[12], data[13])
    return (ax, ay, az, gx, gy, gz)

# Escalas (si configuraste ±2g y ±250°/s)
ACCEL_SCALE = 16384.0
GYRO_SCALE = 131.0

# --- Variables ---
ultimo_angulo = 90
contador_paquetes = 0
contador_por_segundo = 0
t_inicio = utime.ticks_ms()

# Telemetría: enviar cada X ms (ej. 200 ms)
telemetry_interval_ms = 200
t_last_tele = utime.ticks_ms()
tele_seq = 0

print("🟢 RX listo. Recibiendo control y enviando telemetría MPU6050...")

while True:
    # --- Procesar paquetes entrantes (control desde TX) ---
    while nrf.any():
        msg = nrf.recv()
        # esperamos al menos 2 bytes: seq + angle_byte
        if len(msg) >= 2:
            seq = msg[0]
            angle_byte = msg[1]
            angulo = angle_byte * 180 / 255

            # Suavizado leve
            if abs(angulo - ultimo_angulo) > 2:
                paso = (angulo - ultimo_angulo) / 3
                for i in range(1, 4):
                    servo_Angle(ultimo_angulo + paso * i)
                    utime.sleep_ms(3)
            else:
                servo_Angle(angulo)

            ultimo_angulo = angulo
            contador_paquetes += 1
            contador_por_segundo += 1
        else:
            # paquete invalido
            continue

    # --- Envío periódico de telemetría MPU6050 al TX ---
    if utime.ticks_diff(utime.ticks_ms(), t_last_tele) >= telemetry_interval_ms:
        raw = read_mpu_raw(i2c)
        if raw:
            ax, ay, az, gx, gy, gz = raw
            # Empaquetamos: seq (1 byte) + 6 x int16 => total 13 bytes
            payload = struct.pack('<B6h', tele_seq & 0xFF, ax, ay, az, gx, gy, gz)
            try:
                nrf.stop_listening()
                nrf.send(payload)
                nrf.start_listening()
            except OSError:
                # En caso de fallo, intentamos reanudar escucha
                try:
                    nrf.start_listening()
                except:
                    pass
            tele_seq = (tele_seq + 1) % 256
        t_last_tele = utime.ticks_ms()

    # Estadísticas cada segundo
    if utime.ticks_diff(utime.ticks_ms(), t_inicio) > 1000:
        print(f"📦 {contador_por_segundo} paquetes/seg recibidos | Total: {contador_paquetes}")
        contador_por_segundo = 0
        t_inicio = utime.ticks_ms()

    utime.sleep_ms(2)
