# Reto 3 — Control ON/OFF · Robot seguidor de línea

Microcontroladores 2026-2 · Universidad Nacional de Colombia  
Ingeniería de Sistemas y Computación · Ingeniería Mecatrónica  
Nicolás Muñoz · Fredy Garcia · Sofía Calderón · Alejandro Llano

Una ESP32 con MicroPython lee una regleta QTR-8A de ocho sensores y manda dos motores DC por un puente H TB6612FNG. El control es discreto tipo ON/OFF: cada sensor en negro impone un par de PWM. Un HC-SR04 arranca y frena el robot por distancia. La entrega es **modalidad B**: chasis provisional y respuesta física a la línea.

| Carpeta | Qué es |
| --- | --- |
| [principal](principal/README.md) | `code.py`. Sensores, motores, ultrasonido y reglas ON/OFF. Incluye el esquemático. |

La presentación de la exposición está en `presentacion_reto3.pdf`.

Se ejecuta en Thonny, con el firmware de MicroPython en la ESP32. El archivo se copia a la placa como `main.py`, o se corre con Run. Lo que el programa imprime aparece en el shell de Thonny.
