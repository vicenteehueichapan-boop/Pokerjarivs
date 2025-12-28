# Auditoría del Sistema vs Estándar NL25/NL50

Este documento analiza componente por componente si el sistema actual cumple con el estándar profesional para "minar dinero" y propone la integración de Base de Datos para garantizarlo.

## 1. Análisis Componente por Componente

### A. Módulo de Percepción (`modules/evaluator.py`)
*   **Estado:** Profesional (Estándar).
*   **Capacidad:** Identifica manos hechas y texturas básicas (Flush Draws).
*   **Veredicto:** ✅ **Suficiente**. En NL50 no necesitas redes neuronales para ver que tienes Trio. `treys` es robusto.

### B. Modelo de Oponente (`modules/opponent_model.py`)
*   **Estado:** Sólido pero "Amnésico".
*   **Capacidad:** Asigna rangos basados en la Posición (GTO/Poblacional). Distingue UTG de BTN.
*   **Fallo Crítico:** No recuerda. Si un jugador nos hace 3-bet con 7-2 en la mano anterior, en la siguiente mano lo tratamos con respeto de nuevo.
*   **Veredicto:** ⚠️ **Mejorable**. Para "minar" de verdad, necesitamos explotar tendencias específicas de jugadores recurrentes.

### C. Motor de Estrategia (`modules/strategy.py`)
*   **Estado:** Avanzado (Range-Based Monte Carlo).
*   **Capacidad:** Simula nuestra mano contra un *Rango*, no contra cartas al azar. Esto es nivel profesional.
*   **Veredicto:** ✅ **Excelente**. Es matemáticamente superior a la mayoría de humanos en NL25 que juegan por "intuición".

### D. Árbol de Decisión (`modules/game_tree.py`)
*   **Estado:** Básico (1-Step Lookahead).
*   **Capacidad:** Calcula EV de Check/Bet/Raise inmediato.
*   **Limitación:** No planifica "Bet Flop -> Bet Turn -> Shove River".
*   **Veredicto:** ⚠️ **Suficiente para MVP, pero limitante**. En el futuro, un árbol de 2 pasos aumentaría el winrate.

---

## 2. La Pieza Faltante: Persistencia (Base de Datos)

El usuario preguntó: *"bases de datos para guardar jugadores"*.
Esta es la clave para pasar de "Ganar poco" a "Explotar masivamente".

### Propuesta de Mejora: `PlayerDatabase`
Implementaremos una base de datos SQLite local para rastrear a cada villano que enfrentamos.

**Flujo de Datos:**
1.  **Recibir Contexto:** Identificar `villain_id`.
2.  **Consulta DB:** "¿Conozco a este tipo?".
3.  **Si existe:** Recuperar sus stats reales (VPIP, Agresividad).
    *   Si es un **Fish** (VPIP Alto): Asignar rango basura -> Atacarle más.
    *   Si es un **Nit** (VPIP Bajo): Asignar rango Nuts -> Respetarle más.
4.  **Fin de Mano:** Actualizar DB con lo que vimos (¿Entró al bote? ¿Hizo Raise?).

### Impacto en EV
*   **Sin DB:** Ganamos por fundamentos matemáticos (winrate ~2-4 bb/100).
*   **Con DB:** Ganamos por explotación personalizada (winrate ~6-8 bb/100).

---

## 3. Conclusión
El sistema actual es un "Reg Sólido". Con la Base de Datos, se convertirá en un "Shark" que recuerda y castiga los errores recurrentes de los rivales.
