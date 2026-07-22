export type MeResponse = {
  id: string;
  email: string;
  status: string;
  role: string;
  email_verified: boolean;
};

export type TokenProvider = () => Promise<string | null> | string | null;

export class CareerOsApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(status: number, body: unknown, message?: string) {
    super(message ?? `API request failed with status ${status}`);
    this.name = "CareerOsApiError";
    this.status = status;
    this.body = body;
  }
}

export class CareerOsClient {
  constructor(
    private readonly baseUrl: string,
    private readonly getAccessToken?: TokenProvider,
  ) {}

  async me(): Promise<MeResponse> {
    return this.request<MeResponse>("GET", "/v1/me");
  }

  private async request<T>(method: string, path: string): Promise<T> {
    const headers: Record<string, string> = {
      Accept: "application/json",
    };
    const token = this.getAccessToken ? await this.getAccessToken() : null;
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl.replace(/\/$/, "")}${path}`, {
      method,
      headers,
      cache: "no-store",
    });

    const text = await response.text();
    const body = text ? (JSON.parse(text) as unknown) : null;
    if (!response.ok) {
      throw new CareerOsApiError(response.status, body);
    }
    return body as T;
  }
}
