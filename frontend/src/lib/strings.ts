/**
 * All user-facing UI strings for Refugio Animal Paraguay.
 * Centralized here for future i18n support.
 * Tone: warm, conversational Paraguayan Spanish per UX-PRINCIPLES.md.
 */

// --- Layout / Global ---
export const SITE_TITLE = "Refugio Animal Paraguay";
export const SITE_DESCRIPTION =
  "Refugio de animales en Paraguay — adopta, dona, se voluntario. Dando a los animales una segunda oportunidad.";
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
    `© ${year} Refugio Animal Paraguay. Todos los derechos reservados.`,
} as const;

// --- Homepage ---
export const HOME = {
  heroTitle: "Cada animal merece un hogar lleno de amor",
  heroSubtitle:
    "Refugio Animal Paraguay rescata, rehabilita y encuentra hogares para animales que lo necesitan. Sumate a hacer la diferencia — adopta, dona o se voluntario.",
  meetAnimals: "Conoce nuestros animales",
  donateNow: "Quiero donar",
  statsRescued: "Animales rescatados",
  statsAdoptions: "Adopciones exitosas",
  statsVolunteers: "Voluntarios activos",
  howToHelpTitle: "¿Como podes ayudar?",
  adoptTitle: "Adoptar",
  adoptDescription:
    "Dale un hogar para siempre a un animal rescatado. Explora los animales disponibles y comenza tu camino de adopcion.",
  donateTitle: "Donar",
  donateDescription:
    "Tu aporte nos ayuda a brindar alimento, refugio y atencion medica. Aceptamos donaciones en EUR y PYG.",
  volunteerTitle: "Ser Voluntario",
  volunteerDescription:
    "Unite a nuestro equipo de voluntarios. Ayuda con el cuidado diario, eventos y programas de difusion.",
  trustTeamTitle: "Nuestro Equipo",
  trustTeam: [
    { name: "Ana Rodriguez", role: "Directora del Refugio" },
    { name: "Dr. Carlos Benitez", role: "Veterinario Principal" },
    { name: "Laura Gomez", role: "Coordinadora de Adopciones" },
    { name: "Miguel Torres", role: "Coordinador de Voluntarios" },
  ],
  trustLocationTitle: "Donde Encontrarnos",
  trustAddress: "Asuncion, Paraguay",
  trustHours: "Lunes a Sabado: 8:00 - 17:00",
  trustWhatsApp: "+595 981 000 000",
  trustEmail: "contacto@refugio.org.py",
  socialProofTitle: "Historias de Adopcion",
  testimonials: [
    {
      quote: "Adoptamos a Max hace 6 meses y cambio nuestras vidas. Cada dia nos despierta con alegria.",
      name: "Maria y Juan",
      animal: "Max (perro)",
    },
    {
      quote: "Mia era tímida cuando llego, pero con amor encontro confianza y ahora es la mascota mas feliz del barrio.",
      name: "Sofia",
      animal: "Mia (gata)",
    },
    {
      quote: "No podemos imaginar la vida sin Buddy. Gracias al refugio por hacernos una familia completa.",
      name: "Los Martinez",
      animal: "Buddy (perro)",
    },
  ],
  footerCtaText: "Cada adopcion, donacion o hora de voluntariado hace una diferencia enorme.",
  footerCtaWhatsApp: "Escribinos por WhatsApp",
  footerCtaDonate: "Hacer una donacion",
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
  emptyTitle: "No encontramos animales con esos filtros",
  emptySubtitle:
    "Proba quitando algun filtro o busca con otras palabras. Siempre hay nuevos amiguitos llegando.",
  emptyClearFilters: "Limpiar filtros",
  emptyNoAnimals: "No hay animales disponibles ahora. Volve pronto!",
  errorTitle: "Algo salio mal al cargar los animales",
  errorSubtitle: "Por favor intenta de nuevo. Si el problema persiste, contactanos por WhatsApp.",
  previous: "Anterior",
  next: "Siguiente",
  meetAnimal: (name: string) => `Conocer a ${name}`,
  // Filter labels
  filterSpecies: "Especie",
  filterSize: "Tamano",
  filterAge: "Edad",
  filterSearch: "Buscar por nombre...",
  filterActiveCount: (count: number) =>
    count === 1 ? "1 filtro activo" : `${count} filtros activos`,
  filterClear: "Limpiar",
  // Size options
  sizeAll: "Todos",
  sizeSmall: "Pequeno",
  sizeMedium: "Mediano",
  sizeLarge: "Grande",
  // Age options
  ageAll: "Todas",
  agePuppy: "Cachorro (<1 ano)",
  ageYoung: "Joven (1-3)",
  ageAdult: "Adulto (3-8)",
  ageSenior: "Senior (8+)",
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
  successTitle: "¡Solicitud enviada!",
  successMessage: (name: string, email: string) =>
    `¡Gracias por tu interes en adoptar a ${name}! Recibimos tu solicitud y la revisaremos pronto. Recibiras una confirmacion en ${email}.`,
  backTo: (name: string) => `Volver a ${name}`,
  browseMore: "Ver mas animales",
  // Errors
  animalNotAvailable: "Este animal no esta disponible para adopcion actualmente.",
  submitError: "Algo salio mal al enviar. ¿Podes intentar de nuevo?",
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
  successTitle: "¡Mensaje enviado!",
  successMessage:
    "¡Gracias por escribirnos! Te respondemos lo antes posible.",
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

// --- About Page ---
export const ABOUT = {
  title: "Sobre Nosotros",
  metaDescription:
    "Conoce la historia, mision y equipo de Refugio Animal Paraguay.",
  heroTitle: "Nuestra Mision",
  heroSubtitle:
    "Refugio Animal Paraguay nacio con un sueno simple: que ningun animal en Paraguay sufra abandono o maltrato. Rescatamos, rehabilitamos y encontramos hogares amorosos para cada animal que llega a nuestras puertas.",
  historyTitle: "Nuestra Historia",
  historyP1:
    "Fundado por un grupo de amantes de los animales con raices en los Paises Bajos y Paraguay, Refugio Animal Paraguay combina la pasion latinoamericana con estandares europeos de bienestar animal.",
  historyP2:
    "Lo que empezo como un esfuerzo voluntario para rescatar animales callejeros en Asuncion se convirtio en un refugio completo, con instalaciones de cuarentena, atencion veterinaria y un programa de adopcion estructurado.",
  historyP3:
    "Hoy contamos con una red de donantes internacionales, voluntarios locales y familias de acogida que hacen posible nuestra labor diaria.",
  teamTitle: "Nuestro Equipo",
  teamMembers: [
    { name: "Ana Rodriguez", role: "Directora del Refugio" },
    { name: "Dr. Carlos Benitez", role: "Veterinario Principal" },
    { name: "Laura Gomez", role: "Coordinadora de Adopciones" },
    { name: "Miguel Torres", role: "Coordinador de Voluntarios" },
  ],
  locationTitle: "Donde Estamos",
  locationAddress: "Asuncion, Paraguay",
  locationHours: "Lunes a Sabado: 8:00 - 17:00",
  locationVisit:
    "Coordina tu visita con anticipacion por WhatsApp para conocer a nuestros animales.",
  impactTitle: "Nuestro Impacto",
  impactStats: [
    { value: "150+", label: "Animales rescatados" },
    { value: "80+", label: "Adopciones exitosas" },
    { value: "50+", label: "Voluntarios activos" },
    { value: "200+", label: "Atenciones veterinarias" },
  ],
  ctaTitle: "Sumate a nuestra causa",
  ctaSubtitle:
    "Cada adopcion, donacion o hora de voluntariado hace una diferencia enorme en la vida de un animal.",
  ctaAdopt: "Adoptar un animal",
  ctaDonate: "Hacer una donacion",
} as const;

// --- Donate Page ---
export const DONATE = {
  title: "Donar",
  metaDescription:
    "Dona a Refugio Animal Paraguay. Tu aporte nos ayuda a rescatar, alimentar y dar atencion veterinaria a animales.",
  heroTitle: "Tu donacion transforma vidas",
  heroSubtitle:
    "Cada guarani y cada euro que donas se convierte en alimento, medicina y refugio para animales que no tienen a nadie mas.",
  howHelpsTitle: "Como ayuda tu donacion",
  howHelps: [
    { icon: "\u{1F35B}", title: "Alimento", description: "Alimentamos a mas de 50 animales diariamente con alimento balanceado y suplementos.", amount: "Gs. 50.000/mes" },
    { icon: "\u{1F3E5}", title: "Atencion Veterinaria", description: "Vacunas, esterilizaciones, cirugias de emergencia y tratamientos continuos.", amount: "Gs. 150.000/mes" },
    { icon: "\u{1F3E0}", title: "Mantenimiento", description: "Reparaciones, limpieza y servicios basicos para las instalaciones del refugio.", amount: "Gs. 100.000/mes" },
    { icon: "\u{1F698}", title: "Operaciones de Rescate", description: "Transporte y recursos para rescatar animales en situacion de calle o maltrato.", amount: "Gs. 75.000/mes" },
  ],
  donateOptionsTitle: "Opciones de Donacion",
  bankTransferTitle: "Transferencia Bancaria (Paraguay)",
  bankDetails: [
    { label: "Banco", value: "Banco Itau Paraguay" },
    { label: "Tipo", value: "Cuenta Corriente" },
    { label: "Titular", value: "Refugio Animal Paraguay" },
    { label: "RUC", value: "80000000-0" },
  ],
  bankNote:
    "Envia tu comprobante por WhatsApp para que podamos agradecerte y emitir tu recibo.",
  euTitle: "Donantes de la Union Europea",
  euDescription:
    "Aceptamos donaciones en EUR via transferencia SEPA. Tu aporte esta sujeto a beneficios fiscales segun la legislacion de tu pais.",
  euComingSoon:
    "Estamos configurando pagos online con Stripe para donaciones con tarjeta en EUR. Mientras tanto, contactanos por WhatsApp.",
  otherWaysTitle: "Otras Formas de Ayudar",
  otherWays: [
    { icon: "\u{1F4E6}", title: "Donacion de Insumos", description: "Alimento, mantas, medicamentos, productos de limpieza. Coordinamos el retiro." },
    { icon: "\u{2764}\u{FE0F}", title: "Apadrina un Animal", description: "Cubri los gastos mensuales de un animal. Recibis actualizaciones y fotos." },
    { icon: "\u{1F91D}", title: "Dona tu Tiempo", description: "Unite como voluntario. Necesitamos ayuda en cuidado diario, transporte y eventos." },
  ],
  transparencyTitle: "Transparencia",
  transparencyText:
    "Nos comprometemos a la transparencia total. Publicamos informes periodicos sobre el uso de fondos. Cada donante merece saber como se usa su contribucion.",
  whatsappCta: "Consultas sobre donaciones",
  whatsappNumber: "+595 981 000 000",
} as const;

// --- Volunteer Page ---
export const VOLUNTEER = {
  title: "Ser Voluntario",
  metaDescription: "Unite como voluntario a Refugio Animal Paraguay. Ayuda con el cuidado diario, eventos y mas.",
  heroTitle: "Tu tiempo hace la diferencia",
  heroSubtitle: "Nuestros voluntarios son el corazon del refugio. Sin su dedicacion, nada de lo que hacemos seria posible. Unite y cambia vidas.",
  activitiesTitle: "Que hacen nuestros voluntarios",
  activities: [
    { icon: "\u{1F436}", title: "Cuidado Diario", description: "Alimentacion, paseos, socializacion y carino para los animales del refugio." },
    { icon: "\u{1F3C3}", title: "Transporte", description: "Llevar animales a consultas veterinarias, eventos de adopcion y hogares de acogida." },
    { icon: "\u{1F389}", title: "Eventos", description: "Organizar y participar en ferias de adopcion, campanas de concientizacion y recaudacion." },
    { icon: "\u{1F4F8}", title: "Difusion", description: "Fotos, videos y publicaciones en redes sociales para dar visibilidad a los animales." },
  ],
  requirementsTitle: "Requisitos",
  requirements: [
    "Ser mayor de 16 anos (menores con autorizacion de un tutor)",
    "Disponibilidad minima de 4 horas por semana",
    "Amor por los animales y ganas de aprender",
    "No se requiere experiencia previa — te capacitamos",
  ],
  howToJoinTitle: "Como unirte",
  howToJoinSteps: [
    { step: "1", title: "Contactanos", description: "Escribinos por WhatsApp para expresar tu interes." },
    { step: "2", title: "Orientacion", description: "Te damos una charla sobre el refugio, nuestros procesos y los animales." },
    { step: "3", title: "Empeza", description: "Eleji tus horarios y empeza a hacer la diferencia desde el primer dia." },
  ],
  testimonialTitle: "Lo que dicen nuestros voluntarios",
  testimonials: [
    { quote: "Ser voluntario aca me cambio la vida. Cada dia es una oportunidad de hacer algo significativo.", name: "Sofia M.", role: "Voluntaria desde 2024" },
    { quote: "El equipo es increible y los animales te llenan el corazon. No hay mejor forma de pasar un sabado.", name: "Marcos L.", role: "Voluntario de fin de semana" },
  ],
  ctaTitle: "Queres ser voluntario?",
  whatsappNumber: "+595 981 000 000",
} as const;

// --- Foster Page ---
export const FOSTER = {
  title: "Acogida Temporal",
  metaDescription: "Ofrece tu hogar temporalmente a un animal del refugio. Programa de acogida de Refugio Animal Paraguay.",
  heroTitle: "Un hogar temporal, un impacto permanente",
  heroSubtitle: "La acogida temporal salva vidas. Al abrir tu hogar a un animal, le das el tiempo y el espacio que necesita para recuperarse y encontrar su familia definitiva.",
  howItWorksTitle: "Como funciona",
  howItWorksSteps: [
    { step: "1", title: "Aplica", description: "Contactanos por WhatsApp y contanos sobre tu hogar y disponibilidad." },
    { step: "2", title: "Evaluacion", description: "Conversamos sobre el tipo de animal que mejor se adapta a tu situacion." },
    { step: "3", title: "Recibis al animal", description: "Te entregamos al animal con todo lo necesario: alimento, medicamentos e indicaciones." },
    { step: "4", title: "Acompanamiento", description: "Nuestro equipo te acompana durante todo el proceso con visitas y consultas veterinarias." },
  ],
  requirementsTitle: "Que necesitas",
  requirements: [
    { icon: "\u{1F3E0}", title: "Espacio adecuado", description: "Un ambiente seguro y tranquilo donde el animal se sienta comodo." },
    { icon: "\u{23F0}", title: "Tiempo y dedicacion", description: "Compromiso de al menos 2 semanas. La duracion varia segun las necesidades del animal." },
    { icon: "\u{2764}\u{FE0F}", title: "Paciencia y amor", description: "Algunos animales vienen de situaciones dificiles y necesitan tiempo para confiar." },
  ],
  shelterProvides: "El refugio cubre alimento, medicamentos, vacunas y atencion veterinaria. Vos pones el carino.",
  faqTitle: "Preguntas frecuentes",
  faqs: [
    { question: "Cuanto tiempo dura la acogida?", answer: "Generalmente entre 2 semanas y 2 meses, dependiendo de las necesidades del animal y la velocidad de adopcion." },
    { question: "Que pasa si el animal se enferma?", answer: "Nuestro veterinario se encarga. Solo tenes que avisarnos y coordinamos la atencion." },
    { question: "Puedo elegir que animal acoger?", answer: "Si. Te presentamos opciones que se adapten a tu hogar y estilo de vida." },
    { question: "Que pasa si me enamoro y quiero adoptarlo?", answer: "Pasa seguido y nos encanta. Tenes prioridad de adopcion como familia de acogida." },
  ],
  ctaTitle: "Queres ser familia de acogida?",
  ctaSubtitle: "Contactanos por WhatsApp y te contamos todo lo que necesitas saber.",
  whatsappNumber: "+595 981 000 000",
} as const;

// --- Common ---
export const COMMON = {
  loading: "Cargando...",
  error: "Algo salio mal. ¿Podes intentar de nuevo?",
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
