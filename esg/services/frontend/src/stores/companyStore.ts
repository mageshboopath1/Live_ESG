import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Company, Report } from '@/types'
import apiClient from '@/services/api'

interface CompanyCache {
  data: Company[]
  timestamp: number
}

interface ReportCache {
  [companyId: number]: {
    data: Report[]
    timestamp: number
  }
}

const CACHE_TTL = 60 * 60 * 1000 // 1 hour in milliseconds

export const useCompanyStore = defineStore('company', () => {
  // State
  const companies = ref<Company[]>([])
  const selectedCompany = ref<Company | null>(null)
  const reports = ref<Report[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // Cache
  const companyCache = ref<CompanyCache | null>(null)
  const reportCache = ref<ReportCache>({})
  const companyDetailsCache = ref<Map<number, { data: Company; timestamp: number }>>(new Map())

  // Computed
  const companiesByIndustry = computed(() => {
    const grouped: Record<string, Company[]> = {}
    companies.value.forEach((company) => {
      const industry = company.industry || 'Other'
      if (!grouped[industry]) {
        grouped[industry] = []
      }
      grouped[industry].push(company)
    })
    return grouped
  })

  const selectedCompanyReports = computed(() => {
    if (!selectedCompany.value) return []
    return reports.value.filter((r) => r.company_id === selectedCompany.value!.id)
  })

  // Helper: Check if cache is valid
  const isCacheValid = (timestamp: number): boolean => {
    return Date.now() - timestamp < CACHE_TTL
  }

  // Actions
  const fetchCompanies = async (params?: {
    page?: number
    limit?: number
    industry?: string
    forceRefresh?: boolean
  }) => {
    // Check cache first
    if (!params?.forceRefresh && companyCache.value && isCacheValid(companyCache.value.timestamp)) {
      companies.value = companyCache.value.data
      return companyCache.value.data
    }

    loading.value = true
    error.value = null

    try {
      const response = await apiClient.getCompanies(params)
      companies.value = response.companies
      
      // Update cache
      companyCache.value = {
        data: response.companies,
        timestamp: Date.now()
      }

      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch companies'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchCompanyById = async (companyId: number, forceRefresh = false) => {
    // Check cache first
    const cached = companyDetailsCache.value.get(companyId)
    if (!forceRefresh && cached && isCacheValid(cached.timestamp)) {
      selectedCompany.value = cached.data
      return cached.data
    }

    loading.value = true
    error.value = null

    try {
      const company = await apiClient.getCompany(companyId)
      selectedCompany.value = company
      
      // Update cache
      companyDetailsCache.value.set(companyId, {
        data: company,
        timestamp: Date.now()
      })

      return company
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch company'
      throw err
    } finally {
      loading.value = false
    }
  }

  const searchCompanies = async (query: string) => {
    if (!query.trim()) {
      return []
    }

    loading.value = true
    error.value = null

    try {
      const results = await apiClient.searchCompanies(query)
      return results
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to search companies'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchCompanyReports = async (companyId: number, forceRefresh = false) => {
    // Check cache first
    const cached = reportCache.value[companyId]
    if (!forceRefresh && cached && isCacheValid(cached.timestamp)) {
      reports.value = cached.data
      return cached.data
    }

    loading.value = true
    error.value = null

    try {
      const companyReports = await apiClient.getCompanyReports(companyId)
      reports.value = companyReports
      
      // Update cache
      reportCache.value[companyId] = {
        data: companyReports,
        timestamp: Date.now()
      }

      return companyReports
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch reports'
      throw err
    } finally {
      loading.value = false
    }
  }

  const triggerReportProcessing = async (objectKey: string) => {
    loading.value = true
    error.value = null

    try {
      const result = await apiClient.triggerReportProcessing(objectKey)
      
      // Invalidate report cache for the company
      const companyId = selectedCompany.value?.id
      if (companyId && reportCache.value[companyId]) {
        delete reportCache.value[companyId]
      }

      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to trigger processing'
      throw err
    } finally {
      loading.value = false
    }
  }

  const selectCompany = (company: Company | null) => {
    selectedCompany.value = company
  }

  const clearCache = () => {
    companyCache.value = null
    reportCache.value = {}
    companyDetailsCache.value.clear()
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // State
    companies,
    selectedCompany,
    reports,
    loading,
    error,
    
    // Computed
    companiesByIndustry,
    selectedCompanyReports,
    
    // Actions
    fetchCompanies,
    fetchCompanyById,
    searchCompanies,
    fetchCompanyReports,
    triggerReportProcessing,
    selectCompany,
    clearCache,
    clearError
  }
})
