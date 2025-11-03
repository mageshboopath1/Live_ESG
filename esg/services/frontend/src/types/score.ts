import type { Citation } from './indicator'

export interface Score {
  environmental: number
  social: number
  governance: number
  overall: number
  breakdown: ScoreBreakdown
}

export interface ESGScore {
  id: number
  company_id: number
  report_year: number
  environmental_score: number
  social_score: number
  governance_score: number
  overall_score: number
  calculation_metadata: CalculationMetadata
  calculated_at: string
}

export interface CalculationMetadata {
  weights: {
    environmental: number
    social: number
    governance: number
  }
  indicators: {
    [key: string]: {
      value: number
      weight: number
      pillar: 'E' | 'S' | 'G'
    }
  }
}

export interface ScoreBreakdown {
  pillars: PillarBreakdown[]
}

export interface PillarBreakdown {
  name: string
  score: number
  weight: number
  indicators: IndicatorContribution[]
}

export interface IndicatorContribution {
  code: string
  value: number
  weight: number
  citations: Citation[]
}
