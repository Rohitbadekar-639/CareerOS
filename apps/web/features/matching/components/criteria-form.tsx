"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import type { SeekerCriteria } from "@career-os/sdk";

import { saveSeekerCriteria } from "@/features/matching/actions";

export function CriteriaForm({ initial }: { initial: SeekerCriteria | null }) {
  const router = useRouter();
  const [resumeText, setResumeText] = useState(initial?.resume_text ?? "");
  const [skills, setSkills] = useState((initial?.skills ?? []).join(", "));
  const [locations, setLocations] = useState(
    (initial?.preferred_locations ?? []).join(", "),
  );
  const [years, setYears] = useState(
    initial?.years_experience != null ? String(initial.years_experience) : "",
  );
  const [salary, setSalary] = useState(
    initial?.salary_expectation_min != null
      ? String(initial.salary_expectation_min)
      : "",
  );
  const [remote, setRemote] = useState(initial?.remote_preference ?? "any");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    const result = await saveSeekerCriteria({
      resume_text: resumeText,
      skills: skills
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      preferred_locations: locations
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      years_experience: years ? Number(years) : null,
      salary_expectation_min: salary ? Number(salary) : null,
      salary_currency: "INR",
      remote_preference: remote,
    });
    setPending(false);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    router.refresh();
  }

  return (
    <form
      className="flex flex-col gap-3"
      onSubmit={(event) => {
        void onSubmit(event);
      }}
    >
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium">Resume / experience notes</span>
        <textarea
          className="min-h-28 rounded border border-neutral-300 px-3 py-2"
          value={resumeText}
          onChange={(event) => setResumeText(event.target.value)}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium">Skills (comma-separated)</span>
        <input
          className="rounded border border-neutral-300 px-3 py-2"
          value={skills}
          onChange={(event) => setSkills(event.target.value)}
          placeholder="python, fastapi, postgres"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium">Preferred locations</span>
        <input
          className="rounded border border-neutral-300 px-3 py-2"
          value={locations}
          onChange={(event) => setLocations(event.target.value)}
          placeholder="Bengaluru, Hyderabad"
        />
      </label>
      <div className="grid grid-cols-2 gap-3">
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium">Years experience</span>
          <input
            className="rounded border border-neutral-300 px-3 py-2"
            type="number"
            min={0}
            value={years}
            onChange={(event) => setYears(event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium">Min salary (INR)</span>
          <input
            className="rounded border border-neutral-300 px-3 py-2"
            type="number"
            min={0}
            value={salary}
            onChange={(event) => setSalary(event.target.value)}
          />
        </label>
      </div>
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium">Remote preference</span>
        <select
          className="rounded border border-neutral-300 px-3 py-2"
          value={remote}
          onChange={(event) => setRemote(event.target.value)}
        >
          <option value="any">Any</option>
          <option value="remote_only">Remote only</option>
          <option value="hybrid_or_onsite">Hybrid / onsite</option>
        </select>
      </label>
      {error ? (
        <p className="text-sm text-red-700" role="alert">
          {error}
        </p>
      ) : null}
      <button
        className="w-fit rounded bg-neutral-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
        type="submit"
        disabled={pending}
      >
        {pending ? "Saving…" : "Save & recompute"}
      </button>
    </form>
  );
}
