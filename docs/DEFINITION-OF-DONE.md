# Definition of Done — Refugio Animal Paraguay

## ¿Qué es esto?

Los criterios que TODA historia o tarea debe cumplir para considerarse completada. Aplica a todo el equipo de desarrollo, sin excepciones.

---

## Nivel 1 — Código

- [ ] El código está en el repositorio en una rama feature (`feat/...`, `fix/...`)
- [ ] No hay `console.log`, `debugger`, ni código comentado sin justificación
- [ ] No hay TypeScript `any` sin comentario explicando por qué es necesario
- [ ] No hay variables declaradas y no usadas
- [ ] Las funciones tienen un propósito único y claro
- [ ] El código pasa `eslint` sin errores ni warnings
- [ ] El código pasa `tsc --noEmit` sin errores de tipos

---

## Nivel 2 — Funcionalidad

- [ ] La feature cumple todos los criterios de aceptación definidos en la historia
- [ ] La feature funciona en Chrome (última versión) en Android móvil
- [ ] La feature funciona en Safari (última versión) en iPhone
- [ ] La feature funciona en Chrome/Firefox desktop
- [ ] Los formularios validan correctamente (campos requeridos, formatos, mensajes de error claros)
- [ ] Los estados de carga (skeleton/spinner) están implementados — no pantalla en blanco
- [ ] Los estados de error (red, servidor) están manejados y muestran mensaje útil al usuario
- [ ] Los estados vacíos ("no hay animales disponibles") tienen un mensaje amigable

---

## Nivel 3 — Performance

- [ ] Las imágenes nuevas usan el componente `<Image>` de Next.js (no `<img>`)
- [ ] Las imágenes tienen `alt` descriptivo
- [ ] Las imágenes cargadas desde Cloudinary usan transformaciones optimizadas (WebP, tamaño correcto)
- [ ] No se realiza fetching de datos innecesario (evitar N+1 queries)
- [ ] Las páginas nuevas tienen Lighthouse score ≥ 80 en Mobile (4G throttled)
- [ ] El bundle size del feature no excede +20KB gzipped sin justificación

---

## Nivel 4 — Seguridad

- [ ] Los inputs de usuario se sanean antes de persistir en BD (Prisma por defecto previene SQLi)
- [ ] Las rutas de API que modifican datos verifican autenticación y autorización
- [ ] Los datos sensibles (tokens, passwords) no aparecen en logs ni en respuestas de API
- [ ] Los endpoints públicos tienen rate limiting configurado
- [ ] No hay secretos hardcodeados — usar variables de entorno

---

## Nivel 5 — Accesibilidad

- [ ] El contraste de texto nuevo cumple WCAG AA (4.5:1 mínimo)
- [ ] Los nuevos inputs tienen `<label>` asociado (no solo placeholder)
- [ ] Los botones tienen texto descriptivo (no solo íconos sin aria-label)
- [ ] Las notificaciones de error usan `role="alert"` o `aria-live`
- [ ] Los modals/dialogs tienen `role="dialog"` y manejan focus trap

---

## Nivel 6 — Internacionalización

- [ ] El texto visible en la UI usa claves de i18n (`t('clave')`) — no strings hardcodeados en español
- [ ] Las claves nuevas están definidas en `/i18n/messages/es-PY.json`
- [ ] Las fechas se formatean con `Intl.DateTimeFormat` usando el locale `es-PY`
- [ ] Los montos en guaraníes se formatean: `₲ 150.000` (sin decimales, punto como separador)

---

## Nivel 7 — Testing

- [ ] Lógica de negocio nueva tiene tests unitarios (Vitest)
- [ ] Flujos críticos nuevos tienen test E2E (Playwright):
  - Nuevo flujo de adopción → test E2E obligatorio
  - Nuevo flujo de pago → test E2E obligatorio
  - Nuevo flujo de admin → test E2E obligatorio
- [ ] Los tests pasan en CI (GitHub Actions) sin flakiness
- [ ] La cobertura de código no disminuye con el merge

---

## Nivel 8 — Revisión y Merge

- [ ] Pull Request creado con descripción que incluye: qué hace, cómo probar, screenshots si hay UI
- [ ] Al menos 1 aprobación del PR antes de merge a `main`
- [ ] El PR está actualizado con `main` (sin conflictos)
- [ ] El PR pasa todos los checks de CI (lint, types, tests, Lighthouse)
- [ ] El PR fue probado en el entorno de staging antes del merge a producción

---

## Criterios adicionales por tipo de tarea

### Tarea de base de datos / migración

- [ ] La migración es reversible (tiene `down` o es aditiva)
- [ ] Los índices necesarios están creados (para búsquedas frecuentes)
- [ ] La migración fue probada en staging antes de ejecutar en producción

### Tarea de integración externa (WhatsApp, pagos, etc.)

- [ ] El webhook maneja idempotencia (reintento del mismo evento no crea duplicados)
- [ ] El webhook valida la firma/autenticidad de la fuente (HMAC o equivalente)
- [ ] El comportamiento en caso de falla de la integración está definido y no rompe el flujo principal

### Tarea de admin / panel interno

- [ ] Las acciones destructivas (rechazar solicitud, eliminar animal) piden confirmación
- [ ] Las acciones tienen logging (quién hizo qué y cuándo)
- [ ] Los roles de usuario están correctamente verificados (un voluntario no puede aprobar adopciones)

### Tarea de cumplimiento legal

- [ ] La funcionalidad fue revisada contra los requisitos en [COMPLIANCE.md](COMPLIANCE.md)
- [ ] Si involucra datos personales, el consentimiento del usuario fue verificado antes de procesar

---

## Checklist rápido para self-review antes de abrir PR

```
□ ¿Funciona en el celular?
□ ¿Funciona sin conexión / con conexión lenta?
□ ¿Los estados de error están cubiertos?
□ ¿Pasé el linter?
□ ¿Escribí los tests necesarios?
□ ¿Hay strings hardcodeados en español que deberían estar en i18n?
□ ¿Hay datos sensibles expuestos?
□ ¿El PR tiene descripción y screenshots?
```
