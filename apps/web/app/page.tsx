import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-semibold tracking-tight">CareerOS</h1>
      <p className="max-w-md text-center text-neutral-600">
        AI Career Operating System — sign in to continue.
      </p>
      <div className="flex gap-3">
        <Link
          className="rounded bg-neutral-900 px-4 py-2 text-sm font-medium text-white"
          href="/login"
        >
          Sign in
        </Link>
        <Link
          className="rounded border border-neutral-300 px-4 py-2 text-sm font-medium"
          href="/signup"
        >
          Create account
        </Link>
      </div>
    </main>
  );
}
