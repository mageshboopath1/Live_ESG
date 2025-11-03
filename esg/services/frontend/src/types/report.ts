export interface Report {
  id: number
  company_id: number
  source: string
  file_path: string
  file_type: string
  ingested_at: string
  status: 'SUCCESS' | 'FAILED' | 'PENDING' | 'PROCESSING'
  object_key: string
  report_year: number
  report_type: string
}
