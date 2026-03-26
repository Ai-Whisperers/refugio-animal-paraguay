---
epic_id: EPIC-18
epic_title: Mobile Application
epic_status: planned
created_date: 2026-03-26
last_updated: 2026-03-26
epic_owner: Mobile Engineering
target_release: FPUNA-2026 Wave 4
priority: high
estimated_effort: 40 story points
---

# EPIC-18: Mobile Application

## Overview

This epic develops a mobile application (iOS and Android via React Native or Flutter) for shelter staff and volunteers enabling field operations. Primary features include animal check-in and health status updates, on-the-go medical record documentation with photo capture, adoption appointment scheduling and navigation, volunteer shift tracking and clock-in/out, and push notifications for urgent tasks and adoption updates.

Operationally, the app reduces paper-based workflows and eliminates need to return to office for data entry. Staff can document animal medical conditions, treatment given, and medication administration in real-time. Volunteers can capture photographic evidence of animal conditions, behavioral observations, or intake documentation while in the field. The app syncs with the backend when connectivity is available, supporting intermittent/offline operation in areas with unreliable connectivity (relevant for rural Paraguay).

## Why This Epic Matters

Shelter operations are field-heavy: staff and volunteers spend significant time with animals in pens, treatment areas, and adoption events. Requiring staff to return to office to enter data into web browser is inefficient. A mobile-first interface optimized for field use (large buttons, camera integration, offline capability) directly improves operational efficiency.

EU donors fund the organization partly based on demonstrated professional standards. Using mobile technology for medical records and animal documentation signals operational sophistication, supporting donor confidence and potentially enabling integration with government inspection/licensing.

For volunteer recruitment and retention, providing volunteers with a mobile app creates a sense of technological sophistication and makes volunteering feel like meaningful contribution to organized effort rather than ad-hoc helping. Badge notifications and hour tracking provide real-time feedback on volunteer impact.

## Target Users

**Shelter Staff**: Use app for daily animal care documentation, medical record updates, adoption appointment management, and incident reporting. Require offline capability for areas without reliable connectivity.

**Veterinary/Medical Staff**: Document medical examinations, prescriptions, treatment protocols, and follow-up requirements with photo evidence.

**Volunteers**: Clock in/out for shifts, receive volunteer assignments, log volunteer hours, earn and view recognition badges, receive push notifications for urgent tasks.

**Adopters**: Search for animals, view availability, schedule adoption appointments, receive adoption updates and appointment reminders.

**Drivers/Transport Volunteers**: Navigate inter-shelter transfers, document animal condition upon arrival, confirm receipt of transferred animals.

## Scope: In Scope

Cross-platform mobile app for iOS and Android using React Native (for code sharing) or Flutter (for performance). User authentication via existing JWT system with biometric login (fingerprint/face) for convenience.

Animal check-in functionality enabling staff/volunteers to mark animal status (present, medical hold, transferred, adopted), add health observations (appetite, behavior, injury assessment), and capture photos for documentation. Offline queue for check-ins performed without connectivity.

Medical documentation with structured forms for examination findings, prescribed treatments, medication doses, and follow-up schedules. Photo attachment for wounds, skin conditions, or diagnostic evidence. Integration with backend medical records for history display.

Adoption appointment management enabling staff to schedule appointments, volunteers to receive push notifications, and adopters to receive confirmations and reminders. Location/navigation support showing directions to shelter.

Volunteer management including clock in/out, shift assignment viewing, hours tracking, and badge/recognition display. Push notifications for volunteer opportunities ("need 3 volunteers tomorrow at 10am for dog walking").

Push notifications for urgent tasks (critical animal health alert, adoption processing milestone, volunteer needed), appointment reminders, and recognition updates.

Offline capability for core functions (check-in, medical notes, clock in/out) with automatic sync when connectivity resumes. Conflict resolution for simultaneous offline edits.

Camera integration for photo capture, OCR capability for reading medical documents or animal ID tags, and barcode scanning for animal identification and inventory tracking.

Admin dashboard on mobile for supervisors to view real-time staff location and activity (optional location tracking).

## Scope: Out of Scope

Advanced geolocation tracking or GPS tracking of staff/volunteers (privacy concerns). Video recording for behavior documentation (photo evidence only). AR features for educational content. Integration with government mobile systems. Advanced offline mode with full database replication. Custom deployment to enterprise app stores. Support for Windows Phone or other platforms beyond iOS/Android. Custom biometric handling beyond OS-provided APIs.

## Stories

This epic consists of four major stories. Story S01 implements mobile authentication and core app architecture for iOS/Android. Story S02 builds animal check-in and medical documentation with camera integration and offline sync. Story S03 implements volunteer management (clock in/out, shift assignment, badge display). Story S04 develops push notifications, adoption appointment management, and admin dashboard.

## Dependencies

This epic depends on stable REST API from backend (EPIC-03 and related) with offline-friendly design (paginated, filterable endpoints). Push notification infrastructure (Firebase Cloud Messaging for Android, Apple Push Notification service for iOS). Camera and location permissions handled properly. Authentication system must support mobile JWT token refresh. Comprehensive API documentation required before mobile development starts.

## Success Metrics

Mobile app adoption is successful when 80% of shelter staff use app for daily check-in within first month, medical record documentation completeness increases to 95% (from current estimated 70%), and staff report 30% reduction in time spent on data entry.

Offline capability is successful when core functions (check-in, medical notes) work without connectivity, sync completes within 5 minutes of connectivity resumption, and zero data loss in offline-to-online transitions.

Volunteer engagement increases with app adoption: clock in/out usage reaches 75% of volunteers, badge notifications are viewed by 85% of users, and volunteer retention improves by 15% in volunteer cohort using app vs. not.

Push notifications show 70% open rate for critical alerts, adoption reminder notifications increase appointment show-up rate by 10%, and volunteer opportunity notifications achieve 40% registration rate.

Adoptions conducted via mobile appointment scheduling represent at least 30% of adoption appointments within six months.

Performance metrics require app startup time <3 seconds, medical documentation form completion <2 minutes per animal, and offline queue sync completion <1 minute for typical session.

## Risk Factors

**Connectivity risk**: Unreliable internet in rural Paraguay could cause sync failures and data loss. Mitigated by robust offline mode, comprehensive conflict resolution, and local audit logs. Field testing in low-connectivity areas essential before release.

**Privacy risk**: Storing animal/adopter photos and medical data on staff phones increases breach risk. Mitigated by encrypted storage, app-level PIN/biometric lock, automatic remote wipe capability, and data minimization (only current/recent records cached).

**Staff resistance risk**: Existing staff accustomed to paper workflows may resist learning new system. Mitigated by intuitive UX, training program, ongoing support, and demonstrable efficiency gains.

**Performance risk**: App with poor battery consumption or data usage could be rejected by volunteers/staff. Mitigated by performance profiling, optimization focus, and testing on lower-end devices common in Paraguay.

**Maintenance burden**: Supporting two platforms (iOS, Android) doubles maintenance cost. Mitigated by choosing React Native or Flutter for code sharing, shared backend API, and careful design to minimize platform-specific code.

**Security risk**: Mobile devices are more vulnerable to physical theft. Mitigated by app-level PIN, biometric auth, backend session management (sessions can be revoked), and automatic logout after inactivity.

## Technical Notes

The mobile app uses React Native or Flutter for cross-platform development. Authentication uses JWT token from backend with optional refresh token stored securely in platform-provided secure storage. Biometric login enabled via platform APIs (FaceID/TouchID for iOS, BiometricPrompt for Android).

The app maintains a local SQLite database for offline storage of animals, medical records, volunteer data, and appointment information. A sync engine compares local changes against backend, resolving conflicts via last-write-wins or user prompt for critical fields. Network connectivity is monitored; when connectivity is detected, sync automatically initiates.

Camera integration uses native platform APIs (Camera Permissions for iOS, Camera2 API for Android) abstracted through plugin. Photos are stored locally encrypted, synced to backend in background. Image compression reduces bandwidth usage.

Push notifications use Firebase Cloud Messaging (FCM) for Android and Apple Push Notification service (APNs) for iOS. Device tokens are registered with backend upon installation. Admin can target notifications by role, location, or specific user.

Medical documentation uses structured forms with conditional fields (e.g., if injury selected, show wound assessment section). Form data is validated on client before submission to reduce invalid offline submissions.

Volunteer clock in/out is timestamped and synced asynchronously. If offline, timestamp is local time; upon sync, backend accepts timestamp as-is (trusting field users). Supervisor dashboard shows real-time volunteer count and hours logged.

Location services are optional and require explicit user permission. If enabled, staff location is sent to backend at regular intervals for supervision visibility. Location data is encrypted in transit and at rest, with clear privacy policy.

The app version is closely tied to backend API version. Incompatible versions prevent login with clear upgrade prompts.

