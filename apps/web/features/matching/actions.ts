"use server";

import { revalidatePath } from "next/cache";

import type { SeekerCriteria } from "@career-os/sdk";

import { createCareerOsServerClient } from "@/lib/api";

export async function saveSeekerCriteria(input: SeekerCriteria): Promise<{ ok: true } | { ok: false; error: string }> {
  try {
    const api = await createCareerOsServerClient();
    await api.upsertCriteria(input);
    revalidatePath("/app");
    revalidatePath("/app/profile");
    return { ok: true };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Save failed",
    };
  }
}
