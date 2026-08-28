Estamos desarrollando el MVP funcional de **Ruta de Recuperación**.

Quiero que evoluciones el proyecto actual sin romper lo que ya funciona.

# 1. CONCEPTO DEL PRODUCTO

La arquitectura conceptual del proyecto es:

```text
                    RUTA DE RECUPERACIÓN
                           │
              ┌────────────┴────────────┐
              ↓                         ↓
        PERSONA AFECTADA             ENTIDAD
              │                         │
        WhatsApp / Web              Dashboard
              │                         │
         DIAGNÓSTICO                  Datos
              │                         │
          SITUACIÓN               Necesidades
              │                         │
           CONTEXTO                  Recursos
              │                         │
              ↓                       Brechas
       MOTOR DE DECISIÓN              Alertas
              │                       Tendencias
       ┌──────┴──────┐                  │
       ↓             ↓                  │
 QUÉ HACER       A QUÉ ACCEDER          │
 PRIMERO                              │
       │                               │
       └──────┬────────────────────────┘
              ↓
       RUTA PERSONALIZADA
              ↓
          PASAPORTE
              ↓
            ACCIÓN
              ↓
         SEGUIMIENTO
              ↓
           IMPACTO
              ↓
       DATOS ACTUALIZADOS
              ↓
        ANÁLISIS PERIÓDICO
              ↓
           DASHBOARD
```

La persona afectada debe poder obtener una ruta personalizada.

Las entidades responsables deben poder visualizar información agregada para entender dónde están las necesidades y las brechas.

---

# 2. ESTADO ACTUAL

El proyecto utiliza:

* Python 3.12
* FastAPI
* Pydantic
* HTML
* CSS
* JavaScript
* Uvicorn

El servidor funciona actualmente en:

```text
http://127.0.0.1:8001
```

Actualmente existen:

```text
app/
├── main.py
├── schemas.py
├── services/
│   └── motor_ruta.py
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
```

Actualmente funcionan:

```text
GET /
POST /diagnostico
```

El diagnóstico tiene estos campos:

```text
municipio
actividad_economica
danos
puede_operar
necesidades
```

El motor ya genera:

```text
que_hacer_primero
ruta
```

El frontend ya permite realizar el diagnóstico y visualizar la ruta.

---

# 3. OBJETIVO DE ESTA ITERACIÓN

Convertir el proyecto actual en un MVP funcional de extremo a extremo:

```text
DIAGNÓSTICO
     ↓
SITUACIÓN
     ↓
MOTOR DE DECISIÓN
     ↓
QUÉ HACER PRIMERO
     ↓
RUTA
     ↓
PASAPORTE
     ↓
ACCIONES
     ↓
SEGUIMIENTO
     ↓
DATOS AGREGADOS
     ↓
DASHBOARD DE ENTIDAD
```

También queremos preparar:

```text
CONTEXTO
   ↓
RECURSOS / AYUDAS
   ↓
COMPATIBILIDAD
```

pero inicialmente utilizando datos DEMOSTRATIVOS.

---

# 4. BACKEND — PASAPORTE

Crear en backend una representación sencilla del Pasaporte de Recuperación.

Debe contener:

```text
id
municipio
actividad_economica
danos
necesidades
puede_operar
que_hacer_primero
ruta
progreso
estado
```

Ejemplo:

```json
{
  "id": "PAS-0001",
  "municipio": "Jojutla",
  "actividad_economica": "Taller",
  "danos": [
    "maquinaria",
    "herramientas"
  ],
  "necesidades": [
    "equipamiento",
    "dinero"
  ],
  "puede_operar": false,
  "que_hacer_primero": "Recuperar el equipamiento indispensable para volver a operar",
  "ruta": [
    "Identificar el equipamiento indispensable",
    "Determinar qué puede repararse o reemplazarse",
    "Buscar apoyo para recuperar el equipamiento",
    "Preparar la reactivación de la actividad"
  ],
  "progreso": 0,
  "estado": "En recuperación"
}
```

El ID debe generarse automáticamente.

Para este MVP NO necesitamos base de datos.

Puede utilizarse una estructura en memoria del servidor.

---

# 5. BACKEND — ALMACENAMIENTO TEMPORAL

Cada vez que se reciba:

```text
POST /diagnostico
```

se debe:

1. Validar el diagnóstico.
2. Ejecutar `generar_ruta()`.
3. Crear un Pasaporte.
4. Guardarlo temporalmente en memoria.
5. Devolver el resultado.

Esto permitirá que posteriormente el dashboard pueda utilizar los diagnósticos acumulados.

NO instalar base de datos.

NO instalar dependencias.

La memoria temporal es suficiente para esta demostración.

---

# 6. BACKEND — PASAPORTE Y ACCIONES

Crear endpoints mínimos para poder actualizar el progreso.

Por ejemplo:

```text
GET /pasaporte/{id}
```

Debe devolver el Pasaporte.

Y:

```text
PATCH /pasaporte/{id}/accion/{numero}
```

Debe permitir marcar una acción como completada.

El número de acción comienza en:

```text
0
```

La ruta tiene normalmente 4 acciones.

Al completar una acción:

```text
progreso = acciones_completadas / total_acciones * 100
```

Ejemplo:

```text
0 / 4 = 0%
1 / 4 = 25%
2 / 4 = 50%
3 / 4 = 75%
4 / 4 = 100%
```

Cuando llegue a 100:

```text
estado = "Ruta completada"
```

En caso contrario:

```text
estado = "En recuperación"
```

---

# 7. BACKEND — DATOS AGREGADOS

Crear un endpoint:

```text
GET /dashboard/resumen
```

Este endpoint debe analizar los Pasaportes almacenados temporalmente y devolver información agregada.

Como mínimo:

```text
total_afectados
total_no_operativos
total_operativos
total_rutas_completadas
por_municipio
por_actividad
por_necesidad
por_tipo_de_dano
progreso_promedio
```

Ejemplo:

```json
{
  "total_afectados": 25,
  "total_no_operativos": 14,
  "total_operativos": 11,
  "total_rutas_completadas": 5,
  "progreso_promedio": 42,
  "por_municipio": {
    "Jojutla": 15,
    "Tlaquiltenango": 10
  },
  "por_actividad": {
    "Taller": 8,
    "Tienda": 10,
    "Panadería": 7
  },
  "por_necesidad": {
    "equipamiento": 12,
    "dinero": 15,
    "reparacion": 8
  },
  "por_tipo_de_dano": {
    "maquinaria": 9,
    "infraestructura": 7
  }
}
```

Los nombres y estructura pueden adaptarse al código existente, pero deben conservar estas métricas.

---

# 8. ACTUALIZACIÓN PERIÓDICA

Queremos demostrar el concepto:

```text
Nuevos diagnósticos
        ↓
Datos acumulados
        ↓
Procesamiento periódico
        ↓
Dashboard actualizado
```

Para este MVP NO crear un sistema complejo de tareas.

El dashboard puede consultar:

```text
GET /dashboard/resumen
```

cada cierto tiempo desde JavaScript.

Usar un intervalo razonable, por ejemplo:

```text
30 segundos
```

El objetivo es demostrar que el dashboard se actualiza periódicamente.

No necesitamos todavía un scheduler externo.

NO crear Celery.

NO crear Redis.

NO crear cron.

NO crear servicios externos.

---

# 9. FRONTEND — PERSONA AFECTADA

Mantener la interfaz actual.

No rehacer completamente el diseño.

El flujo debe continuar siendo:

```text
Inicio
 ↓
Diagnóstico 3 min
 ↓
Resultado
 ↓
Ruta de recuperación
```

Agregar después del resultado una sección:

```text
MI PASAPORTE DE RECUPERACIÓN
```

Mostrar:

```text
ID del Pasaporte

Municipio

Actividad económica

Afectaciones

Necesidades

Estado

Progreso
```

Mostrar las acciones de la ruta como elementos interactivos:

```text
☐ Acción 1
☐ Acción 2
☐ Acción 3
☐ Acción 4
```

Cuando el usuario marque una acción:

```text
PATCH /pasaporte/{id}/accion/{numero}
```

Actualizar el progreso visual.

Mostrar:

```text
0%
25%
50%
75%
100%
```

Cuando llegue a 100%:

```text
Ruta completada
```

---

# 10. FRONTEND — CONTEXTO Y AYUDAS

Agregar una sección:

```text
AYUDAS QUE PUEDEN AYUDARTE
```

Por ahora utilizar únicamente recursos DEMOSTRATIVOS.

NO afirmar que son programas oficiales.

Relacionarlos con:

```text
necesidades
+
danos
```

Ejemplo:

```text
Necesidad:
equipamiento

↓

Recurso compatible:
"Apoyo demostrativo para recuperación de equipamiento"
```

Mostrar las ayudas como tarjetas.

Incluir un aviso:

```text
Los recursos mostrados en esta versión son demostrativos.
En producción se conectarían con fuentes oficiales verificadas.
```

---

# 11. FRONTEND — DASHBOARD DE ENTIDAD

Crear una segunda vista dentro del mismo frontend para representar cómo utilizaría el sistema una:

* Alcaldía
* Gobierno
* Organización humanitaria
* Cooperación

Debe ser claramente diferente de la vista de la persona afectada.

Puede utilizar una ruta como:

```text
/dashboard
```

o un botón:

```text
Vista de entidades
```

No necesitamos autenticación.

---

# 12. DASHBOARD DE ENTIDAD

El dashboard debe responder cinco preguntas:

## 1. ¿Dónde están los afectados?

Mostrar:

```text
Afectados por municipio
```

Para esta versión puede utilizarse una visualización tipo tarjetas o barras.

NO implementar todavía Google Maps.

---

## 2. ¿Qué necesitan?

Mostrar un ranking:

```text
Necesidades principales

Dinero          ██████████
Equipamiento    ████████
Reparación      █████
Insumos         ███
```

Los valores deben venir de:

```text
GET /dashboard/resumen
```

No utilizar valores escritos directamente en HTML.

---

## 3. ¿Qué está pasando?

Mostrar indicadores:

```text
Personas afectadas
Negocios no operativos
Rutas completadas
Progreso promedio
```

Agregar una sección:

```text
Tendencias
```

que muestre cambios cuando lleguen nuevos diagnósticos.

---

## 4. ¿Qué recursos existen?

Mostrar una sección de:

```text
Recursos disponibles
```

utilizando los recursos demostrativos del MVP.

---

## 5. ¿Dónde están las brechas?

Crear una tabla:

```text
Necesidad       Solicitudes
Equipamiento       XX
Dinero             XX
Reparación         XX
Insumos            XX
```

Por ahora la brecha puede representarse simplemente como demanda registrada.

NO inventar disponibilidad real de recursos.

Dejar preparada la estructura para posteriormente comparar:

```text
necesidad
-
recursos disponibles
=
brecha
```

---

# 13. DASHBOARD — ACTUALIZACIÓN

El frontend del dashboard debe consultar periódicamente:

```text
GET /dashboard/resumen
```

Por ejemplo cada 30 segundos.

Cuando existan nuevos datos, actualizar automáticamente:

* métricas
* rankings
* tendencias
* brechas

Mostrar discretamente:

```text
Última actualización: HH:MM:SS
```

Esto debe demostrar el concepto de información dinámica.

---

# 14. ARQUITECTURA DE DATOS

La estructura conceptual debe quedar preparada para evolucionar:

```text
DIAGNÓSTICOS INDIVIDUALES
        ↓
PASAPORTES
        ↓
DATOS AGREGADOS
        ↓
DASHBOARD
        ↓
TENDENCIAS
        ↓
BRECHAS
        ↓
RECOMENDACIONES
```

Posteriormente:

```text
DATOS
 ↓
PATRONES
 ↓
MACHINE LEARNING
```

pero NO implementar Machine Learning todavía.

---

# 15. WHATSAPP

NO integrar WhatsApp todavía.

Sin embargo, dejar claro en el código/documentación que posteriormente WhatsApp será otro canal de entrada:

```text
WhatsApp
   ↓
mismos datos del diagnóstico
   ↓
POST /diagnostico
```

La lógica de negocio NO debe depender del frontend.

Esto es importante.

El diagnóstico debe poder llegar mañana desde:

```text
Web
WhatsApp
otro canal
```

sin tener que reescribir el motor.

---

# 16. IA

NO agregar IA todavía.

La lógica actual basada en reglas debe mantenerse.

Posteriormente la IA podrá utilizarse para interpretar lenguaje libre, por ejemplo:

```text
"Se me dañó el horno y no tengo dinero para comprar otro"
```

y convertirlo en datos estructurados.

Pero eso queda fuera de esta iteración.

---

# 17. FUENTES REALES

NO inventar ayudas gubernamentales.

NO inventar entidades.

NO inventar enlaces.

Los recursos actuales deben estar claramente identificados como DEMOSTRATIVOS.

Posteriormente se conectarán fuentes oficiales verificadas.

---

# 18. RESTRICCIONES IMPORTANTES

NO eliminar funcionalidades actuales.

NO romper:

```text
GET /
POST /diagnostico
```

NO cambiar el puerto.

NO instalar nuevas dependencias.

NO utilizar React.

NO utilizar Vue.

NO utilizar Angular.

NO utilizar una base de datos.

NO utilizar Redis.

NO utilizar Celery.

NO utilizar cron.

NO agregar IA.

NO agregar Machine Learning.

NO integrar WhatsApp.

NO integrar Google Maps todavía.

NO crear autenticación.

NO crear login.

NO crear servicios externos.

Mantener el código sencillo y explicable.

---

# 19. ANTES DE MODIFICAR

Primero revisa:

```text
app/main.py
app/schemas.py
app/services/motor_ruta.py
app/frontend/index.html
app/frontend/style.css
app/frontend/app.js
```

Identifica cómo está construido actualmente.

Reutiliza el código existente.

No reemplaces innecesariamente archivos completos.

---

# 20. PRUEBA OBLIGATORIA

Utiliza varios diagnósticos para demostrar que el dashboard cambia.

Caso 1:

```json
{
  "municipio": "Jojutla",
  "actividad_economica": "Taller",
  "danos": [
    "maquinaria",
    "herramientas"
  ],
  "puede_operar": false,
  "necesidades": [
    "equipamiento",
    "dinero"
  ]
}
```

Caso 2:

```json
{
  "municipio": "Jojutla",
  "actividad_economica": "Tienda",
  "danos": [
    "local"
  ],
  "puede_operar": false,
  "necesidades": [
    "reparacion"
  ]
}
```

Caso 3:

```json
{
  "municipio": "Tlaquiltenango",
  "actividad_economica": "Panadería",
  "danos": [
    "equipos"
  ],
  "puede_operar": true,
  "necesidades": [
    "dinero",
    "insumos"
  ]
}
```

Después verificar:

```text
GET /dashboard/resumen
```

y comprobar que los totales y categorías cambian.

---

# 21. FLUJO FINAL QUE DEBE FUNCIONAR

La demostración completa debe ser:

```text
1. Usuario entra
        ↓
2. Realiza diagnóstico de 3 minutos
        ↓
3. Sistema identifica situación
        ↓
4. Motor genera qué hacer primero
        ↓
5. Sistema genera ruta
        ↓
6. Se crea Pasaporte
        ↓
7. Usuario marca acciones
        ↓
8. Progreso cambia
        ↓
9. Datos quedan registrados temporalmente
        ↓
10. Dashboard de entidad consulta datos
        ↓
11. Dashboard muestra necesidades agregadas
        ↓
12. Dashboard se actualiza periódicamente
```

Este flujo es el objetivo principal de esta iteración.

---

# 22. AL TERMINAR

No agregues funcionalidades adicionales.

Muéstrame:

1. Archivos modificados.
2. Estructura final del proyecto.
3. Endpoints disponibles.
4. Código relevante del almacenamiento temporal.
5. Cómo funciona el Pasaporte.
6. Cómo funciona el dashboard.
7. Cómo se actualiza periódicamente.
8. Ejemplo de `GET /dashboard/resumen`.
9. Cómo probar todo desde el navegador.
10. Qué partes están preparadas para futuras integraciones.
