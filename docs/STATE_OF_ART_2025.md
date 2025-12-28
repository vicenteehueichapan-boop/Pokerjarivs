# Estado del Arte 2025: Ingeniería de Software Autónoma y Poker AI

Este documento resume los paradigmas emergentes y tecnologías clave que definen el estándar de excelencia para el desarrollo de Poker AI en 2025, basado en el análisis de Google Antigravity y la teoría de juegos algorítmica.

## 1. Paradigma de Desarrollo: "Agent-First"
El desarrollo moderno ya no es manual. Se basa en la **Orquestación Agéntica** (Google Antigravity).
*   **Concepto:** El desarrollador actúa como arquitecto; la IA (Agentes) ejecuta, planifica y verifica.
*   **Ciclo de Confianza:** Uso de "Artefactos" (Blueprints, Diffs, Videos de prueba) para verificar el trabajo de la IA sin micro-gestión.

## 2. Stack Tecnológico de Poker AI (Referencia 2025)

Para competir en niveles altos (NL50+), el stack tecnológico ha evolucionado:

### A. Percepción (Visión Artificial)
*   **Estándar Anterior:** Lectura de memoria (Inseguro).
*   **Estándar 2025:** OCR y Template Matching con **OpenCV**.
*   **Evasión:** Captura de video vía hardware externo (HDMI capture) para invisibilidad total.

### B. Evaluación y Lógica (Performance)
*   **Legacy:** `Treys` (Lookup tables grandes, lento en Python puro).
*   **Vanguardia:** **`Phevaluator` (Perfect Hash Evaluator)**.
    *   Mapea 7 cartas a un entero de fuerza único usando hash perfecto.
    *   Órdenes de magnitud más rápido para simulaciones Monte Carlo masivas.

### C. Estrategia (GTO & Solvers)
*   **Herramientas:** **TexasSolver** (C++ Open Source Solver).
*   **IA Neuronal:** Arquitecturas tipo **DeepStack** (Continual Re-solving) o **PokerRL** (Deep CFR).
*   **Objetivo:** Aproximar el Equilibrio de Nash para ser inexplotable.

### D. Biometría Conductual (Anti-Detección)
*   **Problema:** Los casinos detectan el movimiento robótico del mouse.
*   **Solución:** **HumanCursor** (Curvas de Bézier + Ley de Fitts).
*   **Características:** Aceleración variable, "overshoot", micro-jitters.

### E. Ingeniería de Datos
*   **Base de Datos:** **PostgreSQL** (JSONB para historiales de manos).
*   **Tracking:** Integración con Hand2Note (H2N).

---

## 3. Hoja de Ruta del Proyecto "Poker Brain"

Basado en este estándar, nuestro sistema `poker_brain` está evolucionando:
1.  **Evaluación:** Migración de `treys` a `phevaluator` (En Progreso).
2.  **Memoria:** Implementación de persistencia (SQLite por ahora, escalable a Postgres).
3.  **Arquitectura:** Diseño modular listo para integrar Solvers externos.
