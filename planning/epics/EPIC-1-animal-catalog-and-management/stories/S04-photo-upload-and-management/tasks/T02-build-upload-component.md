---
epic: EPIC-1
story: S04
task: T02
title: Implement Photo Upload and Management API Endpoints
status: pending
effort_hours: 4
priority: medium
dependencies:
  - S04/T01-configure-supabase-storage-for-animal-photos
  - S01/T01-define-supabase-schema-for-animals-table
---

## Overview

Implement the FastAPI endpoints that allow staff to upload photos for a specific animal, designate a primary photo, and delete photos. These endpoints are the write counterpart to the read endpoints defined in S03/T03. Together they form the complete photo management API: S03/T03 handles GET requests for reading the photo list, and this task handles POST, PATCH, and DELETE requests for writing photo records and managing the files on disk.

## Why This Matters

The adoption catalog and animal detail page are only useful to potential adopters when animals have clear, well-chosen photos. Without upload and management endpoints, shelter staff have no way to add photos to animal records after the initial data entry. The primary photo designation is especially important because it determines which photo appears in the catalog grid and at the top of the detail page — staff need to be able to change it when a better photo becomes available without deleting and re-uploading photos.

## Context

Photo files are stored on the server's local filesystem during development, organized under a configurable base directory. The storage base directory is set via the environment variable PHOTO_STORAGE_PATH and defaults to a local uploads directory when not set. Each animal's photos are stored in a subdirectory named after the animal's integer id. In production, the storage backend can be replaced with an S3-compatible object store by changing the storage service implementation, but the API endpoint contracts do not change.

The photo upload endpoint accepts multipart/form-data requests rather than JSON, because it must receive the binary file data alongside optional metadata fields. FastAPI's UploadFile type handles multipart parsing automatically and provides the file's content type, original filename, and a file-like object for reading the bytes.

All photo management endpoints require authentication with a JWT token. The token must carry a role claim of staff or admin. Adopters and unauthenticated visitors cannot upload or delete photos. The detail and gallery endpoints in S03 remain public — only the write operations require authentication.

The maximum file size for a single photo upload is five megabytes. The accepted MIME types are image/jpeg, image/png, and image/webp. The application validates both constraints before writing any bytes to disk, returning a 422 response with a descriptive error message if validation fails.

## Implementation Steps

### Step 1: Define the File Storage Service

In src/services/photo_storage.py, define a class named PhotoStorageService that manages reading and writing photo files. The class is initialized with the storage base path from the environment variable PHOTO_STORAGE_PATH. It exposes three methods: save_photo, which accepts an animal id integer and a file-like binary stream and returns the relative path where the file was written; get_photo_url, which accepts the stored relative path and returns a fully qualified URL that can be embedded in API responses; and delete_photo, which accepts the relative path and removes the file from disk.

The save_photo method generates a random UUID as the filename to avoid collisions, appends the appropriate extension based on the MIME type of the uploaded file, creates the animal's subdirectory if it does not exist, and writes the file bytes. The subdirectory name is the string representation of the animal's integer id. The returned relative path is in the format animal_id/filename.ext so that it can be stored in the url column of the animal_photos table without any further transformation.

The get_photo_url method constructs the public URL by combining the application's base URL from the APP_BASE_URL environment variable with the static file mount path and the relative path. This assumes that the FastAPI application mounts the storage directory as a static file route, which allows photos to be served directly by the application without requiring a separate web server or CDN for development. The application's main.py registers the static mount during startup using FastAPI's StaticFiles middleware pointed at the PHOTO_STORAGE_PATH directory.

### Step 2: Implement the Photo Upload Service Function

In src/services/animal_service.py, define an async function named create_animal_photo that accepts a SQLAlchemy AsyncSession, an integer animal_id, a string url, and a boolean is_primary. The function first verifies that the animal with the given id exists, raising a not-found error if it does not. When is_primary is true, the function executes an UPDATE statement on the animal_photos table to set is_primary to false for all existing photos belonging to that animal before inserting the new row. This two-step operation clears the old primary flag atomically within a single database transaction. The function then inserts a new AnimalPhoto row with the provided animal_id, url, and is_primary values and returns the newly created AnimalPhoto instance.

The order of operations is critical: the existing primary flag must be cleared before the new row is inserted to avoid briefly having two primary photos, even though the partial unique index would prevent the second insert if the first update is not yet visible. Running both operations in the same transaction ensures that no other concurrent reader sees an intermediate state.

### Step 3: Define the Photo Upload Route Handler

In src/routers/animals.py, add a route at POST /animals/{id}/photos with no response model type constraint at the Pydantic level, returning an AnimalPhotoResponse object. The route handler is an async function that accepts the integer id path parameter, an UploadFile instance named file, an optional boolean query parameter named is_primary defaulting to false, a SQLAlchemy AsyncSession via the database dependency, and the current staff user via the require_staff_role dependency.

The handler first validates the file's content type against the list of accepted MIME types and checks that the file size does not exceed the five-megabyte limit. File size validation requires reading the file bytes into memory, because UploadFile does not expose the content length before reading. The handler reads the bytes once, performs the size check, and then passes the bytes to the storage service rather than reading from the UploadFile stream a second time. If either validation fails, the handler raises a 422 HTTPException with a detail message that identifies whether the problem is the file type or the file size.

After validation, the handler calls the storage service's save_photo method to write the file to disk and receive the stored path. It then calls create_animal_photo with the path and the is_primary flag. Finally, it constructs and returns an AnimalPhotoResponse from the newly created photo record.

### Step 4: Implement the Set Primary Photo Route Handler

In src/routers/animals.py, add a route at PATCH /animals/{id}/photos/{photo_id}/primary with a response model of AnimalPhotoResponse. This endpoint designates the photo identified by photo_id as the primary photo for the animal identified by id. The route handler verifies that both the animal and the photo exist, and that the photo belongs to the specified animal — if any of these checks fail it raises a 404. It then calls a service function named set_primary_photo that clears the existing primary flag on all of the animal's photos and sets is_primary to true on the specified photo, all within a single transaction. The handler returns the updated AnimalPhotoResponse for the newly designated primary photo.

### Step 5: Implement the Delete Photo Route Handler

In src/routers/animals.py, add a route at DELETE /animals/{id}/photos/{photo_id} with a 204 No Content response status. The route handler verifies that the photo exists and belongs to the specified animal, calls the storage service to delete the file from disk, and then deletes the AnimalPhoto row from the database. If the deleted photo was the primary photo and other photos remain for the animal, the handler automatically promotes the oldest remaining photo to primary by setting its is_primary flag to true. This automatic promotion prevents the animal from being left without a primary photo after a deletion. The handler returns a 204 response with no body on success.

### Step 6: Write Integration Tests

In tests/integration/test_animal_photos.py, add integration tests for all three new endpoints. The upload test creates an animal fixture, constructs a small valid JPEG file in memory as a bytes object, sends a multipart POST request to /animals/{animal.id}/photos with a valid staff JWT token, and verifies that the response status is 201 and that the response body contains a url field and an id field. A second upload test verifies that uploading with is_primary equal to true returns a response with is_primary equal to true.

The validation test sends a POST request with a text/plain file and verifies the response status is 422. A second validation test sends a POST request with a file larger than five megabytes and verifies the response status is 422. An authentication test sends a POST request with no JWT token and verifies the response status is 401.

The set-primary test creates an animal with two photos, sends a PATCH request to the primary endpoint for the non-primary photo, and verifies that the response shows the photo as primary and that querying the photo list confirms only one primary photo exists.

The delete test creates an animal with one photo, sends a DELETE request, and verifies the response is 204 and that a subsequent GET to the photo list returns an empty array.

## Acceptance Criteria

- POST /animals/{id}/photos accepts multipart/form-data with a file field and an optional is_primary query parameter
- The endpoint returns 422 for files with non-image MIME types
- The endpoint returns 422 for files larger than five megabytes
- The endpoint returns 401 when no valid staff JWT token is present
- The endpoint returns 404 when the animal does not exist
- Uploading with is_primary true clears the existing primary flag before setting the new one
- PATCH /animals/{id}/photos/{photo_id}/primary designates the specified photo as primary and returns the updated photo
- DELETE /animals/{id}/photos/{photo_id} removes the file from storage and the row from the database
- Deleting the primary photo automatically promotes the oldest remaining photo to primary when other photos exist
- Integration tests cover the upload, validation, authentication, set-primary, and delete scenarios

## Common Issues and Solutions

If the file size check produces incorrect results for small files, verify that the UploadFile stream has not been partially consumed before the size check runs. Reading bytes from the UploadFile object advances the stream position, so if any code reads from the stream before the size check, the bytes remaining will be less than the actual file size. Read all bytes once at the start of the handler and operate on the in-memory bytes object thereafter.

If two photos end up with is_primary equal to true after an upload with is_primary set to true, verify that the clear-existing-primary UPDATE and the new row INSERT are executed within the same database transaction. If the UPDATE is committed before the INSERT begins and an exception occurs during the INSERT, the animal will be left with no primary photo. Wrapping both operations in a single transaction ensures that either both succeed or neither does.

If uploaded photos are served with 404 errors from the static file mount, verify that the PHOTO_STORAGE_PATH directory is the same directory that FastAPI mounts as the static files route. A common mistake is mounting the parent directory of the storage path, which changes the URL prefix needed to reach the files.

## Related Tasks

- S04/T01: animal_photos table — the database table this endpoint writes to
- S03/T03: Photo gallery endpoint — the read counterpart to the upload endpoint
- S03/T02: AnimalPhotoResponse schema — the response model all photo endpoints share
- EPIC-7: Admin dashboard — the staff interface that will call these endpoints to manage photos
