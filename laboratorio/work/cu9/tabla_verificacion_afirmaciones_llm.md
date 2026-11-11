| # | Afirmación generada por el LLM | Evidencia que respalda / contradice (en `alertas_enriquecidas.json`) | Estado de Verificación |
| :---: | :--- | :--- | :---: |
| **1** | Prioridad ALTA con score de 93.6 sobre el host `LAB_0cd6b412d0de791d`. | Coincide exactamente con `"prioridad": "ALTA"`, `"score": 93.6` y `"host": "LAB_0cd6b412d0de791d"`. | **Verificada** |
| **2** | 40 eventos generados únicamente por la fuente `suricata`. | Coincide con `"eventos": 40` y `"fuentes": ["suricata"]` (`convergencia_fuentes: 0`). | **Verificada** |
| **3** | Activación de 10 firmas distintas y componente de anomalía por ML (20 pts). | Coincide con `"firmas_distintas": 10` y `"anomalia_ML": 20` en la estructura de desglose. | **Verificada** |
| **4** | Las IPs de origen, puertos y marcas de tiempo no son determinables en los datos. | Coincide; el JSON anonimizado omite los campos de `ip.src`, `src_port` y `timestamp`. | **Verificada** |
| **5** | Pasos de investigación orientados a `flow_ids` y logs de procesos del endpoint. | Propuesta de investigación operacionalmente coherente; no inventa datos sobre el incidente. | **Verificada** |