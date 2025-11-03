import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ESGScore, ScoreBreakdown } from '@/types'
import apiClient from '@/services/api'

interface ScoreCache {
  [key: string]: {
    data: ESGScore
    timestamp: number
  }
}

interface BreakdownCache {
  [key: string]: {
    data: ScoreBreakdown
    timestamp: number
  }
}

interface HistoryCache {
  [companyId: number]: {
    data: ESGScore[]
    timestamp: number
  }
}

const CACHE_TTL = 60 * 60 * 1000 // 1 hour in milliseconds

export const useScoreStore = defineStore('score', () => {
  // State
  const scores = ref<ESGScore[]>([])
  const selectedScore = ref<ESGScore | null>(null)
  const scoreBreakdown = ref<ScoreBreakdown | null>(null)
  const scoreHistory = ref<ESGScore[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Cache
  const scoreCache = ref<ScoreCache>({})
  const breakdownCache = ref<BreakdownCache>({})
  const historyCache = ref<HistoryCache>({})

  // Computed
  const latestScore = computed(() => {
    if (scores.value.length === 0) return null
    return scores.value.reduce((latest, score) => {
      return score.report_year > latest.report_year ? score : latest
    })
  })

  const scoresByYear = computed(() => {
    const grouped: Record<number, ESGScore[]> = {}
    scores.value.forEach((score) => {
      if (!grouped[score.report_year]) {
        grouped[score.report_year] = []
      }
      grouped[score.report_year].push(score)
    })
    return grouped
  })

  const averageScores = computed(() => {
    if (scores.value.length === 0) {
      return {
        environmental: 0,
        social: 0,
        governance: 0,
        overall: 0
      }
    }

    const sum = scores.value.reduce(
      (acc, score) => ({
        environmental: acc.environmental + score.environmental_score,
        social: acc.social + score.social_score,
        governance: acc.governance + score.governance_score,
        overall: acc.overall + score.overall_score
      }),
      { environmental: 0, social: 0, governance: 0, overall: 0 }
    )

    const count = scores.value.length
    return {
      environmental: sum.environmental / count,
      social: sum.social / count,
      governance: sum.governance / count,
      overall: sum.overall / count
    }
  })

  const scoreTrend = computed(() => {
    if (scoreHistory.value.length < 2) return null

    const sorted = [...scoreHistory.value].sort((a, b) => a.report_year - b.report_year)
    const first = sorted[0]
    const last = sorted[sorted.length - 1]

    return {
      environmental: last.environmental_score - first.environmental_score,
      social: last.social_score - first.social_score,
      governance: last.governance_score - first.governance_score,
      overall: last.overall_score - first.overall_score,
      years: last.report_year - first.report_year
    }
  })

  // Helper: Check if cache is valid
  const isCacheValid = (timestamp: number): boolean => {
    return Date.now() - timestamp < CACHE_TTL
  }

  // Actions
  const fetchCompanyScore = async (
    companyId: number,
    year: number,
    forceRefresh = false
  ) => {
    const cacheKey = `${companyId}-${year}`
    
    // Check cache first
    const cached = scoreCache.value[cacheKey]
    if (!forceRefresh && cached && isCacheValid(cached.timestamp)) {
      selectedScore.value = cached.data
      return cached.data
    }

    loading.value = true
    error.value = null

    try {
      const score = await apiClient.getCompanyScores(companyId, year)
      selectedScore.value = score
      
      // Update cache
      scoreCache.value[cacheKey] = {
        data: score,
        timestamp: Date.now()
      }

      // Add to scores array if not already present
      const existingIndex = scores.value.findIndex(
        (s) => s.company_id === companyId && s.report_year === year
      )
      if (existingIndex >= 0) {
        scores.value[existingIndex] = score
      } else {
        scores.value.push(score)
      }

      return score
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch score'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchScoreBreakdown = async (
    companyId: number,
    year: number,
    forceRefresh = false
  ) => {
    const cacheKey = `${companyId}-${year}`
    
    // Check cache first
    const cached = breakdownCache.value[cacheKey]
    if (!forceRefresh && cached && isCacheValid(cached.timestamp)) {
      scoreBreakdown.value = cached.data
      return cached.data
    }

    loading.value = true
    error.value = null

    try {
      const breakdown = await apiClient.getScoreBreakdown(companyId, year)
      scoreBreakdown.value = breakdown
      
      // Update cache
      breakdownCache.value[cacheKey] = {
        data: breakdown,
        timestamp: Date.now()
      }

      return breakdown
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch score breakdown'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchScoreHistory = async (
    companyId: number,
    startYear?: number,
    endYear?: number,
    forceRefresh = false
  ) => {
    // Check cache first
    const cached = historyCache.value[companyId]
    if (!forceRefresh && cached && isCacheValid(cached.timestamp)) {
      scoreHistory.value = cached.data
      return cached.data
    }

    loading.value = true
    error.value = null

    try {
      const history = await apiClient.getScoreHistory(companyId, startYear, endYear)
      scoreHistory.value = history
      
      // Update cache
      historyCache.value[companyId] = {
        data: history,
        timestamp: Date.now()
      }

      // Update scores array
      history.forEach((score) => {
        const existingIndex = scores.value.findIndex(
          (s) => s.company_id === score.company_id && s.report_year === score.report_year
        )
        if (existingIndex >= 0) {
          scores.value[existingIndex] = score
        } else {
          scores.value.push(score)
        }
      })

      return history
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch score history'
      throw err
    } finally {
      loading.value = false
    }
  }

  const getScoreByYear = (year: number): ESGScore | undefined => {
    return scores.value.find((s) => s.report_year === year)
  }

  const compareScores = (companyIds: number[], year: number) => {
    return scores.value.filter(
      (s) => companyIds.includes(s.company_id) && s.report_year === year
    )
  }

  const selectScore = (score: ESGScore | null) => {
    selectedScore.value = score
  }

  const clearCache = () => {
    scoreCache.value = {}
    breakdownCache.value = {}
    historyCache.value = {}
  }

  const clearError = () => {
    error.value = null
  }

  const clearSelection = () => {
    selectedScore.value = null
    scoreBreakdown.value = null
  }

  const clearHistory = () => {
    scoreHistory.value = []
  }

  return {
    // State
    scores,
    selectedScore,
    scoreBreakdown,
    scoreHistory,
    loading,
    error,
    
    // Computed
    latestScore,
    scoresByYear,
    averageScores,
    scoreTrend,
    
    // Actions
    fetchCompanyScore,
    fetchScoreBreakdown,
    fetchScoreHistory,
    getScoreByYear,
    compareScores,
    selectScore,
    clearCache,
    clearError,
    clearSelection,
    clearHistory
  }
})
