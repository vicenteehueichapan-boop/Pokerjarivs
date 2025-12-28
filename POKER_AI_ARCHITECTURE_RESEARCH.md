# Investigación de Arquitectura de IA para Poker (Texas Hold'em)

Este documento analiza las arquitecturas "Estado del Arte" (SOTA) para construir un cerebro de poker capaz de decidir óptimamente en cualquier contexto.

## 1. Análisis del Estado Actual (MVP v0.1)

El código actual (`feature/poker-brain-mvp`) implementa un motor **Heurístico de Valor Esperado (EV)**.
*   **Funcionamiento:** Calcula la Equity inmediata (Probabilidad de ganar al showdown) y la compara con las Pot Odds.
*   **Limitaciones:**
    *   **Miopía:** No "ve" el futuro. No considera que si hacemos Call ahora, podríamos enfrentar una apuesta impagable en el River.
    *   **Explotabilidad:** Juega sus cartas boca arriba. No balancea rangos (no tiene faroles/bluffs sistemáticos). Un humano atento notará que "Solo apuesta fuerte cuando tiene mano".
    *   **Contexto Limitado:** Ignora la textura dinámica del board más allá de la fuerza bruta de la mano.

## 2. Arquitecturas Avanzadas (Investigación Atómica)

Para superar al MVP, debemos explorar las arquitecturas que han vencido a campeones mundiales.

### Opción A: CFR (Counterfactual Regret Minimization) - "El Enfoque Libratus"
Esta es la arquitectura de *Libratus* y *Pluribus* (Facebook AI).
*   **Concepto:** Se construye un árbol de juego gigante. La IA juega contra sí misma billones de veces. En cada nodo, si toma una acción y pierde, acumula "Arrepentimiento" (Regret) por no haber tomado la otra acción. Con el tiempo, minimiza este arrepentimiento para encontrar el Equilibrio de Nash.
*   **Estructura:**
    *   **Abstraction Module:** Simplifica el juego (agrupa manos similares, ej. "K-high flush draw" y "Q-high flush draw" son lo mismo) para reducir el tamaño del árbol.
    *   **Blueprint Strategy:** Una estrategia pre-calculada enorme (cientos de TBs comprimidos) para los primeros movimientos.
    *   **Subgame Solving:** En el Turn/River, resuelve el resto del juego en tiempo real usando el contexto actual.
*   **Pros:** Inexplotable teóricamente.
*   **Contras:** Requiere inmensa potencia de cómputo (superordenadores) para entrenar el "Blueprint". Difícil de implementar en un script ligero.

### Opción B: Deep Learning + Search (DeepStack) - "El Enfoque Neuronal"
*   **Concepto:** En lugar de calcular todo el árbol hasta el final, usa una Red Neuronal para estimar el valor de un estado futuro (como AlphaZero usa una red para evaluar posiciones de ajedrez).
*   **Estructura:**
    *   **Value Network:** Una DNN que recibe (Rango Hero, Rango Villano, Board, Pot) y devuelve el valor esperado de la mano.
    *   **Continual Resolving:** En cada turno, genera un pequeño árbol de búsqueda local (Lookahead) y usa la Red Neuronal para evaluar las hojas de ese árbol.
*   **Pros:** Más flexible que CFR puro. No necesita almacenar tablas gigantes (la "intuición" está en la red neuronal).
*   **Contras:** Entrenar la Value Network es complejo y requiere generar millones de situaciones de poker.

### Opción C: Árbol de Búsqueda Heurística (MCTS / Expectiminimax) - "El Enfoque Pragmático"
Una evolución directa del MVP, añadiendo "visión de futuro".
*   **Concepto:** Simular no solo la equidad actual, sino los posibles movimientos futuros del rival.
*   **Estructura:**
    *   **Árbol de Decisión:** Generar nodos: "Si yo apuesto 50, el rival puede (Fold 20%, Call 50%, Raise 30%)".
    *   **Evaluación:** Calcular el EV de cada rama ponderado por la probabilidad de la acción del rival.
*   **Pros:** Mucho mejor que el MVP. Puede planificar faroles ("Si apuesto ahora y él paga, en el River sale una carta de miedo y apuesto fuerte, él foldeará").
*   **Contras:** La calidad depende de cuán bien modelemos al rival (Opponent Modeling).

---

## 3. Recomendación: Arquitectura Modular Híbrida

Para "decidir en cualquier situación" de forma efectiva sin necesitar un cluster de GPUs hoy mismo, propongo una arquitectura **Modular Jerárquica**.

### Diseño del "Cerebro v2"

El sistema se divide en 3 capas atómicas:

1.  **Perception Layer (Percepción):**
    *   Recibe el JSON crudo.
    *   Analiza el Board (Textura: ¿Hay posibilidad de color? ¿Escalera?).
    *   Categoriza la mano del Hero (Made Hand, Draw, Air).
    *   *Nuevo:* Estima el **Rango del Villano** (basado en acciones previas).

2.  **Reasoning Layer (Razonamiento - El "Árbol"):**
    *   Genera 3-5 líneas de acción candidatas (Check-Call, Bet 33%, Bet 75%, Check-Raise).
    *   Para cada línea, simula 1 nivel de profundidad (¿Qué hará el villano?).
    *   Usa el motor de Equity (del MVP) para evaluar los nodos finales.

3.  **Decision Layer (Decisión):**
    *   Selecciona la línea con mayor EV.
    *   Aplica **Randomización** (Mixed Strategy) para no ser predecible (ej. si dos acciones tienen EV similar, elige una al azar 50/50).

### Plan de Implementación (Código)

1.  Crear clase `GameTree`.
2.  Mejorar `Evaluator` para detectar "Draws" (Proyectos), no solo manos hechas.
3.  Implementar `OpponentModel` (aunque sea básico: "El villano nunca foldea top pair").
4.  El `Brain` orquesta: `Context -> OpponentRange -> GameTree -> BestAction`.
