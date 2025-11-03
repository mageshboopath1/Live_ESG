import axios, { AxiosInstance, AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios'
import type {
  Company,
  Report,
  BRSRIndicatorDefinition,
  ExtractedIndicator,
  Citation,
  ESGScore,
  ScoreBreakdown
} from '@/types'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'
const API_TIMEOUT = 30000 // 30 seconds
const MAX_RETRIES = 3
const RETRY_DELAY = 1000 // 1 second

// Custom error class for API errors
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// API Client class
class ApiClient {
  private client: AxiosInstance
  private authToken: string | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    this.setupInterceptors()
  }

  // Setup request and response interceptors
  private setupInterceptors(): void {
    // Request interceptor for auth
    this.client.interceptors.request.use(
      (config) => {
        // Only add auth headers for mutation operations (POST, PUT, DELETE, PATCH)
        const method = config.method?.toUpperCase()
        const isMutation = method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH'
        
        if (isMutation) {
          // Add auth token if available
          if (this.authToken) {
            config.headers.Authorization = `Bearer ${this.authToken}`
          }

          // Add API key from environment if available
          const apiKey = import.meta.env.VITE_API_KEY
          if (apiKey) {
            config.headers['X-API-Key'] = apiKey
          }
        }

        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean; _retryCount?: number }

        // Handle network errors with retry
        if (!error.response && originalRequest && !originalRequest._retry) {
          return this.retryRequest(originalRequest, error)
        }

        // Handle specific HTTP errors
        if (error.response) {
          const { status, data } = error.response

          switch (status) {
            case 401:
              // Unauthorized - only clear token for mutation operations
              const method = originalRequest?.method?.toUpperCase()
              const isMutation = method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH'
              
              if (isMutation) {
                // Clear token and require authentication for mutations
                this.clearAuth()
                throw new ApiError('Authentication required for this operation', 401, data)
              } else {
                // For GET requests, this shouldn't happen but handle gracefully
                throw new ApiError('Authentication required', 401, data)
              }
            
            case 403:
              throw new ApiError('Access forbidden', 403, data)
            
            case 404:
              throw new ApiError('Resource not found', 404, data)
            
            case 429:
              // Rate limit - retry with exponential backoff
              if (originalRequest && !originalRequest._retry) {
                return this.retryRequest(originalRequest, error)
              }
              throw new ApiError('Rate limit exceeded', 429, data)
            
            case 500:
            case 502:
            case 503:
            case 504:
              // Server errors - retry
              if (originalRequest && !originalRequest._retry) {
                return this.retryRequest(originalRequest, error)
              }
              throw new ApiError('Server error', status, data)
            
            default:
              throw new ApiError(
                (data as any)?.message || 'An error occurred',
                status,
                data
              )
          }
        }

        throw new ApiError('Network error', undefined, error)
      }
    )
  }

  // Retry logic with exponential backoff
  private async retryRequest(
    config: AxiosRequestConfig & { _retry?: boolean; _retryCount?: number },
    error: AxiosError
  ): Promise<AxiosResponse> {
    config._retryCount = config._retryCount || 0

    if (config._retryCount >= MAX_RETRIES) {
      throw error
    }

    config._retry = true
    config._retryCount += 1

    // Exponential backoff
    const delay = RETRY_DELAY * Math.pow(2, config._retryCount - 1)
    await new Promise((resolve) => setTimeout(resolve, delay))

    return this.client.request(config)
  }

  // Auth methods
  setAuthToken(token: string): void {
    this.authToken = token
    localStorage.setItem('auth_token', token)
  }

  clearAuth(): void {
    this.authToken = null
    localStorage.removeItem('auth_token')
  }

  loadAuthToken(): void {
    const token = localStorage.getItem('auth_token')
    if (token) {
      this.authToken = token
    }
  }

  // Generic request method with retry support
  private async request<T>(
    method: string,
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    try {
      const response = await this.client.request<T>({
        method,
        url,
        data,
        ...config
      })
      return response.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new ApiError('Request failed', undefined, error)
    }
  }

  // Company endpoints
  async getCompanies(params?: {
    page?: number
    limit?: number
    industry?: string
  }): Promise<{ companies: Company[]; total: number; page: number; limit: number }> {
    return this.request('GET', '/companies', undefined, { params })
  }

  async getCompany(companyId: number): Promise<Company> {
    return this.request('GET', `/companies/${companyId}`)
  }

  async searchCompanies(query: string): Promise<Company[]> {
    return this.request('GET', '/companies/search', undefined, {
      params: { q: query }
    })
  }

  // Report endpoints
  async getCompanyReports(companyId: number): Promise<Report[]> {
    return this.request('GET', `/companies/${companyId}/reports`)
  }

  async getReport(objectKey: string): Promise<Report> {
    return this.request('GET', `/reports/${encodeURIComponent(objectKey)}`)
  }

  async triggerReportProcessing(objectKey: string): Promise<{ message: string; status: string }> {
    return this.request('POST', '/reports/trigger-processing', { object_key: objectKey })
  }

  // Indicator endpoints
  async getCompanyIndicators(
    companyId: number,
    year: number,
    params?: { attribute?: number; pillar?: 'E' | 'S' | 'G' }
  ): Promise<ExtractedIndicator[]> {
    return this.request('GET', `/companies/${companyId}/indicators`, undefined, {
      params: { year, ...params }
    })
  }

  async getIndicator(indicatorId: number): Promise<{
    indicator: ExtractedIndicator
    definition: BRSRIndicatorDefinition
    citations: Citation[]
  }> {
    return this.request('GET', `/indicators/${indicatorId}`)
  }

  async compareIndicators(
    companyIds: number[],
    year: number,
    indicatorCode?: string
  ): Promise<{
    companies: Company[]
    indicators: Record<number, ExtractedIndicator[]>
  }> {
    return this.request('GET', '/indicators/compare', undefined, {
      params: {
        companies: companyIds.join(','),
        year,
        indicator_code: indicatorCode
      }
    })
  }

  async getBRSRIndicatorDefinitions(): Promise<BRSRIndicatorDefinition[]> {
    return this.request('GET', '/indicators/definitions')
  }

  // Score endpoints
  async getCompanyScores(
    companyId: number,
    year: number
  ): Promise<ESGScore> {
    return this.request('GET', `/companies/${companyId}/scores`, undefined, {
      params: { year }
    })
  }

  async getScoreBreakdown(
    companyId: number,
    year: number
  ): Promise<ScoreBreakdown> {
    return this.request('GET', `/scores/breakdown/${companyId}/${year}`)
  }

  async getScoreHistory(
    companyId: number,
    startYear?: number,
    endYear?: number
  ): Promise<ESGScore[]> {
    return this.request('GET', `/companies/${companyId}/scores/history`, undefined, {
      params: { start_year: startYear, end_year: endYear }
    })
  }

  // Citation endpoints
  async getCitations(extractedIndicatorId: number): Promise<Citation[]> {
    return this.request('GET', `/citations/${extractedIndicatorId}`)
  }

  async getDocumentPage(
    objectKey: string,
    pageNumber: number
  ): Promise<{ url: string; presigned_url: string }> {
    return this.request('GET', `/documents/${encodeURIComponent(objectKey)}/page/${pageNumber}`)
  }

  async getDocumentUrl(objectKey: string): Promise<{ url: string; presigned_url: string }> {
    return this.request('GET', `/documents/${encodeURIComponent(objectKey)}`)
  }
}

// Create and export singleton instance
const apiClient = new ApiClient()

// Load auth token on initialization
apiClient.loadAuthToken()

export default apiClient
export { apiClient }
