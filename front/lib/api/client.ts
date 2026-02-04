export const BACKEND_URL = "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: any,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = path.startsWith("http") ? path : `${BACKEND_URL}${path}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (response.status === 204) {
    return {} as T;
  }

  const json = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new ApiError(
      response.status,
      json.detail || json.error || "API request failed",
      json.detail,
    );
  }

  return json;
}
