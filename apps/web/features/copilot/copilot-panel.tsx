import type { CopilotAdvice } from "@career-os/sdk";

export function CopilotPanel({ advice }: { advice: CopilotAdvice }) {
  return (
    <aside className="rounded border border-neutral-200 bg-white p-5">
      <h2 className="text-lg font-semibold tracking-tight">AI Career Copilot</h2>
      <p className="mt-1 text-xs text-neutral-500">
        Grounded in your ranking profile and match score · {advice.model_version}
      </p>
      {advice.match_score != null ? (
        <p className="mt-4 text-sm">
          Fit score:{" "}
          <span className="font-medium tabular-nums">
            {(advice.match_score * 100).toFixed(0)}%
          </span>
        </p>
      ) : null}
      <section className="mt-4 space-y-2">
        <h3 className="text-sm font-medium">Why this matches</h3>
        <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-700">
          {advice.why_match.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
      <section className="mt-4 space-y-2">
        <h3 className="text-sm font-medium">Missing / weak skills</h3>
        {advice.missing_skills.length === 0 ? (
          <p className="text-sm text-neutral-600">No major skill gaps flagged.</p>
        ) : (
          <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-700">
            {advice.missing_skills.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}
      </section>
      <section className="mt-4 space-y-2">
        <h3 className="text-sm font-medium">Resume improvements</h3>
        <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-700">
          {advice.resume_suggestions.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </aside>
  );
}
