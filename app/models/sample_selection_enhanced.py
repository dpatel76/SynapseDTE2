"""
Enhanced sample selection models with intelligent sampling strategies
Supports anomaly-based, boundary, and risk-based sampling
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
import uuid

from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin


class SamplingStrategy(str, Enum):
    """Sampling strategies for intelligent selection"""
    RANDOM = "random"  # Pure random sampling
    STRATIFIED = "stratified"  # Stratified by key attributes
    ANOMALY_BASED = "anomaly_based"  # Focus on anomalies
    BOUNDARY = "boundary"  # Edge cases and boundaries
    RISK_BASED = "risk_based"  # High-risk transactions
    SYSTEMATIC = "systematic"  # Every nth record
    CLUSTER = "cluster"  # Cluster-based sampling
    HYBRID = "hybrid"  # Combination of strategies


class SampleCategory(str, Enum):
    """Categories of samples for testing"""
    NORMAL = "normal"  # Clean, no anomalies
    ANOMALY = "anomaly"  # Failed profiling rules
    BOUNDARY_HIGH = "boundary_high"  # Highest values
    BOUNDARY_LOW = "boundary_low"  # Lowest values
    OUTLIER = "outlier"  # Statistical outliers
    EDGE_CASE = "edge_case"  # Business edge cases
    HIGH_RISK = "high_risk"  # High-risk indicators


class IntelligentSamplingJob(CustomPKModel, AuditMixin):
    """Orchestrates intelligent sample selection"""
    __tablename__ = 'intelligent_sampling_jobs'
    
    job_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    cycle_id = Column(Integer, ForeignKey('test_cycles.cycle_id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    profiling_job_id = Column(UUID, ForeignKey('profiling_jobs.job_id'), nullable=False)
    
    # Sampling configuration
    target_sample_size = Column(Integer, nullable=False)
    sampling_strategies = Column(ARRAY(String), nullable=False)  # Multiple strategies
    
    # Distribution targets (percentages)
    normal_percentage = Column(Integer, default=40)
    anomaly_percentage = Column(Integer, default=30)
    boundary_percentage = Column(Integer, default=20)
    edge_case_percentage = Column(Integer, default=10)
    
    # Source configuration
    source_type = Column(String(50), nullable=False)  # database, file
    source_criteria = Column(JSONB, nullable=False)  # Same as profiling criteria
    
    # Execution tracking
    status = Column(String(50), nullable=False)  # pending, running, completed, failed
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    
    # Results
    total_samples_selected = Column(Integer, default=0)
    selection_quality_score = Column(Float)  # 0.0 to 1.0
    
    # Relationships
    # profiling_job = relationship("ProfilingJob")  # Disabled due to missing foreign key constraint
    sample_pools = relationship("SamplePool", back_populates="sampling_job")
    selected_samples = relationship("IntelligentSample", back_populates="sampling_job")
    
    __table_args__ = (
        Index('idx_sampling_job_cycle', 'cycle_id', 'report_id'),
        Index('idx_sampling_job_profiling', 'profiling_job_id'),
    )


class SamplePool(CustomPKModel):
    """Pool of candidate samples by category"""
    __tablename__ = 'sample_pools'
    
    pool_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID, ForeignKey('intelligent_sampling_jobs.job_id'), nullable=False)
    
    # Pool identification
    category = Column(SQLEnum(SampleCategory), nullable=False)
    subcategory = Column(String(100))  # More specific classification
    
    # Pool statistics
    total_candidates = Column(Integer, nullable=False)
    selection_criteria = Column(JSONB)  # Criteria used to identify candidates
    
    # Quality metrics
    diversity_score = Column(Float)  # How diverse the pool is
    relevance_score = Column(Float)  # How relevant to testing objectives
    
    # Candidate records
    candidate_ids = Column(JSONB)  # Array of record identifiers
    candidate_metadata = Column(JSONB)  # Summary statistics of candidates
    
    # Relationships
    sampling_job = relationship("IntelligentSamplingJob", back_populates="sample_pools")
    
    __table_args__ = (
        Index('idx_sample_pool_job_category', 'job_id', 'category'),
    )


class IntelligentSample(CustomPKModel, AuditMixin):
    """Individual samples selected through intelligent sampling"""
    __tablename__ = 'intelligent_samples'
    
    sample_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID, ForeignKey('intelligent_sampling_jobs.job_id'), nullable=False)
    pool_id = Column(UUID, ForeignKey('sample_pools.pool_id'), nullable=False)
    
    # Sample identification
    record_identifier = Column(String(500), nullable=False)  # Primary key or composite
    record_data = Column(JSONB, nullable=False)  # Sample data (masked if sensitive)
    
    # Sample characteristics
    category = Column(SQLEnum(SampleCategory), nullable=False)
    selection_reason = Column(Text)  # Why this sample was selected
    
    # Anomaly information (if applicable)
    anomaly_types = Column(ARRAY(String))  # Types of anomalies detected
    anomaly_rules = Column(ARRAY(String))  # Rules that flagged anomalies
    anomaly_score = Column(Float)  # Severity of anomalies
    
    # Boundary information (if applicable)
    boundary_attributes = Column(JSONB)  # Which attributes are at boundaries
    boundary_values = Column(JSONB)  # The boundary values
    
    # Risk scoring
    risk_score = Column(Float)  # 0.0 to 1.0
    risk_factors = Column(JSONB)  # Factors contributing to risk
    
    # Selection metadata
    selection_strategy = Column(SQLEnum(SamplingStrategy), nullable=False)
    selection_rank = Column(Integer)  # Priority within category
    
    # Testing priority
    testing_priority = Column(Integer)  # 1-10, higher = test first
    must_test = Column(Boolean, default=False)  # Critical samples
    
    # Relationships
    sampling_job = relationship("IntelligentSamplingJob", back_populates="selected_samples")
    
    __table_args__ = (
        Index('idx_intelligent_sample_job', 'job_id', 'category'),
        Index('idx_intelligent_sample_priority', 'testing_priority', 'must_test'),
        Index('idx_intelligent_sample_identifier', 'record_identifier'),
    )


class SamplingRule(CustomPKModel, AuditMixin):
    """Rules for intelligent sample selection"""
    __tablename__ = 'sampling_rules'
    
    rule_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    
    # Rule definition
    rule_name = Column(String(255), nullable=False)
    rule_type = Column(String(50), nullable=False)  # anomaly, boundary, risk
    rule_definition = Column(JSONB, nullable=False)
    
    # Rule configuration
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=5)  # 1-10
    
    # Applicability
    applicable_attributes = Column(ARRAY(String))
    applicable_categories = Column(ARRAY(String))
    
    # Performance impact
    estimated_cost = Column(Integer)  # Relative computational cost
    
    __table_args__ = (
        Index('idx_sampling_rule_report', 'report_id', 'is_active'),
        Index('idx_sampling_rule_type', 'rule_type', 'priority'),
    )


class SampleLineage(CustomPKModel):
    """Tracks sample selection history and lineage"""
    __tablename__ = 'sample_lineage'
    
    lineage_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    sample_id = Column(UUID, ForeignKey('intelligent_samples.sample_id'), nullable=False)
    
    # Lineage tracking
    source_type = Column(String(50), nullable=False)  # profiling, manual, previous_cycle
    source_reference = Column(String(500))  # Reference to source
    
    # Selection context
    selection_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    selection_criteria = Column(JSONB)
    
    # Changes from source
    changes_from_source = Column(JSONB)  # What changed if resampled
    
    __table_args__ = (
        Index('idx_sample_lineage_sample', 'sample_id'),
        Index('idx_sample_lineage_source', 'source_type', 'source_reference'),
    )