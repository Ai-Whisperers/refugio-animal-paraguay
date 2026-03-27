/**
 * Shared API types for the Refugio Animal Paraguay frontend.
 * These mirror the backend Pydantic schemas.
 */

// --- Auth ---

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface TokenPayload {
  sub: string;
  role: UserRole;
  exp: number;
}

export type UserRole = "admin" | "staff" | "adopter";

// --- Animals ---

export type AnimalSpecies = "dog" | "cat" | "other";

export type AnimalSize = "small" | "medium" | "large" | "extra_large";

export type AnimalGender = "male" | "female" | "unknown";

export type AnimalStatus =
  | "intake"
  | "quarantine"
  | "available"
  | "foster"
  | "under_treatment"
  | "adopted"
  | "deceased";

export interface AnimalPhoto {
  id: string;
  animal_id: string;
  url: string;
  caption: string | null;
  display_order: number;
  created_at: string;
}

export interface Animal {
  id: string;
  name: string;
  species: AnimalSpecies;
  status: AnimalStatus;
  breed: string | null;
  size: AnimalSize | null;
  gender: AnimalGender | null;
  birth_date: string | null;
  description: string | null;
  primary_photo_url: string | null;
  photos: AnimalPhoto[];
  created_at: string;
  updated_at: string;
}

export interface AnimalCreate {
  name: string;
  species?: AnimalSpecies;
  status?: AnimalStatus;
  birth_date?: string | null;
  description?: string | null;
  primary_photo_url?: string | null;
}

export interface AnimalUpdate {
  name?: string;
  species?: AnimalSpecies;
  status?: AnimalStatus;
  birth_date?: string | null;
  description?: string | null;
  primary_photo_url?: string | null;
}

// --- Adoption Requests (Staff) ---

export type AdoptionRequestStatus = "pending" | "approved" | "rejected" | "cancelled";

export interface AdoptionRequestResponse {
  id: string;
  animal_id: string;
  adopter_id: string;
  status: AdoptionRequestStatus;
  submitted_at: string;
  decided_at: string | null;
  notes: string | null;
  contract_pdf_path: string | null;
  contract_generated_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdoptionRequestStatusUpdate {
  status: AdoptionRequestStatus;
}

// --- Adoption Applications (Public) ---

export interface PublicAdoptionApplicationCreate {
  animal_id: string;
  full_name: string;
  email: string;
  phone?: string;
  message?: string;
  gdpr_consent: boolean;
}

export interface PublicAdoptionApplicationResponse {
  id: string;
  animal_id: string;
  status: string;
  submitted_at: string;
  message: string;
}

// --- Public animal browsing (unauthenticated) ---

/** Compact animal representation returned by GET /public/animals. */
export interface PublicAnimalListItem {
  id: string;
  name: string;
  species: AnimalSpecies;
  breed: string | null;
  size: AnimalSize | null;
  gender: AnimalGender | null;
  birth_date: string | null;
  description: string | null;
  primary_photo_url: string | null;
  created_at: string;
}

/** Pagination metadata embedded in paginated responses. */
export interface AnimalPaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

/** Paginated response from GET /public/animals. */
export interface PaginatedAnimalListResponse {
  items: PublicAnimalListItem[];
  pagination: AnimalPaginationMeta;
}

// --- Pagination ---

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// --- Campaigns ---

export type CampaignStatus = "draft" | "active" | "completed" | "cancelled";

export type FundCategory =
  | "medical"
  | "food"
  | "operations"
  | "rescue"
  | "infrastructure"
  | "general";

export type CurrencyCode = "EUR" | "PYG" | "USD";

export interface CampaignPublic {
  id: string;
  title: string;
  description: string;
  impact_story: string | null;
  target_amount_cents: number;
  raised_amount_cents: number;
  currency: CurrencyCode;
  fund_category: FundCategory;
  status: CampaignStatus;
  featured: boolean;
  image_url: string | null;
  photo_urls: string[];
  deadline: string | null;
  days_remaining: number | null;
  min_donation_cents: number | null;
  max_donation_cents: number | null;
  allow_overfunding: boolean;
  donation_count: number;
  progress_percentage: number;
  created_at: string;
}

export interface CampaignListResponse {
  items: CampaignPublic[];
  total: number;
  page: number;
  page_size: number;
}

/** Social proof data for a campaign (from GET /public/campaigns/{id}/social-proof). */
export interface RecentDonorEntry {
  display_name: string;
  amount_cents: number;
  currency: CurrencyCode;
  donated_at: string;
  is_anonymous: boolean;
}

export interface CampaignSocialProof {
  campaign_id: string;
  donor_count: number;
  total_raised_cents: number;
  currency: CurrencyCode;
  progress_percentage: number;
  donations_last_24_hours: number;
  donations_last_7_days: number;
  recent_donors: RecentDonorEntry[];
}

export interface DonationCreateRequest {
  donor_id?: string | null;
  campaign_id?: string | null;
  amount_cents: number;
  currency: CurrencyCode;
  payment_method: "stripe" | "cash" | "transfer";
  notes?: string | null;
}

export interface DonationResponse {
  id: string;
  donor_id: string | null;
  amount_cents: number;
  currency: CurrencyCode;
  payment_method: string;
  stripe_payment_intent_id: string | null;
  status: string;
  fund_category: string | null;
  receipt_number: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface StripeIntentResponse {
  donation_id: string;
  stripe_payment_intent_id: string;
  client_secret: string;
  amount_cents: number;
  currency: CurrencyCode;
}

export interface DonorCreateRequest {
  full_name: string;
  email: string;
  country?: string;
  currency_preference?: CurrencyCode;
  gdpr_consent_at?: string;
}

export interface DonorResponse {
  id: string;
  full_name: string;
  email: string;
  country: string | null;
  currency_preference: CurrencyCode;
  gdpr_consent_at: string | null;
  created_at: string;
  updated_at: string;
}

// --- Audit Logs ---

export interface AuditLogEntry {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  timestamp: string;
  ip_address: string | null;
  user_agent: string | null;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  request_id: string | null;
}

export interface AuditLogListResponse {
  items: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
}

// --- Medical Records ---

export type VisitType =
  | "checkup"
  | "emergency"
  | "surgery"
  | "vaccination"
  | "follow_up"
  | "dental"
  | "other";

export type VisitStatus =
  | "scheduled"
  | "in_progress"
  | "completed"
  | "cancelled"
  | "no_show";

export type DiagnosisSeverity = "mild" | "moderate" | "severe" | "critical";

export type TreatmentStatus = "planned" | "in_progress" | "completed" | "discontinued";

export type MedicationFrequency =
  | "once"
  | "twice_daily"
  | "three_times_daily"
  | "daily"
  | "every_other_day"
  | "weekly"
  | "as_needed";

export type MedicationStatus = "active" | "completed" | "discontinued";

export interface MedicationRecord {
  id: string;
  treatment_id: string;
  name: string;
  dosage: string;
  frequency: MedicationFrequency;
  route: string | null;
  start_date: string;
  end_date: string | null;
  medication_status: MedicationStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface TreatmentRecord {
  id: string;
  diagnosis_id: string;
  name: string;
  description: string | null;
  treatment_status: TreatmentStatus;
  start_date: string | null;
  end_date: string | null;
  notes: string | null;
  medications: MedicationRecord[];
  created_at: string;
  updated_at: string;
}

export interface DiagnosisRecord {
  id: string;
  vet_visit_id: string;
  condition: string;
  description: string | null;
  severity: DiagnosisSeverity;
  is_chronic: boolean;
  treatments: TreatmentRecord[];
  created_at: string;
}

export interface MedicalDocument {
  id: string;
  vet_visit_id: string;
  document_type: string;
  title: string;
  description: string | null;
  file_url: string;
  file_name: string;
  file_size_bytes: number | null;
  mime_type: string | null;
  created_at: string;
}

export interface VetVisit {
  id: string;
  animal_id: string;
  veterinarian_name: string;
  visit_type: VisitType;
  visit_status: VisitStatus;
  visit_date: string;
  reason: string | null;
  notes: string | null;
  weight_kg: number | null;
  temperature_celsius: number | null;
  next_visit_date: string | null;
  diagnoses: DiagnosisRecord[];
  medical_documents: MedicalDocument[];
  created_at: string;
  updated_at: string;
}

export interface VetVisitListResponse {
  items: VetVisit[];
  total: number;
  page: number;
  page_size: number;
}

export interface VetVisitCreate {
  veterinarian_name: string;
  visit_type: VisitType;
  visit_status: VisitStatus;
  visit_date: string;
  reason?: string | null;
  notes?: string | null;
  weight_kg?: number | null;
  temperature_celsius?: number | null;
  next_visit_date?: string | null;
}

// --- Vaccinations ---

export interface VaccineType {
  id: string;
  name: string;
  description: string | null;
  manufacturer: string | null;
  target_species: string;
  is_required: boolean;
  created_at: string;
}

export interface VaccinationRecord {
  id: string;
  animal_id: string;
  vaccine_type_id: string;
  vaccination_status: string;
  scheduled_date: string;
  administered_date: string | null;
  administered_by: string | null;
  batch_number: string | null;
  dose_number: number;
  next_due_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  vaccine_type: VaccineType | null;
}

export interface VaccinationListResponse {
  items: VaccinationRecord[];
  total: number;
  page: number;
  size: number;
}

// --- Vaccination Alerts ---

export type AlertSeverity = "overdue" | "due_today" | "upcoming";

export interface VaccinationAlertItem {
  vaccination_id: string;
  animal_id: string;
  animal_name: string;
  vaccine_name: string;
  scheduled_date: string;
  days_until_due: number;
  severity: AlertSeverity;
  dose_number: number;
}

export interface VaccinationAlertSummary {
  overdue: VaccinationAlertItem[];
  due_today: VaccinationAlertItem[];
  upcoming: VaccinationAlertItem[];
  total_overdue: number;
  total_due_today: number;
  total_upcoming: number;
}

// --- Surgeries ---

export type SurgeryType =
  | "spay"
  | "neuter"
  | "mass_removal"
  | "orthopedic"
  | "dental"
  | "emergency"
  | "biopsy"
  | "eye"
  | "other";

export type SurgeryStatus =
  | "scheduled"
  | "in_progress"
  | "completed"
  | "cancelled"
  | "complications";

export type SurgeryOutcome =
  | "successful"
  | "complications"
  | "incomplete"
  | "failed";

export interface Surgery {
  id: string;
  animal_id: string;
  surgery_type: SurgeryType;
  surgery_status: SurgeryStatus;
  veterinarian_name: string;
  scheduled_date: string;
  performed_date: string | null;
  anesthesia_type: string | null;
  procedure_description: string | null;
  outcome: SurgeryOutcome | null;
  outcome_notes: string | null;
  complications: string | null;
  weight_kg: number | null;
  recovery_notes: string | null;
  follow_up_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface SurgeryWithAnimal extends Surgery {
  animal_name: string;
}

export interface SurgeryScheduleListResponse {
  items: SurgeryWithAnimal[];
  total: number;
  page: number;
  size: number;
}

// --- PostOpChecks ---

export type PostOpStatus = "pending" | "completed" | "missed" | "concern";

export interface PostOpCheck {
  id: string;
  surgery_id: string;
  check_status: PostOpStatus;
  scheduled_time: string;
  completed_time: string | null;
  checked_by: string | null;
  temperature_celsius: number | null;
  pain_level: number | null;
  appetite: string | null;
  mobility: string | null;
  wound_condition: string | null;
  notes: string | null;
  concerns: string | null;
  created_at: string;
}

export interface PostOpCheckListResponse {
  items: PostOpCheck[];
  total: number;
}

// --- Subscriptions (Recurring Donations) ---

export type SubscriptionInterval = "month" | "year";

export type SubscriptionStatus =
  | "active"
  | "paused"
  | "canceled"
  | "past_due"
  | "incomplete"
  | "trialing";

export interface SubscriptionCreateRequest {
  donor_id: string;
  amount_cents: number;
  currency: CurrencyCode;
  interval: SubscriptionInterval;
  payment_method_id: string;
  notes?: string | null;
}

export interface SubscriptionDetailResponse {
  id: string;
  donor_id: string;
  stripe_subscription_id: string;
  stripe_customer_id: string;
  stripe_price_id: string | null;
  amount_cents: number;
  currency: string;
  interval: string;
  status: SubscriptionStatus;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  canceled_at: string | null;
  last_payment_error: string | null;
  failed_payment_count: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

// --- API Error ---

export interface ApiError {
  detail?: string;
  message?: string;
  error_code?: string;
  status_code?: number;
}
