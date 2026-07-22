"use client";

import { useState, type FormEvent } from "react";

import type { CoverLetterDraft } from "@career-os/sdk";

import {
  generateCoverLetterAction,
  markAppliedAction,
  saveOpportunityAction,
} from "@/features/jobs/actions";

export function OpportunityActions({
  opportunityId,
  applyUrl,
  applicationStatus,
}: {
  opportunityId: string;
  applyUrl: string;
  applicationStatus: string | null;
}) {
  const [status, setStatus] = useState(applicationStatus);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [draft, setDraft] = useState<CoverLetterDraft | null>(null);

  async function onSave() {
    setPending(true);
    setError(null);
    try {
      await saveOpportunityAction(opportunityId);
      setStatus((prev) => prev ?? "interested");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setPending(false);
    }
  }

  async function onApply() {
    setPending(true);
    setError(null);
    try {
      await markAppliedAction(opportunityId);
      setStatus("applied");
      window.open(applyUrl, "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Apply failed");
    } finally {
      setPending(false);
    }
  }

  async function onCoverLetter(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      const result = await generateCoverLetterAction(opportunityId);
      setDraft(result);
      setStatus((prev) => (prev === "interested" || !prev ? "prepared" : prev));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cover letter failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={pending}
          className="rounded border border-neutral-300 px-3 py-2 text-sm disabled:opacity-60"
          onClick={() => {
            void onSave();
          }}
        >
          {status ? "Saved" : "Save job"}
        </button>
        <button
          type="button"
          disabled={pending}
          className="rounded bg-neutral-900 px-3 py-2 text-sm text-white disabled:opacity-60"
          onClick={() => {
            void onApply();
          }}
        >
          Mark applied & open listing
        </button>
        <button
          type="button"
          disabled={pending}
          className="rounded border border-neutral-300 px-3 py-2 text-sm disabled:opacity-60"
          onClick={(event) => {
            void onCoverLetter(event);
          }}
        >
          Generate cover letter draft
        </button>
      </div>
      {status ? (
        <p className="text-xs uppercase tracking-wide text-neutral-500">Status: {status}</p>
      ) : null}
      {error ? (
        <p className="text-sm text-red-700" role="alert">
          {error}
        </p>
      ) : null}
      {draft ? (
        <div className="rounded border border-amber-200 bg-amber-50 p-4 text-sm">
          <p className="font-medium">Draft cover letter (review before sending)</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-neutral-700">
            {draft.grounding_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
          <pre className="mt-3 whitespace-pre-wrap font-sans text-neutral-800">{draft.body}</pre>
        </div>
      ) : null}
    </div>
  );
}
