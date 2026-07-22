export type MeResponse = {
  id: string;
  email: string;
  status: string;
  role: string;
  email_verified: boolean;
};

export type Opportunity = {
  id: string;
  title: string;
  company: string;
  location: string | null;
  is_remote: boolean;
  apply_url: string;
  source_kind: string;
  skills: string[];
  posted_at: string | null;
  updated_at: string;
  description_text?: string | null;
};

export type OpportunityDetail = Opportunity & {
  description_text: string;
  application_status: string | null;
  match_score: number | null;
};

export type SeekerCriteria = {
  resume_text: string;
  skills: string[];
  years_experience: number | null;
  preferred_locations: string[];
  salary_expectation_min: number | null;
  salary_currency: string | null;
  remote_preference: string;
};

export type Recommendation = {
  opportunity_id: string;
  title: string;
  company: string;
  location: string | null;
  is_remote: boolean;
  apply_url: string;
  score: number;
  reasons: string[];
  gaps: string[];
  model_version: string;
};

export type CopilotAdvice = {
  match_score: number | null;
  why_match: string[];
  missing_skills: string[];
  resume_suggestions: string[];
  model_version: string;
};

export type CoverLetterDraft = {
  body: string;
  grounding_notes: string[];
  requires_human_review: boolean;
  model_version: string;
  application_id: string | null;
};

export type Application = {
  id: string;
  opportunity_id: string;
  status: string;
  notes: string;
  cover_letter_draft: string | null;
  created_at: string;
  updated_at: string;
  title: string | null;
  company: string | null;
  apply_url: string | null;
  location: string | null;
  is_remote: boolean | null;
};

export type CandidateProfile = {
  version: number;
  headline: string;
  summary: string;
  resume_text: string;
  linkedin_text: string;
  skills: string[];
  experiences: {
    title: string;
    company: string;
    start_year: number | null;
    end_year: number | null;
    summary: string;
  }[];
  years_experience: number | null;
  preferred_locations: string[];
  salary_expectation_min: number | null;
  salary_currency: string | null;
  remote_preference: string;
  github_username: string | null;
  linkedin_url: string | null;
  portfolio_url: string | null;
  github_summary: string;
  portfolio_summary: string;
};

export type AppNotification = {
  id: string;
  kind: string;
  title: string;
  body: string;
  status: string;
  created_at: string;
  read_at: string | null;
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

  async searchOpportunities(params?: {
    q?: string;
    location?: string;
    remote_only?: boolean;
    company?: string;
    source?: string;
    limit?: number;
  }): Promise<{ items: Opportunity[] }> {
    const query = new URLSearchParams();
    if (params?.q) query.set("q", params.q);
    if (params?.location) query.set("location", params.location);
    if (params?.remote_only != null) query.set("remote_only", String(params.remote_only));
    if (params?.company) query.set("company", params.company);
    if (params?.source) query.set("source", params.source);
    if (params?.limit != null) query.set("limit", String(params.limit));
    const suffix = query.size ? `?${query.toString()}` : "";
    return this.request<{ items: Opportunity[] }>("GET", `/v1/opportunities${suffix}`);
  }

  async getOpportunity(id: string): Promise<OpportunityDetail> {
    return this.request<OpportunityDetail>("GET", `/v1/opportunities/${id}`);
  }

  async getCopilot(opportunityId: string): Promise<CopilotAdvice> {
    return this.request<CopilotAdvice>("GET", `/v1/opportunities/${opportunityId}/copilot`);
  }

  async generateCoverLetter(opportunityId: string): Promise<CoverLetterDraft> {
    return this.request<CoverLetterDraft>(
      "POST",
      `/v1/opportunities/${opportunityId}/cover-letter`,
    );
  }

  async saveOpportunity(opportunityId: string): Promise<Application> {
    return this.request<Application>("POST", `/v1/opportunities/${opportunityId}/save`);
  }

  async markApplied(opportunityId: string): Promise<Application> {
    return this.request<Application>("POST", `/v1/opportunities/${opportunityId}/apply`);
  }

  async listApplications(status?: string): Promise<{ items: Application[] }> {
    const suffix = status ? `?status=${encodeURIComponent(status)}` : "";
    return this.request<{ items: Application[] }>("GET", `/v1/me/applications${suffix}`);
  }

  async updateApplicationStatus(id: string, status: string): Promise<Application> {
    return this.request<Application>("PATCH", `/v1/me/applications/${id}`, { status });
  }

  async getCriteria(): Promise<SeekerCriteria> {
    return this.request<SeekerCriteria>("GET", "/v1/me/criteria");
  }

  async upsertCriteria(body: SeekerCriteria): Promise<SeekerCriteria> {
    return this.request<SeekerCriteria>("PUT", "/v1/me/criteria", body);
  }

  async recommendations(limit = 50): Promise<{ items: Recommendation[] }> {
    return this.request<{ items: Recommendation[] }>(
      "GET",
      `/v1/me/recommendations?limit=${limit}`,
    );
  }

  async getProfile(): Promise<CandidateProfile> {
    return this.request<CandidateProfile>("GET", "/v1/me/profile");
  }

  async upsertProfile(body: {
    headline?: string;
    preferred_locations?: string[];
    salary_expectation_min?: number | null;
    salary_currency?: string | null;
    remote_preference?: string;
    github_username?: string | null;
    linkedin_url?: string | null;
    portfolio_url?: string | null;
  }): Promise<CandidateProfile> {
    return this.request<CandidateProfile>("PUT", "/v1/me/profile", body);
  }

  async ingestResume(text: string): Promise<CandidateProfile> {
    return this.request<CandidateProfile>("POST", "/v1/me/profile/resume", { text });
  }

  async ingestLinkedIn(text: string): Promise<CandidateProfile> {
    return this.request<CandidateProfile>("POST", "/v1/me/profile/linkedin", { text });
  }

  async enrichGitHub(username: string): Promise<CandidateProfile> {
    return this.request<CandidateProfile>("POST", "/v1/me/profile/github", { username });
  }

  async enrichPortfolio(url: string): Promise<CandidateProfile> {
    return this.request<CandidateProfile>("POST", "/v1/me/profile/portfolio", { url });
  }

  async listNotifications(): Promise<{ items: AppNotification[] }> {
    return this.request<{ items: AppNotification[] }>("GET", "/v1/me/notifications");
  }

  async markNotificationRead(id: string): Promise<AppNotification> {
    return this.request<AppNotification>("POST", `/v1/me/notifications/${id}/read`);
  }

  private async request<T>(
    method: string,
    path: string,
    jsonBody?: unknown,
  ): Promise<T> {
    const headers: Record<string, string> = {
      Accept: "application/json",
    };
    const token = this.getAccessToken ? await this.getAccessToken() : null;
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    let body: string | undefined;
    if (jsonBody !== undefined) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(jsonBody);
    }

    const response = await fetch(`${this.baseUrl.replace(/\/$/, "")}${path}`, {
      method,
      headers,
      body,
      cache: "no-store",
    });

    const text = await response.text();
    const parsed = text ? (JSON.parse(text) as unknown) : null;
    if (!response.ok) {
      throw new CareerOsApiError(response.status, parsed);
    }
    return parsed as T;
  }
}
