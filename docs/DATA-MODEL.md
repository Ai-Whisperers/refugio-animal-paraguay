# Modelo de Datos — Refugio Animal Paraguay

## Entidades Principales

### Animal

```prisma
model Animal {
  id                String          @id @default(cuid())
  internalCode      String          @unique  // Código interno del refugio (ej: RAP-2025-001)
  name              String
  species           Species         // PERRO | GATO | OTRO
  breed             String?
  estimatedAge      Int?            // En meses
  sex               Sex             // MACHO | HEMBRA | DESCONOCIDO
  size              Size            // PEQUEÑO | MEDIANO | GRANDE | EXTRA_GRANDE
  weightKg          Decimal?
  color             String
  status            AnimalStatus    // DISPONIBLE | EN_FOSTER | PENDIENTE | ADOPTADO | FALLECIDO | TRANSFERIDO

  // Temperamento y comportamiento
  energyLevel       Int             @default(3)  // 1-5
  goodWithKids      Boolean?
  goodWithDogs      Boolean?
  goodWithCats      Boolean?
  temperamentNotes  String?
  behavioralNeeds   String?

  // Salud
  vaccinated        Boolean         @default(false)
  sterilized        Boolean         @default(false)
  sterilizationDate DateTime?
  microchipped      Boolean         @default(false)
  microchipNumber   String?
  specialNeeds      Boolean         @default(false)
  specialNeedsDesc  String?

  // Clasificaciones especiales
  isUrgent          Boolean         @default(false)
  longStay          Boolean         @default(false)  // +30 días

  // Ingreso al refugio
  intakeType        IntakeType      // CALLEJERO | ENTREGADO | RESCATE | TRANSFERENCIA
  intakeDate        DateTime
  intakeNotes       String?

  // Fotos y videos
  photos            AnimalPhoto[]
  videoUrl          String?

  // Relaciones
  location          Location?       @relation(fields: [locationId], references: [id])
  locationId        String?
  medicalRecords    MedicalRecord[]
  adoptionApps      AdoptionApplication[]
  fosterAssignments FosterAssignment[]
  sponsorships      Sponsorship[]
  waitlistEntries   WaitlistEntry[]

  createdAt         DateTime        @default(now())
  updatedAt         DateTime        @updatedAt
}

model AnimalPhoto {
  id          String   @id @default(cuid())
  animalId    String
  animal      Animal   @relation(fields: [animalId], references: [id])
  url         String
  publicId    String   // Cloudinary public_id
  isPrimary   Boolean  @default(false)
  caption     String?
  order       Int      @default(0)
  createdAt   DateTime @default(now())
}
```

### Registro Médico

```prisma
model MedicalRecord {
  id              String      @id @default(cuid())
  animalId        String
  animal          Animal      @relation(fields: [animalId], references: [id])
  date            DateTime
  type            MedicalType // VACUNA | TRATAMIENTO | CIRUGIA | CONSULTA | DESPARASITACION
  description     String
  veterinarian    String?
  medications     String?     // JSON array de medicamentos
  nextVisitDate   DateTime?
  createdById     String
  createdBy       User        @relation(fields: [createdById], references: [id])
  createdAt       DateTime    @default(now())
}
```

### Solicitud de Adopción

```prisma
model AdoptionApplication {
  id                    String              @id @default(cuid())
  animalId              String
  animal                Animal              @relation(fields: [animalId], references: [id])
  applicantId           String
  applicant             User                @relation(fields: [applicantId], references: [id])
  status                ApplicationStatus   // RECIBIDA | EN_REVISION | APROBADA | VISITA_ACORDADA | COMPLETADA | RECHAZADA | RETIRADA

  // Datos del hogar
  housingType           HousingType         // CASA | APARTAMENTO | CAMPO
  hasFencedGarden       Boolean
  houseArea             Int?                // m²
  numAdults             Int
  numChildren           Int                 @default(0)
  childrenAges          Int[]
  currentPets           String?             // JSON descripción mascotas actuales

  // Experiencia
  previousPetsHistory   String?
  hasExperienceWithBreed Boolean           @default(false)
  experienceDescription String?

  // Estilo de vida
  hoursAlonePerDay      Int
  exerciseFrequency     String?
  travelFrequency       String?

  // Referencias
  vetReference          String?
  personalReference     String?

  // Declaraciones Ley 4840
  declaresGardenFenced  Boolean             @default(false)
  declaresCanAffordVet  Boolean             @default(false)
  declaresNoResale      Boolean             @default(false)
  declaresReturnToShelter Boolean           @default(false)

  // Matching
  matchingScore         Int?                // 0-100, calculado por algoritmo
  matchingNotes         String?

  // Admin
  reviewerId            String?
  reviewer              User?               @relation("ReviewedApplications", fields: [reviewerId], references: [id])
  adminNotes            String?
  rejectionReason       String?

  // Tarifa
  feeAmount             Decimal?
  feePaid               Boolean             @default(false)
  paymentMethod         PaymentMethod?

  // Post-adopción
  followUps             PostAdoptionFollowUp[]
  contract              AdoptionContract?

  // Foster-to-adopt
  isFosterToAdopt       Boolean             @default(false)
  fosterAssignmentId    String?

  waitlistPosition      Int?

  createdAt             DateTime            @default(now())
  updatedAt             DateTime            @updatedAt
}

model AdoptionContract {
  id                String              @id @default(cuid())
  applicationId     String              @unique
  application       AdoptionApplication @relation(fields: [applicationId], references: [id])
  signedAt          DateTime?
  documentUrl       String?             // PDF firmado en Cloudinary
  sterilizationCertUrl String?
  signatureData     String?             // Base64 o referencia a proveedor de firma
  createdAt         DateTime            @default(now())
}

model PostAdoptionFollowUp {
  id              String              @id @default(cuid())
  applicationId   String
  application     AdoptionApplication @relation(fields: [applicationId], references: [id])
  scheduledFor    DateTime            // Día 2, 7, 30, 90
  dayNumber       Int                 // 2 | 7 | 30 | 90
  sentAt          DateTime?
  respondedAt     DateTime?
  response        String?
  photos          String[]            // URLs de fotos enviadas por la familia
  status          FollowUpStatus      // PENDIENTE | ENVIADO | RESPONDIDO | OMITIDO
  createdAt       DateTime            @default(now())
}
```

### Usuario

```prisma
model User {
  id                String          @id @default(cuid())
  email             String?         @unique
  phone             String?         @unique  // Formato E.164: +595981xxxxxx
  name              String
  ci                String?         // Cédula de identidad paraguaya
  role              UserRole        // ADMIN | VET | VOLUNTEER | PHOTOGRAPHER | FOSTER_COORD | ADOPTER | DONOR
  status            UserStatus      @default(ACTIVE)

  // Auth
  passwordHash      String?
  emailVerified     DateTime?
  phoneVerified     DateTime?
  accounts          Account[]       // NextAuth OAuth accounts

  // Portal
  savedAnimals      String[]        // Array de animalIds (favoritos)

  // GDPR Ley 7593
  gdprConsent       Boolean         @default(false)
  gdprConsentDate   DateTime?
  dataExportedAt    DateTime?
  deletionRequestedAt DateTime?

  // Relaciones
  adoptionApps      AdoptionApplication[]
  donations         Donation[]
  fosterAssignments FosterAssignment[]
  volunteerShifts   VolunteerShift[]
  sponsorships      Sponsorship[]
  notifications     Notification[]

  createdAt         DateTime        @default(now())
  updatedAt         DateTime        @updatedAt
}
```

### Donaciones

```prisma
model Donation {
  id              String          @id @default(cuid())
  donorId         String?
  donor           User?           @relation(fields: [donorId], references: [id])
  donorEmail      String?         // Para donaciones sin cuenta
  donorName       String?

  amount          Decimal
  currency        String          @default("PYG")
  type            DonationType    // UNICA | RECURRENTE | PATROCINIO | ESPECIE
  status          PaymentStatus   // PENDIENTE | COMPLETADO | FALLIDO | CANCELADO

  paymentMethod   PaymentMethod   // TIGO_MONEY | PERSONAL_PAY | PAGOEXPRESS | TRANSFERENCIA | STRIPE | EFECTIVO
  paymentReference String?       // ID de transacción del proveedor
  stripePaymentIntentId String?

  // Recurrencia
  isRecurring     Boolean         @default(false)
  recurringDay    Int?            // Día del mes para cobro recurrente
  nextChargeDate  DateTime?
  cancelledAt     DateTime?

  // Campaña / Destino
  campaignId      String?
  campaign        Campaign?       @relation(fields: [campaignId], references: [id])
  sponsoredAnimalId String?
  sponsoredAnimal  Animal?        @relation(fields: [sponsoredAnimalId], references: [id], name: "Sponsorship")

  receiptUrl      String?         // PDF en Cloudinary
  notes           String?

  createdAt       DateTime        @default(now())
  updatedAt       DateTime        @updatedAt
}

model Campaign {
  id              String          @id @default(cuid())
  title           String
  description     String
  goalAmount      Decimal
  currentAmount   Decimal         @default(0)
  startDate       DateTime
  endDate         DateTime?
  imageUrl        String?
  isActive        Boolean         @default(true)
  donations       Donation[]
  createdAt       DateTime        @default(now())
  updatedAt       DateTime        @updatedAt
}
```

### Lost & Found

```prisma
model LostFoundReport {
  id              String              @id @default(cuid())
  type            ReportType          // PERDIDO | ENCONTRADO
  status          ReportStatus        // ACTIVO | RESUELTO | EXPIRADO

  // Datos del reportante
  reporterName    String
  reporterPhone   String
  reporterUserId  String?

  // Datos del animal
  species         Species
  breed           String?
  color           String
  sex             Sex?
  estimatedAge    String?
  description     String
  photos          String[]            // URLs
  microchipNumber String?

  // Ubicación y tiempo
  location        String              // Descripción textual
  lat             Decimal?
  lng             Decimal?
  date            DateTime            // Fecha del evento (no del reporte)

  // Estado actual (para ENCONTRADO)
  currentStatus   String?             // "lo tengo" | "lo dejé" | "entregué al refugio"

  // Matching
  matchedWithId   String?             // ID de reporte coincidente o animalId en refugio
  matchType       String?             // "otro_reporte" | "animal_refugio"
  matchedAt       DateTime?

  // Admin
  adminNotes      String?
  resolvedById    String?

  createdAt       DateTime            @default(now())
  updatedAt       DateTime            @updatedAt
}
```

### Inventario

```prisma
model InventoryItem {
  id              String          @id @default(cuid())
  name            String
  category        ItemCategory    // ALIMENTO | MEDICAMENTO | INSUMO | EQUIPO
  unit            String          // kg, unidad, caja, etc.
  currentStock    Decimal
  minimumStock    Decimal         // Para alertas de stock bajo
  location        String?
  expiryDate      DateTime?
  movements       InventoryMovement[]
  createdAt       DateTime        @default(now())
  updatedAt       DateTime        @updatedAt
}

model InventoryMovement {
  id              String              @id @default(cuid())
  itemId          String
  item            InventoryItem       @relation(fields: [itemId], references: [id])
  type            MovementType        // ENTRADA | SALIDA | AJUSTE
  quantity        Decimal
  notes           String?
  createdById     String
  createdAt       DateTime            @default(now())
}
```

---

## Enums

```prisma
enum Species        { PERRO GATO OTRO }
enum Sex            { MACHO HEMBRA DESCONOCIDO }
enum Size           { PEQUEÑO MEDIANO GRANDE EXTRA_GRANDE }
enum AnimalStatus   { DISPONIBLE EN_FOSTER PENDIENTE ADOPTADO FALLECIDO TRANSFERIDO }
enum IntakeType     { CALLEJERO ENTREGADO RESCATE TRANSFERENCIA }
enum MedicalType    { VACUNA TRATAMIENTO CIRUGIA CONSULTA DESPARASITACION }
enum ApplicationStatus { RECIBIDA EN_REVISION APROBADA VISITA_ACORDADA COMPLETADA RECHAZADA RETIRADA }
enum HousingType    { CASA APARTAMENTO CAMPO }
enum PaymentMethod  { TIGO_MONEY PERSONAL_PAY PAGOEXPRESS TRANSFERENCIA STRIPE EFECTIVO }
enum PaymentStatus  { PENDIENTE COMPLETADO FALLIDO CANCELADO REEMBOLSADO }
enum DonationType   { UNICA RECURRENTE PATROCINIO ESPECIE }
enum UserRole       { ADMIN VET VOLUNTEER PHOTOGRAPHER FOSTER_COORD ADOPTER DONOR }
enum UserStatus     { ACTIVE SUSPENDED DELETED }
enum ReportType     { PERDIDO ENCONTRADO }
enum ReportStatus   { ACTIVO RESUELTO EXPIRADO }
enum ItemCategory   { ALIMENTO MEDICAMENTO INSUMO EQUIPO }
enum MovementType   { ENTRADA SALIDA AJUSTE }
enum FollowUpStatus { PENDIENTE ENVIADO RESPONDIDO OMITIDO }
```

---

## Índices Críticos

```sql
-- Búsqueda de animales disponibles (catálogo principal)
CREATE INDEX idx_animals_status_species ON animals(status, species);
CREATE INDEX idx_animals_status_size ON animals(status, size);
CREATE INDEX idx_animals_intake_date ON animals(intake_date);

-- Solicitudes de adopción por estado
CREATE INDEX idx_applications_status ON adoption_applications(status);
CREATE INDEX idx_applications_animal ON adoption_applications(animal_id);
CREATE INDEX idx_applications_applicant ON adoption_applications(applicant_id);

-- Lost & Found por ubicación y estado
CREATE INDEX idx_lost_found_status_type ON lost_found_reports(status, type);
CREATE INDEX idx_lost_found_geo ON lost_found_reports(lat, lng);

-- Donaciones
CREATE INDEX idx_donations_donor ON donations(donor_id);
CREATE INDEX idx_donations_status ON donations(status, payment_method);
```

---

## Relaciones Resumidas

```
Animal ──< AnimalPhoto
Animal ──< MedicalRecord
Animal ──< AdoptionApplication ──< PostAdoptionFollowUp
Animal ──< FosterAssignment
Animal ──< Sponsorship (via Donation)
Animal ──< WaitlistEntry

User ──< AdoptionApplication
User ──< Donation
User ──< FosterAssignment
User ──< VolunteerShift
User ──< Notification

Campaign ──< Donation
```
