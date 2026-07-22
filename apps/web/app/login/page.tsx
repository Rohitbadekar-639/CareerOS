import Link from "next/link";

import { AuthForm } from "@/features/identity/components/auth-form";

export default function LoginPage() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-8 p-8">
      <div className="text-center">
        <h1 className="text-3xl font-semibold tracking-tight">Sign in</h1>
        <p className="mt-2 text-sm text-neutral-600">
          New here?{" "}
          <Link className="underline" href="/signup">
            Create an account
          </Link>
        </p>
      </div>
      <AuthForm mode="login" />
    </main>
  );
}
