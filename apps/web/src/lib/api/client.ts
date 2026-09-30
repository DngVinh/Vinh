export interface FieldError {
  code: string;
  pointer: string;
  detail: string;
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  code: string;
  request_id?: string;
  retryable?: boolean;
  errors?: FieldError[];
}

export class ApiClientError extends Error {
  readonly problem: ProblemDetails;

  constructor(problem: ProblemDetails) {
    super(problem.detail || problem.title || "API Error");
    this.name = "ApiClientError";
    this.problem = problem;
    Object.setPrototypeOf(this, ApiClientError.prototype);
  }
}

export interface ApiClientConfig {
  baseUrl?: string;
  defaultHeaders?: Record<string, string>;
}

export class ApiClient {
  private readonly baseUrl: string;
  private readonly defaultHeaders: Record<string, string>;

  constructor(config: ApiClientConfig = {}) {
    this.baseUrl = (config.baseUrl || "").replace(/\/$/, "");
    let token: string | null = null;
    try {
      if (typeof window !== "undefined" && typeof window.localStorage !== "undefined") {
        token = window.localStorage.getItem("campus247_token");
      }
    } catch {
      // ignore
    }
    this.defaultHeaders = {
      Accept: "application/json, application/problem+json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...config.defaultHeaders,
    };
  }

  async get<T>(path: string, headers?: Record<string, string>): Promise<T> {
    return this.request<T>("GET", path, undefined, headers);
  }

  async post<T>(path: string, body?: unknown, headers?: Record<string, string>): Promise<T> {
    return this.request<T>("POST", path, body, headers);
  }

  async put<T>(path: string, body?: unknown, headers?: Record<string, string>): Promise<T> {
    return this.request<T>("PUT", path, body, headers);
  }

  async delete<T>(path: string, headers?: Record<string, string>): Promise<T> {
    return this.request<T>("DELETE", path, undefined, headers);
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    headers?: Record<string, string>
  ): Promise<T> {
    const url = `${this.baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
    const reqHeaders: Record<string, string> = {
      ...this.defaultHeaders,
      ...headers,
    };

    let reqBody: string | undefined;
    if (body !== undefined) {
      reqHeaders["Content-Type"] = "application/json";
      reqBody = JSON.stringify(body);
    }

    let response: Response;
    try {
      response = await fetch(url, {
        method,
        headers: reqHeaders,
        body: reqBody,
        credentials: "include",
      });
    } catch (err: unknown) {
      throw new ApiClientError({
        type: "https://campus247.example/problems/network-error",
        title: "Lỗi kết nối",
        status: 0,
        detail: "Không thể kết nối đến máy chủ.",
        code: "NETWORK_ERROR",
        retryable: true,
      });
    }

    if (!response.ok) {
      const requestId = response.headers.get("x-request-id") || undefined;
      let problem: ProblemDetails;
      try {
        const json = await response.json();
        problem = {
          type: json.type || "https://campus247.example/problems/unknown",
          title: json.title || "Lỗi máy chủ",
          status: json.status || response.status,
          detail: json.detail || "Đã xảy ra lỗi khi xử lý yêu cầu.",
          code: json.code || "INTERNAL_ERROR",
          instance: json.instance,
          request_id: json.request_id || requestId,
          retryable: json.retryable ?? false,
          errors: json.errors,
        };
      } catch {
        problem = {
          type: "https://campus247.example/problems/http-error",
          title: `Lỗi HTTP ${response.status}`,
          status: response.status,
          detail: response.statusText || "Máy chủ phản hồi lỗi không xác định.",
          code: "HTTP_ERROR",
          request_id: requestId,
          retryable: response.status >= 500,
        };
      }
      throw new ApiClientError(problem);
    }

    return (await response.json()) as T;
  }
}
