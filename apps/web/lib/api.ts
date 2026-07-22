import { CareerOsClient } from "@career-os/sdk";

import { createSupabaseServerClient } from "@/lib/supabase/server";

export function getApiBaseUrl(): string {
  return process.env.CAREEROS_API_BASE_URL ?? "http://127.0.0.1:8000";
}

export async function createCareerOsServerClient(): Promise<CareerOsClient> {
  const supabase = await createSupabaseServerClient();
  return new CareerOsClient(getApiBaseUrl(), async () => {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    return session?.access_token ?? null;
  });
}
