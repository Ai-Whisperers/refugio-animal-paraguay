"use client";

/**
 * IndexedDB-backed queue for offline donation form submissions.
 *
 * Database: "refugio"
 * Object store: "queuedDonations" (keyPath: "id", autoIncrement)
 *
 * Queue schema:
 *   id: number (auto)
 *   amount: number
 *   currency: "PYG" | "EUR" | "USD"
 *   name: string
 *   email: string
 *   message: string
 *   timestamp: string (ISO 8601)
 *   retries: number
 */

export interface QueuedDonation {
  id?: number;
  amount: number;
  currency: string;
  name: string;
  email: string;
  message: string;
  timestamp: string;
  retries: number;
}

const DB_NAME = "refugio";
const STORE_NAME = "queuedDonations";
const DB_VERSION = 1;
const MAX_QUEUED = 5;
const MAX_RETRIES = 3;
const BACKOFF_BASE_MS = 1000;
const STALE_DAYS = 7;

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, {
          keyPath: "id",
          autoIncrement: true,
        });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function getQueuedDonations(): Promise<QueuedDonation[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readonly");
    const store = tx.objectStore(STORE_NAME);
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result as QueuedDonation[]);
    req.onerror = () => reject(req.error);
  });
}

export async function getQueueCount(): Promise<number> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readonly");
    const store = tx.objectStore(STORE_NAME);
    const req = store.count();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export async function addToQueue(
  donation: Omit<QueuedDonation, "id" | "timestamp" | "retries">
): Promise<{ success: boolean; message: string }> {
  const count = await getQueueCount();
  if (count >= MAX_QUEUED) {
    return {
      success: false,
      message: "Maximo 5 donaciones en cola",
    };
  }

  const entry: Omit<QueuedDonation, "id"> = {
    ...donation,
    timestamp: new Date().toISOString(),
    retries: 0,
  };

  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);
    const req = store.add(entry);
    req.onsuccess = () =>
      resolve({
        success: true,
        message:
          "Donacion guardada sin conexion - se enviara cuando haya conexion",
      });
    req.onerror = () => reject(req.error);
  });
}

export async function removeFromQueue(id: number): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);
    const req = store.delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

export async function updateRetries(
  id: number,
  retries: number
): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);
    const getReq = store.get(id);
    getReq.onsuccess = () => {
      const donation = getReq.result as QueuedDonation;
      if (!donation) {
        resolve();
        return;
      }
      donation.retries = retries;
      const putReq = store.put(donation);
      putReq.onsuccess = () => resolve();
      putReq.onerror = () => reject(putReq.error);
    };
    getReq.onerror = () => reject(getReq.error);
  });
}

export async function clearStaleEntries(): Promise<number> {
  const donations = await getQueuedDonations();
  const cutoff = Date.now() - STALE_DAYS * 24 * 60 * 60 * 1000;
  let cleared = 0;

  for (const donation of donations) {
    const ts = new Date(donation.timestamp).getTime();
    if (ts < cutoff) {
      await removeFromQueue(donation.id!);
      cleared++;
    }
  }

  return cleared;
}

async function submitDonation(
  donation: QueuedDonation
): Promise<{ ok: boolean }> {
  const response = await fetch("/api/donations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      amount: donation.amount,
      currency: donation.currency,
      donor_name: donation.name,
      donor_email: donation.email,
      message: donation.message,
    }),
  });
  return { ok: response.ok };
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function processQueue(
  onSuccess?: (donation: QueuedDonation) => void,
  onRetrying?: (donation: QueuedDonation, attempt: number) => void,
  onFailed?: (donation: QueuedDonation) => void
): Promise<{ submitted: number; failed: number }> {
  const donations = await getQueuedDonations();
  let submitted = 0;
  let failed = 0;

  for (const donation of donations) {
    let success = false;
    let retries = donation.retries;

    while (retries < MAX_RETRIES && !success) {
      try {
        const result = await submitDonation(donation);
        if (result.ok) {
          success = true;
          await removeFromQueue(donation.id!);
          submitted++;
          onSuccess?.(donation);
        } else {
          retries++;
          await updateRetries(donation.id!, retries);
          onRetrying?.(donation, retries);
          if (retries < MAX_RETRIES) {
            await delay(BACKOFF_BASE_MS * Math.pow(2, retries - 1));
          }
        }
      } catch {
        retries++;
        await updateRetries(donation.id!, retries);
        onRetrying?.(donation, retries);
        if (retries < MAX_RETRIES) {
          await delay(BACKOFF_BASE_MS * Math.pow(2, retries - 1));
        }
      }
    }

    if (!success) {
      failed++;
      onFailed?.(donation);
    }
  }

  return { submitted, failed };
}

export {
  DB_NAME,
  STORE_NAME,
  DB_VERSION,
  MAX_QUEUED,
  MAX_RETRIES,
  BACKOFF_BASE_MS,
  STALE_DAYS,
};
