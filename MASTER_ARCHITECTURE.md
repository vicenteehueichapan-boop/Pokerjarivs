# Master Architecture: Superhuman Poker AI (Jules AI Implementation)

Este documento rastrea la implementación de la "Arquitectura Maestra" basada en la convergencia de GTO, MDA y Node Locking Automatizado.

## 1. Estructura del Sistema
El proyecto ha sido reestructurado para seguir un diseño modular de microservicios:

*   **`core/`**: Lógica fundamental de poker (Reglas, Cartas, Rangos). Basado en `PokerKit`.
*   **`data/`**: Motor MDA (Mass Data Analysis).
    *   **Backend:** Diseño de esquema estrella para TimescaleDB (simulado en SQLite para dev).
    *   **Ingestión:** ETL pipeline usando `PokerKit`.
*   **`solver/`**: Controlador de Estrategia.
    *   **Cliente:** Wrapper para PioSolver UPI.
    *   **Node Locking:** Generador automático de scripts de bloqueo basado en desviación poblacional.
*   **`ai/`**: Deep Learning.
    *   **Tensores:** Codificación espacial del estado (AlphaHoldem style).
    *   **Modelos:** Definición de Value Networks (ResNet).
*   **`api/`**: Interfaz de despliegue para el agente/bot.

## 2. Estado de Implementación
*   [x] Estructura de Directorios.
*   [ ] Esquema de Base de Datos (Star Schema).
*   [ ] Pipeline ETL con PokerKit.
*   [ ] Cliente PioSolver UPI.
*   [ ] Codificación Tensorial.

## 3. Tecnologías Clave
*   **PokerKit**: Parsing y simulación de reglas.
*   **SQLAlchemy**: ORM para gestión de datos.
*   **Phevaluator**: Evaluación de manos de alto rendimiento.
*   **TimescaleDB**: (Target de despliegue) Series temporales.
