# Poker Brain Engineering Design

Este documento detalla la planificación atómica para la creación de un motor de decisiones de Poker (No Limit Texas Hold'em) capaz de generar EV (Valor Esperado) positivo.

## 1. Definición de la Interfaz (Input/Output)

Independientemente de la arquitectura interna (el "cómo"), la interfaz de datos debe ser estandarizada.

### Contexto de Entrada (Input)
El "Cerebro" recibirá un objeto JSON con el estado actual del juego:

```json
{
  "game_id": "uuid",
  "street": "PREFLOP", // PREFLOP, FLOP, TURN, RIVER
  "pot_size": 150.0,
  "current_bet": 20.0, // La apuesta que debemos igualar (0 si es check)
  "board": ["Ah", "Kd", "2s"], // Cartas comunitarias (vacío en preflop)
  "hero": {
    "position": "BTN", // SB, BB, UTG, MP, CO, BTN
    "cards": ["Th", "Tc"],
    "stack": 1000.0,
    "current_investment": 0.0 // Cuanto ha puesto en esta calle
  },
  "villains": [
    {
      "position": "SB",
      "status": "ACTIVE", // ACTIVE, FOLDED, ALLIN
      "stack": 950.0,
      "current_investment": 20.0,
      "stats": { // Opcional: Estadísticas del HUD si existen
        "vpip": 0.25,
        "pfr": 0.20
      }
    }
  ]
}
```

### Decisión de Salida (Output)
```json
{
  "action": "RAISE", // FOLD, CHECK, CALL, RAISE
  "amount": 60.0, // Cantidad total (si es raise)
  "reasoning": "Equity 75% vs Range, Pot Odds 3:1 favored.",
  "ev_estimation": 12.5
}
```

---

## 2. Opciones de Arquitectura (El "Cerebro")

Presentamos tres niveles de complejidad para la ingeniería del cerebro.

### Opción A: Motor de Equidad y Matemáticas (Recomendado para MVP)
Este enfoque es determinista y sólido. Se basa en las "Matemáticas del Poker" puras.

*   **Lógica:**
    1.  **Cálculo de Fuerza de Mano:** Usar un evaluador (ej. `treys` o `eval7`) para saber qué tenemos.
    2.  **Estimación de Rango Rival:** Asignar un rango de manos al rival basado en su posición y acción (ej. UTG abre con el top 15% de manos).
    3.  **Cálculo de Equity:** Simular nuestra mano vs el rango del rival + el board.
    4.  **Cálculo de Pot Odds:** `(Cantidad a llamar) / (Bote total + Cantidad a llamar)`.
    5.  **Decisión:** Si `Equity > Pot Odds` -> Call/Raise. Si no -> Fold (con ajustes de bluff).
*   **Pros:** Rápido de construir, explicable, genera EV positivo contra jugadores malos/medios.
*   **Contras:** Predecible, difícil de balancear (bluffs), no se adapta bien a jugadores expertos.

### Opción B: Motor GTO Simplificado (Tablas + Reglas)
Intenta imitar el juego "Game Theory Optimal" sin ejecutar un solver en tiempo real.

*   **Lógica:**
    1.  **Preflop:** Consulta tablas de apertura/defensa pre-calculadas (Lookup Tables).
    2.  **Postflop:** Usa heurísticas de texturas de board (ej. "En board seco A-7-2, c-bet 33% del bote con 100% del rango").
    3.  **MDF (Minimum Defense Frequency):** Calcula cuánto debemos defender para no ser explotados.
*   **Pros:** Difícil de explotar, juego sólido teórico.
*   **Contras:** Muy rígido, requiere introducir manualmente muchas tablas, no explota a los "peces" (jugadores malos) tanto como la Opción A.

### Opción C: Deep Reinforcement Learning (IA Pura)
Similar a Pluribus o DeepStack. Una red neuronal aprende jugando contra sí misma.

*   **Lógica:**
    1.  **Input:** Estado del juego codificado en tensor.
    2.  **Modelo:** Red Neuronal Profunda (DNN) predice la acción óptima.
    3.  **Entrenamiento:** Requiere millones de manos simuladas (Self-play) y algoritmo MCCFR (Monte Carlo Counterfactual Regret Minimization).
*   **Pros:** Potencial sobrehumano, adaptación dinámica.
*   **Contras:** Costo computacional inmenso, "Caja negra" (difícil saber por qué hizo algo), requiere meses de desarrollo e ingeniería de datos.

---

## 3. Plan de Ingeniería Sugerido

Para obtener un cerebro funcional, que decida y gane rápido, sugiero una **Arquitectura Híbrida (Opción A+)**:

1.  **Core:** Motor de Equidad (Opción A).
2.  **Preflop:** Tablas simples de Rangos (Opción B) para no calcular equity preflop innecesariamente.
3.  **Postflop:** Cálculo de Equity en tiempo real vs Rango estimado.

### Stack Tecnológico
*   **Lenguaje:** Python 3.10+ (Librerías fuertes de data science y poker).
*   **Librerías:**
    *   `treys` o `deuces`: Para evaluación rápida de manos.
    *   `numpy`: Para cálculos vectoriales de equity.
    *   `pytest`: Para asegurar que la lógica es correcta.

### Pasos Siguientes
1.  Configurar entorno Python.
2.  Crear clases de datos (`Hand`, `Range`, `Pot`).
3.  Implementar `EquityCalculator`.
4.  Implementar lógica de decisión `Brain.decide()`.
