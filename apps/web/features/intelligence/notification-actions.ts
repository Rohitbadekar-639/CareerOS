"use server";

import { revalidatePath } from "next/cache";

import { createCareerOsServerClient } from "@/lib/api";

export async function markNotificationReadAction(id: string) {
  const api = await createCareerOsServerClient();
  await api.markNotificationRead(id);
  revalidatePath("/app/notifications");
}
