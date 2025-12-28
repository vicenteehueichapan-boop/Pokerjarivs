# Poker Brain: Sistema de Decisión de Valor Esperado (EV)

Este repositorio contiene la ingeniería de un "Cerebro de Poker" diseñado para **generar rentabilidad (minar dinero)** en mesas de No Limit Texas Hold'em (NL25-NL50).

El sistema utiliza una **Arquitectura Modular Híbrida** alineada con el paradigma "Agent-First" y las tecnologías de vanguardia de 2025 (Google Antigravity Standard).

---

## 1. Arquitectura del Sistema (Visión Atómica 2025)

El cerebro implementa un stack tecnológico de alto rendimiento:

### Capa 1: Percepción & Evaluación (Phevaluator)
*   **Input:** JSON Estandarizado (Pot, Board, Stacks, Cartas, Posiciones).
*   **Motor:** `phevaluator` (Perfect Hash Evaluator).
*   **Mejora:** Sustitución de algoritmos lineales por Tablas Hash Perfectas, permitiendo millones de simulaciones por segundo.
*   **Función:** Convierte "Ah 9d" en un valor entero de fuerza de mano instantáneo.

### Capa 2: Conocimiento & Memoria (PostgreSQL/SQLite)
*   **Módulo:** `opponent_model.py` + `player_db.py`.
*   **Base de Datos:** SQLite (escalable a PostgreSQL para producción).
*   **Función:**
    *   **Orquestación de Rangos:** Asigna rangos GTO poblacionales ajustados para NL25 (`preflop_charts.py`).
    *   **Explotación Persistente:** Recuerda a los "Fish" (VPIP > 40%) y ajusta matemáticamente la equity para explotarlos.

### Capa 3: Razonamiento & Estrategia (Game Tree)
*   **Módulo:** `strategy.py` + `game_tree.py`.
*   **Lógica:** Monte Carlo Counterfactual Simulation.
*   **Función:**
    *   Simula 1000 escenarios futuros (Hero vs Rango).
    *   Calcula el EV de cada rama del árbol de decisión (Check, Bet, Raise).

---

## 2. El Flujo de Decisión: ¿Cómo decide?

1.  **Reconstrucción del Contexto:** Analiza la situación.
2.  **Perfilado del Rival:**
    *   Consulta `PlayerDB`: ¿Es un Maniaco conocido?
    *   Si sí: Carga rango explotable (Any Two Cards).
    *   Si no: Carga rango GTO posicional (Tight en UTG, Wide en BTN).
3.  **Simulación de Equity (Phevaluator):**
    *   Ejecuta simulaciones de alta velocidad.
    *   Evalúa interacciones complejas de rango (Range Advantage).
4.  **Cálculo de EV:**
    *   Evalúa: `EV = (%Victoria * Bote) - Coste`.
5.  **Selección de Acción:**
    *   Elige la acción con el EV más alto.

---

## 3. ¿Por qué este sistema "Mina Dinero"? (Estándar NL50)

### A. Velocidad y Precisión (Phevaluator)
Al usar algoritmos de Hash Perfecto, el bot puede simular escenarios más profundos en menos tiempo, reduciendo la varianza.

### B. Ventaja de Rango (Profesional)
Entiende que la fuerza de la mano es relativa.
*   *Prueba:* En `tests/test_exploitation.py`, el bot apuesta agresivamente cuando tiene "Ventaja de Rango".

### C. Ventaja de Explotación (Memoria)
Gracias a `player_db.py`, el sistema tiene memoria y castiga los errores recurrentes.

---

## 4. Estructura del Código

```text
poker_brain/
├── main.py             # Punto de entrada
├── model.py            # Modelos de Datos
├── strategy.py         # Orquestador (Phevaluator Integration)
└── modules/
    ├── evaluator.py    # Wrapper Phevaluator (High Performance)
    ├── opponent_model.py # Lógica de rangos
    ├── preflop_charts.py # Rangos NL25
    ├── game_tree.py    # Motor EV
    └── player_db.py    # Memoria Persistente
```

## 5. Ejecución de Pruebas

```bash
pip install -r requirements.txt
python3 -m unittest discover tests
```

### Documentación Adicional
*   [Estado del Arte 2025](docs/STATE_OF_ART_2025.md) - Análisis de Tecnologías Emergentes.
*   [Investigación de Arquitectura](POKER_AI_ARCHITECTURE_RESEARCH.md)
*   [Auditoría del Sistema](SYSTEM_AUDIT_NL50.md)
