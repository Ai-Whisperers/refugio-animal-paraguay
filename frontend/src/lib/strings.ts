/**
 * All user-facing UI strings for Refugio Animal Paraguay.
 * Centralized here for future i18n support.
 * Tone: warm, conversational Paraguayan Spanish per UX-PRINCIPLES.md.
 */

// --- Layout / Global ---
export const SITE_TITLE = "Refugio Animal Paraguay";
export const SITE_DESCRIPTION =
  "Refugio de animales en Paraguay \u2014 adopta, dona, se voluntario. Dando a los animales una segunda oportunidad.";
export const SKIP_LINK = "Saltar al contenido principal";

// --- Navbar ---
export const NAV = {
  home: "Inicio",
  animals: "Animales",
  about: "Nosotros",
  contact: "Contacto",
  donate: "Donar",
} as const;

// --- Footer ---
export const FOOTER = {
  brand: "Refugio Animal Paraguay",
  tagline:
    "Dando a los animales una segunda oportunidad. Con base en Paraguay, apoyado por donantes de todo el mundo.",
  shelter: "Refugio",
  supportUs: "Apoyanos",
  aboutUs: "Nosotros",
  ourAnimals: "Nuestros Animales",
  contact: "Contacto",
  donate: "Donar",
  volunteer: "Ser Voluntario",
  foster: "Acogida",
  copyright: (year: number) =>
    `\u00A9 ${year} Refugio Animal Paraguay. Todos los derechos reservados.`,
} as const;

// --- Homepage ---
export const HOME = {
  heroTitle: "Cada animal merece un hogar lleno de amor",
  heroSubtitle:
    "Refugio Animal Paraguay rescata, rehabilita y encuentra hogares para animales que lo necesitan. Sumate a hacer la diferencia \u2014 adopta, dona o se voluntario.",
  meetAnimals: "Conoce nuestros animales",
  donateNow: "Donar ahora",
  statsRescued: "Animales rescatados",
  statsAdoptions: "Adopciones exitosas",
  statsVolunteers: "Voluntarios activos",
  howToHelpTitle: "\u00BFComo podes ayudar?",
  adoptTitle: "Adoptar",
  adoptDescription:
    "Dale un hogar para siempre a un animal rescatado. Explora los animales disponibles y comenza tu camino de adopcion.",
  donateTitle: "Donar",
  donateDescription:
    "Tu aporte nos ayuda a brindar alimento, refugio y atencion medica. Aceptamos donaciones en EUR y PYG.",
  volunteerTitle: "Ser Voluntario",
  volunteerDescription:
    "Unite a nuestro equipo de voluntarios. Ayuda con el cuidado diario, eventos y programas de difusion.",
} as const;

// --- Animals List ---
export const ANIMALS_LIST = {
  title: "Animales disponibles para adopcion",
  subtitle:
    "Conoce a nuestros amiguitos que buscan su hogar para siempre. Hace clic en cualquier animal para saber mas y comenzar el proceso de adopcion.",
  allSpecies: "Todas las especies",
  dogs: "Perros",
  cats: "Gatos",
  other: "Otros",
  loading: "Cargando animales...",
  errorRetry: "Intentar de nuevo",
  emptyState: "\u00A1No hay animales disponibles ahora. Volve pronto!",
  previous: "Anterior",
  next: "Siguiente",
} as const;

// --- Animal Detail ---
export const ANIMAL_DETAIL = {
  loading: "Cargando detalles...",
  notFound: "Animal no encontrado",
  backToAnimals: "Volver a animales",
  species: "Especie",
  age: "Edad",
  arrived: "Llego al refugio",
  about: (name: string) => `Sobre ${name}`,
  applyToAdopt: (name: string) => `Solicitar adopcion de ${name}`,
  notAvailable: "Este animal no esta disponible para adopcion actualmente",
  breadcrumbAnimals: "Animales",
} as const;

// --- Adoption Form ---
export const ADOPTION_FORM = {
  title: "Solicitud de Adopcion",
  subtitle: (name: string) =>
    `Completa tus datos para solicitar la adopcion de ${name}. Revisaremos tu solicitud y te contactamos lo antes posible.`,
  fullName: "Nombre completo",
  fullNamePlaceholder: "Maria Garcia",
  email: "Correo electronico",
  emailPlaceholder: "maria@ejemplo.com",
  phone: "Telefono",
  phonePlaceholder: "+595 981 123 456",
  phoneOptional: "(opcional)",
  message: "Mensaje",
  messageOptional: "(opcional)",
  messagePlaceholder:
    "Contanos sobre vos y por que te gustaria adoptar a este animal...",
  gdprTitle: "Consentimiento de Datos",
  gdprText:
    "Doy mi consentimiento para el procesamiento de mis datos personales con el fin de esta solicitud de adopcion. Mis datos seran utilizados unicamente para evaluar mi solicitud y seran tratados conforme a las regulaciones de proteccion de datos (GDPR).",
  submit: "Enviar solicitud",
  submitting: "Enviando...",
  cancel: "Cancelar",
  required: "*",
  // Validation
  nameRequired: "El nombre completo es obligatorio.",
  nameTooLong: "El nombre debe tener 255 caracteres o menos.",
  emailRequired: "El correo electronico es obligatorio.",
  emailInvalid: "Por favor ingresa un correo electronico valido.",
  phoneTooLong: "El telefono debe tener 50 caracteres o menos.",
  messageTooLong: (max: number) =>
    `El mensaje debe tener ${max} caracteres o menos.`,
  gdprRequired:
    "Debes dar tu consentimiento para el procesamiento de datos para enviar esta solicitud.",
  // Success
  successTitle: "\u00A1Solicitud enviada!",
  successMessage: (name: string, email: string) =>
    `\u00A1Gracias por tu interes en adoptar a ${name}! Recibimos tu solicitud y la revisaremos pronto. Recibiras una confirmacion en ${email}.`,
  backTo: (name: string) => `Volver a ${name}`,
  browseMore: "Ver mas animales",
  // Errors
  animalNotAvailable: "Este animal no esta disponible para adopcion actualmente.",
  submitError: "Algo salio mal al enviar. \u00BFPodes intentar de nuevo?",
} as const;

// --- Contact ---
export const CONTACT = {
  title: "Contacto",
  subtitle:
    "Tenes alguna pregunta o queres saber mas sobre el refugio? Escribinos y te respondemos lo antes posible.",
  fullName: "Nombre completo",
  email: "Correo electronico",
  subject: "Asunto",
  message: "Mensaje",
  submit: "Enviar mensaje",
  submitting: "Enviando...",
  successTitle: "\u00A1Mensaje enviado!",
  successMessage:
    "\u00A1Gracias por escribirnos! Te respondemos lo antes posible.",
  sendAnother: "Enviar otro mensaje",
} as const;

// --- Status Labels ---
export const STATUS_LABELS_ES: Record<string, string> = {
  intake: "Recien llegado",
  quarantine: "En cuarentena",
  available: "Disponible",
  foster: "En acogida",
  under_treatment: "En tratamiento",
  adopted: "Adoptado",
  deceased: "Fallecido",
} as const;

// --- Species Labels ---
export const SPECIES_LABELS: Record<string, string> = {
  dog: "Perro",
  cat: "Gato",
  other: "Otro",
} as const;

// --- Common ---
export const COMMON = {
  loading: "Cargando...",
  error: "Algo salio mal. \u00BFPodes intentar de nuevo?",
  paw: "\u{1F43E}",
} as const;

// --- Date Formatting ---
export const DATE_LOCALE = "es-PY";
export const DATE_FORMAT_OPTIONS: Intl.DateTimeFormatOptions = {
  year: "numeric",
  month: "long",
  day: "numeric",
};

/** Format a date string for display using es-PY locale. */
export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(DATE_LOCALE, DATE_FORMAT_OPTIONS);
}
