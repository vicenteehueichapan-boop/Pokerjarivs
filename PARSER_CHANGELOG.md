# Parser Changelog

## Version 2.1 (2024-11-22)

### 🐛 Bug Fixes
- **Compatibilidad**: Agregado campo `accion` explícito en el diccionario de retorno del adaptador `parse_deepseek_response` para mantener compatibilidad con tests y código legacy que espera esa clave específica.

## Version 2.0 (2024-11-22)

### 🐛 Bug Fix Crítico
- **Problema**: Regex `r'\{[^}]+\}'` fallaba con JSON anidado
- **Impacto**: Decisiones incorrectas cuando JSON contenía objetos como `contexto: {...}`
- **Solución**: Implementado extractor de JSON balanceado con contador de llaves

### ✨ Nuevas Características

#### Múltiples Métodos de Extracción (Cascada)
1. **Markdown Code Blocks** (Prioridad Alta)
   - Extrae JSON de bloques ```json ... ```
   - Soporta con y sin label 'json'
   - Limpia comentarios estilo JS (`//`)

2. **Balanced JSON Extraction** (Prioridad Media)
   - Usa contador de llaves para manejar anidamiento
   - Ignora llaves dentro de strings
   - Encuentra cierre balanceado correcto

3. **Simple JSON** (Fallback)
   - Regex greedy para casos simples
   - Funciona si JSON es lo único en el texto

4. **Text Parsing** (Último Recurso)
   - Busca keywords (FOLD, CHECK, BET, etc.)
   - Solo se activa si JSON no encontrado

#### Logging Detallado
- Log de cada método intentado
- Log del método exitoso
- Warnings cuando se usa fallback

#### Validación Robusta
- Campos obligatorios verificados
- Normalización a lowercase
- Defaults para campos opcionales
- Validación de acciones válidas

### 📊 Mejoras de Testing
- 4 test cases agregados en `tests/test_parser_upgrade.py`
- Cobertura de JSON anidado hasta 3+ niveles
- Test de markdown blocks
- Test de fallback a texto

### 🔧 Backward Compatibility
- Función `parse_deepseek_response()` mantenida
- Signature idéntica
- Código existente no requiere cambios

### 📈 Métricas
- Líneas de código: ~50 → ~250
- Métodos de extracción: 1 → 4
- Robustez: Alta (maneja anidamiento arbitrario)

