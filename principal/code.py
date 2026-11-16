from machine import Pin, ADC, PWM
import time

# 1. Configuración del Puente H TB6612FNG
stby = Pin(23, Pin.OUT)
stby.value(1)  # Habilitar driver permanentemente

# Motor Izquierdo (Motor A)
pwm_a = PWM(Pin(18), freq=1000)
ain1 = Pin(17, Pin.OUT)
ain2 = Pin(16, Pin.OUT)

# Motor Derecho (Motor B)
pwm_b = PWM(Pin(19), freq=1000)
bin1 = Pin(21, Pin.OUT)
bin2 = Pin(22, Pin.OUT)

# --- FACTORES DE COMPENSACIÓN Y VELOCIDAD ---
FACTOR_A = 0.85  
FACTOR_B = 1.00
VELOCIDAD_ESCALA = 0.45  # Un poco más bajo para controlar mejor el tablero pequeño

vel_actual_a = 0.0
vel_actual_b = 0.0
SUAVIZADO = 0.95  # Cambiado a 0.95 para que responda de inmediato en las curvas

def aplicar_motor(pwm, in1, in2, porcentaje):
    if porcentaje > 100: porcentaje = 100
    if porcentaje < -100: porcentaje = -100
    
    duty = int(abs(porcentaje) / 100 * 1023)
    
    if porcentaje > 0:
        in1.value(1)
        in2.value(0)
        pwm.duty(duty)
    elif porcentaje < 0:
        in1.value(0)
        in2.value(1)
        pwm.duty(duty)
    else:
        in1.value(0)
        in2.value(0)
        pwm.duty(0)

# 2. Configuración de la Regleta QTR-8A (S1 en GPIO 14 confirmado)
pines_sensores = [14, 34, 35, 32, 33, 25, 26, 27]
sensores = []
for pin in pines_sensores:
    adc = ADC(Pin(pin))
    adc.atten(ADC.ATTN_11DB)  # Rango completo (0 a 3.3V)
    sensores.append(adc)

UMBRAL = 3700  # Punto medio

def leer_sensores():
    estados = []
    for s in sensores:
        val = s.read()
        if val > UMBRAL:
            estados.append(1)  # Detecta línea negra
        else:
            estados.append(0)  # Detecta fondo blanco
    return estados

# --- 3. CONFIGURACIÓN SENSOR ULTRASÓNICO HC-SR04 ---
trig = Pin(12, Pin.OUT)
echo = Pin(15, Pin.IN)

def medir_distancia_cm():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    
    inicio_espera = time.ticks_us()
    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), inicio_espera) > 25000:
            return -1
            
    t1 = time.ticks_us()
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), t1) > 25000:
            return -1
    t2 = time.ticks_us()
    
    duracion = time.ticks_diff(t2, t1)
    distancia = (duracion * 0.0343) / 2
    return distancia

# HC-SR04: igual que en la presentación
DIST_INICIO_CM = 10   # acercarse a ≤ 10 cm para pedir arranque
DIST_PARADA_CM = 15   # obstáculo a ≤ 15 cm detiene el robot

robot_activo = False
esperando_retiro_inicio = False
esperando_liberacion_stop = False

print("Robot optimizado para pista pequeña listo...")

while True:
    dist = medir_distancia_cm()
    
    # --- MÁQUINA DE ESTADOS DEL HC-SR04 ---
    if not robot_activo:
        if esperando_liberacion_stop:
            if dist == -1 or dist > DIST_PARADA_CM:
                esperando_liberacion_stop = False
        elif not esperando_retiro_inicio:
            if dist != -1 and dist <= DIST_INICIO_CM:
                esperando_retiro_inicio = True
        elif esperando_retiro_inicio:
            if dist == -1 or dist > DIST_INICIO_CM:
                robot_activo = True
                esperando_retiro_inicio = False
                print("¡Iniciado!")
    else:
        if dist != -1 and dist <= DIST_PARADA_CM:
            robot_activo = False
            esperando_liberacion_stop = True
            print("¡Detenido por obstáculo!")

    # --- LÓGICA DE MOVIMIENTO ---
    if robot_activo:
        s = leer_sensores()
        
        # Reglas más agresivas para curvas cerradas
        if s[0] == 1:       # S1: Giro fuerte derecho
            obj_a, obj_b = 70, -40
        elif s[1] == 1:     # S2: Derecha marcada
            obj_a, obj_b = 60, 10
        elif s[2] == 1:     # S3: Derecha suave
            obj_a, obj_b = 45, 30
        elif s[3] == 1 or s[4] == 1:  # S4 o S5: Recto
            obj_a, obj_b = 40, 40
        elif s[5] == 1:     # S6: Izquierda suave
            obj_a, obj_b = 30, 45
        elif s[6] == 1:     # S7: Izquierda marcada
            obj_a, obj_b = 10, 60
        elif s[7] == 1:     # S8: Giro fuerte izquierdo
            obj_b, obj_a = 70, -40
        else:               # Si pierde la línea, se detiene
            obj_a, obj_b = 0, 0
            
        # Aplicar escala y compensación
        obj_a = obj_a * VELOCIDAD_ESCALA
        obj_b = obj_b * VELOCIDAD_ESCALA
        
        obj_a = obj_a * FACTOR_A
        obj_b = obj_b * FACTOR_B

        # Respuesta casi instantánea (Suavizado alto)
        vel_actual_a += (obj_a - vel_actual_a) * SUAVIZADO
        vel_actual_b += (obj_b - vel_actual_b) * SUAVIZADO
    else:
        vel_actual_a = 0.0
        vel_actual_b = 0.0

    aplicar_motor(pwm_a, ain1, ain2, vel_actual_a)
    aplicar_motor(pwm_b, bin1, bin2, vel_actual_b)
    
    time.sleep(0.015)  # Ciclo un poco más rápido para muestrear mejor la pista