## Tarea 9 — Integración avanzada de wellness

**Por qué:** Los datos de bienestar ya se capturan pero no tienen impacto en ninguna decisión. Esta tarea convierte esos datos en inteligencia accionable para el trainer y el cliente.

**Backend:**
1. **Correlación wellness vs volumen** (`services/wellness_insights.py`):
   - Para cada semana: promedio de fatiga vs volumen de esa semana y la siguiente.
   - Endpoint: `GET /clients/{id}/wellness-correlation?from=&to=` → pares `{ date, avg_fatigue, volume_this_week, volume_next_week }`.
   - El trainer puede ver: "cuando fatiga > 4, el volumen cae 30% la semana siguiente" → señal de deload.

2. **Alerta de sobrecarga** (en el mismo servicio):
   - Si `muscle_fatigue >= 4` por 3+ días seguidos → `overload_alert: true` en el endpoint del cliente.
   - Incluir en `GET /clients/{id}/wellness-summary` → `{ overload_alert, avg_fatigue_7d, avg_energy_7d, readiness_score }`.

3. **Readiness score**:
   - `readiness = (energy * 0.4 + (6 - fatigue) * 0.4 + sleep_quality * 0.2)` — normalizado 1–10.
   - Disponible en el summary del día para el cliente.

**Frontend:**
1. **Wellness como checkpoint en day progress bar**:
   - El `DayProgressBar.vue` (o equivalente) tiene actualmente: entrenamiento, comidas, agua, métricas.
   - Agregar un 5º checkpoint: "Bienestar registrado hoy".
   - Incentiva el registro diario y completa el cuadro visual del día.

2. **Alerta visual en ClientProfileView.vue (trainer)**:
   - Badge naranja "⚠ Sobrecarga" si `overload_alert: true`.
   - Tooltip: "Fatiga ≥ 4 por 3+ días consecutivos".

3. **Readiness score en dashboard del cliente**:
   - Card pequeña: "Tu disposición hoy: 7.2 / 10" con ícono de batería o color.
   - Solo visible si el cliente registró bienestar hoy.

4. **Gráfica superpuesta wellness + volumen (trainer)**:
   - En `MetricsView.vue` — gráfica de doble eje: barras de volumen semanal + línea de fatiga promedio.
   - Usa los datos de `wellness-correlation`.

**Archivos afectados:**
- `trainerGM/app/services/wellness_insights.py` (nuevo)
- `trainerGM/app/routers/wellness.py` (ampliar con nuevos endpoints)
- `gym-trainer-client/vue/components/DayProgressBar.vue` (agregar checkpoint wellness)
- `gym-trainer-client/vue/views/trainer/ClientProfileView.vue` (badge sobrecarga)
- `gym-trainer-client/vue/views/client/DashboardView.vue` (readiness card)
- `gym-trainer-client/vue/views/trainer/MetricsView.vue` (gráfica superpuesta)

**Criterio de aceptación:**
- El wellness cuenta como checkpoint en el day progress bar del cliente.
- Si un cliente tiene fatiga ≥ 4 por 3+ días, el trainer ve la alerta en su perfil.
- El trainer puede ver la gráfica superpuesta fatiga vs volumen para tomar decisiones de deload.

  Contrato para el backend                                                                                                          
                                                            
  1. GET /clients/{id}/wellness-summary                                                                                             
  {                                                         
    "overload_alert": true,                                         
    "avg_fatigue_7d": 4.2,                                  
    "avg_energy_7d": 2.8, 
    "readiness_score": 5.6,
    "today_entry": { "energy": 3, "sleep_quality": 4, "muscle_fatigue": 5 } | null                                                  
  }                                                        
  2. GET /clients/{id}/wellness-correlation?from=&to=       
  {                                                                                                                                 
    "points": [                                             
      { "week": "2026-03-03", "avg_fatigue": 3.2, "volume": 12500 },                                                                
      { "week": "2026-03-10", "avg_fatigue": 4.5, "volume": 8200 }  
    ]                                                                                                                               
  }
  Fórmulas:                                                                                                                         
  - readiness_score = (energy * 0.4 + (6 - fatigue) * 0.4 + sleep_quality * 0.2) normalizado 1-10
  - overload_alert = muscle_fatigue >= 4 por 3+ días consecutivos   