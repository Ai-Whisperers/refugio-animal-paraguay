# Contexto Paraguay — Refugio Animal Paraguay

## Por qué este documento existe

El software construido sin considerar el contexto local falla. Este documento captura las restricciones, oportunidades y particularidades de Paraguay que informan cada decisión técnica y de producto.

---

## Conectividad e Infraestructura Digital

### Dispositivos

| Métrica | Dato |
|---------|------|
| Acceso a internet desde móvil | ~90% del tráfico web |
| Penetración de smartphones | ~78% población adulta |
| Dispositivos predominantes | Android midrange y budget (Samsung A-series, Xiaomi) |
| iOS | ~10–15% (segmento ABC1) |
| Resoluciones comunes | 360×800, 390×844, 412×915 |

### Conectividad

| Métrica | Dato |
|---------|------|
| 4G LTE | Disponible en Gran Asunción y ciudades principales |
| 3G | Presente en zonas periurbanas y rurales |
| Velocidad promedio 4G | 15–30 Mbps (vs 50+ Mbps en LATAM promedio) |
| Zonas sin señal | Interior del país (Chaco, zonas rurales del Este) |
| Latencia 4G típica | 50–100ms |

**Implicaciones de diseño:**
- Lighthouse target: LCP <2.5s en 4G emulado (throttled 4G: 9 Mbps, 170ms RTT)
- Imágenes en WebP/AVIF, máximo 150KB para thumbnails de catálogo
- Service Worker obligatorio para cache de assets y catálogo offline
- Formularios deben guardar progreso (no perder datos si se corta la señal)

---

## Pagos y Finanzas

### Medios de pago por adopción y penetración estimada

| Medio | Penetración | Notas |
|-------|-------------|-------|
| **Tigo Money** | ~60% adultos bancarizados | Primario para clases media-baja |
| **Personal Pay** | ~20% | Usuarios de Personal (Telecom) |
| **PagoExpress** | ~15% | Kioscos físicos en todo el país |
| Transferencia bancaria | ~30% adultos con cuenta | BNF, BBVA, Itaú, etc. |
| Tarjeta de débito/crédito | ~20% | Segmento ABC1 solamente |
| **Stripe** | International | Diáspora paraguaya, donantes internacionales |
| Efectivo | ~40% | Todavía preferido en sectores populares |

### Guaraní Paraguayo (PYG)

- Moneda: Guaraní (₲, código PYG)
- Tipo de cambio referencial (2025): ~1 USD ≈ 7,800 PYG
- Tarifas de adopción propuestas:
  - Cachorros: Gs. 150,000–300,000 (~$20–40 USD)
  - Adultos: Gs. 80,000–150,000 (~$10–20 USD)
  - Seniors/especiales: Gratuito

**Implicaciones técnicas:**
- Almacenar montos en enteros (PYG no tiene centavos en la práctica)
- Mostrar precios formateados: `₲ 150.000` (punto como separador de miles)
- Tigo Money API requiere contrato comercial previo (proceso 3-4 semanas)
- PagoExpress funciona con códigos de pago en kioscos físicos

---

## Comunicación y Redes Sociales

### WhatsApp

| Métrica | Dato |
|---------|------|
| Penetración de WhatsApp | ~97.5% de usuarios de internet |
| Uso como canal de soporte | Estándar en comercios y ONGs |
| WhatsApp Business | Usado por ~30% de pequeños negocios |
| WhatsApp Web | ~40% de accesos (desde PC en el trabajo) |

**Implicaciones:**
- WhatsApp es el canal de comunicación principal, no el email
- El "botón flotante de WhatsApp" en el sitio es obligatorio, no opcional
- OTP por WhatsApp > OTP por SMS (mayor tasa de entrega y confianza)
- Notificaciones de estado de solicitud DEBEN llegar por WhatsApp
- Los refugios actuales operan enteramente por grupos de WhatsApp → el sistema debe integrar ese flujo, no reemplazarlo abruptamente

### Redes Sociales

| Red | Penetración | Uso para refugios |
|-----|-------------|-------------------|
| Facebook | ~80% adultos internet | Grupos de adopción/rescate, eventos |
| Instagram | ~60% | Fotos de animales, stories |
| TikTok | ~40% (18–35 años) | Oportunidad no prioritaria |
| Twitter/X | ~10% | Irrelevante para este público |

**Facebook es el canal dominante de rescate animal en Paraguay** — grupos como "Adopciones Responsables Paraguay" tienen 50k+ miembros.

---

## Idioma

### Español Paraguayo

- El español paraguayo tiene características propias (voseo, palabras del guaraní)
- Usos específicos: "tatú" en vez de "armadillo", "mbo'e" en contexto guaraní
- Evitar castellano peninsular (vosotros, leísmo), usar estándares rioplatenses/paraguayos
- Expresiones afectivas frecuentes: "mi amor", "linda criatura", "pichón" (para animales bebés)

### Guaraní

| Dato | Valor |
|------|-------|
| Hablantes | ~80% de la población habla guaraní |
| Guaraní como primera lengua | ~30% en áreas rurales |
| Bilingüismo activo | ~50% |
| Guaraní en medios digitales | Escaso → oportunidad SEO real |

**Estrategia para el sitio:**
- Español paraguayo (es-PY) — idioma primario, todo el contenido
- Guaraní (gn) — secciones clave: homepage CTA, cómo adoptar, cómo reportar perdido
- Palabras guaraní de alta resonancia emocional para animales:
  - "Mymba" = animal
  - "Hendápe" = en su lugar / en casa
  - "Ñorairõ" = luchar (por los animales)
  - "Mborayhu" = amor / cariño

---

## Marco Legal

### Ley 4840/2013 — Protección y Bienestar Animal

**Artículos clave para el sistema de adopción:**

| Requisito | Implementación |
|-----------|----------------|
| Esterilización previa a adopción | Campo obligatorio + certificado adjunto al contrato |
| Jardín cercado declarado | Checkbox en formulario + cláusula contractual |
| Prohibición de reventa o regalo del animal | Cláusula obligatoria en contrato digital |
| Devolución obligatoria al refugio de origen | Formulario de devolución + cláusula contractual |
| Registro de adopciones | Número de registro en el contrato |

Ver [COMPLIANCE.md](COMPLIANCE.md) para implementación detallada.

### Ley 7593/2025 — Protección de Datos Personales

**Vigencia:** Marzo 2027 (período de adecuación hasta esa fecha)

| Derecho | Implementación |
|---------|----------------|
| Derecho al olvido | Eliminación de cuenta + datos en <24 horas |
| Portabilidad de datos | Exportación JSON/PDF desde el portal |
| Consentimiento informado | Banner de cookies + registro con timestamp |
| Propósito limitado | DPA con proveedores (WhatsApp, Google, Cloudinary) |
| Notificación de brechas | Proceso interno + notificación al titular en <72h |

**Dato crítico:** Aunque la ley tiene vigencia plena desde marzo 2027, implementarla desde el inicio evita reingeniería costosa. El banner de cookies con "Rechazar todo" funcional es obligatorio.

---

## Cultura y Comportamiento

### Particularidades culturales para UX

1. **Desconfianza inicial alta** hacia organizaciones digitales → necesario mostrar credenciales, equipo real, dirección física
2. **Decisión consultada en familia** → formulario compartible por WhatsApp es una feature, no un extra
3. **Preferencia por comunicación verbal** → el formulario largo puede asustar; dividir en pasos cortos
4. **Alto valor al trato personalizado** → respuesta automática debe sentirse cálida, no corporativa
5. **Sensibilidad religiosa** → evitar lenguaje secular extremo; tonos neutrales/cálidos funcionan mejor
6. **"No quedar mal"** → errores en formulario deben ser suaves, nunca agresivos

### Sobre el bienestar animal en Paraguay

- El maltrato animal era común e impune antes de la Ley 4840 → la ley fue un avance cultural importante
- **Zoonosis** (rabia, leptospirosis) es una preocupación real de salud pública
- Las ferias de adopción periódicas tienen fuerte tradición social
- Los "rescatistas independientes" (sin afiliación a refugio formal) son un actor clave en la comunidad

---

## SEO Local

### Términos de búsqueda con volumen en Paraguay

| Keyword | Estimado mensual | Intención |
|---------|-----------------|-----------|
| "adoptar perro Asunción" | 500–1,000 | Comercial |
| "perro perdido Asunción" | 200–500 | Urgente |
| "refugio animal Paraguay" | 300–800 | Informacional |
| "gato en adopción Paraguay" | 200–400 | Comercial |
| "mascota perdida Paraguay" | 100–300 | Urgente |
| "donar perros Paraguay" | 100–200 | Navegacional |
| "esterilización gratuita Paraguay" | 200–500 | Informacional |

**Google My Business** es más relevante para búsquedas locales que el SEO técnico — registro obligatorio desde Fase 1.

---

## Infraestructura del País

### Electricidad

- Suministro 220V/50Hz, estable en zonas urbanas
- Cortes frecuentes en interior del país → PWA offline es crítico para voluntarios itinerantes

### Dirección y Geolocalización

- Paraguay no tiene sistema de código postal uniforme
- Las direcciones se expresan por referencias: "calle X casi Y, barrio Z"
- Google Maps funciona bien en Gran Asunción; menos preciso en interior
- Para Lost & Found: permitir pin en mapa + descripción textual como alternativa

### Dispositivos de Staff del Refugio

- PC de escritorio: generalmente Windows 10, Chrome actualizado
- Tablets: Android midrange compartidas entre voluntarios
- El admin debe funcionar perfectamente en ambos contextos
