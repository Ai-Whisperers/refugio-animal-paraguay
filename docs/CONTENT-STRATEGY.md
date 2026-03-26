# Estrategia de Contenido y SEO — Refugio Animal Paraguay

---

## Objetivo del Contenido

Conectar animales del refugio con familias compatibles a través de contenido que:
1. Aparece cuando alguien busca adoptar o encuentra un animal perdido (SEO)
2. Genera confianza en el refugio como organización seria
3. Educa sobre tenencia responsable y bienestar animal
4. Impulsa donaciones recurrentes

---

## Arquitectura de Contenido

### Páginas Estáticas Obligatorias (Fase 1)

| Página | URL | Propósito |
|--------|-----|-----------|
| Homepage | `/` | Conversión principal: adoptar, donar, reportar |
| Catálogo | `/adoptar` | Listar animales disponibles |
| Cómo Adoptar | `/como-adoptar` | Guía del proceso — reduce fricción |
| Sobre Nosotros | `/nosotros` | Credibilidad, equipo, historia |
| Contacto | `/contacto` | Dirección, teléfono, WhatsApp, formulario |

### Páginas SEO de Alta Prioridad (Fase 1–2)

| Página | URL | Keyword objetivo |
|--------|-----|-----------------|
| Adoptar perro en Asunción | `/adoptar/perros` | "adoptar perro Asunción" |
| Adoptar gato en Paraguay | `/adoptar/gatos` | "adoptar gato Paraguay" |
| Animales urgentes | `/adoptar/urgentes` | "rescate animal Paraguay" |
| Cómo donar | `/donar` | "donar refugio animal Paraguay" |
| Lost & Found | `/perdidos-encontrados` | "perro perdido Asunción" |

### Páginas Adicionales (Fase 3–4)

| Página | URL |
|--------|-----|
| Blog | `/blog` |
| Galería de alumni | `/familias` |
| Voluntariado | `/voluntariado` |
| Socios y aliados | `/socios` |
| Eventos | `/eventos` |
| Veterinarias aliadas | `/veterinarias` |
| Política de privacidad | `/privacidad` |
| Términos y condiciones | `/terminos` |
| Cookies | `/cookies` |

---

## SEO Técnico

### Meta Tags por Tipo de Página

```typescript
// Perfil de animal
export const generateMetadata = async ({ params }) => {
  const animal = await getAnimal(params.id)
  return {
    title: `${animal.name} en adopción — Refugio Animal Paraguay`,
    description: `${animal.name} es un/a ${animal.breed || animal.species} de ${animal.estimatedAge} meses. ${animal.specialNeeds ? 'Necesita cuidados especiales.' : 'Sano/a y listo/a para un hogar.'} Adoptá en Asunción, Paraguay.`,
    openGraph: {
      title: `${animal.name} busca hogar en Paraguay`,
      description: `Conocé a ${animal.name} — ${animal.species} disponible para adopción`,
      images: [{ url: animal.photos[0].url, width: 1200, height: 630 }],
    },
    twitter: {
      card: 'summary_large_image',
    }
  }
}
```

### Schema.org Markup

```json
// Perfil de animal (AnimalShelter + Animal)
{
  "@context": "https://schema.org",
  "@type": "Animal",
  "name": "Luna",
  "description": "Perrita mestiza de 2 años, muy cariñosa...",
  "image": "https://res.cloudinary.com/...",
  "additionalProperty": [
    { "@type": "PropertyValue", "name": "species", "value": "Canis lupus familiaris" },
    { "@type": "PropertyValue", "name": "sex", "value": "Hembra" },
    { "@type": "PropertyValue", "name": "age", "value": "2 años" }
  ],
  "provider": {
    "@type": "AnimalShelter",
    "name": "Refugio Animal Paraguay",
    "address": { "@type": "PostalAddress", "addressLocality": "Asunción", "addressCountry": "PY" }
  }
}
```

```json
// Homepage (Organization)
{
  "@context": "https://schema.org",
  "@type": "NGO",
  "name": "Refugio Animal Paraguay",
  "url": "https://refugiopar.org",
  "logo": "...",
  "contactPoint": {
    "@type": "ContactPoint",
    "contactType": "customer service",
    "availableLanguage": ["Spanish", "Guarani"]
  },
  "sameAs": ["https://facebook.com/refugiopar", "https://instagram.com/refugiopar"]
}
```

### Sitemap y Robots

```xml
<!-- sitemap.xml (generado automáticamente por next-sitemap) -->
<url>
  <loc>https://refugiopar.org/adoptar/luna-abc123</loc>
  <changefreq>weekly</changefreq>
  <priority>0.8</priority>
</url>
```

```
# robots.txt
User-agent: *
Allow: /
Disallow: /admin
Disallow: /api
Sitemap: https://refugiopar.org/sitemap.xml
```

### Google My Business

- Registrar perfil como "Refuge for Animals" en Gran Asunción
- Categoría: "Animal Shelter" / "Refugio de animales"
- Fotos actualizadas mensualmente
- Responder reseñas (positivas y negativas)
- Publicaciones de Google Business: nuevo animal disponible, eventos

---

## Estrategia de Palabras Clave

### Tier 1 — Alto volumen, alta intención

| Keyword | Volumen est. | Dificultad | Página objetivo |
|---------|-------------|-----------|----------------|
| adoptar perro Asunción | 500–1,000/mes | Media | /adoptar/perros |
| adoptar gato Paraguay | 300–600/mes | Baja | /adoptar/gatos |
| refugio animal Paraguay | 300–800/mes | Media | / |
| perro perdido Asunción | 300–600/mes | Baja | /perdidos-encontrados |

### Tier 2 — Long tail, alta conversión

| Keyword | Página objetivo |
|---------|----------------|
| "cómo adoptar un perro en Paraguay" | /como-adoptar |
| "requisitos para adoptar un animal Paraguay" | /como-adoptar |
| "esterilización gratuita perros Asunción" | /blog/esterilizacion |
| "donar alimento refugio animal Asunción" | /donar |
| "voluntariado con animales Paraguay" | /voluntariado |
| "perro perdido San Lorenzo" | /perdidos-encontrados (filtro) |
| "cachorro gratis Asunción" | /adoptar (SEO negativo: no son "gratis") |

### Tier 3 — Informacional, construcción de audiencia

- "Ley 4840 Paraguay bienestar animal"
- "costo de tener un perro en Paraguay"
- "cómo preparar tu casa para un gato"
- "señales de maltrato animal Paraguay"
- "cómo funciona el programa foster"

---

## Plan Editorial del Blog

### Frecuencia objetivo
- Fase 4: 2 artículos/mes
- Fase 5: 4 artículos/mes

### Pilares de contenido

#### 1. Guías Prácticas (alto SEO)
- "Cómo adoptar en Paraguay: paso a paso [2025]"
- "Cuánto cuesta tener un perro en Paraguay: guía real"
- "Cómo preparar tu departamento para un gato"
- "Qué vacunas necesita tu perro en Paraguay"

#### 2. Historias de Éxito (conversión)
- "Luna encontró su hogar en Fernando de la Mora"
- "Tobby: de la calle al sofá en 3 semanas"
- Formato: Antes y después con fotos, cita del adoptante

#### 3. Educación y Bienestar (engagement + SEO long tail)
- "Señales de que tu mascota está estresada"
- "La Ley 4840 y lo que significa para los dueños de mascotas en Paraguay"
- "Por qué la esterilización salva vidas en Paraguay"

#### 4. Noticias del Refugio (confianza)
- Resumen mensual de adopciones ("En enero, 12 animales encontraron hogar")
- Nuevos ingresos urgentes
- Eventos próximos

---

## Contenido en Guaraní

### Secciones prioritarias en guaraní

| Sección | Texto en guaraní | Por qué |
|---------|-----------------|---------|
| Hero CTA | "Eheka nde irū" (Encontrá tu compañero) | Alcance rural, diferenciación |
| Cómo adoptar — título | "Mba'éichapa rejopy peteĩ mymba" | SEO guaraní |
| Botón WhatsApp | "Eñe'ẽ ore ndive" (Hablá con nosotros) | Confianza |
| Formulario — encabezado | "Ereikuaave ndejehe" (Contanos sobre vos) | Menor barrera |
| Footer | "Mymba rehegua" (Sobre los animales) | Presencia cultural |

### Internacionalización técnica

```typescript
// i18n/messages/es-PY.json
{
  "hero.cta.adopt": "¡Adoptá hoy!",
  "hero.cta.donate": "Doná al refugio",
  "catalog.filters.species.dog": "Perros",
  "catalog.filters.species.cat": "Gatos",
  "animal.status.available": "Disponible",
  "animal.status.urgent": "¡Urgente!"
}

// i18n/messages/gn.json (secciones clave)
{
  "hero.cta.adopt": "Eheka nde irū",
  "hero.cta.donate": "Eme'ẽ refugiope",
  "catalog.title": "Mymba oikotevẽva peteĩ tuvicha"
}
```

---

## Open Graph para WhatsApp

WhatsApp es el canal de sharing dominante. Las previsualizaciones deben ser atractivas.

```typescript
// Perfil de animal compartido por WhatsApp
openGraph: {
  title: "🐾 Luna busca hogar en Paraguay",
  description: "Hembra, 2 años, súper cariñosa. ¿Podés darle una familia? 🏠",
  images: [{
    url: animal.primaryPhoto,  // Imagen cuadrada 1200×1200 funciona mejor en WhatsApp
    width: 1200,
    height: 1200,
  }],
  locale: 'es_PY',
  type: 'website',
}
```

**Regla:** Las fotos de animales deben tener el animal bien encuadrado, fondo limpio, mirada hacia la cámara — optimiza el engagement en WhatsApp y Facebook.

---

## Métricas de Contenido

| Métrica | Herramienta | Meta 6 meses |
|---------|------------|-------------|
| Visitantes orgánicos/mes | GA4 | 2,000 |
| Posición promedio en GSC | Google Search Console | <30 para keywords Tier 1 |
| Click-through rate blog | GSC | >3% |
| Tiempo en página perfil de animal | GA4 | >2 minutos |
| Tasa de conversión catálogo → formulario | GA4 | >5% |
| Shares por animal en redes | Manual/GA4 | >10 por animal |
