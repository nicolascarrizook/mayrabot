# Guía del Sistema de Personalización de Macronutrientes

## Resumen de Implementación

El sistema ahora permite una personalización completa de la distribución de macronutrientes con las siguientes características:

### 1. Nuevos Objetivos de Peso
- **Bajar 0.25 kg/semana**: Déficit de 250 kcal/día
- **Bajar 0.75 kg/semana**: Déficit de 750 kcal/día
- **Subir 0.25 kg/semana**: Superávit de 250 kcal/día
- **Subir 0.75 kg/semana**: Superávit de 750 kcal/día

### 2. Niveles de Proteína Personalizados
- **Muy baja (0.5-0.8 g/kg)**: Para patologías renales
- **Conservada (0.8-1.2 g/kg)**: Nivel normal
- **Moderada (1.2-1.6 g/kg)**: Personas activas no deportistas
- **Alta (1.6-2.2 g/kg)**: Uso deportivo
- **Muy alta (2.2-2.8 g/kg)**: Deportistas de alto rendimiento
- **Extrema (3.0-3.5 g/kg)**: Atletas en ciclos especiales

### 3. Ajustes de Carbohidratos
- Rango: -50% a +50% en intervalos de 5%
- La base depende del objetivo:
  - **Pérdida de peso**: Base 40% (enfoque en saciedad)
  - **Ganancia de peso**: Base 50% (más energía)
  - **Mantenimiento**: Base 45% (equilibrio)

### 4. Personalización de Grasas
- Rango: 20% a 45% en intervalos de 5%
- Opción automática que calcula el restante para completar 100%

## Flujo de Usuario

1. El usuario selecciona su objetivo (incluye nuevas opciones)
2. Sistema muestra la distribución base según objetivo
3. Usuario decide si quiere personalizar macros
4. Si personaliza:
   - Selecciona nivel de proteína
   - Ajusta carbohidratos (opcional)
   - Define grasas o deja automático
5. Sistema valida que macros sumen 100%

## Lógica de Cálculo

### Distribución Base por Objetivo
```python
# Pérdida de peso (cualquier déficit)
base_carbs = 40%
base_protein = 25-30%
base_fats = 30-35%

# Ganancia de peso (cualquier superávit)
base_carbs = 50%
base_protein = 20-25%
base_fats = 25-30%

# Mantenimiento
base_carbs = 45%
base_protein = 25%
base_fats = 30%
```

### Aplicación de Ajustes
1. **Proteína**: Se calcula en base a g/kg de peso corporal
2. **Carbohidratos**: Base × (1 + ajuste/100)
3. **Grasas**: Especificado o calculado como restante

### Validaciones
- Proteína máxima: 40% de calorías totales
- Carbohidratos: 20-65% del total
- Grasas: 15-45% del total
- Total debe sumar 100% (±2% tolerancia)

## Ejemplos de Uso

### Ejemplo 1: Deportista buscando perder grasa
- Objetivo: Bajar 0.5 kg/semana
- Proteína: Alta (1.9 g/kg)
- Carbohidratos: -20% (base 40% × 0.8 = 32%)
- Grasas: Automático

### Ejemplo 2: Persona con patología renal
- Objetivo: Mantenimiento
- Proteína: Muy baja (0.65 g/kg)
- Carbohidratos: Sin ajuste (45%)
- Grasas: 35%

### Ejemplo 3: Atleta en volumen
- Objetivo: Subir 0.75 kg/semana
- Proteína: Muy alta (2.5 g/kg)
- Carbohidratos: +20% (base 50% × 1.2 = 60%)
- Grasas: Automático

## Consideraciones Técnicas

- Los cálculos se realizan en `plan_generator.py`
- La interfaz de usuario está en `new_plan_handler.py`
- Los modelos de datos están en `patient.py`
- Las validaciones garantizan planes nutricionalmente seguros