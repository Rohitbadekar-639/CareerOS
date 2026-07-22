import Link from "next/link";

import { AuthForm } from "@/features/identity/components/auth-form";

export default function SignupPage() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-8 p-8">
      <div className="text-center">
        <h1 className="text-3xl font-semibold tracking-tight">Create account</h1>
        <p className="mt-2 text-sm text-neutral-600">
          Already registered?{" "}
          <Link className="underline" href="/login">
            Sign in
          </Link>
        </p>
      </div>
      <AuthForm mode="signup" />
    </main>
  );
}
