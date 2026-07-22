import { redirect } from "next/navigation";

import type { ReactNode } from "react";

import { AppNav } from "@/features/jobs/components/app-nav";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export default async function AppLayout({ children }: { children: ReactNode }) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    redirect("/login");
  }

  return (
    <div className="min-h-dvh bg-[linear-gradient(180deg,#fafafa_0%,#ffffff_40%)]">
      <AppNav email={user.email} />
      <div className="mx-auto w-full max-w-5xl px-6 py-8">{children}</div>
    </div>
  );
}
