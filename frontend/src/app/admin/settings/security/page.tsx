"use client";

import { useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { api } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Step = "status" | "scan" | "verify" | "success";

interface StatusResponse {
  enabled: boolean;
}

interface SetupResponse {
  provisioning_uri: string;
  secret: string;
}

interface BackupCodesResponse {
  codes: string[];
}

interface BackupCodesCountResponse {
  remaining: number;
}

// ---------------------------------------------------------------------------
// Helper: masked secret display
// ---------------------------------------------------------------------------

function formatSecretForDisplay(secret: string): string {
  // Break into groups of 4 for easier manual entry
  return secret.match(/.{1,4}/g)?.join(" ") ?? secret;
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function TwoFactorSettingsPage() {
  const [step, setStep] = useState<Step>("status");
  const [isEnabled, setIsEnabled] = useState<boolean | null>(null);
  const [provisioningUri, setProvisioningUri] = useState("");
  const [rawSecret, setRawSecret] = useState("");
  const [code, setCode] = useState("");
  const [disableCode, setDisableCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSecret, setShowSecret] = useState(false);

  // Backup codes state
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null);
  const [backupCodesRemaining, setBackupCodesRemaining] = useState<number | null>(null);
  const [backupCodesLoading, setBackupCodesLoading] = useState(false);
  const [backupCodesError, setBackupCodesError] = useState("");

  // Load current 2FA status and backup code count on mount
  useEffect(() => {
    async function loadStatus() {
      try {
        const data = await api.get<StatusResponse>("/auth/2fa/status");
        setIsEnabled(data.enabled);
        setStep("status");
        if (data.enabled) {
          try {
            const countData = await api.get<BackupCodesCountResponse>("/auth/2fa/backup-codes/count");
            setBackupCodesRemaining(countData.remaining);
          } catch {
            // non-critical — silently ignore
          }
        }
      } catch {
        setError("Could not load 2FA status. Please refresh.");
      }
    }
    loadStatus();
  }, []);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  async function handleStartSetup() {
    setError("");
    setLoading(true);
    try {
      const data = await api.post<SetupResponse>("/auth/2fa/setup", {});
      setProvisioningUri(data.provisioning_uri);
      setRawSecret(data.secret);
      setStep("scan");
    } catch {
      setError("Failed to initiate 2FA setup. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify() {
    if (code.length < 6) {
      setError("Please enter a 6-digit code.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/2fa/verify", { code });
      setIsEnabled(true);
      setStep("success");
    } catch {
      setError("Invalid code. Check your authenticator app and try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDisable() {
    if (disableCode.length < 6) {
      setError("Please enter your current 6-digit code to confirm.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/2fa/disable", { code: disableCode });
      setIsEnabled(false);
      setDisableCode("");
      setBackupCodes(null);
      setBackupCodesRemaining(null);
      setStep("status");
    } catch {
      setError("Invalid code. Enter the current code from your authenticator app.");
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateBackupCodes() {
    setBackupCodesError("");
    setBackupCodesLoading(true);
    try {
      const data = await api.post<BackupCodesResponse>("/auth/2fa/backup-codes", {});
      setBackupCodes(data.codes);
      setBackupCodesRemaining(data.codes.length);
    } catch {
      setBackupCodesError("Failed to generate backup codes. Please try again.");
    } finally {
      setBackupCodesLoading(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Render helpers
  // ---------------------------------------------------------------------------

  if (isEnabled === null) {
    return (
      <div className="flex min-h-[200px] items-center justify-center">
        <span className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Two-Factor Authentication
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Protect your account with a time-based one-time password (TOTP).
        </p>
      </div>

      {/* Current status badge */}
      <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <span
          className={[
            "inline-flex h-3 w-3 rounded-full",
            isEnabled ? "bg-green-500" : "bg-gray-300",
          ].join(" ")}
          aria-hidden="true"
        />
        <span className="text-sm font-medium text-gray-800">
          2FA is currently{" "}
          <strong>{isEnabled ? "enabled" : "disabled"}</strong>
        </span>
      </div>

      {/* Error banner */}
      {error && (
        <div
          role="alert"
          className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-red-200"
        >
          {error}
        </div>
      )}

      {/* --- Step: status — enable or disable --- */}
      {step === "status" && (
        <>
          {!isEnabled ? (
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-base font-semibold text-gray-900">
                Enable Two-Factor Authentication
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                Use an authenticator app like Google Authenticator, Authy, or
                Bitwarden to generate time-based codes. Once enabled, you will
                need a code at every login.
              </p>
              <button
                type="button"
                onClick={handleStartSetup}
                disabled={loading}
                className="mt-4 inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50"
              >
                {loading ? "Setting up…" : "Set up 2FA"}
              </button>
            </div>
          ) : (
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-base font-semibold text-gray-900">
                Disable Two-Factor Authentication
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                Enter the current 6-digit code from your authenticator app to
                confirm you want to disable 2FA protection.
              </p>
              <div className="mt-4 flex gap-3">
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  placeholder="000000"
                  value={disableCode}
                  onChange={(e) =>
                    setDisableCode(e.target.value.replace(/\D/g, ""))
                  }
                  className="w-32 rounded-md border border-gray-300 px-3 py-2 text-center text-lg font-mono tracking-widest shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  aria-label="Confirmation code"
                />
                <button
                  type="button"
                  onClick={handleDisable}
                  disabled={loading}
                  className="rounded-md bg-red-600 px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50"
                >
                  {loading ? "Disabling…" : "Disable 2FA"}
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* --- Step: scan QR code --- */}
      {step === "scan" && (
        <div className="space-y-5 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-gray-900">
            Step 1 — Scan with your authenticator app
          </h2>
          <p className="text-sm text-gray-600">
            Open your authenticator app and scan the QR code below. If you
            cannot scan, tap{" "}
            <button
              type="button"
              onClick={() => setShowSecret((v) => !v)}
              className="text-primary underline hover:text-primary-dark"
            >
              enter code manually
            </button>{" "}
            instead.
          </p>

          {/* QR code */}
          <div className="flex justify-center">
            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <QRCodeSVG
                value={provisioningUri}
                size={200}
                bgColor="#ffffff"
                fgColor="#111827"
                level="M"
                aria-label="Two-factor authentication QR code"
              />
            </div>
          </div>

          {/* Manual entry fallback */}
          {showSecret && (
            <div className="rounded-md bg-gray-50 p-3 text-center">
              <p className="mb-1 text-xs text-gray-500">Manual entry key</p>
              <p className="font-mono text-sm font-semibold tracking-widest text-gray-900">
                {formatSecretForDisplay(rawSecret)}
              </p>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={() => {
                setStep("status");
                setError("");
              }}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => {
                setError("");
                setStep("verify");
              }}
              className="rounded-md bg-primary px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
            >
              I&apos;ve scanned it →
            </button>
          </div>
        </div>
      )}

      {/* --- Step: verify first code --- */}
      {step === "verify" && (
        <div className="space-y-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-gray-900">
            Step 2 — Enter the code to activate
          </h2>
          <p className="text-sm text-gray-600">
            Enter the 6-digit code now shown in your authenticator app to
            confirm the setup.
          </p>
          <div className="flex gap-3">
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              placeholder="000000"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              className="w-32 rounded-md border border-gray-300 px-3 py-2 text-center text-lg font-mono tracking-widest shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              aria-label="Authentication code"
              autoFocus
            />
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => {
                setStep("scan");
                setError("");
              }}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
            >
              ← Back
            </button>
            <button
              type="button"
              onClick={handleVerify}
              disabled={loading || code.length < 6}
              className="rounded-md bg-primary px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50"
            >
              {loading ? "Verifying…" : "Activate 2FA"}
            </button>
          </div>
        </div>
      )}

      {/* --- Step: success confirmation --- */}
      {step === "success" && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-6 shadow-sm">
          <h2 className="text-base font-semibold text-green-800">
            Two-factor authentication is now active!
          </h2>
          <p className="mt-2 text-sm text-green-700">
            Your account is protected. You will be asked for a code at each
            login. Generate backup codes below in case you lose access to your
            authenticator device.
          </p>
          <button
            type="button"
            onClick={() => {
              setStep("status");
              api
                .get<BackupCodesCountResponse>("/auth/2fa/backup-codes/count")
                .then((d) => setBackupCodesRemaining(d.remaining))
                .catch(() => null);
            }}
            className="mt-4 rounded-md bg-green-700 px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-800 focus:outline-none"
          >
            Done
          </button>
        </div>
      )}

      {/* --- Backup codes section (shown when 2FA is enabled) --- */}
      {isEnabled && step === "status" && (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-base font-semibold text-gray-900">
                Backup Recovery Codes
              </h2>
              <p className="mt-1 text-sm text-gray-600">
                Single-use codes you can use to sign in if you lose access to
                your authenticator app. Store them somewhere safe — they are
                shown only once.
              </p>
              {backupCodesRemaining !== null && (
                <p className="mt-2 text-sm">
                  <span
                    className={
                      backupCodesRemaining === 0
                        ? "font-medium text-red-600"
                        : backupCodesRemaining <= 3
                          ? "font-medium text-amber-600"
                          : "text-gray-500"
                    }
                  >
                    {backupCodesRemaining} unused code
                    {backupCodesRemaining !== 1 ? "s" : ""} remaining
                  </span>
                </p>
              )}
            </div>
            <button
              type="button"
              onClick={handleGenerateBackupCodes}
              disabled={backupCodesLoading}
              className="ml-4 shrink-0 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50"
            >
              {backupCodesLoading
                ? "Generating…"
                : backupCodes
                  ? "Regenerate codes"
                  : "Generate codes"}
            </button>
          </div>

          {backupCodesError && (
            <p className="mt-3 text-sm text-red-600">{backupCodesError}</p>
          )}

          {/* Display freshly generated codes — shown exactly once */}
          {backupCodes && (
            <div className="mt-4">
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">
                Save these codes now — they will not be shown again
              </p>
              <div className="grid grid-cols-2 gap-2 rounded-md bg-gray-50 p-4 sm:grid-cols-5">
                {backupCodes.map((code) => (
                  <span
                    key={code}
                    className="rounded border border-gray-200 bg-white px-2 py-1 text-center font-mono text-sm text-gray-900 shadow-sm"
                  >
                    {code}
                  </span>
                ))}
              </div>
              <p className="mt-2 text-xs text-gray-500">
                Each code can only be used once. Generating new codes invalidates
                all previous ones.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
