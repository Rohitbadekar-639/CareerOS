import Link from "next/link";
import { redirect } from "next/navigation";

import { CareerOsApiError } from "@career-os/sdk";

import { createCareerOsServerClient } from "@/lib/api";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export default async function AppHomePage() {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    redirect("/login");
  }

  let meError: string | null = null;
  let me: {
    id: string;
    email: string;
    status: string;
    role: string;
    email_verified: boolean;
  } | null = null;

  try {
    const api = await createCareerOsServerClient();
    me = await api.me();
  } catch (error) {
    if (error instanceof CareerOsApiError) {
      meError = `API ${error.status}: could not load profile`;
    } else {
      meError = error instanceof Error ? error.message : "Could not load profile";
    }
  }

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-lg flex-col gap-6 p-8">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">CareerOS</h1>
        <form action="/auth/logout" method="post">
          <button
            className="rounded border border-neutral-300 px-3 py-1.5 text-sm"
            type="submit"
          >
            Sign out
          </button>
        </form>
      </div>

      <p className="text-sm text-neutral-600">
        Signed in as <span className="font-medium text-neutral-900">{user.email}</span>
      </p>

      {me ? (
        <section className="rounded border border-neutral-200 p-4 text-sm">
          <h2 className="font-medium">Your CareerOS account</h2>
          <dl className="mt-3 space-y-1 text-neutral-700">
            <div>
              <dt className="inline font-medium">User id: </dt>
              <dd className="inline font-mono text-xs">{me.id}</dd>
            </div>
            <div>
              <dt className="inline font-medium">Status: </dt>
              <dd className="inline">{me.status}</dd>
            </div>
            <div>
              <dt className="inline font-medium">Role: </dt>
              <dd className="inline">{me.role}</dd>
            </div>
            <div>
              <dt className="inline font-medium">Email verified: </dt>
              <dd className="inline">{me.email_verified ? "yes" : "no"}</dd>
            </div>
          </dl>
        </section>
      ) : (
        <p className="text-sm text-red-700" role="alert">
          {meError}
        </p>
      )}

      <Link className="text-sm underline" href="/">
        Back to home
      </Link>
    </main>
  );
}
