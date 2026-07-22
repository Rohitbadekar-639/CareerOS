import { describe, expect, it, vi } from "vitest";

import { CareerOsApiError, CareerOsClient } from "../src/index";

describe("CareerOsClient", () => {
  it("calls /v1/me with bearer token", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify({
          id: "00000000-0000-0000-0000-000000000001",
          email: "user@example.com",
          status: "active",
          role: "candidate",
          email_verified: true,
        }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new CareerOsClient("http://api.test", async () => "tok");
    const me = await client.me();
    expect(me.email).toBe("user@example.com");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/v1/me",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({ Authorization: "Bearer tok" }),
      }),
    );
  });

  it("throws CareerOsApiError on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        text: async () => JSON.stringify({ detail: "Missing" }),
      }),
    );
    const client = new CareerOsClient("http://api.test");
    await expect(client.me()).rejects.toBeInstanceOf(CareerOsApiError);
  });
});
