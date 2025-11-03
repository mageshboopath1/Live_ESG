"""
ESG Intelligence Platform - Main Pipeline DAG

This DAG orchestrates the complete ESG data processing pipeline using DockerOperator
for all service execution. This ensures consistency with production deployments and
eliminates duplicate logic between Airflow and services.

Pipeline Stages:
1. Company Catalog Sync (optional, can be scheduled separately)
2. Ingestion - Download PDFs for selected companies
3. Embeddings - Generate vector embeddings for semantic search
4. Extraction - Extract BRSR indicators using LangChain + GenAI

All orchestration logic is handled by Airflow, while business logic remains in services.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.task_group import TaskGroup

# ============================================================================
# DAG Configuration
# ============================================================================

default_args = {
    'owner': 'esg-platform',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

dag = DAG(
    'esg_pipeline',
    default_args=default_args,
    description='ESG Intelligence Platform - Complete Data Pipeline',
    schedule_interval=None,  # Manual trigger or API trigger
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['esg', 'pipeline', 'production'],
    params={
        'companies': '',  # Comma-separated company symbols, empty = all
        'report_year': '',  # Specific year or empty for latest
        'skip_company_sync': True,  # Skip company catalog sync
    },
    max_active_runs=1,  # Prevent concurrent pipeline runs
)

# ============================================================================
# Shared Docker Configuration
# ============================================================================

docker_config = {
    'docker_url': 'unix://var/run/docker.sock',
    'network_mode': 'esg-backend',
    'auto_remove': True,
    'mount_tmp_dir': False,
    'tty': True,
}

# Environment variables passed to all services
# These reference Airflow variables set via UI or environment
base_env = {
    'DB_HOST': 'postgres',
    'DB_PORT': '5432',
    'DB_NAME': '{{ var.value.db_name }}',
    'DB_USER': '{{ var.value.db_user }}',
    'DB_PASSWORD': '{{ var.value.db_password }}',
    'MINIO_ENDPOINT': 'http://minio:9000',
    'MINIO_ACCESS_KEY': '{{ var.value.minio_access_key }}',
    'MINIO_SECRET_KEY': '{{ var.value.minio_secret_key }}',
    'RABBITMQ_HOST': 'rabbitmq',
    'RABBITMQ_PORT': '5672',
    'RABBITMQ_USER': '{{ var.value.get("rabbitmq_user", "guest") }}',
    'RABBITMQ_PASS': '{{ var.value.get("rabbitmq_pass", "guest") }}',
    'GOOGLE_API_KEY': '{{ var.value.google_api_key }}',
}

# ============================================================================
# Pipeline Tasks
# ============================================================================

with dag:
    
    # ------------------------------------------------------------------------
    # Start
    # ------------------------------------------------------------------------
    
    start = EmptyOperator(
        task_id='start',
        doc_md="""
        ## Pipeline Start
        
        This pipeline processes ESG reports through the following stages:
        1. Company catalog sync (optional)
        2. PDF ingestion
        3. Embedding generation
        4. Indicator extraction
        
        **Parameters:**
        - `companies`: Comma-separated list of company symbols (empty = all)
        - `report_year`: Specific year to process (empty = latest)
        - `skip_company_sync`: Skip company catalog sync (default: true)
        """
    )
    
    # ------------------------------------------------------------------------
    # Stage 1: Company Catalog Sync (Optional)
    # ------------------------------------------------------------------------
    
    with TaskGroup('company_catalog', tooltip='Sync company catalog') as company_catalog_group:
        
        sync_company_catalog = DockerOperator(
            task_id='sync_catalog',
            image='esg-company-catalog:latest',
            **docker_config,
            environment=base_env,
            command='python src/main.py',
            doc_md="""
            ## Company Catalog Sync
            
            Synchronizes the company catalog with the latest data.
            This task can be skipped if the catalog is already up-to-date.
            """,
        )
    
    # ------------------------------------------------------------------------
    # Stage 2: Ingestion
    # ------------------------------------------------------------------------
    
    with TaskGroup('ingestion', tooltip='Download and store PDF reports') as ingestion_group:
        
        ingest_reports = DockerOperator(
            task_id='download_pdfs',
            image='esg-ingestion:latest',
            **docker_config,
            environment={
                **base_env,
                'COMPANIES': '{{ params.companies }}',
                'REPORT_YEAR': '{{ params.report_year }}',
            },
            command='python src/main.py',
            execution_timeout=timedelta(hours=1),
            doc_md="""
            ## PDF Ingestion
            
            Downloads BRSR PDF reports for specified companies and stores them in MinIO.
            
            **Environment Variables:**
            - `COMPANIES`: Comma-separated company symbols (empty = all active companies)
            - `REPORT_YEAR`: Specific year to download (empty = latest available)
            
            **Output:**
            - PDFs stored in MinIO bucket: `esg-reports`
            - Metadata stored in `document_metadata` table
            """,
        )
    
    # ------------------------------------------------------------------------
    # Stage 3: Embeddings
    # ------------------------------------------------------------------------
    
    with TaskGroup('embeddings', tooltip='Generate vector embeddings') as embeddings_group:
        
        generate_embeddings = DockerOperator(
            task_id='generate_vectors',
            image='esg-embeddings:latest',
            **docker_config,
            environment=base_env,
            command='python src/batch_processor.py',
            execution_timeout=timedelta(minutes=45),
            doc_md="""
            ## Embedding Generation
            
            Processes PDFs to generate vector embeddings for semantic search.
            
            **Process:**
            1. Extracts text from PDFs
            2. Splits text into chunks
            3. Generates embeddings using Google GenAI
            4. Stores vectors in PostgreSQL with pgvector
            
            **Output:**
            - Embeddings stored in `document_embeddings` table
            - Enables semantic search for indicator extraction
            """,
        )
    
    # ------------------------------------------------------------------------
    # Stage 4: Extraction
    # ------------------------------------------------------------------------
    
    with TaskGroup('extraction', tooltip='Extract BRSR indicators') as extraction_group:
        
        extract_indicators = DockerOperator(
            task_id='extract_brsr_indicators',
            image='esg-extraction:latest',
            **docker_config,
            environment=base_env,
            command='python src/batch_extractor.py',
            execution_timeout=timedelta(hours=1),
            doc_md="""
            ## Indicator Extraction
            
            Extracts BRSR indicators from documents using LangChain and GenAI.
            
            **Process:**
            1. Retrieves relevant document chunks using semantic search
            2. Uses LLM to extract structured indicator data
            3. Validates extracted data
            4. Calculates ESG scores
            
            **Output:**
            - Extracted indicators in `extracted_indicators` table
            - ESG scores in `esg_scores` table
            - Citations in `indicator_citations` table
            """,
        )
    
    # ------------------------------------------------------------------------
    # End
    # ------------------------------------------------------------------------
    
    end = EmptyOperator(
        task_id='end',
        doc_md="""
        ## Pipeline Complete
        
        All stages have completed successfully. Data is now available via the API Gateway.
        
        **Next Steps:**
        - View results in the frontend application
        - Query data via API endpoints
        - Run validation queries to verify data quality
        """
    )
    
    # ------------------------------------------------------------------------
    # Define Task Dependencies
    # ------------------------------------------------------------------------
    
    # Linear pipeline flow
    start >> company_catalog_group >> ingestion_group >> embeddings_group >> extraction_group >> end
    
    # Note: Company catalog sync can be made conditional using BranchPythonOperator
    # if needed, but for simplicity we keep it linear. Users can skip it via params.
