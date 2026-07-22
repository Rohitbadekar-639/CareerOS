"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { CandidateProfile } from "@career-os/sdk";

import {
  enrichGitHubAction,
  enrichPortfolioAction,
  ingestLinkedInAction,
  ingestResumeAction,
  saveProfilePreferencesAction,
} from "@/features/intelligence/actions";

export function IntelligenceProfileForm({ initial }: { initial: CandidateProfile }) {
  const router = useRouter();
  const [profile, setProfile] = useState(initial);
  const [resume, setResume] = useState(initial.resume_text);
  const [linkedin, setLinkedin] = useState(initial.linkedin_text);
  const [github, setGithub] = useState(initial.github_username ?? "");
  const [portfolio, setPortfolio] = useState(initial.portfolio_url ?? "");
  const [locations, setLocations] = useState(initial.preferred_locations.join(", "));
  const [headline, setHeadline] = useState(initial.headline);
  const [remote, setRemote] = useState(initial.remote_preference);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function run(fn: () => Promise<CandidateProfile>) {
    setPending(true);
    setError(null);
    try {
      const next = await fn();
      setProfile(next);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <section className="space-y-3">
        <h2 className="text-lg font-medium">Preferences</h2>
        <label className="flex flex-col gap-1 text-sm">
          Headline
          <input
            className="rounded border border-neutral-300 px-3 py-2"
            value={headline}
            onChange={(e) => setHeadline(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Preferred locations
          <input
            className="rounded border border-neutral-300 px-3 py-2"
            value={locations}
            onChange={(e) => setLocations(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Remote preference
          <select
            className="rounded border border-neutral-300 px-3 py-2"
            value={remote}
            onChange={(e) => setRemote(e.target.value)}
          >
            <option value="any">Any</option>
            <option value="remote_only">Remote only</option>
            <option value="hybrid_or_onsite">Hybrid / onsite</option>
          </select>
        </label>
        <button
          type="button"
          disabled={pending}
          className="w-fit rounded bg-neutral-900 px-3 py-2 text-sm text-white disabled:opacity-60"
          onClick={() => {
            void run(() =>
              saveProfilePreferencesAction({
                headline,
                preferred_locations: locations
                  .split(",")
                  .map((s) => s.trim())
                  .filter(Boolean),
                salary_expectation_min: profile.salary_expectation_min,
                salary_currency: profile.salary_currency,
                remote_preference: remote,
                github_username: github || null,
                linkedin_url: profile.linkedin_url,
                portfolio_url: portfolio || null,
              }),
            );
          }}
        >
          Save preferences & rerank
        </button>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Resume parser</h2>
        <textarea
          className="min-h-32 rounded border border-neutral-300 px-3 py-2 text-sm"
          value={resume}
          onChange={(e) => setResume(e.target.value)}
          placeholder="Paste resume text"
        />
        <button
          type="button"
          disabled={pending}
          className="w-fit rounded border border-neutral-300 px-3 py-2 text-sm"
          onClick={() => {
            void run(() => ingestResumeAction(resume));
          }}
        >
          Parse resume
        </button>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">LinkedIn import</h2>
        <p className="text-xs text-neutral-500">Paste your own export/profile text — never scraped.</p>
        <textarea
          className="min-h-28 rounded border border-neutral-300 px-3 py-2 text-sm"
          value={linkedin}
          onChange={(e) => setLinkedin(e.target.value)}
        />
        <button
          type="button"
          disabled={pending}
          className="w-fit rounded border border-neutral-300 px-3 py-2 text-sm"
          onClick={() => {
            void run(() => ingestLinkedInAction(linkedin));
          }}
        >
          Import LinkedIn text
        </button>
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-3">
          <h2 className="text-lg font-medium">GitHub analysis</h2>
          <input
            className="w-full rounded border border-neutral-300 px-3 py-2 text-sm"
            value={github}
            onChange={(e) => setGithub(e.target.value)}
            placeholder="username"
          />
          <button
            type="button"
            disabled={pending}
            className="rounded border border-neutral-300 px-3 py-2 text-sm"
            onClick={() => {
              void run(() => enrichGitHubAction(github));
            }}
          >
            Analyze GitHub
          </button>
          {profile.github_summary ? (
            <p className="text-sm text-neutral-600">{profile.github_summary}</p>
          ) : null}
        </div>
        <div className="space-y-3">
          <h2 className="text-lg font-medium">Portfolio import</h2>
          <input
            className="w-full rounded border border-neutral-300 px-3 py-2 text-sm"
            value={portfolio}
            onChange={(e) => setPortfolio(e.target.value)}
            placeholder="https://"
          />
          <button
            type="button"
            disabled={pending}
            className="rounded border border-neutral-300 px-3 py-2 text-sm"
            onClick={() => {
              void run(() => enrichPortfolioAction(portfolio));
            }}
          >
            Import portfolio
          </button>
          {profile.portfolio_summary ? (
            <p className="text-sm text-neutral-600">{profile.portfolio_summary}</p>
          ) : null}
        </div>
      </section>

      <section className="space-y-2 rounded border border-neutral-200 p-4">
        <h2 className="text-lg font-medium">Unified profile</h2>
        <p className="text-sm text-neutral-700">
          Skills: {profile.skills.length ? profile.skills.join(", ") : "none yet"}
        </p>
        <p className="text-sm text-neutral-700">
          Experience entries: {profile.experiences.length}
          {profile.years_experience != null ? ` · ~${profile.years_experience} years` : ""}
        </p>
        {profile.experiences.slice(0, 4).map((exp) => (
          <p key={`${exp.title}-${exp.company}`} className="text-sm text-neutral-600">
            {exp.title} @ {exp.company}
          </p>
        ))}
      </section>

      {error ? (
        <p className="text-sm text-red-700" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
