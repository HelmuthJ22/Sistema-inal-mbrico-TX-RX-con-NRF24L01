Sistema Inalámbrico TX–RX con NRF24L01 y MPU6050

Este proyecto implementa un sistema inalámbrico de transmisión y recepción basado en Raspberry Pi Pico, utilizando los módulos NRF24L01 y MPU6050. El sistema permite el control de un servomotor mediante un joystick y la transmisión de telemetría IMU, verificando su correcto funcionamiento mediante análisis SPI, PWM e inspección espectral.

Resumen

Se analizó la comunicación SPI entre la Raspberry Pi Pico y el módulo nRF24L01 usando Logic2 y un analizador lógico.
Se conectaron las líneas SCK, MOSI, MISO, CSN e IRQ, y se empleó la librería del nRF24L01 para decodificar las tramas.
Los resultados mostraron secuencias de inicialización y transmisión con comandos como W_REGISTER, R_REGISTER, W_TX_PAYLOAD y STATUS, evidenciando una comunicación estable y conforme al protocolo SPI.

Objetivos
Objetivo General

Diseñar, implementar y documentar un sistema inalámbrico TX–RX basado en NRF24L01 y MPU6050 que permita el control por joystick de un servomotor y la transmisión de telemetría IMU, verificando su correcto funcionamiento mediante mediciones eléctricas (SPI, PWM) y análisis espectral.

Objetivos Específicos

Verificar la comunicación SPI entre MCU y NRF24L01 mediante mediciones con analizador lógico y osciloscopio.
Medir y caracterizar la señal PWM del servomotor, evaluando su relación pulso–ángulo.
Evaluar el enlace RF modificando canal, potencia y data rate, midiendo PER y estabilidad.
Analizar la ocupación espectral y posibles interferencias en la banda de 2.4 GHz.
Validar la lectura del MPU6050, convertir valores a unidades físicas y transmitir telemetría hacia el transmisor.

Descripción Técnica

El transmisor (TX) lee los valores del joystick y los envía mediante el módulo NRF24L01.

El receptor (RX) recibe los datos, ajusta el ángulo del servomotor y envía la telemetría del MPU6050 de regreso al transmisor.

En el transmisor, los datos IMU recibidos se muestran en la pantalla OLED, junto con la posición del joystick.

La comunicación SPI fue verificada con Logic2, observando comandos como:

R_REGISTER CONFIG

W_TX_PAYLOAD

R_RX_PL_WID

Las mediciones PWM confirmaron periodos de 20 ms (50 Hz) y anchos de pulso:

0.5 ms → 0°

1.38 ms → 90°

2.4 ms → 180°

Resultados de Pruebas
🔹 Comunicación SPI

Capturas realizadas en Logic2 mostraron sincronización correcta entre SCK, MOSI, MISO y CSN.

Los comandos R_REGISTER, W_TX_PAYLOAD y STATUS fueron correctamente decodificados, evidenciando el intercambio adecuado entre MCU y módulo RF.

🔹 Señal PWM

Frecuencia medida: 50 Hz

Duty cycles observados: 2.55 % (0°), 7.04 % (90°), 12 % (180°)

Servomotor con respuesta mecánica estable y precisa.

🔹 Espectro RF

Frecuencia de transmisión: 2.5 GHz (canal 100)

Potencia observada: −55 dBm

Se confirma emisión dentro de la banda ISM 2.4 GHz y coexistencia con Wi-Fi sin interferencias críticas.

Análisis

El sistema integró con éxito las comunicaciones SPI e I2C, permitiendo control y telemetría en tiempo real.
Las mediciones lógicas y eléctricas confirmaron una sincronización adecuada y la correcta configuración del módulo NRF24L01.
El servomotor respondió proporcionalmente al movimiento del joystick, mientras que los datos del MPU6050 se visualizaron de forma precisa en la pantalla OLED.

Conclusiones

La comunicación SPI entre la Raspberry Pi Pico y el NRF24L01 fue estable y confiable.
El PWM presentó una relación lineal entre ciclo útil y ángulo de giro.
El MPU6050 entregó lecturas coherentes de aceleración y rotación, validadas en unidades físicas.
La telemetría inalámbrica fue transmitida con integridad y mostrada correctamente en la pantalla OLED.
El análisis espectral confirmó la transmisión en el canal configurado (2.5 GHz) y con potencia adecuada.
En conjunto, el sistema cumple los objetivos planteados, demostrando su funcionalidad, estabilidad y eficiencia para aplicaciones de control remoto y monitoreo inalámbrico.
