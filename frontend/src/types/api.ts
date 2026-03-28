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

export type UserRole = "admin" | "staff" | "vet" | "adopter" | "donor" | "volunteer" | "foster";

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

// --- Portal Profile ---

export interface ProfileResponse {
  id: string;
  full_name: string | null;
  email: string;
  phone: string | null;
  role: string;
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProfileUpdate {
  full_name?: string;
  phone?: string;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

export interface SimplePreferences {
  email_adoption: boolean;
  email_donations: boolean;
  email_volunteer: boolean;
  whatsapp_enabled: boolean;
  inapp_enabled: boolean;
}

// --- Pre-Qualification ---

export interface PreQualifyQuestion {
  id: string;
  requirement_type: string;
  value: Record<string, unknown>;
  is_mandatory: boolean;
  animal_id: string | null;
  human_readable_description: string;
}

export interface PreQualifyQuestionsResponse {
  animal_id: string;
  questions: PreQualifyQuestion[];
}

export interface PreQualifyRequest {
  animal_id: string;
  answers: Record<string, Record<string, unknown>>;
}

export interface FailedRequirement {
  requirement_type: string;
  message: string;
  is_mandatory: boolean;
}

export interface SuggestedAnimal {
  id: string;
  name: string;
  species: string;
  photo_url: string | null;
  match_score: number;
}

export interface PreQualifyResult {
  qualified: boolean;
  score: number;
  failed_requirements: FailedRequirement[];
  suggested_animals: SuggestedAnimal[];
  estimated_wait_time: string;
}

// --- Castration Campaigns ---

export interface CastrationClinicPublic {
  id: string;
  name: string;
  city: string;
  department: string | null;
  latitude: number | null;
  longitude: number | null;
}

export interface CastrationCampaignPublic {
  id: string;
  title: string;
  description: string;
  goal_message: string | null;
  target_count: number;
  completed_count: number;
  progress_percent: number;
  target_area: string;
  start_date: string;
  end_date: string;
  status: string;
  partner_clinics: CastrationClinicPublic[];
  created_at: string;
}

export interface CastrationCampaignListResponse {
  items: CastrationCampaignPublic[];
  total: number;
}

// --- Castration Drives ---

export type CastrationDriveStatus = "scheduled" | "in_progress" | "completed" | "cancelled";

export interface CastrationDrivePublic {
  id: string;
  campaign_id: string;
  title: string;
  description: string | null;
  location_name: string;
  location_address: string | null;
  drive_date: string;
  start_time: string | null;
  end_time: string | null;
  max_capacity: number;
  registered_count: number;
  spots_available: number;
  is_full: boolean;
  status: CastrationDriveStatus;
  contact_phone: string | null;
  contact_name: string | null;
}

export interface CastrationDriveListResponse {
  items: CastrationDrivePublic[];
// --- Castration Photos ---

export type CastrationPhotoType = "before" | "after" | "recovery";

export interface CastrationPhoto {
  id: string;
  vet_voucher_id: string;
  campaign_id: string;
  photo_url: string;
  photo_type: CastrationPhotoType;
  animal_name: string;
  animal_species: string | null;
  notes: string | null;
  public_consent: boolean;
  is_featured: boolean;
  uploaded_by_clinic_id: string | null;
  uploaded_at: string;
}

export interface CastrationPhotoPublic {
  id: string;
  photo_url: string;
  photo_type: CastrationPhotoType;
  animal_name: string;
  animal_species: string | null;
  is_featured: boolean;
  uploaded_at: string;
}

export interface CastrationGalleryResponse {
  items: CastrationPhotoPublic[];
  total: number;
  page: number;
  page_size: number;
// --- Donor Leaderboard ---

export interface LeaderboardEntry {
  rank: number;
  donor_id: string | null;
  display_name: string;
  country: string | null;
  total_donated_cents: number;
  currency: CurrencyCode;
  donation_count: number;
  is_anonymous: boolean;
}

export interface LeaderboardResponse {
  items: LeaderboardEntry[];
  total_donors: number;
  total_raised_cents: number;
  currency: CurrencyCode;
// --- Castration Impact Report ---

export interface ClinicContribution {
  clinic_id: string;
  clinic_name: string;
  drives_hosted: number;
}

export interface DrivesSummary {
  total_drives: number;
  completed_drives: number;
  total_registered: number;
  total_completed: number;
}

export interface PhotoSummary {
  total_photos: number;
  before_count: number;
  after_count: number;
  recovery_count: number;
  featured_urls: string[];
}

export interface ImpactReportResponse {
  campaign_id: string;
  title: string;
  description: string;
  target_area: string;
  start_date: string;
  end_date: string;
  status: string;
  is_complete: boolean;
  target_count: number;
  completed_count: number;
  progress_percent: number;
  campaign_duration_days: number;
  clinics: ClinicContribution[];
  total_clinics: number;
  drives: DrivesSummary;
  photos: PhotoSummary;

// --- Public Statistics ---

export interface PublicStatisticsResponse {
  total_animals_rescued: number;
  total_adopted: number;
  total_castrated: number;
  total_donors: number;
  total_donations_amount_cents: number;
  total_volunteers: number;
  last_updated: string;
}

// --- API Error ---

export interface ApiError {
  detail?: string;
  message?: string;
  error_code?: string;
  status_code?: number;
}
