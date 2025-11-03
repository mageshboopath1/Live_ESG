export interface Indicator {
  id: number
  code: string
  name: string
  value: string
  numericValue?: number
  unit: string
  confidence: number
  validationStatus: 'valid' | 'invalid' | 'pending'
  attributeNumber: number
  pillar: 'E' | 'S' | 'G'
}

export interface BRSRIndicatorDefinition {
  id: number
  indicator_code: string
  attribute_number: number
  parameter_name: string
  measurement_unit: string | null
  description: string
  pillar: 'E' | 'S' | 'G'
  weight: number
  created_at: string
}

export interface ExtractedIndicator {
  id: number
  object_key: string
  company_id: number
  report_year: number
  indicator_id: number
  extracted_value: string
  numeric_value: number | null
  confidence_score: number
  validation_status: 'valid' | 'invalid' | 'pending'
  source_pages: number[]
  source_chunk_ids: number[]
  extracted_at: string
}

export interface Citation {
  pdfName: string
  pages: number[]
  chunkText: string
  url: string
}
