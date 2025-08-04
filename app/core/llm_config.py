"""
LLM Configuration Management
Centralized configuration for LLM batch sizes and parameters
"""

from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    CLAUDE = "claude"
    GEMINI = "gemini"


class LLMOperation(str, Enum):
    """Types of LLM operations"""
    ATTRIBUTE_DISCOVERY = "attribute_discovery"
    ATTRIBUTE_DETAILS = "attribute_details"
    DATA_PROFILING = "data_profiling"
    SCOPING_RECOMMENDATIONS = "scoping_recommendations"
    SAMPLE_GENERATION = "sample_generation"
    TEST_CASE_GENERATION = "test_case_generation"
    OBSERVATION_ANALYSIS = "observation_analysis"
    GENERAL = "general"


class BatchSizeConfig(BaseModel):
    """Batch size configuration for a specific operation"""
    default: int = Field(..., description="Default batch size")
    min_size: int = Field(1, description="Minimum batch size")
    max_size: int = Field(..., description="Maximum batch size")
    optimal_for_speed: int = Field(..., description="Optimal size for speed")
    optimal_for_quality: int = Field(..., description="Optimal size for quality")


class ProviderConfig(BaseModel):
    """Configuration for a specific LLM provider"""
    name: str
    model: str
    max_tokens: int
    temperature: float
    batch_sizes: Dict[LLMOperation, BatchSizeConfig]
    rate_limit: int = Field(description="Requests per minute")
    retry_config: Dict[str, Any]


class LLMConfiguration:
    """Central LLM configuration management"""
    
    # Claude batch sizes by operation
    CLAUDE_BATCH_SIZES = {
        LLMOperation.ATTRIBUTE_DISCOVERY: BatchSizeConfig(
            default=15,
            min_size=5,
            max_size=30,
            optimal_for_speed=25,
            optimal_for_quality=10
        ),
        LLMOperation.ATTRIBUTE_DETAILS: BatchSizeConfig(
            default=25,
            min_size=10,
            max_size=50,
            optimal_for_speed=40,
            optimal_for_quality=20
        ),
        LLMOperation.DATA_PROFILING: BatchSizeConfig(
            default=20,
            min_size=5,
            max_size=40,
            optimal_for_speed=35,
            optimal_for_quality=15
        ),
        LLMOperation.SCOPING_RECOMMENDATIONS: BatchSizeConfig(
            default=20,
            min_size=10,
            max_size=40,
            optimal_for_speed=30,
            optimal_for_quality=15
        ),
        LLMOperation.SAMPLE_GENERATION: BatchSizeConfig(
            default=10,
            min_size=5,
            max_size=20,
            optimal_for_speed=15,
            optimal_for_quality=8
        ),
        LLMOperation.TEST_CASE_GENERATION: BatchSizeConfig(
            default=15,
            min_size=5,
            max_size=30,
            optimal_for_speed=25,
            optimal_for_quality=12
        ),
        LLMOperation.OBSERVATION_ANALYSIS: BatchSizeConfig(
            default=30,
            min_size=10,
            max_size=60,
            optimal_for_speed=50,
            optimal_for_quality=25
        ),
        LLMOperation.GENERAL: BatchSizeConfig(
            default=20,
            min_size=5,
            max_size=50,
            optimal_for_speed=40,
            optimal_for_quality=15
        )
    }
    
    # Gemini batch sizes by operation
    GEMINI_BATCH_SIZES = {
        LLMOperation.ATTRIBUTE_DISCOVERY: BatchSizeConfig(
            default=50,
            min_size=20,
            max_size=100,
            optimal_for_speed=80,
            optimal_for_quality=40
        ),
        LLMOperation.ATTRIBUTE_DETAILS: BatchSizeConfig(
            default=100,
            min_size=50,
            max_size=200,
            optimal_for_speed=150,
            optimal_for_quality=75
        ),
        LLMOperation.DATA_PROFILING: BatchSizeConfig(
            default=75,
            min_size=30,
            max_size=150,
            optimal_for_speed=120,
            optimal_for_quality=60
        ),
        LLMOperation.SCOPING_RECOMMENDATIONS: BatchSizeConfig(
            default=75,
            min_size=30,
            max_size=150,
            optimal_for_speed=120,
            optimal_for_quality=60
        ),
        LLMOperation.SAMPLE_GENERATION: BatchSizeConfig(
            default=40,
            min_size=20,
            max_size=80,
            optimal_for_speed=60,
            optimal_for_quality=30
        ),
        LLMOperation.TEST_CASE_GENERATION: BatchSizeConfig(
            default=60,
            min_size=30,
            max_size=120,
            optimal_for_speed=100,
            optimal_for_quality=50
        ),
        LLMOperation.OBSERVATION_ANALYSIS: BatchSizeConfig(
            default=100,
            min_size=50,
            max_size=200,
            optimal_for_speed=150,
            optimal_for_quality=80
        ),
        LLMOperation.GENERAL: BatchSizeConfig(
            default=75,
            min_size=25,
            max_size=150,
            optimal_for_speed=120,
            optimal_for_quality=60
        )
    }
    
    @classmethod
    def get_batch_size(
        cls,
        provider: LLMProvider,
        operation: LLMOperation,
        optimization: str = "default"
    ) -> int:
        """
        Get batch size for a specific provider and operation.
        
        Args:
            provider: LLM provider
            operation: Type of operation
            optimization: "default", "speed", or "quality"
            
        Returns:
            Batch size
        """
        batch_configs = (
            cls.CLAUDE_BATCH_SIZES if provider == LLMProvider.CLAUDE 
            else cls.GEMINI_BATCH_SIZES
        )
        
        config = batch_configs.get(operation, batch_configs[LLMOperation.GENERAL])
        
        if optimization == "speed":
            return config.optimal_for_speed
        elif optimization == "quality":
            return config.optimal_for_quality
        else:
            return config.default
    
    @classmethod
    def get_provider_config(cls, provider: LLMProvider, settings) -> ProviderConfig:
        """Get complete configuration for a provider"""
        if provider == LLMProvider.CLAUDE:
            return ProviderConfig(
                name="claude",
                model=settings.claude_model,
                max_tokens=settings.claude_max_tokens,
                temperature=settings.claude_comprehensive_temperature,
                batch_sizes=cls.CLAUDE_BATCH_SIZES,
                rate_limit=100,  # Requests per minute
                retry_config={
                    "max_retries": settings.llm_max_retries,
                    "retry_delay": settings.llm_retry_delay,
                    "backoff_factor": 2.0
                }
            )
        else:  # Gemini
            return ProviderConfig(
                name="gemini",
                model=settings.gemini_model,
                max_tokens=settings.gemini_max_tokens,
                temperature=settings.llm_temperature,
                batch_sizes=cls.GEMINI_BATCH_SIZES,
                rate_limit=200,  # Requests per minute
                retry_config={
                    "max_retries": settings.llm_max_retries,
                    "retry_delay": settings.llm_retry_delay,
                    "backoff_factor": 1.5
                }
            )
    
    @classmethod
    def get_dynamic_batch_size(
        cls,
        provider: LLMProvider,
        operation: LLMOperation,
        input_size: int,
        complexity: str = "medium"
    ) -> int:
        """
        Calculate dynamic batch size based on input characteristics.
        
        Args:
            provider: LLM provider
            operation: Type of operation
            input_size: Size of input data
            complexity: "low", "medium", or "high"
            
        Returns:
            Adjusted batch size
        """
        base_config = (
            cls.CLAUDE_BATCH_SIZES if provider == LLMProvider.CLAUDE 
            else cls.GEMINI_BATCH_SIZES
        )[operation]
        
        # Start with default
        batch_size = base_config.default
        
        # Adjust based on input size
        if input_size > 1000:
            batch_size = int(batch_size * 0.8)
        elif input_size < 100:
            batch_size = int(batch_size * 1.2)
        
        # Adjust based on complexity
        complexity_factors = {
            "low": 1.2,
            "medium": 1.0,
            "high": 0.7
        }
        batch_size = int(batch_size * complexity_factors.get(complexity, 1.0))
        
        # Ensure within bounds
        batch_size = max(base_config.min_size, min(batch_size, base_config.max_size))
        
        return batch_size


class RegulationPromptMapping:
    """Mapping of regulations to prompt directories"""
    
    REGULATION_MAPPING = {
        "FR Y-14M": {
            "normalized_name": "fr_y_14m",
            "schedules": {
                "Schedule A.1": "schedule_a_1",
                "Schedule A.2": "schedule_a_2",
                "Schedule B.1": "schedule_b_1",
                "Schedule B.2": "schedule_b_2",
                "Schedule C.1": "schedule_c_1",
                "Schedule D.1": "schedule_d_1",
                "Schedule D.2": "schedule_d_2"
            },
            "default_prompts": "common",
            "special_handling": {
                "Schedule D.1": {
                    "use_enhanced_extraction": True,
                    "preferred_provider": "gemini"
                }
            }
        },
        "FR Y-14Q": {
            "normalized_name": "fr_y_14q",
            "schedules": {
                "Schedule A": "schedule_a",
                "Schedule B": "schedule_b",
                "Schedule C": "schedule_c"
            },
            "default_prompts": "common"
        },
        "CCAR": {
            "normalized_name": "ccar",
            "schedules": {
                "Schedule 1A": "schedule_1a",
                "Schedule 1B": "schedule_1b",
                "Schedule 2A": "schedule_2a"
            },
            "default_prompts": "common"
        },
        "Basel III": {
            "normalized_name": "basel_iii",
            "schedules": {},
            "default_prompts": "basel_common"
        },
        "FR Y-9C": {
            "normalized_name": "fr_y_9c",
            "schedules": {},
            "default_prompts": "common"
        }
    }
    
    @classmethod
    def get_prompt_path(
        cls,
        regulation: str,
        schedule: Optional[str] = None,
        prompt_type: str = "attribute_discovery"
    ) -> str:
        """
        Get the prompt file path for a regulation and schedule.
        
        Args:
            regulation: Regulation name (e.g., "FR Y-14M")
            schedule: Schedule name (e.g., "Schedule D.1")
            prompt_type: Type of prompt needed
            
        Returns:
            Path to prompt file
        """
        reg_config = cls.REGULATION_MAPPING.get(regulation)
        if not reg_config:
            # Fallback to generic prompts
            return f"prompts/generic/{prompt_type}.txt"
        
        base_path = f"prompts/regulatory/{reg_config['normalized_name']}"
        
        if schedule and schedule in reg_config["schedules"]:
            schedule_dir = reg_config["schedules"][schedule]
            return f"{base_path}/{schedule_dir}/{prompt_type}.txt"
        else:
            # Use regulation common prompts
            return f"{base_path}/{reg_config['default_prompts']}/{prompt_type}.txt"
    
    @classmethod
    def get_special_handling(
        cls,
        regulation: str,
        schedule: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get special handling instructions for a regulation/schedule"""
        reg_config = cls.REGULATION_MAPPING.get(regulation, {})
        special = reg_config.get("special_handling", {})
        
        if schedule:
            return special.get(schedule)
        
        return None
    
    @classmethod
    def normalize_regulation_name(cls, regulation: str) -> str:
        """Normalize regulation name for file paths"""
        # Remove special characters and convert to lowercase
        return regulation.lower().replace(" ", "_").replace("-", "_").replace(".", "")
    
    @classmethod
    def normalize_schedule_name(cls, schedule: str) -> str:
        """Normalize schedule name for file paths"""
        # Remove "Schedule" prefix and normalize
        schedule = schedule.replace("Schedule", "").strip()
        return schedule.lower().replace(" ", "_").replace(".", "_")


# Singleton instance
_llm_config = LLMConfiguration()


def get_llm_config() -> LLMConfiguration:
    """Get LLM configuration instance"""
    return _llm_config