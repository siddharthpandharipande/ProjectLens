const API_BASE_URL = '/api';

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers = new Headers(options.headers || {});

  // Don't set Content-Type if sending FormData (browser handles boundary)
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = `API request failed with status ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch {
      // Use default status message
    }
    throw new ApiError(errorMessage, response.status);
  }

  return response.json();
}
