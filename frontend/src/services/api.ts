/**
 * API client configuration using ky
 */

import ky, { type KyInstance, type Options } from 'ky';

// API configuration
const API_URL = import.meta.env.VITE_API_URL || '/api/v1';
const API_KEY = import.meta.env.VITE_API_KEY || '';

// Custom error class for API errors
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Create the base API client
const createApiClient = (): KyInstance => {
  return ky.create({
    prefixUrl: API_URL,
    timeout: 30000,
    headers: {
      ...(API_KEY && { 'X-API-Key': API_KEY }),
    },
    hooks: {
      beforeRequest: [
        (request) => {
          // Add any request interceptors here
          console.debug(`[API] ${request.method} ${request.url}`);
        },
      ],
      beforeError: [
        async (error) => {
          const { response } = error;
          if (response) {
            try {
              const body = await response.json() as { detail?: string };
              const message = body.detail || error.message;
              throw new ApiError(message, response.status, body);
            } catch (parseError) {
              if (parseError instanceof ApiError) {
                throw parseError;
              }
              throw new ApiError(error.message, response.status);
            }
          }
          return error;
        },
      ],
    },
    retry: {
      limit: 2,
      methods: ['get'],
      statusCodes: [408, 429, 500, 502, 503, 504],
    },
  });
};

// Export the API client instance
export const api = createApiClient();

// Helper function for file uploads
export async function uploadFile(
  endpoint: string,
  file: File,
  additionalData?: Record<string, string>,
  options?: Options
): Promise<Response> {
  const formData = new FormData();
  formData.append('file', file);

  if (additionalData) {
    Object.entries(additionalData).forEach(([key, value]) => {
      formData.append(key, value);
    });
  }

  return api.post(endpoint, {
    body: formData,
    timeout: 120000, // 2 minutes for file uploads
    ...options,
  });
}

// Helper for polling with exponential backoff
export async function pollUntil<T>(
  fetchFn: () => Promise<T>,
  checkFn: (data: T) => boolean,
  options: {
    maxAttempts?: number;
    initialDelay?: number;
    maxDelay?: number;
    backoffMultiplier?: number;
  } = {}
): Promise<T> {
  const {
    maxAttempts = 60,
    initialDelay = 1000,
    maxDelay = 10000,
    backoffMultiplier = 1.5,
  } = options;

  let attempts = 0;
  let delay = initialDelay;

  while (attempts < maxAttempts) {
    const data = await fetchFn();
    if (checkFn(data)) {
      return data;
    }

    await new Promise((resolve) => setTimeout(resolve, delay));
    delay = Math.min(delay * backoffMultiplier, maxDelay);
    attempts++;
  }

  throw new Error('Polling timeout exceeded');
}
