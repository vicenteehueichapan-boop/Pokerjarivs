# Guía de Entrenamiento Masivo (The Training Factory)

El usuario preguntó: *"¿Con esto podré entrenar masivamente para que sepa jugar CUALQUIER situación?"*

**Respuesta: SÍ, pero necesitas la infraestructura industrial.**
El código actual es el motor. Ahora te entregamos la FÁBRICA.

## 1. El Ciclo de Entrenamiento Infinito (Self-Play Loop)
Para que el sistema aprenda "cualquier situación", debe vivir miles de años de póker en pocos días. Esto se logra con el script `scripts/train_loop.py`.

### Flujo de Trabajo:
1.  **Generación:** 10 Agentes juegan en paralelo (Multiprocessing).
2.  **Ingesta:** Las manos se guardan en TimescaleDB (optimizada para millones de filas).
3.  **Análisis (MDA):** Cada 10,000 manos, el sistema busca "Leaks".
4.  **Optimización:** El Solver corrige la estrategia.
5.  **Despliegue:** Los agentes se actualizan con la nueva estrategia y vuelven a jugar.

## 2. Requisitos de Hardware para Escala Masiva
Para entrenar con billones de manos (Nivel AlphaZero):
*   **CPU:** 64+ Cores (para simular manos en paralelo).
*   **RAM:** 128GB+ (para mantener árboles de juego grandes en memoria).
*   **Almacenamiento:** 4TB NVMe (para la base de datos de historial).

## 3. Cómo Ejecutar
```bash
# Construir la imagen de Docker
docker build -t poker-brain-trainer .

# Ejecutar el Loop Infinito (en background)
docker run -d --name trainer poker-brain-trainer python3 scripts/train_loop.py
```

## 4. Validación de "Cualquier Situación"
El sistema usa **Re-resolución Continua**. No memoriza cada mano (imposible). Aprende **Patrones**.
Al entrenar masivamente, la Red Neuronal (definida en `ai/representation.py`) generaliza:
*   "Ah, esta situación se parece a aquella donde el rival estaba foldeando mucho."
*   Aplica la corrección aprendida.

Este es el estándar usado por **Pluribus** y **Libratus** para vencer a humanos.
