# Gap Analysis: Elevating to NL25/NL50 Winner

Para batir niveles como NL25/NL50 (donde los jugadores ya entienden los fundamentos), el sistema actual (v2) tiene brechas críticas.

## 1. Análisis de Brechas (Current vs Professional)

| Componente | Estado Actual (v2) | Estándar Profesional (NL25+) | Por qué perdemos hoy |
| :--- | :--- | :--- | :--- |
| **Modelo de Oponente** | Porcentaje estático (ej. "Top 15%"). | **Rangos GTO + Explotativos.** El rival no tiene "15% random", tiene combinaciones específicas (combos) dependiendo de su posición y acción previa. | Asumir que el rival tiene manos aleatorias diluye su fuerza real. Subestimamos sus "nuts". |
| **Motor de Equity** | Hero vs Random Cards. | **Hero vs Range.** La equity debe calcularse contra el rango percibido del rival. | Calculamos mal el EV. Tener Top Pair es bueno vs Random, pero puede ser terrible vs el Rango de un nit que solo hace 3-bet con JJ+. |
| **Juego Preflop** | Cálculo de Equity cruda (lento e impreciso). | **Tablas Pre-Resueltas (Charts).** No se calcula equity preflop en tiempo real; se usan tablas de Open/Fold/3Bet probadas por solvers. | Perderemos dinero por "rake" y dominación jugando manos marginales fuera de posición. |
| **Comprensión del Board** | Textura básica (Flush draw?). | **Interacción de Rangos.** "¿A quién favorece este board, a mi rango o al suyo?". | No aprovechamos la "Ventaja de Rango" (Range Advantage) para farolear en boards favorables (ej. A-K-x siendo el agresor). |

## 2. Plan de Acción Atómico

Para cerrar estas brechas y profesionalizar el cerebro:

### A. Implementación de Rangos GTO Preflop
No podemos "calcular" el preflop en cada mano. Necesitamos una base de datos de conocimiento (Charts).
*   *Acción:* Crear un módulo `PreflopManager` con rangos de apertura para 6-max (UTG, MP, CO, BTN, SB).

### B. Simulación Range-Based (Monte Carlo Avanzado)
El cambio más importante.
*   *Antes:* `VillainHand = Random(Deck)`
*   *Ahora:* `VillainHand = WeightedSample(OpponentRange)`
*   *Detalle:* Si el rival abrió en UTG, su rango es {66+, ATs+, KJs+, ...}. Al simular el flop, solo le damos manos de ese conjunto.

### C. Lógica de "Range Advantage"
El bot debe saber cuándo ser agresivo incluso con aire.
*   *Regla:* Si mi rango percibido impacta el board mejor que el del rival -> C-Bet frecuente (Apuesta de continuación).

Esta actualización transformará al bot de un "Calculador de Probabilidades" a un "Jugador de Poker Estratégico".
