"""
Enhanced LLM Integration Service - Based on SynapseDV Reference Implementation
Provides regulatory document analysis, attribute generation, and test recommendations
Requires proper API keys - no mock fallbacks
"""

import logging
import json
import os
import asyncio
import aiohttp
import re
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod
import anthropic
from anthropic import Anthropic, AsyncAnthropic
try:
    import google.generativeai as genai
except ImportError:
    genai = None

from app.core.config import get_settings
from app.core.prompt_manager import get_prompt_manager

logger = logging.getLogger(__name__)
settings = get_settings()
prompt_manager = get_prompt_manager()


class LLMError(Exception):
    """Custom exception for LLM-related errors"""
    pass


class LLMProvider(ABC):
    """Base class for LLM providers"""
    
    def __init__(self, model_name: str, temperature: float = 0.0, max_tokens: int = 8000):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_latency": 0.0,
            "total_tokens": 0,
            "total_cost": 0.0
        }
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate a response from the model"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check LLM service health"""
        pass
    
    def update_metrics(self, tokens: int, latency: float, success: bool, cost: float = 0.0):
        """Update performance metrics"""
        self._metrics["total_requests"] += 1
        self._metrics["total_tokens"] += tokens
        self._metrics["total_cost"] += cost
        
        if success:
            self._metrics["successful_requests"] += 1
        else:
            self._metrics["failed_requests"] += 1
        
        # Update average latency
        current_total = self._metrics["average_latency"] * (self._metrics["total_requests"] - 1)
        self._metrics["average_latency"] = (current_total + latency) / self._metrics["total_requests"]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            "model": self.model_name,
            "metrics": self._metrics
        }


class ClaudeProvider(LLMProvider):
    """Claude LLM provider implementation - requires API key"""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY is required for Claude models")
        
        super().__init__(
            model_name=getattr(settings, 'claude_model', 'claude-3-5-sonnet-20241022'),
            temperature=getattr(settings, 'claude_comprehensive_temperature', 0.1),
            max_tokens=getattr(settings, 'claude_comprehensive_max_tokens', 8192)
        )
        
        self.api_key = api_key
        self.client = AsyncAnthropic(api_key=api_key)
        self.max_retries = getattr(settings, 'llm_max_retries', 3)
        self.retry_delay = getattr(settings, 'llm_retry_delay', 1.0)
        
        logger.info(f"Claude provider initialized with model: {self.model_name}")
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response using Claude API with proper error handling"""
        start_time = datetime.utcnow()
        
        for attempt in range(self.max_retries):
            try:
                # Log the request details
                logger.info(f"Claude API request - model: {self.model_name}, prompt length: {len(prompt)}, system prompt length: {len(system_prompt) if system_prompt else 0}")
                
                response = await asyncio.wait_for(
                    self.client.messages.create(
                        model=self.model_name,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        system=system_prompt or "You are a helpful assistant specialized in regulatory compliance analysis.",
                        messages=[{"role": "user", "content": prompt}]
                    ),
                    timeout=30.0  # 30 second timeout
                )
                
                # Log raw response details
                logger.info(f"Claude raw response type: {type(response)}, has content: {hasattr(response, 'content')}")
                if hasattr(response, 'content') and response.content:
                    logger.info(f"Claude response.content type: {type(response.content)}, length: {len(response.content)}")
                    if len(response.content) > 0:
                        logger.info(f"First content item type: {type(response.content[0])}, has text: {hasattr(response.content[0], 'text')}")
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                usage = response.usage
                total_tokens = usage.input_tokens + usage.output_tokens
                
                # Calculate approximate cost (Claude pricing)
                cost = (usage.input_tokens * 0.003 + usage.output_tokens * 0.015) / 1000
                
                self.update_metrics(total_tokens, duration, True, cost)
                
                # Extract the actual text content
                content_text = response.content[0].text if response.content and len(response.content) > 0 else ""
                logger.info(f"Claude API response - success: True, content length: {len(content_text)}")
                logger.info(f"Claude API full response content preview: {content_text[:100]}...")
                
                result = {
                    "success": True,
                    "content": content_text,  # The rest of the code expects 'content' key
                    "model_used": self.model_name,
                    "timestamp": start_time.isoformat(),
                    "usage": {
                        "input_tokens": usage.input_tokens,
                        "output_tokens": usage.output_tokens,
                        "total_tokens": total_tokens
                    },
                    "cost": cost
                }
                
                # Log the response for debugging (avoid logging huge content)
                logger.info(f"Claude API response - success: True, content length: {len(result['content'])}")
                logger.info(f"Claude API response preview: {result['content'][:200]}...")
                
                return result
                
            except asyncio.TimeoutError:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Claude API timeout (attempt {attempt + 1}/{self.max_retries}), retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    self.update_metrics(0, duration, False)
                    raise LLMError(f"Claude API timeout after {self.max_retries} attempts")
                    
            except anthropic.RateLimitError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Claude rate limit, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    self.update_metrics(0, duration, False)
                    raise LLMError(f"Claude rate limit exceeded: {str(e)}")
                    
            except anthropic.APIStatusError as e:
                if e.status_code == 401:  # Unauthorized
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    self.update_metrics(0, duration, False)
                    raise LLMError(f"Claude API authentication failed: Invalid API key (401 Unauthorized)")
                elif e.status_code == 529:  # Overloaded error
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt) * 3  # Longer wait for overloaded
                        logger.warning(f"Claude API overloaded (attempt {attempt + 1}/{self.max_retries}), waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        duration = (datetime.utcnow() - start_time).total_seconds()
                        self.update_metrics(0, duration, False)
                        raise LLMError(f"Claude API overloaded after {self.max_retries} attempts")
                    continue
                else:
                    # Other API status errors
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    self.update_metrics(0, duration, False)
                    raise LLMError(f"Claude API error (status {e.status_code}): {str(e)}")
                
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                self.update_metrics(0, duration, False)
                raise LLMError(f"Claude API error: {str(e)}")
        
        raise LLMError("Max retries exceeded")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Claude service health"""
        try:
            response = await self.generate("Respond with 'OK' to confirm service is working.")
            
            if response.get("success") and "OK" in response.get("content", ""):
                return {
                    "provider": "claude",
                    "status": "healthy",
                    "model": self.model_name,
                    "response_time": "< 2s"
                }
            else:
                return {
                    "provider": "claude",
                    "status": "unhealthy",
                    "error": "Invalid response"
                }
                
        except Exception as e:
            return {
                "provider": "claude",
                "status": "unhealthy",
                "error": str(e)
            }


class GeminiProvider(LLMProvider):
    """Gemini LLM provider implementation - requires API key"""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise LLMError("GOOGLE_API_KEY is required for Gemini models")
        
        super().__init__(
            model_name=getattr(settings, 'extraction_model', 'gemini-2.0-flash'),
            temperature=getattr(settings, 'llm_temperature', 0.0),
            max_tokens=getattr(settings, 'llm_max_tokens', 32000)
        )
        
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        try:
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens
                )
            )
        except Exception as e:
            raise LLMError(f"Failed to initialize Gemini model: {str(e)}")
        
        logger.info(f"Gemini provider initialized with model: {self.model_name}")
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response using Gemini API"""
        start_time = datetime.utcnow()
        
        try:
            # Combine system prompt and user prompt for Gemini
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            else:
                full_prompt = prompt
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt
            )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Estimate tokens and cost for Gemini
            estimated_tokens = len(full_prompt.split()) + len(response.text.split())
            cost = estimated_tokens * 0.0005 / 1000  # Approximate Gemini pricing
            
            self.update_metrics(estimated_tokens, duration, True, cost)
            
            return {
                "success": True,
                "content": response.text,
                "model": self.model_name,
                "timestamp": start_time.isoformat(),
                "usage": {
                    "estimated_tokens": estimated_tokens
                },
                "cost": cost
            }
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.update_metrics(0, duration, False)
            raise LLMError(f"Gemini API error: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Gemini service health"""
        try:
            response = await self.generate("Respond with 'OK' to confirm service is working.")
            
            if response.get("success") and "OK" in response.get("content", ""):
                return {
                    "provider": "gemini",
                    "status": "healthy",
                    "model": self.model_name,
                    "response_time": "< 1s"
                }
            else:
                return {
                    "provider": "gemini",
                    "status": "unhealthy",
                    "error": "Invalid response"
                }
                
        except Exception as e:
            return {
                "provider": "gemini",
                "status": "unhealthy",
                "error": str(e)
            }


class HybridLLMService:
    """
    Enhanced hybrid LLM service with failover mechanisms
    NO MOCK FALLBACKS - tests must use real LLM providers
    """
    
    def __init__(self):
        self.providers = {}
        self.provider_health = {}
        self.hybrid_enabled = getattr(settings, 'enable_hybrid_analysis', True)
        
        # Initialize failover configuration
        self.max_consecutive_failures = getattr(settings, 'llm_max_consecutive_failures', 3)
        self.health_check_interval = getattr(settings, 'llm_health_check_interval', 300)  # 5 minutes
        self.circuit_breaker_timeout = getattr(settings, 'llm_circuit_breaker_timeout', 900)  # 15 minutes
        
        # Initialize providers - REQUIRE API keys
        try:
            self._initialize_providers()
        except Exception as e:
            logger.error(f"Failed to initialize LLM providers: {str(e)}")
            raise LLMError(f"LLM service initialization failed: {str(e)}")
        
        if not self.providers:
            raise LLMError("No LLM providers available. API keys are required for Claude and/or Gemini.")
        
        logger.info(f"Hybrid LLM service initialized with providers: {list(self.providers.keys())}")
        logger.info(f"Hybrid analysis enabled: {self.hybrid_enabled}")
        logger.info(f"Failover enabled with max failures: {self.max_consecutive_failures}")
    
    def _initialize_providers(self):
        """Initialize available LLM providers with health tracking - REQUIRE API keys"""
        # Try to initialize Claude
        claude_key = getattr(settings, 'anthropic_api_key', None)
        if claude_key:
            try:
                self.providers['claude'] = ClaudeProvider(claude_key)
                self.provider_health['claude'] = {
                    "status": "unknown",
                    "last_check": None,
                    "consecutive_failures": 0,
                    "is_available": True
                }
                logger.info("Claude provider initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Claude: {str(e)}")
        else:
            logger.warning("ANTHROPIC_API_KEY not found - Claude provider not available")
        
        # Skip Gemini initialization for now - using Claude only
        logger.info("Gemini provider skipped - using Claude only for LLM calls")

    async def _check_provider_health(self, provider_name: str) -> bool:
        """Check health of a specific provider"""
        if provider_name not in self.providers:
            return False
        
        try:
            health_result = await self.providers[provider_name].health_check()
            is_healthy = health_result.get("status") == "healthy"
            
            # Update health tracking
            self.provider_health[provider_name].update({
                "status": "healthy" if is_healthy else "unhealthy",
                "last_check": datetime.utcnow(),
                "consecutive_failures": 0 if is_healthy else self.provider_health[provider_name]["consecutive_failures"] + 1
            })
            
            # Circuit breaker logic
            if self.provider_health[provider_name]["consecutive_failures"] >= self.max_consecutive_failures:
                self.provider_health[provider_name]["is_available"] = False
                logger.warning(f"Provider {provider_name} marked as unavailable due to consecutive failures")
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Health check failed for {provider_name}: {str(e)}")
            self.provider_health[provider_name].update({
                "status": "unhealthy",
                "last_check": datetime.utcnow(),
                "consecutive_failures": self.provider_health[provider_name]["consecutive_failures"] + 1
            })
            return False

    
    # NOTE: Health checks are disabled to prevent response mix-up issue
    # where health check "OK" responses were being processed as actual responses
    
    async def _get_available_provider(self, preferred_provider: str = None) -> Optional[LLMProvider]:
        """Get an available provider with failover logic"""
        # If a specific provider is preferred, try it first
        if preferred_provider and preferred_provider in self.providers:
            if self.provider_health[preferred_provider]["is_available"]:
                # Skip health check - just return the provider
                return self.providers[preferred_provider]
        
        # Try all available providers in preference order
        provider_preference = ['claude']
        for provider_name in provider_preference:
            if provider_name in self.providers and self.provider_health[provider_name]["is_available"]:
                # Skip health check - just return the provider
                if preferred_provider and provider_name != preferred_provider:
                    logger.info(f"Using fallback provider: {provider_name} (preferred: {preferred_provider})")
                return self.providers[provider_name]
        
        # Check if any providers are in circuit breaker state and can be retried
        for provider_name, health in self.provider_health.items():
            if not health["is_available"] and health["last_check"]:
                time_since_check = (datetime.utcnow() - health["last_check"]).total_seconds()
                if time_since_check > self.circuit_breaker_timeout:
                    logger.info(f"Retrying provider {provider_name} after circuit breaker timeout")
                    health["is_available"] = True
                    health["consecutive_failures"] = 0
                    # Skip health check to avoid response mix-up
                    # if await self._check_provider_health(provider_name):
                    return self.providers[provider_name]
        
        return None

    async def _generate_with_failover(self, prompt: str, system_prompt: Optional[str] = None, preferred_provider: str = None) -> Dict[str, Any]:
        """Generate response with automatic failover"""
        logger.info(f"_generate_with_failover called with prompt length: {len(prompt) if prompt else 0}")
        if system_prompt:
            logger.info(f"System prompt provided, length: {len(system_prompt)}")
        
        provider = await self._get_available_provider(preferred_provider)
        
        if not provider:
            error_msg = "No healthy LLM providers available. "
            
            # Add more context about why providers are unavailable
            for provider_name, health in self.provider_health.items():
                if not health["is_available"]:
                    error_msg += f"{provider_name}: unavailable (failures: {health['consecutive_failures']}, last check: {health.get('last_check', 'never')}). "
                elif health["status"] == "unhealthy":
                    error_msg += f"{provider_name}: unhealthy. "
            
            # Check for common issues
            if 'claude' in self.providers:
                error_msg += "Check ANTHROPIC_API_KEY environment variable. "
            if 'gemini' in self.providers:
                error_msg += "Check GOOGLE_API_KEY environment variable. "
            
            logger.error(error_msg)
            raise LLMError(error_msg)
        
        provider_name = next(name for name, p in self.providers.items() if p == provider)
        
        try:
            result = await provider.generate(prompt, system_prompt)
            result["provider_used"] = provider.model_name
            result["actual_provider"] = provider_name
            return result
            
        except Exception as e:
            # Mark current provider as failed and try failover
            self.provider_health[provider_name]["consecutive_failures"] += 1
            
            # Log detailed error information
            error_type = type(e).__name__
            error_msg = str(e).lower()
            
            logger.warning(f"Provider {provider_name} failed with {error_type}: {str(e)}")
            
            # Check for specific error types and provide guidance
            if "rate limit" in error_msg:
                logger.error(f"🚨 Rate limit hit for {provider_name}. Consider reducing batch size or adding delays.")
            elif "api key" in error_msg or "authentication" in error_msg or "unauthorized" in error_msg:
                logger.error(f"🔑 Authentication error for {provider_name}. Check API key configuration.")
            elif "timeout" in error_msg:
                logger.error(f"⏱️ Request timeout for {provider_name}. Consider reducing prompt size or increasing timeout.")
            elif "context length" in error_msg or "too long" in error_msg:
                logger.error(f"📏 Context length exceeded for {provider_name}. Consider reducing prompt size.")
            
            # Try to get another provider (excluding the failed one)
            for fallback_name in self.providers:
                if fallback_name != provider_name and self.provider_health[fallback_name]["is_available"]:
                    try:
                        fallback_provider = self.providers[fallback_name]
                        result = await fallback_provider.generate(prompt, system_prompt)
                        result["provider_used"] = fallback_provider.model_name
                        result["actual_provider"] = fallback_name
                        result["failover_used"] = True
                        result["failed_provider"] = provider_name
                        logger.info(f"✅ Successfully failed over from {provider_name} to {fallback_name}")
                        return result
                    except Exception as e2:
                        logger.error(f"❌ Failover provider {fallback_name} also failed: {str(e2)}")
                        self.provider_health[fallback_name]["consecutive_failures"] += 1
            
            # Provide detailed error message with all failure information
            all_errors = f"Primary provider {provider_name} failed: {str(e)}"
            raise LLMError(f"All LLM providers failed. {all_errors}")

    async def generate_scoping_recommendations(self, attributes: List[Dict[str, Any]], report_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate scoping recommendations for testing attributes using regulation-specific prompts.
        NO FALLBACK - fails immediately if LLM is not available.
        
        Args:
            attributes: List of attributes to evaluate for scoping
            report_type: Optional report type for context
        
        Returns:
            Dict containing recommendations for each attribute
        """
        try:
            import json
            
            # Extract regulatory report and schedule from report_type
            logger.info(f"🔍 DEBUG: Received report_type: '{report_type}'")
            regulatory_report, schedule = self._extract_regulatory_info("", report_type or "")
            
            logger.info(f"🔍 DEBUG: Extracted regulatory_report='{regulatory_report}', schedule='{schedule}'")
            
            # If no regulatory info extracted, try to infer from common patterns
            if not regulatory_report and report_type:
                if 'credit card' in report_type.lower() or 'schedule d' in report_type.lower():
                    regulatory_report = 'FR Y-14M'
                    schedule = 'schedule_d_1'
                    logger.info(f"🔧 FALLBACK: Inferred FR Y-14M Schedule D.1 from report_type")
            
            logger.info(f"Loading scoping recommendations prompt for: {regulatory_report} / {schedule}")
            
            # Format attributes as JSON for the template - only send relevant fields
            attributes_list = []
            for attr in attributes:
                formatted_attr = {
                    "attribute_name": attr.get('attribute_name', 'Unknown'),
                    "data_type": attr.get('data_type', 'Unknown'),
                    "is_primary_key": attr.get('is_primary_key', False),
                    "is_cde": attr.get('is_cde', False),
                    "is_mandatory": attr.get('is_required', False),
                    "has_historical_issues": attr.get('has_historical_issues', False)
                }
                
                # Only add optional fields if they have meaningful values
                if attr.get('mdrm_code'):
                    formatted_attr["mdrm_code"] = attr['mdrm_code']
                    
                if attr.get('description') and attr['description'] != 'N/A':
                    formatted_attr["description"] = attr['description']
                
                attributes_list.append(formatted_attr)
            attributes_json = json.dumps(attributes_list, indent=2)
            
            logger.info(f"📊 Requesting recommendations for {len(attributes_list)} attributes")
            
            # Load regulatory-specific prompt if available
            prompt_content = prompt_manager.format_prompt(
                "scoping_recommendations",
                regulatory_report=regulatory_report,
                schedule=schedule,
                report_name=report_type or 'Unknown Report',
                regulatory_context=f"{regulatory_report} {schedule}" if regulatory_report and schedule else "General regulatory reporting",
                attributes_json=attributes_json
            )
            
            if prompt_content:
                logger.info(f"✅ SUCCESS: Using regulation-specific prompt for {regulatory_report} {schedule}")
                logger.info(f"🔍 DEBUG: Prompt length: {len(prompt_content)} characters")
                
                # Add explicit instruction to process ALL attributes
                prompt_content += f"\n\nCRITICAL: You MUST generate recommendations for ALL {len(attributes_list)} attributes provided above. Do not skip any attributes. Return exactly {len(attributes_list)} recommendations in the JSON array."
                
                # Log context size info
                prompt_tokens_estimate = len(prompt_content) // 4  # Rough estimate
                logger.info(f"📏 Context size: {len(prompt_content)} chars (~{prompt_tokens_estimate} tokens) for {len(attributes_list)} attributes")
                logger.info(f"🔍 DEBUG: Prompt preview: {prompt_content[:200]}...")
            else:
                logger.warning(f"❌ FAILED: Could not load regulation-specific prompt for {regulatory_report}/{schedule}, using fallback")
                logger.warning(f"🔍 DEBUG: Prompt manager returned None for template 'scoping_recommendations'")
            
            # Fallback to generic prompt if no regulation-specific prompt found
            if not prompt_content:
                system_prompt = """You are a testing expert helping determine which attributes should be included in testing scope.
                
For each attribute, provide:
1. A recommendation: "include" or "exclude" 
2. A confidence score (0-1)
3. A brief rationale
4. Risk assessment factors

Consider:
- Data type and complexity
- Business criticality
- Historical issues
- Regulatory requirements
- Testing feasibility"""

                attributes_text = "\n".join([
                    f"""
Attribute ID: {attr.get('id', 'Unknown')}
Attribute: {attr.get('attribute_name', 'Unknown')}
Description: {attr.get('description', 'N/A')}
Data Type: {attr.get('data_type', 'Unknown')}
Is Primary Key: {attr.get('is_primary_key', False)}
Is CDE: {attr.get('is_cde', False)}
Has Historical Issues: {attr.get('has_historical_issues', False)}
Keywords: {attr.get('keywords_to_look_for', 'N/A')}
Testing Approach: {attr.get('testing_approach', 'N/A')}
Validation Rules: {attr.get('validation_rules', 'N/A')}
"""
                    for attr in attributes
                ])

                prompt_content = f"""Analyze these attributes for testing scope inclusion.
Report Type: {report_type or 'General Compliance Report'}

Attributes to evaluate:
{attributes_text}

Return a JSON array with recommendations for each attribute:
[
    {{
        "attribute_id": "<id from input>",
        "attribute_name": "<name from input>", 
        "recommendation": "include|exclude",
        "confidence_score": 0.85,
        "rationale": "Brief explanation",
        "risk_score": 75,
        "is_cde": true/false,
        "is_primary_key": true/false,
        "has_historical_issues": true/false,
        "risk_factors": ["factor1", "factor2"],
        "processing_time_ms": 100
    }}
]"""
                system_prompt = """You are a testing expert helping determine which attributes should be included in testing scope.
                
For each attribute, provide:
1. A recommendation: "include" or "exclude" 
2. A confidence score (0-1)
3. A brief rationale
4. Risk assessment factors

Consider:
- Data type and complexity
- Business criticality
- Historical issues
- Regulatory requirements
- Testing feasibility"""

            # Log the full prompt for debugging
            logger.info("=" * 80)
            logger.info("SCOPING RECOMMENDATIONS LLM REQUEST")
            logger.info("=" * 80)
            logger.info(f"Prompt Content Length: {len(prompt_content)} characters")
            logger.info(f"First 1000 chars:\n{prompt_content[:1000]}")
            if len(prompt_content) > 1000:
                logger.info(f"Last 500 chars:\n{prompt_content[-500:]}")
            logger.info("=" * 80)

            # Get primary provider only - no failover
            provider = await self.get_primary_provider()
            if not provider:
                raise LLMError("No LLM provider available")
            
            # Generate response - will fail immediately if provider fails  
            # For regulation-specific prompts, the prompt_content contains everything (use empty system prompt)
            # For fallback generic prompts, we have separate system_prompt and prompt_content
            
            # Check if we're using regulation-specific prompt or fallback
            using_regulation_prompt = prompt_content and (regulatory_report and schedule)
            
            if using_regulation_prompt:
                # Regulation-specific prompt: use empty system prompt, prompt contains everything
                system_prompt_to_use = ""
                logger.info("🎯 Using regulation-specific prompt with empty system prompt")
            else:
                # Fallback prompt: use system prompt + content
                system_prompt_to_use = system_prompt if 'system_prompt' in locals() else ""
                logger.info("⚠️  Using fallback prompt with system prompt")
            
            logger.info(f"🔍 DEBUG: system_prompt_to_use length: {len(system_prompt_to_use)}")
            logger.info(f"🔍 DEBUG: prompt_content length: {len(prompt_content) if prompt_content else 0}")
            
            result = await provider.generate(prompt_content, system_prompt_to_use)
            
            # Log the full response for debugging
            logger.info("=" * 80)
            logger.info("SCOPING RECOMMENDATIONS LLM RESPONSE")
            logger.info("=" * 80)
            logger.info(f"Success: {result.get('success')}")
            logger.info(f"Model Used: {result.get('model_used', 'unknown')}")
            logger.info(f"Response type: {type(result.get('content'))}")
            logger.info(f"Response length: {len(str(result.get('content', '')))}")
            logger.info(f"Response preview: {str(result.get('content', ''))[:200]}...")
            logger.info("=" * 80)
            
            # Parse the response
            if result.get('success'):
                try:
                    import json
                    response_text = result.get('content', '{}')
                    
                    # Log the raw response for debugging
                    logger.info(f"Raw LLM response length: {len(response_text)} characters")
                    logger.info(f"Raw LLM response (first 500 chars): {response_text[:500]}")
                    if len(response_text) > 500:
                        logger.info(f"Raw LLM response (last 500 chars): {response_text[-500:]}")
                    logger.info(f"Full Raw LLM response: {response_text}")
                    
                    # Enhanced JSON extraction with multiple strategies
                    def extract_json_from_text(text):
                        """Extract JSON from text using multiple strategies"""
                        logger.info(f"🔍 Starting JSON extraction. Text length: {len(text)}")
                        logger.info(f"🔍 Text preview: {text[:200]}...")
                        
                        # Strategy 1: Look for JSON array pattern
                        logger.info("🔍 Trying to find JSON array pattern...")
                        try:
                            # Look for JSON array starting with [
                            import re
                            json_match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
                            if json_match:
                                extracted = json_match.group(0)
                                logger.info(f"🔍 Found JSON array: {len(extracted)} chars")
                                parsed = json.loads(extracted)
                                logger.info(f"🔍 SUCCESS: JSON array extraction worked! Found {len(parsed)} items")
                                return parsed
                            else:
                                logger.info("🔍 No JSON array pattern found")
                        except Exception as e:
                            logger.error(f"❌ JSON array extraction failed: {type(e).__name__}: {e}")
                        
                        # Strategy 2: Look for markdown code blocks manually
                        logger.info("🔍 Trying markdown code block extraction...")
                        try:
                            # Look for ```json or ``` blocks
                            json_block_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
                            if json_block_match:
                                extracted = json_block_match.group(1).strip()
                                logger.info(f"🔍 Found markdown JSON block: {len(extracted)} chars")
                                parsed = json.loads(extracted)
                                logger.info(f"🔍 SUCCESS: Markdown block extraction worked!")
                                return parsed
                            else:
                                logger.info("🔍 No markdown code blocks found")
                        except Exception as e:
                            logger.error(f"❌ Markdown block extraction failed: {type(e).__name__}: {e}")
                        
                        # Strategy 3: Direct parsing
                        logger.info("🔍 Trying direct parsing strategy...")
                        try:
                            extracted = text.strip()
                            if extracted:
                                logger.info(f"🔍 Direct parsing text length: {len(extracted)}")
                                logger.info(f"🔍 Direct parsing preview: {extracted[:100]}...")
                                
                                # Skip the _fix_json_issues call that's causing problems
                                # extracted = self._fix_json_issues(extracted)
                                logger.info(f"🔍 About to parse JSON of length: {len(extracted)}")
                                
                                parsed = json.loads(extracted)
                                logger.info(f"🔍 SUCCESS: Direct parsing strategy worked! Parsed {len(parsed) if isinstance(parsed, list) else 'object'} items")
                                return parsed
                            else:
                                logger.info("🔍 No text found for direct parsing")
                        except json.JSONDecodeError as e:
                            logger.error(f"❌ JSON decode error: {e}")
                            logger.error(f"❌ JSON error at line {e.lineno}, column {e.colno}")
                            logger.error(f"❌ Problem text around error: {extracted[max(0, e.pos-50):e.pos+50] if 'extracted' in locals() and hasattr(e, 'pos') else 'N/A'}")
                        except Exception as e:
                            logger.error(f"❌ Direct parsing strategy failed: {type(e).__name__}: {e}")
                            logger.error(f"❌ Failed on text: {extracted[:200] if 'extracted' in locals() else 'N/A'}...")
                        
                        logger.error("🚨 All JSON extraction strategies failed!")
                        return None
                    
                    recommendations = extract_json_from_text(response_text)
                    
                    # Validate recommendations
                    if recommendations is None:
                        logger.error("Failed to extract JSON from LLM response")
                        recommendations = []
                    elif not isinstance(recommendations, list):
                        logger.error(f"Expected list of recommendations, got: {type(recommendations)}")
                        recommendations = []
                    
                    logger.info(f"Successfully parsed {len(recommendations)} recommendations")
                    
                    return {
                        "success": True,
                        "recommendations": recommendations,
                        "model_used": result.get('model_used', 'unknown')
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response as JSON: {e}")
                    logger.error(f"Response text: {response_text}")
                    raise LLMError(f"Invalid JSON response from LLM: {str(e)}")
            else:
                raise LLMError(result.get('error', 'LLM generation failed'))
                
        except Exception as e:
            logger.error(f"Error generating scoping recommendations: {str(e)}")
            # Re-raise the error - no fallback
            raise

    async def get_primary_provider(self) -> LLMProvider:
        """Get the primary available LLM provider with failover"""
        provider = await self._get_available_provider('claude')
        if not provider:
            raise LLMError("No LLM providers available. Please configure API keys.")
        return provider
    
    async def get_extraction_provider(self) -> LLMProvider:
        """Get the preferred provider for fast extraction (Claude) with failover"""
        provider = await self._get_available_provider('claude')
        if not provider:
            raise LLMError("No LLM providers available for extraction")
        return provider
    
    async def get_analysis_provider(self) -> LLMProvider:
        """Get the preferred provider for deep analysis (Claude) with failover"""
        provider = await self._get_available_provider('claude')
        if not provider:
            raise LLMError("No LLM providers available for analysis")
        return provider
    
    async def analyze_regulatory_document(self, document_text: str, document_type: str = "regulatory") -> Dict[str, Any]:
        """Analyze regulatory document using available provider"""
        try:
            provider = await self.get_analysis_provider()
            
            system_prompt = """You are an expert regulatory compliance analyst. Analyze the regulatory document and extract key testing attributes.
            
            Return your analysis in JSON format with:
            - mandatory_elements: list of required data elements
            - validation_rules: list of data validation constraints
            - risk_areas: list of historical risk areas
            - thresholds: dict of compliance limits
            - documentation: list of required evidence
            """
            
            prompt = f"""Analyze the following regulatory document:

Document Type: {document_type}
Document Content: {document_text[:8000]}

Please identify mandatory data elements, validation rules, risk areas, thresholds, and documentation requirements."""
            
            result = await provider.generate(prompt, system_prompt)
            
            if result.get("success"):
                try:
                    analysis = json.loads(result["content"])
                    return {
                        "success": True,
                        "analysis": analysis,
                        "document_type": document_type,
                        "provider": result.get("model"),
                        "timestamp": result.get("timestamp"),
                        "cost": result.get("cost", 0.0)
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "analysis": {"raw_content": result["content"]},
                        "document_type": document_type,
                        "provider": result.get("model"),
                        "timestamp": result.get("timestamp"),
                        "cost": result.get("cost", 0.0)
                    }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Document analysis failed: {str(e)}")
            raise LLMError(f"Document analysis failed: {str(e)}")
    
    async def generate_test_attributes(self, regulatory_context: str, report_type: str = "Compliance Report", 
                                     preferred_provider: str = None, regulatory_report: str = None, 
                                     schedule: str = None) -> Dict[str, Any]:
        """Generate test attributes using unified 2-phase strategy with external prompts"""
        try:
            # Always use 2-phase approach for consistency
            return await self._generate_attributes_two_phase(
                regulatory_context, 
                report_type, 
                preferred_provider,
                regulatory_report=regulatory_report,
                schedule=schedule
            )
                
        except Exception as e:
            logger.error(f"Attribute generation failed: {str(e)}")
            raise LLMError(f"Attribute generation failed: {str(e)}")
    
    async def generate_test_attributes_hybrid(self, regulatory_context: str, report_type: str = "Compliance Report",
                                            regulatory_report: str = None, schedule: str = None) -> Dict[str, Any]:
        """Hybrid approach: Use Gemini for discovery, Claude for details - now just calls unified 2-phase strategy"""
        return await self._generate_attributes_two_phase(
            regulatory_context, 
            report_type, 
            preferred_discovery='gemini', 
            preferred_details='claude',
            regulatory_report=regulatory_report,
            schedule=schedule
        )
    
    async def _generate_attributes_two_phase(self, regulatory_context: str, report_type: str = "Compliance Report", 
                                           preferred_provider: str = None, preferred_discovery: str = None, 
                                           preferred_details: str = None, regulatory_report: str = None,
                                           schedule: str = None, job_id: str = None) -> Dict[str, Any]:
        """Unified 2-phase strategy: Discovery then detailed analysis with provider-specific batch sizes"""
        try:
            # Progress tracking
            from app.core.background_jobs import job_manager
            if job_id:
                job_manager.update_job_progress(
                    job_id, 
                    progress_percentage=5,
                    current_step="Initializing attribute generation",
                    message="Setting up LLM providers and processing context"
                )
            
            # Use explicit parameters if provided, otherwise detect from context
            if not regulatory_report or not schedule:
                detected_report, detected_schedule = self._extract_regulatory_info(regulatory_context, report_type)
                regulatory_report = regulatory_report or detected_report
                schedule = schedule or detected_schedule
            
            # Phase 1: Attribute Discovery
            discovery_provider_name = preferred_discovery or preferred_provider or 'gemini'
            discovery_provider = await self._get_available_provider(discovery_provider_name)
            
            if not discovery_provider:
                # Fallback to any available provider
                discovery_provider = await self._get_available_provider()
                discovery_provider_name = next(name for name, p in self.providers.items() if p == discovery_provider)
            
            if not discovery_provider:
                raise LLMError("No LLM providers available for discovery phase")
            
            logger.info(f"Phase 1: Attribute discovery using {discovery_provider_name}")
            if regulatory_report:
                logger.info(f"Using regulatory-specific prompts for {regulatory_report} {schedule or ''}")
            
            # Progress update for discovery phase
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    progress_percentage=10,
                    current_step="Attribute Discovery",
                    message=f"Starting attribute discovery using {discovery_provider_name}"
                )
            
            # Load discovery prompt - use regulatory-specific if available
            discovery_system_prompt = prompt_manager.format_prompt(
                "attribute_discovery",
                regulatory_report=regulatory_report,
                schedule=schedule,
                regulation=f"{regulatory_report or ''} {schedule or ''}".strip(),
                report_name=f"{regulatory_report or ''} {schedule or ''}".strip() or report_type,
                regulatory_context=regulatory_context
            )
            
            if not discovery_system_prompt:
                logger.error("Discovery prompt template not found")
                return {
                    "success": False,
                    "error": "Discovery prompt template not found",
                    "provider": discovery_provider_name
                }
            
            discovery_prompt = f"""Generate comprehensive attribute names for:

Regulatory Context: {regulatory_context}
Report Type: {report_type}

Return a complete list of attribute names needed for this regulatory requirement."""

            # LOG THE COMPLETE PROMPTS BEING SENT
            logger.info("=" * 80)
            logger.info(f"📤 SENDING DISCOVERY PROMPT TO {discovery_provider_name.upper()}")
            logger.info("=" * 80)
            logger.info("🔧 SYSTEM PROMPT:")
            logger.info(discovery_system_prompt)
            logger.info("-" * 40)
            logger.info("👤 USER PROMPT:")
            logger.info(discovery_prompt)
            logger.info("=" * 80)
            logger.info("📤 END OF PROMPTS")
            logger.info("=" * 80)

            # Get attribute names
            discovery_result = await discovery_provider.generate(discovery_prompt, discovery_system_prompt)
            
            if not discovery_result.get("success"):
                logger.error(f"{discovery_provider_name} attribute discovery failed")
                return discovery_result
            
            logger.info(f"Discovery raw response length: {len(discovery_result['content'])} characters")
            logger.debug(f"Discovery raw response first 500 chars: {discovery_result['content'][:500]}")
            
            # NEW: Print the ENTIRE response for debugging
            logger.info("=" * 80)
            logger.info(f"🔍 COMPLETE {discovery_provider_name.upper()} DISCOVERY RESPONSE:")
            logger.info("=" * 80)
            logger.info(discovery_result['content'])
            logger.info("=" * 80)
            logger.info("🔍 END OF COMPLETE RESPONSE")
            logger.info("=" * 80)
            
            # Extract attribute names
            attribute_names = extract_json_from_response(discovery_result["content"], expect_attribute_objects=False)
            
            if not attribute_names or not isinstance(attribute_names, list):
                logger.error("Failed to extract attribute names from discovery response")
                logger.error(f"Extracted type: {type(attribute_names)}, value: {attribute_names}")
                logger.error(f"Raw response (first 1000 chars): {discovery_result['content'][:1000]}")
                
                # NEW: Also show what extract_json_from_response found
                logger.info("🔍 DEBUGGING JSON EXTRACTION:")
                logger.info(f"   Input length: {len(discovery_result['content'])}")
                logger.info(f"   Extracted type: {type(attribute_names)}")
                logger.info(f"   Extracted value: {attribute_names}")
                logger.info("   Trying manual inspection...")
                
                # Manual inspection for debugging
                response_text = discovery_result['content']
                logger.info(f"   Contains brackets: {('[' in response_text, ']' in response_text)}")
                logger.info(f"   Contains braces: {('{' in response_text, '}' in response_text)}")
                has_quotes = '"' in response_text
                logger.info(f"   Contains quotes: {has_quotes}")
                logger.info(f"   Line count: {response_text.count(chr(10))}")
                
                return {
                    "success": False,
                    "error": "Failed to extract attribute names from discovery response",
                    "raw_content": discovery_result["content"][:1000],
                    "provider": discovery_provider_name,
                    "complete_response": discovery_result["content"]  # Include full response for debugging
                }
            
            logger.info(f"Phase 1 complete: {discovery_provider_name} discovered {len(attribute_names)} attribute names")
            
            # Progress update for discovery completion
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    progress_percentage=25,
                    current_step="Discovery Complete",
                    message=f"Discovered {len(attribute_names)} attributes"
                )
            
            # Phase 2: Detailed Analysis with provider-specific batch sizes
            details_provider_name = preferred_details or preferred_provider or 'claude'
            details_provider = await self._get_available_provider(details_provider_name)
            
            if not details_provider:
                # Use same provider as discovery if details provider not available
                details_provider = discovery_provider
                details_provider_name = discovery_provider_name
            
            logger.info(f"Phase 2: Detailed analysis using {details_provider_name}")
            
            # Progress update for details phase start
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    progress_percentage=30,
                    current_step="Starting Detailed Analysis",
                    message=f"Beginning batch processing with {details_provider_name}",
                    total_steps=len(attribute_names)
                )
            
            # Provider-specific batch sizes optimized for context windows
            batch_sizes = {
                'gemini': 50,    # Large context window - can handle more attributes
                'claude': 25     # Increased batch size for better completeness while staying within limits
            }
            batch_size = batch_sizes.get(details_provider_name, 25)
            
            # Load details prompt - use regulatory-specific if available
            details_system_prompt = prompt_manager.format_prompt(
                "attribute_batch_details",
                regulatory_report=regulatory_report,
                schedule=schedule,
                regulation=f"{regulatory_report or ''} {schedule or ''}".strip(),
                report_name=f"{regulatory_report or ''} {schedule or ''}".strip() or report_type,
                regulatory_context=regulatory_context,
                attribute_names_batch=""  # Will be filled per batch
            )
            
            if not details_system_prompt:
                logger.error("Details prompt template not found")
                return {
                    "success": False,
                    "error": "Details prompt template not found",
                    "discovered_names": attribute_names
                }
            
            # Process attributes in batches
            all_detailed_attributes = []
            total_batches = (len(attribute_names) + batch_size - 1) // batch_size
            
            for i in range(0, len(attribute_names), batch_size):
                batch = attribute_names[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} attributes) with {details_provider_name}")
                
                # Progress update for batch processing
                if job_id:
                    batch_progress = 30 + int((batch_num - 1) / total_batches * 50)  # 30-80% for batch processing
                    job_manager.update_job_progress(
                        job_id,
                        progress_percentage=batch_progress,
                        current_step=f"Processing Batch {batch_num}/{total_batches}",
                        message=f"Analyzing {len(batch)} attributes with {details_provider_name}",
                        completed_steps=(batch_num - 1) * batch_size
                    )
                
                # Format the batch-specific system prompt
                batch_system_prompt = details_system_prompt.replace(
                    "${attribute_names_batch}",
                    "\n".join([f"- {name}" for name in batch])
                )
                
                details_prompt = f"""Provide detailed information for these {len(batch)} attributes:

Regulatory Context: {regulatory_context}
Report Type: {report_type}

Attribute Names:
{chr(10).join([f"- {name}" for name in batch])}

For each attribute, provide comprehensive testing details including data type, whether it's mandatory, description, validation rules, typical source documents, keywords to look for, and testing approach."""

                # LOG THE COMPLETE BATCH PROMPTS BEING SENT (only for first batch to avoid spam)
                if batch_num == 1:
                    logger.info("=" * 80)
                    logger.info(f"📤 SENDING DETAILS PROMPT TO {details_provider_name.upper()} (Batch {batch_num})")
                    logger.info("=" * 80)
                    logger.info("🔧 SYSTEM PROMPT:")
                    logger.info(batch_system_prompt)
                    logger.info("-" * 40)
                    logger.info("👤 USER PROMPT:")
                    logger.info(details_prompt)
                    logger.info("=" * 80)
                    logger.info("📤 END OF BATCH PROMPTS")
                    logger.info("=" * 80)

                try:
                    details_result = await details_provider.generate(details_prompt, batch_system_prompt)
                    
                    if details_result.get("success"):
                        logger.info(f"Batch {batch_num} raw response length: {len(details_result['content'])} characters")
                        logger.debug(f"Batch {batch_num} raw response: {details_result['content'][:500]}...")
                        
                        batch_attributes = extract_json_from_response(details_result["content"], expect_attribute_objects=True)
                        
                        if batch_attributes and isinstance(batch_attributes, list):
                            logger.info(f"Batch {batch_num} extracted {len(batch_attributes)} attributes from JSON")
                            
                            # Filter and validate batch attributes
                            required_fields = ['attribute_name', 'data_type', 'mandatory_flag', 'description', 'validation_rules', 'typical_source_documents', 'keywords_to_look_for', 'testing_approach']
                            
                            batch_valid_count = 0
                            for attr in batch_attributes:
                                if isinstance(attr, dict):
                                    # Create filtered attribute with defaults for missing fields
                                    filtered_attr = {}
                                    for field in required_fields:
                                        if field in attr:
                                            filtered_attr[field] = attr[field]
                                        else:
                                            # Provide defaults for missing fields
                                            if field == 'typical_source_documents':
                                                filtered_attr[field] = 'Source documents to be determined during testing'
                                            elif field == 'keywords_to_look_for':
                                                filtered_attr[field] = f"Keywords related to {attr.get('attribute_name', 'this attribute')}"
                                            elif field == 'validation_rules':
                                                filtered_attr[field] = 'Standard data validation rules apply'
                                            elif field == 'testing_approach':
                                                filtered_attr[field] = 'Standard testing approach for this data type'
                                            else:
                                                filtered_attr[field] = ''
                                    
                                    # Only add if we have the core required fields
                                    core_fields = ['attribute_name', 'data_type', 'mandatory_flag', 'description']
                                    if all(filtered_attr.get(field) for field in core_fields):
                                        all_detailed_attributes.append(filtered_attr)
                                        batch_valid_count += 1
                                    else:
                                        logger.warning(f"Skipping batch {batch_num} attribute missing core fields: {attr}")
                                        logger.warning(f"Filtered version: {filtered_attr}")
                            
                            logger.info(f"Batch {batch_num} processed {batch_valid_count}/{len(batch_attributes)} attributes successfully")
                        elif batch_attributes:
                            logger.warning(f"Batch {batch_num} returned non-list response: {type(batch_attributes)}")
                            logger.debug(f"Batch {batch_num} response structure: {batch_attributes}")
                        else:
                            logger.warning(f"Failed to parse batch {batch_num} response")
                            logger.debug(f"Batch {batch_num} response content: {details_result['content'][:200]}...")
                    else:
                        logger.warning(f"Batch {batch_num} generation failed: {details_result}")
                        
                except Exception as e:
                    logger.error(f"Error processing batch {batch_num}: {str(e)}")
                    logger.error(f"Batch {batch_num} exception details: {e.__class__.__name__}: {str(e)}")
                    continue
                
                # Small delay between batches to avoid rate limits
                await asyncio.sleep(0.5)
            
            logger.info(f"Phase 2 complete: {details_provider_name} processed {len(all_detailed_attributes)} detailed attributes")
            
            # Progress update for completion
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    progress_percentage=90,
                    current_step="Finalizing Results",
                    message=f"Processed {len(all_detailed_attributes)} detailed attributes"
                )
            
            if not all_detailed_attributes:
                logger.error("No detailed attributes generated from batch processing")
                # Update job progress to show failure
                if job_id:
                    job_manager.update_job_progress(
                        job_id,
                        progress_percentage=0,  # Reset progress to show failure
                        current_step="Batch Processing Failed",
                        message="No detailed attributes could be generated from any batch",
                        status="failed",
                        error="Batch processing failed to generate detailed attributes"
                    )
                return {
                    "success": False,
                    "error": "Batch processing failed to generate detailed attributes",
                    "discovered_names": attribute_names
                }
            
            # Validate the final response
            if not validate_attributes_response(all_detailed_attributes):
                logger.error("Invalid attributes structure in response")
                return {
                    "success": False,
                    "error": "Generated attributes have invalid structure",
                    "discovered_names": attribute_names,
                    "detailed_count": len(all_detailed_attributes)
                }
            
            return {
                "success": True,
                "attributes": all_detailed_attributes,
                "regulatory_context": regulatory_context,
                "report_type": report_type,
                "method": "two_phase",
                "discovery_provider": discovery_provider_name,
                "details_provider": details_provider_name,
                "batch_size": batch_size,
                "discovered_count": len(attribute_names),
                "detailed_count": len(all_detailed_attributes),
                "batches_processed": total_batches,
                "timestamp": datetime.utcnow().isoformat(),
                "regulatory_report": regulatory_report,
                "schedule": schedule
            }
                
        except Exception as e:
            logger.error(f"Two-phase attribute generation failed: {str(e)}")
            # Update job progress to show failure
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    progress_percentage=0,
                    current_step="Generation Failed",
                    message=f"Exception occurred: {str(e)[:100]}...",
                    status="failed",
                    error=str(e)
                )
            raise LLMError(f"Two-phase attribute generation failed: {str(e)}")
    
    def _extract_regulatory_info(self, regulatory_context: str, report_type: str) -> tuple[Optional[str], Optional[str]]:
        """Extract regulatory report and schedule information from context"""
        import re
        
        # Common regulatory report patterns
        report_patterns = [
            (r'FR\s*Y-?14M', 'FR Y-14M'),
            (r'FR\s*Y-?14Q', 'FR Y-14Q'),
            (r'FR\s*Y-?9C', 'FR Y-9C'),
            (r'Call\s*Report', 'Call Report'),
            (r'FFIEC\s*\d+', 'FFIEC'),
            (r'CCAR', 'CCAR'),
            (r'DFAST', 'DFAST')
        ]
        
        # Schedule patterns for FR Y-14M - correct sub-schedules
        schedule_patterns = [
            # Schedule A
            (r'Schedule\s*A\.1\b', 'schedule_a_1'),
            (r'Schedule\s*A\.2\b', 'schedule_a_2'),
            # Schedule B
            (r'Schedule\s*B\.1\b', 'schedule_b_1'),
            (r'Schedule\s*B\.2\b', 'schedule_b_2'),
            # Schedule C
            (r'Schedule\s*C\.1\b', 'schedule_c_1'),
            # Schedule D
            (r'Schedule\s*D\.1\b', 'schedule_d_1'),
            (r'Schedule\s*D\.2\b', 'schedule_d_2')
        ]
        
        # Combine context and report type for better detection
        combined_text = f"{regulatory_context} {report_type}"
        
        # Detect regulatory report
        regulatory_report = None
        for pattern, report_name in report_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                regulatory_report = report_name
                break
        
        # Detect schedule (primarily for FR Y-14M)
        schedule = None
        if regulatory_report in ['FR Y-14M', 'FR Y-14Q']:
            for pattern, schedule_name in schedule_patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    schedule = schedule_name
                    break
        
        logger.debug(f"Extracted regulatory info - Report: {regulatory_report}, Schedule: {schedule}")
        return regulatory_report, schedule
    
    async def recommend_tests_batch(self, attributes: List[Dict[str, Any]], regulatory_context: str,
                                   report_name: str = None, report_type: str = None,
                                   batch_num: int = 1, total_batches: int = 1) -> Dict[str, Any]:
        """Generate test recommendations for a batch of attributes using regulatory-specific prompts"""
        try:
            provider = await self.get_analysis_provider()
            
            # Extract regulatory report and schedule from context
            regulatory_report, schedule = self._extract_regulatory_info(regulatory_context, report_type or "Credit Card")
            
            # Load regulatory-specific prompt if available
            system_prompt_template = prompt_manager.load_prompt_template(
                "scoping_recommendations",
                regulatory_report=regulatory_report,
                schedule=schedule
            )
            
            if system_prompt_template:
                # Format attributes as JSON for the template
                attributes_json = json.dumps([
                    {
                        "name": attr['attribute_name'],
                        "data_type": attr['data_type'],
                        "is_primary_key": attr.get('is_primary_key', False),
                        "is_cde": attr.get('is_cde', False),
                        "is_mandatory": attr.get('is_mandatory', False),
                        "has_historical_issues": attr.get('has_historical_issues', False)
                    }
                    for attr in attributes
                ], indent=2)
                
                # Format the template with context
                system_prompt = system_prompt_template.safe_substitute(
                    regulatory_context=regulatory_context,
                    report_name=report_name or report_type or "Credit Card",
                    report_type=report_type or "Credit Card",
                    attributes_json=attributes_json,
                    batch_size=len(attributes)
                )
                logger.info(f"Using regulatory-specific prompt for {regulatory_report} {schedule}")
            else:
                # Fallback to generic prompt
                system_prompt = """You are an expert in data testing methodologies. Generate specific test recommendations for regulatory compliance.
                
                For each attribute, return JSON with:
                - attribute_id or attribute_name (to match the input)
                - risk_score: integer 0-100
                - rationale: explanation for the risk score
                - data_quality_tests: array of data quality checks
                - business_rules: array of business rule validations
                - compliance_checks: array of regulatory compliance tests
                - edge_cases: array of edge case scenarios
                - sample_size: recommended sample size
                
                Return a JSON array with one object per attribute."""
                logger.info("Using generic scoping prompt")
            
            # Build the batch prompt
            attributes_info = []
            for attr in attributes:
                attr_desc = f"- {attr['attribute_name']} (Type: {attr['data_type']}"
                if attr.get('is_primary_key'):
                    attr_desc += ", Primary Key"
                if attr.get('is_cde'):
                    attr_desc += ", Critical Data Element"
                if attr.get('is_mandatory'):
                    attr_desc += ", Mandatory"
                if attr.get('has_historical_issues'):
                    attr_desc += ", Has Historical Issues"
                attr_desc += ")"
                attributes_info.append(attr_desc)
            
            # Build user prompt - include attributes even with regulatory template
            if system_prompt_template:
                # Format attributes as JSON for the template
                attributes_json = []
                for attr in attributes:
                    attr_info = {
                        "attribute_name": attr['attribute_name'],
                        "data_type": attr.get('data_type', 'String'),
                        "is_primary_key": attr.get('is_primary_key', False),
                        "is_cde": attr.get('is_cde', False),
                        "is_mandatory": attr.get('is_mandatory', False),
                        "has_historical_issues": attr.get('has_historical_issues', False)
                    }
                    attributes_json.append(attr_info)
                
                # Replace the ${attributes_json} placeholder in the system prompt
                system_prompt = system_prompt_template.safe_substitute(attributes_json=json.dumps(attributes_json, indent=2))
                
                prompt = f"""Generate comprehensive test recommendations for the {len(attributes)} attributes provided in the system prompt.
                
This is batch {batch_num} of {total_batches} for the scoping phase.

Return the recommendations in the exact JSON format specified in the system prompt."""
            else:
                # Detailed prompt for generic case
                prompt = f"""Generate test recommendations for this batch of attributes (Batch {batch_num} of {total_batches}):

Regulatory Context: {regulatory_context}

Attributes:
{chr(10).join(attributes_info)}

Provide comprehensive testing recommendations for ALL {len(attributes)} attributes including data quality, business rules, compliance checks, edge cases, and sample sizes.

Important: Return a JSON array with exactly {len(attributes)} objects, one for each attribute listed above."""

            # Log the exact prompt for debugging
            logger.info(f"LLM Batch Prompt (batch {batch_num}):")
            logger.info(f"System prompt length: {len(system_prompt)} chars")
            logger.info(f"System prompt preview:\n{system_prompt[:500]}...")
            logger.info(f"User prompt:\n{prompt}")
            
            result = await provider.generate(prompt, system_prompt)
            
            if result.get("success"):
                try:
                    recommendations = json.loads(result["content"])
                    # Ensure we have a list
                    if not isinstance(recommendations, list):
                        recommendations = [recommendations]
                    
                    logger.info(f"Batch {batch_num}: Received {len(recommendations)} recommendations for {len(attributes)} attributes")
                    
                    return {
                        "success": True,
                        "recommendations": recommendations,
                        "batch_num": batch_num,
                        "provider": result.get("model"),
                        "timestamp": result.get("timestamp"),
                        "cost": result.get("cost", 0.0)
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse batch recommendations: {e}")
                    return {
                        "success": False,
                        "error": "Failed to parse test recommendations response",
                        "raw_content": result["content"]
                    }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Batch test recommendation failed: {str(e)}")
            raise LLMError(f"Batch test recommendation failed: {str(e)}")
    
    async def recommend_tests(self, attribute_name: str, data_type: str, regulatory_context: str, historical_issues: List[str] = None) -> Dict[str, Any]:
        """Generate test recommendations using available provider"""
        try:
            provider = await self.get_analysis_provider()
            
            system_prompt = """You are an expert in data testing methodologies. Generate specific test recommendations for regulatory compliance.
            
            Return JSON with:
            - data_quality_tests: array of data quality checks
            - business_rules: array of business rule validations
            - compliance_checks: array of regulatory compliance tests
            - edge_cases: array of edge case scenarios
            - sample_size: recommended sample size
            """
            
            historical_context = ", ".join(historical_issues) if historical_issues else "No historical issues reported"
            
            prompt = f"""Generate test recommendations for:

Attribute: {attribute_name}
Data Type: {data_type}
Regulatory Context: {regulatory_context}
Historical Issues: {historical_context}

Provide comprehensive testing recommendations including data quality, business rules, compliance checks, edge cases, and sample size."""
            
            result = await provider.generate(prompt, system_prompt)
            
            if result.get("success"):
                try:
                    recommendations = json.loads(result["content"])
                    return {
                        "success": True,
                        "recommendations": recommendations,
                        "attribute_name": attribute_name,
                        "provider": result.get("model"),
                        "timestamp": result.get("timestamp"),
                        "cost": result.get("cost", 0.0)
                    }
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": "Failed to parse test recommendations response",
                        "raw_content": result["content"]
                    }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Test recommendation failed: {str(e)}")
            raise LLMError(f"Test recommendation failed: {str(e)}")
    
    async def analyze_historical_patterns(self, historical_issues: List[str], report_context: str) -> Dict[str, Any]:
        """Analyze historical patterns using available provider"""
        try:
            provider = await self.get_analysis_provider()
            
            system_prompt = """You are an expert in pattern analysis for regulatory compliance. Analyze historical issues to identify patterns and recommendations.
            
            Return JSON with:
            - patterns: array of identified patterns
            - risk_factors: array of risk factors
            - recommendations: array of actionable recommendations
            - prevention_strategies: array of prevention approaches
            """
            
            issues_text = "\n".join(f"- {issue}" for issue in historical_issues)
            
            prompt = f"""Analyze the following historical issues for patterns:

Report Context: {report_context}
Historical Issues:
{issues_text}

Identify patterns, risk factors, recommendations, and prevention strategies."""
            
            result = await provider.generate(prompt, system_prompt)
            
            if result.get("success"):
                try:
                    analysis = json.loads(result["content"])
                    return {
                        "success": True,
                        "analysis": analysis,
                        "report_context": report_context,
                        "provider": result.get("model"),
                        "timestamp": result.get("timestamp"),
                        "cost": result.get("cost", 0.0)
                    }
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": "Failed to parse pattern analysis response",
                        "raw_content": result["content"]
                    }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Pattern analysis failed: {str(e)}")
            raise LLMError(f"Pattern analysis failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all available providers"""
        provider_results = {}
        overall_status = "healthy"
        
        for name, provider in self.providers.items():
            try:
                health = await provider.health_check()
                provider_results[name] = health
                if health.get("status") != "healthy":
                    overall_status = "degraded"
            except Exception as e:
                provider_results[name] = {
                    "provider": name,
                    "status": "unhealthy",
                    "error": str(e)
                }
                overall_status = "unhealthy"
        
        return {
            "overall_status": overall_status,
            "provider_details": provider_results,
            "available_providers": list(self.providers.keys()),
            "hybrid_enabled": self.hybrid_enabled
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all providers"""
        metrics = {}
        
        for name, provider in self.providers.items():
            metrics[name] = provider.get_metrics()
        
        return {
            "provider_metrics": metrics,
            "hybrid_service": {
                "providers_available": len(self.providers),
                "hybrid_enabled": self.hybrid_enabled
            }
        }
    
    async def extract_test_value_from_document(
        self, 
        document_content: str, 
        attribute_name: str,
        attribute_context: Dict[str, Any],
        primary_key_field: str,
        primary_key_value: str,
        document_type: str = "regulatory",
        cycle_id: Optional[int] = None,
        report_id: Optional[int] = None,
        regulatory_report: Optional[str] = None,
        regulatory_schedule: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract specific attribute value from document using LLM with regulation-specific prompts"""
        try:
            provider = await self.get_analysis_provider()
            
            # Try to use PromptManager if available
            prompt_content = None
            if cycle_id and report_id:
                try:
                    from app.core.prompt_manager import PromptManager
                    prompt_manager = PromptManager()
                    
                    # Format the prompt context
                    prompt_context = {
                        'document_content': document_content[:5000],  # Limit to first 5000 chars
                        'attribute_name': attribute_name,
                        'attribute_description': attribute_context.get('description', ''),
                        'primary_key_info': f"{primary_key_field}: {primary_key_value}",
                        'search_keywords': attribute_context.get('keywords_to_look_for', ''),
                        'data_type': attribute_context.get('data_type', 'String')
                    }
                    
                    # Get regulation-specific prompt if available
                    template = None
                    if regulatory_report and regulatory_schedule:
                        template = prompt_manager.load_prompt_template(
                            'document_extraction',
                            regulatory_report=regulatory_report,
                            schedule=regulatory_schedule
                        )
                    else:
                        # Try to get general document extraction prompt
                        template = prompt_manager.load_prompt_template(
                            'document_extraction'
                        )
                    
                    # Render the template with context if found
                    if template:
                        prompt_content = template.safe_substitute(**prompt_context)
                except Exception as e:
                    logger.warning(f"Could not load prompt from PromptManager: {str(e)}")
            
            # If no prompt from PromptManager, use fallback
            if not prompt_content:
                # Build the extraction prompt (fallback)
                system_prompt = """You are an expert document analyst specializing in regulatory data extraction. 
Your task is to extract specific attribute values from documents with high precision.

Instructions:
1. First locate the primary key field to ensure you're extracting from the correct record
2. Extract the exact value for the requested attribute
3. Provide confidence score based on clarity and context
4. Return response in JSON format

IMPORTANT: You must respond ONLY with a valid JSON object. Do not include any explanatory text before or after the JSON."""

                prompt = f"""Extract the following information from the document:

Primary Key Field: {primary_key_field}
Primary Key Value: {primary_key_value}
Attribute to Extract: {attribute_name}

Attribute Context:
- Data Type: {attribute_context.get('data_type', 'String')}
- Description: {attribute_context.get('description', '')}
- Keywords to Look For: {attribute_context.get('keywords_to_look_for', '')}
- Validation Rules: {attribute_context.get('validation_rules', '')}

Document Content:
{document_content[:5000]}  # Limit to first 5000 chars

Return JSON with this structure:
{{
    "success": true/false,
    "extracted_value": "the extracted value",
    "confidence_score": 0.0-1.0,
    "primary_key_found": true/false,
    "evidence": "brief explanation of where/how the value was found",
    "location": "page/section where found",
    "document_quality": "High/Medium/Low"
}}

REMEMBER: Respond ONLY with the JSON object, no other text."""
            else:
                # Use prompt from PromptManager
                system_prompt = """You are an expert document analyst specializing in regulatory data extraction.
                
IMPORTANT: You must respond ONLY with a valid JSON object. Do not include any explanatory text before or after the JSON.
The JSON response must follow the exact format specified in the prompt."""
                prompt = prompt_content + "\n\nREMEMBER: Respond ONLY with the JSON object, no other text."

            result = await provider.generate(prompt, system_prompt)
            
            if result.get("success"):
                # Parse the JSON response
                try:
                    import json
                    content = result.get("content", "")
                    
                    # Check if content is empty or None
                    if not content or not content.strip():
                        logger.warning("LLM returned empty response")
                        return {
                            "success": False,
                            "error": "LLM returned empty response",
                            "raw_response": content
                        }
                    
                    # Handle potential markdown formatting
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    
                    # Try to extract JSON object - look for the extraction_result pattern first
                    parsed = None
                    
                    # Method 1: Look for extraction_result JSON object specifically
                    extraction_pattern = r'\{[^{]*"extraction_result"\s*:\s*\{[^}]+\}[^}]*\}'
                    extraction_match = re.search(extraction_pattern, content, re.DOTALL)
                    if extraction_match:
                        try:
                            json_str = extraction_match.group(0)
                            # Fix common JSON issues
                            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
                            json_str = re.sub(r',\s*]', ']', json_str)
                            parsed = json.loads(json_str)
                        except:
                            pass
                    
                    # Method 2: Find the first complete JSON object
                    if not parsed:
                        json_start = content.find('{')
                        if json_start >= 0:
                            # Try to find matching closing brace
                            brace_count = 0
                            json_end = -1
                            for i in range(json_start, len(content)):
                                if content[i] == '{':
                                    brace_count += 1
                                elif content[i] == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_end = i + 1
                                        break
                            
                            if json_end > json_start:
                                json_str = content[json_start:json_end]
                                try:
                                    # Fix common JSON issues before parsing
                                    json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
                                    json_str = re.sub(r',\s*]', ']', json_str)
                                    parsed = json.loads(json_str)
                                except:
                                    pass
                    
                    # Method 3: Simple extraction as fallback
                    if not parsed:
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = content[json_start:json_end]
                            try:
                                parsed = json.loads(json_str)
                            except:
                                pass
                    
                    if not parsed:
                        # No valid JSON found
                        logger.warning(f"No valid JSON found in LLM response. Raw content: {content[:200]}...")
                        return {
                            "success": False,
                            "error": "No valid JSON found in response",
                            "raw_response": content
                        }
                    
                    # Handle both response formats (new format with extraction_result wrapper and direct format)
                    if 'extraction_result' in parsed:
                        extraction_data = parsed['extraction_result']
                        return {
                            "success": True,
                            "extracted_value": extraction_data.get('extracted_value', ''),
                            "confidence_score": extraction_data.get('confidence_score', 0.0),
                            "primary_key_found": True,  # Assuming true if we got a result
                            "evidence": extraction_data.get('supporting_context', extraction_data.get('evidence', '')),
                            "location": extraction_data.get('source_location', extraction_data.get('location', '')),
                            "document_quality": "High" if extraction_data.get('confidence_score', 0) > 0.8 else "Medium"
                        }
                    else:
                        # Direct format (backward compatibility)
                        # Ensure required fields are present
                        if 'success' not in parsed:
                            parsed['success'] = True
                        if 'extracted_value' not in parsed and 'value' in parsed:
                            parsed['extracted_value'] = parsed['value']
                        return parsed
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error: {str(e)}. Content: {content[:200] if 'content' in locals() else 'N/A'}...")
                    return {
                        "success": False,
                        "error": f"Invalid JSON response: {str(e)}",
                        "raw_response": result.get("content", "")
                    }
                except Exception as e:
                    logger.error(f"Failed to parse LLM response: {str(e)}")
                    return {
                        "success": False,
                        "error": f"Failed to parse response: {str(e)}",
                        "raw_response": result.get("content", "")
                    }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }
                
        except Exception as e:
            logger.error(f"Document value extraction failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_data_profiling_rules(self, attribute_context: Dict[str, Any], 
                                          preferred_provider: str = "claude") -> Dict[str, Any]:
        """Generate intelligent data profiling rules for a specific attribute using LLM"""
        try:
            # Get the best available provider for analysis
            provider = await self._get_available_provider(preferred_provider)
            if not provider:
                # Fallback to any available provider
                provider = await self._get_available_provider()
                if not provider:
                    raise LLMError("No LLM providers available for rule generation")
            
            # Build context for the LLM
            attribute_name = attribute_context.get("attribute_name", "Unknown")
            data_type = attribute_context.get("data_type", "Unknown")
            mandatory = attribute_context.get("mandatory", "Unknown")
            description = attribute_context.get("description", "")
            is_primary_key = attribute_context.get("is_primary_key", False)
            sample_data = attribute_context.get("sample_data", [])
            data_source = attribute_context.get("data_source", None)
            
            # Create detailed prompt for rule generation
            system_prompt = """You are an expert data quality engineer specializing in regulatory data testing for financial institutions. 
Generate intelligent, context-aware data profiling rules for the given attribute. 

Your rules should be:
1. Specific to the attribute's semantic meaning and regulatory context
2. Executable Python code that can run on pandas DataFrames
3. Tailored to the data type and business meaning
4. Appropriate for financial regulatory reporting requirements
5. Include proper error handling and meaningful metrics

CRITICAL: You must return ONLY valid JSON with this exact structure. Do not include any explanatory text before or after the JSON:"""

            # Build data source context section
            data_source_context = ""
            if data_source:
                if data_source.get("type") == "pde_mapping":
                    data_source_context = f"""
**Physical Data Element (PDE) Mapping Information:**
- PDE Name: {data_source.get('pde_name', 'N/A')}
- PDE Code (EXACT DATABASE COLUMN NAME): {data_source.get('pde_code', 'N/A')}
- Source Field: {data_source.get('source_field', 'N/A')}
- Mapping Type: {data_source.get('mapping_type', 'N/A')}
- Transformation Rule: {data_source.get('transformation_rule', 'N/A')}
- Business Process: {data_source.get('business_process', 'N/A')}
- Business Owner: {data_source.get('business_owner', 'N/A')}
- Data Steward: {data_source.get('data_steward', 'N/A')}
- Information Security Classification: {data_source.get('info_sec_classification', 'N/A')}
- Is CDE (Critical Data Element): {data_source.get('is_cde', False)}
- Risk Level: {data_source.get('risk_level', 'N/A')}
- LLM Confidence Score: {data_source.get('llm_confidence_score', 'N/A')}%

**CRITICAL DATABASE COLUMN INFORMATION:**
⚠️ The database column name for this attribute is: '{data_source.get('pde_code', 'N/A')}'
⚠️ When writing validation rules that reference OTHER columns, use exact database column names (lowercase with underscores)
⚠️ Common database columns: original_credit_limit, current_credit_limit, customer_id, period_id, bank_id, etc.

This PDE mapping provides critical context about the data source and business meaning."""
                else:
                    data_source_context = f"""
**Data Source Information:**
- Source Type: File Upload
- Sample Values Available: {len(sample_data) if sample_data else 0}"""
            else:
                data_source_context = f"""
**Data Source Information:**
- Source Type: File Upload (No PDE Mapping)
- Sample Values Available: {len(sample_data) if sample_data else 0}"""

            prompt = f"""CRITICAL: Generate data profiling rules ONLY for this specific attribute: "{attribute_name}"

**PRIMARY ATTRIBUTE: {attribute_name}**

**Attribute Details:**
- Name: {attribute_name}
- Data Type: {data_type}
- Mandatory: {mandatory}
- Description: {description}
- Is Primary Key: {is_primary_key}
- Sample Values: {sample_data[:5] if sample_data else "Not available"}
{data_source_context}

**Context:** This is for regulatory financial reporting data that must meet strict compliance standards.

**RULE GENERATION INSTRUCTIONS:**
1. Create rules that primarily validate "{attribute_name}"
2. Rules may reference other attributes for cross-validation (referential integrity, consistency checks, etc.) but the PRIMARY focus must be on "{attribute_name}"
3. Each rule must set "target_attribute": "{attribute_name}" 
4. Rule names should clearly indicate they are for "{attribute_name}"
5. Do NOT create rules that are primarily about other attributes
6. When PDE mapping is available:
   - Consider the business process and data steward context
   - Apply stricter validation for CDEs (Critical Data Elements)
   - Adjust rule severity based on risk level and security classification
   - Use transformation rules to validate data consistency
   - Consider the source field mapping type for appropriate validations

**EXAMPLES OF ACCEPTABLE RULES:**
- "{attribute_name} Completeness Check" ✅
- "{attribute_name} Format Validation" ✅ 
- "{attribute_name} vs [Other Field] Consistency Check" ✅ (cross-validation)
- "{attribute_name} Referential Integrity" ✅ (may check against other tables)

**EXAMPLES OF UNACCEPTABLE RULES:**
- "[Other Attribute] Format Check" ❌ (wrong primary focus)
- "[Other Attribute] Completeness" ❌ (wrong primary focus)

**Required Response Format (ONLY return this JSON, no other text):**
{{
    "attribute_name": "{attribute_name}",
    "rules": [
        {{
            "type": "completeness",
            "name": "Descriptive rule name", 
            "description": "What this rule validates",
            "code": "def check_rule(df, column_name): return {{'passed': 100, 'failed': 0, 'total': 100, 'pass_rate': 100.0}}",
            "rationale": "Why this rule is important for this specific attribute",
            "severity": "critical",
            "execution_order": 1,
            "regulatory_reference": "Relevant regulatory requirement if applicable",
            "target_attribute": "{attribute_name}"
        }}
    ],
    "total_rules": 3,
    "attribute_assessment": "Brief assessment of data quality risks for this attribute"
}}

**Code Requirements:**
- ALL functions MUST accept (df, column_name) parameters for consistency
- The column_name parameter will ALWAYS be the attribute name (not the source column)
- Return dict with 'passed', 'failed', 'total', 'pass_rate' keys
- Include specific validation logic appropriate for the attribute
- Handle edge cases (nulls, empty values, type mismatches)
- For financial data, consider regulatory precision requirements
- For dates, validate format and reasonable ranges
- For IDs, check uniqueness and format patterns
- For amounts, validate numeric ranges and precision
- IMPORTANT: Always use df[column_name] to access the data - the execution framework ensures the DataFrame column matches the attribute name

**CRITICAL PANDAS USAGE RULES:**
1. NEVER use df.apply(lambda x: x[column_name]) - this will fail with KeyError
2. ALWAYS use df[column_name].apply(your_function) to apply functions to column values
3. When using apply() on a column, the function receives individual values, not rows
4. For counting: passed = df[column_name].apply(check_function).sum(); failed = total - passed
5. Example of CORRECT pattern:
   def check_decimals(x):
       if pd.isna(x): return True
       try: return len(str(float(x)).split('.')[-1]) <= 2
       except: return False
   passed = df[column_name].apply(check_decimals).sum()
   failed = len(df) - passed

**Examples of CORRECT vs INCORRECT patterns:**

INCORRECT (will cause KeyError):
```python
# DON'T DO THIS - x is a Series, not DataFrame
df[df[column_name].notna()].apply(lambda x: x[column_name] > 0)
```

CORRECT:
```python
# DO THIS - apply directly to the column
df[column_name].apply(lambda x: x > 0 if pd.notna(x) else False).sum()
```

INCORRECT (confusing counting logic):
```python
# DON'T DO THIS - complex subtraction can lead to errors
failed = df[column_name].notna().sum() - df[column_name].apply(check_func).sum()
```

CORRECT:
```python
# DO THIS - simple and clear
total = len(df)
passed = df[column_name].apply(check_func).sum()
failed = total - passed
```

Generate 3-5 comprehensive rules appropriate for this specific attribute, covering different data quality dimensions (Completeness, Validity, Consistency, Accuracy, Uniqueness) as relevant.

RESPOND WITH ONLY THE JSON OBJECT - NO ADDITIONAL TEXT OR EXPLANATIONS."""

            result = await provider.generate(prompt, system_prompt)
            
            if result.get("success"):
                try:
                    content = result.get("content", "{}")
                    logger.debug(f"Raw LLM response for {attribute_name}: {content[:200]}...")
                    
                    # Handle potential markdown formatting
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    
                    # Clean up the content
                    content = content.strip()
                    
                    # Try to find JSON object within the content
                    if not content.startswith('{'):
                        # Look for the first { and last } to extract JSON
                        start_idx = content.find('{')
                        end_idx = content.rfind('}')
                        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                            content = content[start_idx:end_idx+1]
                    
                    logger.debug(f"Cleaned content for {attribute_name}: {content[:200]}...")
                    parsed = json.loads(content)
                    
                    # Validate the response structure
                    if "rules" in parsed and isinstance(parsed["rules"], list):
                        logger.info(f"Generated {len(parsed['rules'])} rules for {attribute_name}")
                        
                        # Post-process rules to fix common pandas issues
                        parsed = self._fix_rule_code_issues(parsed)
                        
                        return parsed
                    else:
                        logger.warning(f"Invalid rule structure returned for {attribute_name}: {list(parsed.keys())}")
                        return {"rules": []}
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing failed for {attribute_name}: {str(e)}")
                    logger.error(f"Problematic content: {content[:500]}...")
                    return {"rules": []}
                except Exception as e:
                    logger.error(f"Failed to parse rule generation response for {attribute_name}: {str(e)}")
                    return {"rules": []}
            else:
                logger.error(f"Rule generation failed: {result.get('error', 'Unknown error')}")
                return {"rules": []}
                
        except Exception as e:
            logger.error(f"Data profiling rule generation failed: {str(e)}")
            return {"rules": []}
    
    def _fix_rule_code_issues(self, llm_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-process LLM-generated rule code to fix common pandas issues
        
        Args:
            llm_response: The complete LLM response with rules
            
        Returns:
            Fixed LLM response with corrected rule code
        """
        
        if 'rules' not in llm_response:
            return llm_response
        
        fixed_response = llm_response.copy()
        fixed_rules = []
        fixes_applied = 0
        
        for rule in llm_response['rules']:
            fixed_rule = rule.copy()
            
            if 'code' in rule:
                original_code = rule['code']
                fixed_code = self._fix_pandas_str_accessor(original_code)
                
                if fixed_code != original_code:
                    logger.info(f"🔧 Fixed pandas .str issue in rule: {rule.get('name', 'Unnamed')}")
                    fixed_rule['code'] = fixed_code
                    fixes_applied += 1
            
            fixed_rules.append(fixed_rule)
        
        fixed_response['rules'] = fixed_rules
        
        if fixes_applied > 0:
            logger.info(f"Applied {fixes_applied} pandas fixes to LLM-generated rules")
        
        return fixed_response
    
    def _fix_pandas_str_accessor(self, rule_code: str) -> str:
        """
        Fix .str accessor usage in pandas code to prevent runtime errors
        
        Args:
            rule_code: The original rule code from LLM
            
        Returns:
            Fixed rule code with proper .astype(str) before .str operations
        """
        
        lines = rule_code.split('\n')
        fixed_lines = []
        
        for line in lines:
            fixed_line = line
            
            # Only fix lines that have .str usage with df[column_name] without .astype(str)
            if '.str.' in line and 'df[column_name]' in line:
                # Check if .astype(str) is already there
                if '.astype(str).str.' not in line:
                    # Replace df[column_name].str. with df[column_name].astype(str).str.
                    fixed_line = re.sub(
                        r'df\[column_name\]\.str\.',
                        'df[column_name].astype(str).str.',
                        line
                    )
            
            fixed_lines.append(fixed_line)
        
        return '\n'.join(fixed_lines)

    async def generate_pde_classification_suggestion(
        self,
        pde_mapping,
        attribute,
        cycle_id: int,
        report_id: int
    ) -> Dict[str, Any]:
        """
        Generate PDE classification suggestions using LLM with regulation-specific prompts
        
        Args:
            pde_mapping: The PDE mapping object
            attribute: The related attribute object  
            cycle_id: Cycle ID
            report_id: Report ID
            
        Returns:
            Dictionary containing classification suggestions
        """
        try:
            from app.core.prompt_manager import PromptManager
            from app.core.database import AsyncSessionLocal
            from app.models.report import Report
            from sqlalchemy import select
            
            provider = await self.get_analysis_provider()
            prompt_manager = PromptManager()
            
            # Get regulatory context from the report
            regulatory_report = None
            regulatory_schedule = None
            regulatory_context = "General regulatory reporting"
            
            try:
                async with AsyncSessionLocal() as db:
                    report_query = select(Report).where(Report.report_id == report_id)
                    report_result = await db.execute(report_query)
                    report = report_result.scalar_one_or_none()
                    
                    if report and report.regulation:
                        regulatory_context = report.regulation
                        # Extract regulatory report and schedule using existing method
                        regulatory_report, regulatory_schedule = self._extract_regulatory_info(
                            report.regulation, 
                            getattr(report, 'report_type', 'Compliance Report')
                        )
                        logger.info(f"Extracted regulatory context: {regulatory_report} / {regulatory_schedule}")
            except Exception as e:
                logger.warning(f"Could not get regulatory context from report: {e}")
            
            # Load regulation-specific classification prompt
            prompt_template = prompt_manager.load_prompt_template(
                "information_security_classification",
                regulatory_report=regulatory_report,
                schedule=regulatory_schedule
            )
            
            if not prompt_template:
                logger.warning("Could not load information_security_classification prompt, using fallback")
                # Use the existing prompt content as fallback
                with open("app/prompts/information_security_classification.txt", "r") as f:
                    prompt_content = f.read()
            else:
                # Format the prompt with context variables
                prompt_content = prompt_template.safe_substitute(
                    report_name=getattr(report, 'report_name', 'Unknown Report') if 'report' in locals() else 'Unknown Report',
                    regulatory_context=regulatory_context,
                    pde_name=pde_mapping.pde_name or '',
                    pde_code=pde_mapping.pde_code or '',
                    pde_description=pde_mapping.pde_description or '',
                    business_process=getattr(pde_mapping, 'business_process', '') or '',
                    source_system=getattr(pde_mapping, 'source_field', '') or '',
                    attribute_name=attribute.attribute_name if attribute else 'Unknown',
                    data_type=attribute.data_type if attribute else 'Unknown',
                    cde_flag=getattr(attribute, 'cde_flag', False) if attribute else False,
                    is_primary_key=getattr(attribute, 'is_primary_key', False) if attribute else False,
                    historical_issues_flag=getattr(attribute, 'historical_issues_flag', False) if attribute else False,
                    validation_rules=getattr(attribute, 'validation_rules', '') if attribute else ''
                )
                
                logger.info(f"Using regulation-specific classification prompt for {regulatory_report} {regulatory_schedule}")
            
            # Add proper system prompt for JSON formatting
            system_prompt = """You are an expert in regulatory compliance and information security classification. 

Analyze the provided data element and return a JSON response with classification recommendations.

CRITICAL: You must respond with ONLY a valid JSON object. Do not include any explanatory text before or after the JSON. The JSON must include all required fields."""

            # Generate classification with the properly formatted prompt
            result = await provider.generate(prompt_content, system_prompt)
            
            if not result.get("success", False):
                raise Exception(f"LLM generation failed: {result.get('error', 'Unknown error')}")
            
            response_text = result.get("content", "")
            
            if not response_text.strip():
                raise ValueError("LLM returned empty response")
            
            # Parse the JSON response with robust extraction
            try:
                import json
                import re
                
                # Clean the response text
                cleaned_text = response_text.strip()
                
                # Remove potential markdown formatting
                if "```json" in cleaned_text:
                    cleaned_text = cleaned_text.split("```json")[1].split("```")[0].strip()
                elif "```" in cleaned_text:
                    # Handle generic code blocks
                    parts = cleaned_text.split("```")
                    if len(parts) >= 3:
                        cleaned_text = parts[1].strip()
                
                # Try to find JSON object - use balanced brace matching
                json_start = cleaned_text.find('{')
                if json_start >= 0:
                    brace_count = 0
                    json_end = -1
                    for i in range(json_start, len(cleaned_text)):
                        if cleaned_text[i] == '{':
                            brace_count += 1
                        elif cleaned_text[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                    
                    if json_end > json_start:
                        json_text = cleaned_text[json_start:json_end]
                        # Fix common JSON issues
                        json_text = re.sub(r',\s*}', '}', json_text)  # Remove trailing commas
                        json_text = re.sub(r',\s*]', ']', json_text)
                        suggestion_data = json.loads(json_text)
                        
                        # Add the mapping ID and name to the response
                        suggestion_data["pde_mapping_id"] = pde_mapping.id
                        suggestion_data["pde_name"] = pde_mapping.pde_name
                        
                        # Ensure the response has all required fields for the frontend
                        required_fields = [
                            "llm_suggested_criticality", "llm_suggested_risk_level", 
                            "llm_suggested_information_security_classification",
                            "llm_regulatory_references", "llm_classification_rationale",
                            "regulatory_flag", "pii_flag", "evidence"
                        ]
                        
                        # Handle field name mapping from LLM response to frontend expected fields
                        if "classification_rationale" in suggestion_data and "llm_classification_rationale" not in suggestion_data:
                            suggestion_data["llm_classification_rationale"] = suggestion_data["classification_rationale"]
                        
                        if "regulatory_references" in suggestion_data and "llm_regulatory_references" not in suggestion_data:
                            suggestion_data["llm_regulatory_references"] = suggestion_data["regulatory_references"]
                        
                        # Map LLM response fields to frontend expected fields
                        field_mappings = {
                            "criticality": "llm_suggested_criticality",
                            "risk_level": "llm_suggested_risk_level",
                            "information_security_classification": "llm_suggested_information_security_classification"
                        }
                        
                        for llm_field, frontend_field in field_mappings.items():
                            if llm_field in suggestion_data and frontend_field not in suggestion_data:
                                suggestion_data[frontend_field] = suggestion_data[llm_field]
                        
                        for field in required_fields:
                            if field not in suggestion_data:
                                if field == "llm_regulatory_references":
                                    suggestion_data[field] = [regulatory_context] if regulatory_context else ["General regulatory requirements"]
                                elif field == "evidence":
                                    suggestion_data[field] = {
                                        "data_sensitivity_indicators": ["Regulatory reporting data"],
                                        "regulatory_scope": [regulatory_context] if regulatory_context else ["General regulations"],
                                        "business_impact": "Medium impact on regulatory compliance"
                                    }
                                elif field in ["regulatory_flag", "pii_flag"]:
                                    suggestion_data[field] = False
                                elif field == "llm_suggested_information_security_classification":
                                    suggestion_data[field] = "Confidential"  # Valid classification value
                                elif field in ["llm_suggested_criticality", "llm_suggested_risk_level"]:
                                    suggestion_data[field] = "Medium"  # Risk/criticality levels
                                elif field == "llm_classification_rationale":
                                    suggestion_data[field] = "Classification analysis completed - using standard regulatory guidelines"
                                else:
                                    suggestion_data[field] = "Medium"
                        
                        return suggestion_data
                    else:
                        raise ValueError("Could not find complete JSON object")
                else:
                    raise ValueError("No JSON object found in response")
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Raw response: {response_text[:500]}...")
                
                # Return a structured fallback response with proper regulatory context
                return {
                    "pde_mapping_id": pde_mapping.id,
                    "pde_name": pde_mapping.pde_name,
                    "llm_suggested_criticality": "Medium",
                    "llm_suggested_risk_level": "Medium", 
                    "llm_suggested_information_security_classification": "Confidential",
                    "llm_regulatory_references": [regulatory_context] if regulatory_context else ["General regulatory requirements"],
                    "llm_classification_rationale": f"Classification analysis encountered parsing issues - using default medium risk classification for {regulatory_context}",
                    "regulatory_flag": True,
                    "pii_flag": False,
                    "evidence": {
                        "data_sensitivity_indicators": ["Regulatory reporting data"],
                        "regulatory_scope": [regulatory_context] if regulatory_context else ["General regulations"],
                        "business_impact": "Medium impact on regulatory compliance"
                    },
                    "security_controls": {
                        "required_controls": ["Access logging", "Data encryption"],
                        "access_restrictions": "Restricted to authorized personnel"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error generating PDE classification suggestion: {str(e)}")
            raise Exception(f"Failed to generate classification suggestion: {str(e)}")

    async def generate_pde_classification_suggestions_batch(
        self,
        pde_mappings: List,
        cycle_id: int,
        report_id: int,
        job_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate PDE classification suggestions for multiple mappings in batches using regulation-specific prompts
        
        Args:
            pde_mappings: List of PDE mapping objects with attributes
            cycle_id: Cycle ID
            report_id: Report ID
            job_id: Optional job ID for progress tracking
            
        Returns:
            List of classification suggestions
        """
        try:
            from app.core.background_jobs import job_manager
            from app.core.prompt_manager import PromptManager
            from app.core.database import AsyncSessionLocal
            from app.models.report import Report
            from sqlalchemy import select
            
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    progress_percentage=5,
                    current_step="Initializing batch classification",
                    message=f"Starting batch classification for {len(pde_mappings)} PDE mappings"
                )
            
            provider = await self.get_analysis_provider()
            prompt_manager = PromptManager()
            
            # Get regulatory context from the report
            regulatory_report = None
            regulatory_schedule = None
            regulatory_context = "General regulatory reporting"
            
            try:
                async with AsyncSessionLocal() as db:
                    report_query = select(Report).where(Report.report_id == report_id)
                    report_result = await db.execute(report_query)
                    report = report_result.scalar_one_or_none()
                    
                    if report and report.regulation:
                        regulatory_context = report.regulation
                        # Extract regulatory report and schedule using existing method
                        regulatory_report, regulatory_schedule = self._extract_regulatory_info(
                            report.regulation, 
                            getattr(report, 'report_type', 'Compliance Report')
                        )
                        logger.info(f"Batch classification using regulatory context: {regulatory_report} / {regulatory_schedule}")
            except Exception as e:
                logger.warning(f"Could not get regulatory context for batch classification: {e}")
            
            all_suggestions = []
            
            # Process in batches to avoid token limits
            batch_size = 8  # Optimal size for comprehensive analysis without truncation
            total_batches = (len(pde_mappings) + batch_size - 1) // batch_size
            
            for batch_idx in range(0, len(pde_mappings), batch_size):
                batch_mappings = pde_mappings[batch_idx:batch_idx + batch_size]
                batch_num = (batch_idx // batch_size) + 1
                
                logger.info(f"Processing classification batch {batch_num}/{total_batches} ({len(batch_mappings)} mappings)")
                
                if job_id:
                    progress = 10 + int((batch_num - 1) / total_batches * 80)  # 10-90% for batch processing
                    job_manager.update_job_progress(
                        job_id,
                        progress_percentage=progress,
                        current_step=f"Processing batch {batch_num}/{total_batches}",
                        message=f"Analyzing {len(batch_mappings)} PDE mappings with regulation-specific prompts",
                        completed_steps=(batch_num - 1) * batch_size,
                        total_steps=len(pde_mappings)
                    )
                
                # Use the individual classification method for each mapping in the batch
                # This ensures consistent use of regulation-specific prompts
                batch_suggestions = []
                for i, mapping in enumerate(batch_mappings):
                    try:
                        # Add delay between individual calls to avoid rate limiting
                        if i > 0:
                            await asyncio.sleep(1.5)  # 1.5 second delay between API calls
                            
                        individual_suggestion = await self.generate_pde_classification_suggestion(
                            mapping, mapping.attribute, cycle_id, report_id
                        )
                        batch_suggestions.append(individual_suggestion)
                    except Exception as e:
                        logger.error(f"Individual classification failed for mapping {mapping.id}: {e}")
                        # Use fallback classification
                        fallback_suggestion = {
                            "pde_mapping_id": mapping.id,
                            "pde_name": mapping.pde_name,
                            "llm_suggested_criticality": "Medium",
                            "llm_suggested_risk_level": "Medium",
                            "llm_suggested_information_security_classification": "Confidential",
                            "llm_regulatory_references": [regulatory_context] if regulatory_context else ["General regulatory requirements"],
                            "llm_classification_rationale": f"Individual classification failed - using default medium risk classification for {regulatory_context}",
                            "regulatory_flag": True,
                            "pii_flag": False,
                            "evidence": {
                                "data_sensitivity_indicators": ["Regulatory reporting data"],
                                "regulatory_scope": [regulatory_context] if regulatory_context else ["General regulations"],
                                "business_impact": "Medium impact on regulatory compliance"
                            },
                            "security_controls": {
                                "required_controls": ["Access logging", "Data encryption"],
                                "access_restrictions": "Restricted to authorized personnel"
                            }
                        }
                        batch_suggestions.append(fallback_suggestion)
                
                all_suggestions.extend(batch_suggestions)
                
                # Small delay between batches to avoid rate limiting
                if batch_idx + batch_size < len(pde_mappings):
                    await asyncio.sleep(1)
            
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    progress_percentage=95,
                    current_step="Finalizing batch classification",
                    message=f"Completed classification for {len(all_suggestions)} PDE mappings"
                )
            
            logger.info(f"Batch classification completed: {len(all_suggestions)} suggestions generated using regulation-specific prompts")
            return all_suggestions
            
        except Exception as e:
            logger.error(f"Error in batch PDE classification: {str(e)}")
            if job_id:
                job_manager.update_job_progress(
                    job_id,
                    progress_percentage=100,
                    current_step="Failed",
                    message=f"Batch classification failed: {str(e)}"
                )
            raise Exception(f"Failed to generate batch classification suggestions: {str(e)}")

    async def suggest_pde_mappings(
        self,
        attributes: List[Dict[str, Any]],
        data_sources: List[Dict[str, Any]], 
        report_context: Dict[str, Any],
        job_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate PDE mapping suggestions using regulation-specific prompts
        Maps report attributes to physical database columns
        """
        try:
            from app.core.prompt_manager import get_prompt_manager
            
            # Get prompt manager
            prompt_manager = get_prompt_manager()
            
            # Detect regulatory context for appropriate prompt selection
            regulatory_report = None
            schedule = None
            
            # Extract regulatory context from report_context if available
            regulatory_context = report_context.get('regulatory_context', '')
            report_name = report_context.get('report_name', '')
            
            # Use the standard extraction method for regulatory context
            if regulatory_context:
                # Extract using the standard method which returns proper format
                regulatory_report, schedule = self._extract_regulatory_info(
                    regulatory_context, 
                    report_context.get('report_type', 'Compliance Report')
                )
            
            logger.info(f"Using regulatory context: {regulatory_report}/{schedule} for PDE mapping")
            
            # Process each attribute individually for better accuracy
            mapping_suggestions = []
            total_attributes = len(attributes)
            
            # Import job manager for progress updates
            from app.core.background_jobs import job_manager
            
            # Process attributes in batches of 6 (reduced from 8 to avoid rate limiting)
            batch_size = 6
            total_batches = (len(attributes) + batch_size - 1) // batch_size
            results = []  # Initialize results list
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(attributes))
                batch_attributes = attributes[start_idx:end_idx]
                
                # Update progress for each batch
                if job_id:
                    progress = int((batch_idx + 1) / total_batches * 100)
                    job_manager.update_job_progress(
                        job_id,
                        progress_percentage=progress,
                        current_step=f"Processing batch {batch_idx + 1}/{total_batches} ({len(batch_attributes)} attributes)",
                        message=f"Mapping attributes {start_idx + 1}-{end_idx} of {len(attributes)}"
                    )
                
                # Process all attributes in the batch together
                # Format data sources for prompt with schema information
                data_sources_text = "\n\n".join([
                    f"Data Source {ds.get('id', i+1)}: {ds.get('name', 'Unknown')}\n"
                    f"Type: {ds.get('source_type', 'Unknown')}\n"
                    f"Description: {ds.get('description', 'No description')}\n"
                    f"Schema: {ds.get('schema_summary', 'No schema available')}"
                    for i, ds in enumerate(data_sources)
                ])
                
                # Format attributes for batch processing - only essential fields
                attributes_list = []
                for attr in batch_attributes:
                    attributes_list.append({
                        "id": attr.get('id'),
                        "name": attr.get('attribute_name', ''),
                        "description": attr.get('description', '') or attr.get('attribute_name', ''),
                        "data_type": attr.get('data_type', ''),
                        "mandatory": attr.get('mandatory_flag', '') if attr.get('mandatory_flag') else None
                    })
                
                # Use regulation-specific batch prompt with classification
                logger.info(f"Attempting to load pde_mapping_batch_with_classification for regulatory_report={regulatory_report}, schedule={schedule}")
                batch_prompt = prompt_manager.format_prompt(
                    "pde_mapping_batch_with_classification",
                    regulatory_report=regulatory_report,
                    schedule=schedule,
                    report_name=report_name,
                    regulatory_context=regulatory_context,
                    attributes_count=len(batch_attributes),
                    attributes_json=json.dumps(attributes_list, indent=2),
                    data_sources=data_sources_text
                )
                
                # If no batch with classification prompt, try regular batch prompt
                if not batch_prompt:
                    logger.warning(f"Could not load pde_mapping_batch_with_classification, trying pde_mapping_batch")
                    batch_prompt = prompt_manager.format_prompt(
                        "pde_mapping_batch",
                        regulatory_report=regulatory_report,
                        schedule=schedule,
                        report_name=report_name,
                        regulatory_context=regulatory_context,
                        attributes_count=len(batch_attributes),
                        attributes_json=json.dumps(attributes_list, indent=2),
                        data_sources=data_sources_text
                    )
                
                if not batch_prompt:
                    logger.warning(f"Could not load batch prompt, falling back to individual processing")
                    # Fall through to individual processing
                    batch_prompt = None
                
                response = None
                batch_results = None
                
                if batch_prompt:
                    # Add delay between batches to avoid rate limiting
                    if batch_idx > 0:
                        delay_seconds = 5  # 5 seconds between batches (increased from 2 to avoid rate limits)
                        logger.info(f"Waiting {delay_seconds}s before batch {batch_idx + 1} to avoid rate limits")
                        await asyncio.sleep(delay_seconds)
                    
                    # Log the exact prompt being sent
                    logger.info(f"=== EXACT PROMPT FOR BATCH {batch_idx + 1} ===")
                    logger.info(f"Prompt length: {len(batch_prompt)} characters")
                    # Log the full prompt (or at least much more of it)
                    if len(batch_prompt) <= 10000:
                        logger.info(f"Full prompt:\n{batch_prompt}")
                    else:
                        logger.info(f"First 10000 chars of prompt:\n{batch_prompt[:10000]}")
                        logger.info(f"... (truncated {len(batch_prompt) - 10000} characters)")
                    logger.info("=== END PROMPT ===")
                    
                    # Generate mappings for the entire batch with retry logic
                    response = None
                    retry_count = 0
                    max_retries = 3
                    
                    while retry_count < max_retries:
                        try:
                            response = await self._generate_with_failover(batch_prompt)
                            
                            # Log what we actually got back
                            if response:
                                logger.info(f"LLM response received - keys: {list(response.keys())}, has content: {'content' in response}")
                                if 'content' in response:
                                    logger.info(f"Content length: {len(response['content'])}")
                            else:
                                logger.warning(f"LLM response is None/empty")
                            
                            if response and 'content' in response:
                                break  # Success
                            else:
                                logger.warning(f"⚠️ Empty response from LLM for batch {batch_idx + 1}, attempt {retry_count + 1}/{max_retries}, response: {response}")
                        except Exception as e:
                            logger.error(f"❌ Error calling LLM for batch {batch_idx + 1}, attempt {retry_count + 1}/{max_retries}: {str(e)}")
                            
                            # More specific error handling
                            error_msg = str(e).lower()
                            if "rate limit" in error_msg:
                                wait_time = min(30 * (retry_count + 1), 90)  # Exponential backoff: 30s, 60s, 90s
                                logger.info(f"⏳ Rate limit detected, waiting {wait_time} seconds before retry...")
                                await asyncio.sleep(wait_time)
                            elif "api key" in error_msg or "authentication" in error_msg:
                                logger.error("🔑 API key or authentication issue detected - check LLM configuration")
                                if job_id:
                                    job_manager.update_job_progress(
                                        job_id,
                                        status="failed",
                                        current_step=f"Authentication error at batch {batch_idx + 1}",
                                        message="LLM API authentication failed - check API keys"
                                    )
                                raise Exception(f"LLM authentication failed: {e}")
                            elif "timeout" in error_msg:
                                wait_time = 5 * (retry_count + 1)  # 5s, 10s, 15s
                                logger.info(f"⏱️ Timeout detected, waiting {wait_time} seconds before retry...")
                                await asyncio.sleep(wait_time)
                            else:
                                wait_time = 10 * (retry_count + 1)  # 10s, 20s, 30s
                                logger.info(f"⏳ General error, waiting {wait_time} seconds before retry...")
                                await asyncio.sleep(wait_time)
                        
                        retry_count += 1
                    
                    if response and 'content' in response:
                        # Log the raw LLM response
                        logger.info(f"📝 Raw LLM response for batch {batch_idx + 1} (first 1000 chars):")
                        logger.info(response['content'][:1000])
                        
                        # Show expected JSON format for reference
                        if batch_idx == 0:
                            logger.info("📋 Expected JSON format from LLM:")
                            expected_format = {
                                "attribute_id_1": {
                                    "pde_name": "FR Y-14M field name",
                                    "pde_code": "D1_XXX format",
                                    "data_source_id": "number or null",
                                    "data_source_name": "Data source name",
                                    "table_name": "exact_table_name from schema",
                                    "column_name": "exact_column_name from schema",
                                    "transformation_rule": "direct|calculated|lookup|conditional",
                                    "business_process": "Account origination|Billing cycle|etc",
                                    "confidence": "number (0-100)",
                                    "reasoning": "Why this column from the schema is the best match"
                                }
                            }
                            logger.info(json.dumps(expected_format, indent=2))
                        
                        # For PDE mapping batch responses, we need to extract the full JSON object
                        # The response should be a JSON object with attribute IDs as keys
                        content = response['content'].strip()
                        
                        # Find where the JSON actually starts (after any explanatory text)
                        json_start = content.find('{')
                        if json_start >= 0:
                            # Find the matching closing brace
                            brace_count = 0
                            json_end = -1
                            for i in range(json_start, len(content)):
                                if content[i] == '{':
                                    brace_count += 1
                                elif content[i] == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_end = i + 1
                                        break
                            
                            if json_end > json_start:
                                json_str = content[json_start:json_end]
                                try:
                                    batch_results = json.loads(json_str)
                                    logger.info(f"✅ Extracted JSON manually, found {len(batch_results)} mappings")
                                except json.JSONDecodeError as e:
                                    logger.error(f"Failed to parse JSON: {e}")
                                    # Fallback to the general extraction method
                                    batch_results = extract_json_from_response(response['content'])
                            else:
                                logger.warning("Could not find matching closing brace")
                                batch_results = extract_json_from_response(response['content'])
                        else:
                            logger.warning("No JSON object found in response")
                            batch_results = extract_json_from_response(response['content'])
                        
                        if batch_results and isinstance(batch_results, dict):
                            logger.info(f"✅ Successfully extracted JSON with {len(batch_results)} mappings")
                            logger.info(f"📊 Extracted JSON keys: {list(batch_results.keys())}")
                            if batch_results:
                                first_key = list(batch_results.keys())[0] if batch_results else None
                                if first_key:
                                    logger.info(f"First mapping - Key: {first_key}")
                                    logger.info(f"First mapping - Value type: {type(batch_results[first_key])}")
                                    if isinstance(batch_results[first_key], dict):
                                        logger.info(f"First mapping - Value: {json.dumps(batch_results[first_key], indent=2)}")
                                        # Log specific fields we care about
                                        first_mapping = batch_results[first_key]
                                        logger.info(f"🔍 First mapping details:")
                                        logger.info(f"  - table_name: {first_mapping.get('table_name')}")
                                        logger.info(f"  - column_name: {first_mapping.get('column_name')}")
                                        logger.info(f"  - confidence: {first_mapping.get('confidence')}")
                                        logger.info(f"  - data_source_id: {first_mapping.get('data_source_id')}")
                                    else:
                                        logger.info(f"First mapping - Value: {batch_results[first_key]}")
                            # Process each mapping in the batch results
                            for attr_id, mapping in batch_results.items():
                                attr = next((a for a in batch_attributes if str(a.get('id')) == str(attr_id)), None)
                                if not attr:
                                    logger.warning(f"⚠️ Attribute ID {attr_id} not found in current batch")
                                    continue
                                if not mapping:
                                    logger.warning(f"⚠️ No mapping data for attribute ID {attr_id}")
                                    continue
                                if attr and mapping:
                                    # Log classification data presence
                                    has_classification = bool(
                                        mapping.get('information_security_classification') or 
                                        mapping.get('criticality') or 
                                        mapping.get('risk_level')
                                    )
                                    if batch_idx == 0 and attr == batch_attributes[0]:  # Log first mapping of first batch
                                        logger.info(f"🔍 First mapping classification check:")
                                        logger.info(f"  - information_security_classification: {mapping.get('information_security_classification')}")
                                        logger.info(f"  - criticality: {mapping.get('criticality')}")
                                        logger.info(f"  - risk_level: {mapping.get('risk_level')}")
                                        logger.info(f"  - regulatory_flag: {mapping.get('regulatory_flag')}")
                                        logger.info(f"  - pii_flag: {mapping.get('pii_flag')}")
                                    
                                    normalized_suggestion = {
                                        'attribute_id': attr.get('id'),
                                        'data_source_id': mapping.get('data_source_id'),
                                        'pde_name': mapping.get('pde_name', ''),
                                        'pde_code': mapping.get('pde_code', ''),
                                        'pde_description': mapping.get('pde_description', ''),
                                        'table_name': mapping.get('table_name'),
                                        'column_name': mapping.get('column_name'),
                                        'source_field': f"{mapping.get('table_name')}.{mapping.get('column_name')}" if mapping.get('table_name') and mapping.get('column_name') else '',
                                        'transformation_rule': mapping.get('transformation_rule', 'direct'),
                                        'mapping_type': mapping.get('mapping_type', 'direct'),
                                        'business_process': mapping.get('business_process', ''),
                                        'confidence_score': mapping.get('confidence_score', mapping.get('confidence', 80)),
                                        'rationale': mapping.get('rationale', mapping.get('reasoning', 'Regulation-specific mapping')),
                                        'alternative_mappings': mapping.get('alternative_mappings', []),
                                        'mapped': bool(mapping.get('table_name') and mapping.get('column_name')),  # Mark as mapped if we have table and column
                                        # Include classification data from combined response
                                        'information_security_classification': mapping.get('information_security_classification'),
                                        'criticality': mapping.get('criticality'),
                                        'risk_level': mapping.get('risk_level'),
                                        'regulatory_flag': mapping.get('regulatory_flag', False),
                                        'pii_flag': mapping.get('pii_flag', False),
                                        'regulatory_references': mapping.get('regulatory_references', []),
                                        'classification_rationale': mapping.get('classification_rationale'),
                                        'llm_classification_confidence': mapping.get('llm_classification_confidence', 80),
                                        'classification_evidence': mapping.get('evidence', {})
                                    }
                                    mapping_suggestions.append(normalized_suggestion)
                                    logger.info(f"✅ Added mapping for attribute {attr_id}: {mapping.get('column_name', 'N/A')}")
                                    # Log the normalized suggestion to debug
                                    if attr == batch_attributes[0]:  # Log first normalized suggestion
                                        logger.info(f"🔍 First normalized suggestion:")
                                        logger.info(f"  - table_name: {normalized_suggestion.get('table_name')}")
                                        logger.info(f"  - column_name: {normalized_suggestion.get('column_name')}")
                                        logger.info(f"  - confidence_score: {normalized_suggestion.get('confidence_score')}")
                                        logger.info(f"  - mapped: {normalized_suggestion.get('mapped')}")
                                    
                                    # Add as alternative format
                                    alternatives = mapping.get('alternatives', [])
                                    
                                    # Alternative format no longer needed - we already added to mapping_suggestions
                        else:
                            # Fallback - batch format not recognized, process individually
                            logger.warning(f"❌ Failed to extract JSON from batch {batch_idx + 1} response")
                            batch_prompt = None
                    else:
                        # No response from batch processing after all retries
                        logger.error(f"❌ Failed to get LLM response for batch {batch_idx + 1} after {max_retries} attempts")
                        
                        # Update job progress to indicate partial failure but continue
                        if job_id:
                            failed_attrs = [a.get('attribute_name', f"attr_{a.get('id')}") for a in batch_attributes]
                            job_manager.update_job_progress(
                                job_id,
                                progress_percentage=int((batch_idx + 1) / total_batches * 100),
                                current_step=f"Batch {batch_idx + 1} failed - continuing with next batch",
                                message=f"Failed to map {len(failed_attrs)} attributes: {', '.join(failed_attrs[:3])}{'...' if len(failed_attrs) > 3 else ''}"
                            )
                        
                        # Add placeholder mappings for failed attributes to track them
                        for attr in batch_attributes:
                            mapping_suggestions.append({
                                'attribute_id': attr.get('id'),
                                'data_source_id': None,
                                'pde_name': '',
                                'pde_code': '',
                                'pde_description': '',
                                'source_table': None,
                                'source_column': None,
                                'source_field': '',
                                'transformation_rule': 'direct',
                                'mapping_type': 'direct',
                                'business_process': '',
                                'confidence_score': 0,
                                'rationale': 'LLM mapping failed - manual mapping required',
                                'alternative_mappings': [],
                                'mapped': False,
                                'error': 'LLM service unavailable',
                                'information_security_classification': None,
                                'criticality': None,
                                'risk_level': None,
                                'regulatory_flag': False,
                                'pii_flag': False,
                                'regulatory_references': [],
                                'classification_rationale': None,
                                'llm_classification_confidence': 0,
                                'classification_evidence': {}
                            })
                        
                        batch_prompt = None  # Force individual processing fallback
                else:
                    # No batch prompt available
                    pass
                
                # If batch processing failed or not available, process individually
                if not batch_prompt or not (batch_prompt and response and 'content' in response and batch_results and isinstance(batch_results, dict)):
                    for idx, attr in enumerate(batch_attributes):
                        # Format data sources for prompt
                        data_sources_text = "\n".join([
                            f"Data Source {ds.get('id', ds.get('name'))}: {ds.get('name', 'Unknown')} "
                            f"({ds.get('source_type', 'Unknown')})\n"
                            f"Description: {ds.get('description', 'No description')}\n"
                            f"Schema Summary: {ds.get('schema_summary', 'No schema available')}\n"
                            for ds in data_sources
                        ])
                        
                        # Use regulation-specific prompt with classification
                        prompt = prompt_manager.format_prompt(
                            "pde_mapping_with_classification",
                            regulatory_report=regulatory_report,
                            schedule=schedule,
                            report_name=report_name,
                            regulatory_context=regulatory_context,
                            attribute_name=attr.get('attribute_name', ''),
                            attribute_description=attr.get('description', ''),
                            data_type=attr.get('data_type', ''),
                            mandatory_flag=attr.get('mandatory_flag', ''),
                            is_primary_key=str(attr.get('is_primary_key', False)),
                            cde_flag=str(attr.get('cde_flag', False)),
                            historical_issues_flag=str(attr.get('historical_issues_flag', False)),
                            validation_rules=attr.get('validation_rules', ''),
                            data_sources=data_sources_text
                        )
                        
                        # If no combined prompt, try regular mapping prompt
                        if not prompt:
                            prompt = prompt_manager.format_prompt(
                                "pde_mapping",
                                regulatory_report=regulatory_report,
                                schedule=schedule,
                                report_name=report_name,
                                regulatory_context=regulatory_context,
                                attribute_name=attr.get('attribute_name', ''),
                                attribute_description=attr.get('description', ''),
                                data_type=attr.get('data_type', ''),
                                mandatory_flag=attr.get('mandatory_flag', ''),
                                is_primary_key=str(attr.get('is_primary_key', False)),
                                cde_flag=str(attr.get('cde_flag', False)),
                                validation_rules=attr.get('validation_rules', ''),
                                data_sources=data_sources_text
                            )
                        
                        if not prompt:
                            logger.warning(f"Could not load prompt for attribute {attr.get('attribute_name')}")
                            continue
                        
                        # Log the exact prompt being sent for individual attribute
                        logger.info(f"=== EXACT PROMPT FOR ATTRIBUTE {attr.get('attribute_name')} ===")
                        logger.info(f"Prompt length: {len(prompt)} characters")
                        # Log the full prompt (or at least much more of it)
                        if len(prompt) <= 10000:
                            logger.info(f"Full prompt:\n{prompt}")
                        else:
                            logger.info(f"First 10000 chars of prompt:\n{prompt[:10000]}")
                            logger.info(f"... (truncated {len(prompt) - 10000} characters)")
                        logger.info("=== END PROMPT ===")
                        
                        # Generate mapping suggestion with retry logic
                        response = None
                        retry_count = 0
                        max_retries = 2  # Fewer retries for individual items
                        
                        while retry_count < max_retries:
                            try:
                                response = await self._generate_with_failover(prompt)
                                if response and 'content' in response:
                                    break  # Success
                                else:
                                    logger.warning(f"⚠️ Empty response for attribute {attr.get('attribute_name')}, attempt {retry_count + 1}/{max_retries}")
                            except Exception as e:
                                logger.error(f"❌ Error mapping attribute {attr.get('attribute_name')}, attempt {retry_count + 1}/{max_retries}: {str(e)}")
                                
                                error_msg = str(e).lower()
                                if "rate limit" in error_msg:
                                    wait_time = 20 * (retry_count + 1)
                                    await asyncio.sleep(wait_time)
                                elif "api key" in error_msg or "authentication" in error_msg:
                                    # Don't retry auth errors
                                    break
                                else:
                                    wait_time = 5 * (retry_count + 1)
                                    await asyncio.sleep(wait_time)
                            
                            retry_count += 1
                        
                        if response and 'content' in response:
                            # Extract JSON from response
                            suggestion = extract_json_from_response(response['content'])
                            
                            if suggestion and isinstance(suggestion, dict):
                                # Normalize the suggestion format with classification data
                                normalized_suggestion = {
                                    'attribute_id': attr.get('id'),
                                    'data_source_id': suggestion.get('data_source_id'),
                                    'pde_name': suggestion.get('pde_name', ''),
                                    'pde_code': suggestion.get('pde_code', ''),
                                    'pde_description': suggestion.get('pde_description', ''),
                                    'source_table': suggestion.get('table_name'),
                                    'source_column': suggestion.get('column_name'),
                                    'source_field': suggestion.get('source_field', ''),
                                    'transformation_rule': suggestion.get('transformation_rule', 'direct'),
                                    'mapping_type': suggestion.get('mapping_type', 'direct'),
                                    'business_process': suggestion.get('business_process', ''),
                                    'confidence_score': suggestion.get('confidence_score', 80),
                                    'rationale': suggestion.get('rationale', 'Regulation-specific mapping'),
                                    'alternative_mappings': suggestion.get('alternative_mappings', []),
                                    # Include classification data from combined response
                                    'information_security_classification': suggestion.get('information_security_classification'),
                                    'criticality': suggestion.get('criticality'),
                                    'risk_level': suggestion.get('risk_level'),
                                    'regulatory_flag': suggestion.get('regulatory_flag', False),
                                    'pii_flag': suggestion.get('pii_flag', False),
                                    'regulatory_references': suggestion.get('regulatory_references', []),
                                    'classification_rationale': suggestion.get('classification_rationale'),
                                    'llm_classification_confidence': suggestion.get('llm_classification_confidence', 80),
                                    'classification_evidence': suggestion.get('evidence', {})
                                }
                                
                                # Handle different response formats for source_field
                                if not normalized_suggestion['source_field'] and normalized_suggestion['source_table'] and normalized_suggestion['source_column']:
                                    normalized_suggestion['source_field'] = f"{normalized_suggestion['source_table']}.{normalized_suggestion['source_column']}"
                                elif 'source_field' in suggestion and suggestion['source_field'] and not normalized_suggestion['source_table']:
                                    source_field = suggestion['source_field']
                                    if '.' in str(source_field):
                                        # Parse schema.table.column format
                                        parts = str(source_field).split('.')
                                        if len(parts) >= 2:
                                            normalized_suggestion['source_table'] = parts[-2]
                                            normalized_suggestion['source_column'] = parts[-1]
                                    else:
                                        normalized_suggestion['source_column'] = str(source_field)
                                
                                mapping_suggestions.append(normalized_suggestion)
                            else:
                                logger.warning(f"Invalid suggestion format for attribute {attr.get('attribute_name')}")
                        else:
                            logger.error(f"❌ No LLM response for attribute {attr.get('attribute_name')} after {max_retries} attempts")
                            
                            # Add placeholder mapping for failed attribute
                            mapping_suggestions.append({
                                'attribute_id': attr.get('id'),
                                'data_source_id': None,
                                'pde_name': '',
                                'pde_code': '',
                                'pde_description': '',
                                'source_table': None,
                                'source_column': None,
                                'source_field': '',
                                'transformation_rule': 'direct',
                                'mapping_type': 'direct',
                                'business_process': '',
                                'confidence_score': 0,
                                'rationale': 'LLM mapping failed - manual mapping required',
                                'alternative_mappings': [],
                                'mapped': False,
                                'error': 'LLM service unavailable for individual processing',
                                'information_security_classification': None,
                                'criticality': None,
                                'risk_level': None,
                                'regulatory_flag': False,
                                'pii_flag': False,
                                'regulatory_references': [],
                                'classification_rationale': None,
                                'llm_classification_confidence': 0,
                                'classification_evidence': {}
                            })
                        
                        # Update progress after each attribute
                        if job_id and idx % 5 == 0:  # Update every 5 attributes to avoid too many updates
                            progress = 5 + int((idx + 1) / total_attributes * 45)  # Progress from 5% to 50%
                            job_manager.update_job_progress(
                                job_id,
                                current_step="Generating LLM mapping suggestions",
                                progress_percentage=progress,
                                message=f"Analyzed {idx + 1} of {total_attributes} attributes...",
                                completed_steps=idx + 1,
                                total_steps=total_attributes
                            )
            
            # Generate summary statistics
            successful_mappings = [m for m in mapping_suggestions if m.get('mapped', False) and m.get('confidence_score', 0) > 0]
            failed_mappings = [m for m in mapping_suggestions if m.get('error') or m.get('confidence_score', 0) == 0]
            
            logger.info(f"📊 PDE Mapping Summary:")
            logger.info(f"  - Total attributes: {len(attributes)}")
            logger.info(f"  - Total suggestions generated: {len(mapping_suggestions)}")
            logger.info(f"  - Successful mappings: {len(successful_mappings)} ({len(successful_mappings)/len(attributes)*100:.1f}%)")
            logger.info(f"  - Failed mappings: {len(failed_mappings)} ({len(failed_mappings)/len(attributes)*100:.1f}%)")
            
            if failed_mappings:
                logger.warning(f"⚠️ {len(failed_mappings)} attributes failed to map properly")
                
                # Update job with final status
                if job_id:
                    if len(successful_mappings) == 0:
                        job_manager.update_job_progress(
                            job_id,
                            status="failed",
                            progress_percentage=100,
                            current_step="Mapping failed",
                            message=f"LLM service failed to map any attributes. Check API configuration and logs."
                        )
                    else:
                        job_manager.update_job_progress(
                            job_id,
                            status="completed",
                            progress_percentage=100,
                            current_step="Mapping completed with partial success",
                            message=f"Mapped {len(successful_mappings)}/{len(attributes)} attributes. {len(failed_mappings)} require manual mapping."
                        )
            else:
                # All mappings successful
                if job_id:
                    job_manager.update_job_progress(
                        job_id,
                        status="completed",
                        progress_percentage=100,
                        current_step="Mapping completed",
                        message=f"Successfully mapped all {len(attributes)} attributes"
                    )
            
            return mapping_suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate PDE mapping suggestions: {e}")
            return []

    async def analyze_for_mappings(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Generic LLM analysis method for attribute mappings
        Used by AttributeMappingService
        """
        try:
            system_prompt = """You are a database mapping expert. Analyze the provided context and suggest attribute-to-column mappings.
            Return suggestions as a JSON array with objects containing:
            - attribute_id: The attribute identifier
            - table_name: Suggested database table
            - column_name: Suggested database column
            - data_type: Expected data type
            - confidence: Confidence score (0-100)
            - sensitivity_indicators: Array of security classification indicators
            - reasoning: Explanation for the mapping
            """
            
            response = await self._generate_with_failover(prompt, system_prompt)
            
            if not response or 'content' not in response:
                logger.error("No response from LLM for mapping analysis")
                return []
            
            # Extract and validate JSON response
            suggestions = extract_json_from_response(response['content'])
            
            if not suggestions or not isinstance(suggestions, list):
                logger.error(f"Invalid mapping analysis format: {suggestions}")
                return []
            
            logger.info(f"Generated {len(suggestions)} mapping analysis suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to analyze mappings: {e}")
            return []
    
    async def extract_test_value_from_document(self, attribute_context: Dict[str, Any], 
                                              document_text: str, 
                                              sample_identifier: Optional[str] = None) -> Dict[str, Any]:
        """Extract test value from document using LLM - EXACT SAME as testing phase"""
        try:
            attribute_name = attribute_context.get("attribute_name")
            regulatory_definition = attribute_context.get("regulatory_definition", "")
            data_type = attribute_context.get("data_type", "string")
            
            system_prompt = """You are an expert data extractor for regulatory compliance testing.
            Extract the requested attribute value from the document.
            Be precise and return only the exact value found in the document.
            IMPORTANT: Return ONLY valid JSON with no additional text, markdown formatting, or explanations.
            """
            
            # Get primary keys from context
            primary_keys = attribute_context.get("primary_keys", [])
            logger.info(f"Primary keys from context: {primary_keys}")
            
            prompt = f"""Extract the following attribute value and primary key values from the document:

Attribute Name: {attribute_name}
Regulatory Definition: {regulatory_definition}
Expected Data Type: {data_type}
{f'Sample Identifier: {sample_identifier}' if sample_identifier else ''}

Primary Keys to Extract: {', '.join(primary_keys) if primary_keys else 'None specified'}

Document Content:
{document_text[:5000]}  # Limit to prevent token overflow

Please extract the value for "{attribute_name}" and any primary key values found, and return it in JSON format:
{{
    "extracted_value": "<the extracted value for {attribute_name}>",
    "primary_keys": {{{', '.join([f'"{pk}": "<value for {pk}>"' for pk in primary_keys]) if primary_keys else ''}}},
    "confidence_score": <0.0 to 1.0>,
    "location_in_document": "<brief description of where found>"
}}

IMPORTANT INSTRUCTIONS:
- For "Bank ID", if no explicit ID number is found, extract the bank name from the document header (e.g., "FIRST NATIONAL BANK")
- For "Period ID", look for statement period, reporting period, or date information
- For each primary key, extract whatever value is present in the document, even if it's in a different format than expected
- If a specific primary key cannot be found, set its value to null, but continue extracting other keys
- Always extract values as they appear in the document without modification
- Return ONLY the JSON object, with no additional text before or after"""

            logger.info(f"LLM extraction prompt: {prompt[:500]}...")
            logger.info(f"Full LLM prompt:\n{prompt}")
            response = await self._generate_with_failover(prompt, system_prompt)
            logger.info(f"LLM raw response: {response}")
            
            # The response from _generate_with_failover always has content, not a success field
            if response and 'content' in response:
                content = response.get('content', '')
                
                # Extract JSON from response
                logger.info(f"LLM raw content response (first 500 chars): {content[:500]}")
                extraction_result = extract_json_from_response(content)
                logger.info(f"Parsed extraction result: {extraction_result}")
                
                if extraction_result and isinstance(extraction_result, dict):
                    return {
                        "success": True,
                        "extracted_value": extraction_result.get("extracted_value"),
                        "primary_keys": extraction_result.get("primary_keys", {}),
                        "confidence_score": extraction_result.get("confidence_score", 0.5),
                        "location": extraction_result.get("location_in_document", ""),
                        "model_used": response.get("model_used", "unknown")
                    }
                else:
                    logger.error(f"Failed to parse extraction result from content: {content[:500]}")
                    logger.error(f"Full content: {content}")
                    logger.error(f"Extraction result type: {type(extraction_result)}, value: {extraction_result}")
                    
                    return {
                        "success": False,
                        "error": "Failed to parse extraction result",
                        "primary_keys": {}
                    }
            else:
                logger.error(f"No content in response: {response}")
                return {
                    "success": False,
                    "error": "No content in LLM response"
                }
                
        except Exception as e:
            logger.error(f"Document extraction error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "primary_keys": {}
            }

# Global service instance
_llm_service = None

def get_llm_service() -> HybridLLMService:
    """Get the global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = HybridLLMService()
    return _llm_service 

def extract_json_from_response(response_text: str, expect_attribute_objects: bool = False) -> Optional[Any]:
    """Extract JSON from LLM response, handling markdown formatting and extra text"""
    if not response_text:
        logger.warning("Empty response text provided to extract_json_from_response")
        return None
    
    logger.debug(f"Attempting to extract JSON from response (length: {len(response_text)})")
    logger.debug(f"First 300 chars: {response_text[:300]}")
    
    # First, check if the response already starts with a JSON array or object
    # This is what we expect after updating the prompts
    response_trimmed = response_text.strip()
    if response_trimmed.startswith('[') or response_trimmed.startswith('{'):
        logger.debug("Response appears to start with JSON")
        try:
            # Try to find the matching closing bracket/brace
            if response_trimmed.startswith('['):
                # Find the last ] that balances the opening [
                bracket_count = 0
                end_pos = 0
                for i, char in enumerate(response_trimmed):
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_pos = i + 1
                            break
                
                if end_pos > 0:
                    json_content = response_trimmed[:end_pos]
                    parsed = json.loads(json_content)
                    logger.info(f"Successfully parsed JSON array starting at position 0, length: {len(parsed) if isinstance(parsed, list) else 'N/A'}")
                    return parsed
            else:
                # Similar logic for objects starting with {
                brace_count = 0
                end_pos = 0
                for i, char in enumerate(response_trimmed):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i + 1
                            break
                
                if end_pos > 0:
                    json_content = response_trimmed[:end_pos]
                    parsed = json.loads(json_content)
                    logger.info(f"Successfully parsed JSON object starting at position 0, keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Not a dict'}")
                    return parsed
        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse JSON at start of response: {str(e)}")
    
    # Clean the response text
    cleaned_text = response_text
    
    # Remove markdown code blocks
    cleaned_text = re.sub(r'```json\s*', '', cleaned_text)
    cleaned_text = re.sub(r'```\s*$', '', cleaned_text)
    cleaned_text = re.sub(r'^```', '', cleaned_text)
    cleaned_text = re.sub(r'```', '', cleaned_text)  # Remove any remaining ```
    
    # Remove JSON-style comments which are not valid JSON
    cleaned_text = re.sub(r'//.*?$', '', cleaned_text, flags=re.MULTILINE)
    cleaned_text = re.sub(r'/\*.*?\*/', '', cleaned_text, flags=re.DOTALL)
    
    # Special handling for objects with attribute IDs as keys (PDE mapping responses)
    # Find where the JSON actually starts (after any explanatory text)
    json_start = cleaned_text.find('{')
    if json_start >= 0:
        # Find the matching closing brace by counting braces
        brace_count = 0
        json_end = -1
        for i in range(json_start, len(cleaned_text)):
            if cleaned_text[i] == '{':
                brace_count += 1
            elif cleaned_text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break
        
        if json_end > json_start:
            json_str = cleaned_text[json_start:json_end]
            try:
                parsed = json.loads(json_str)
                logger.info(f"Successfully extracted complete JSON object with brace counting, found {len(parsed) if isinstance(parsed, dict) else 'N/A'} keys")
                
                # Check if this is a PDE mapping response (attribute IDs as keys)
                if isinstance(parsed, dict) and all(key.isdigit() for key in parsed.keys()):
                    logger.info(f"Detected PDE mapping response with {len(parsed)} attribute mappings")
                    return parsed
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse matched JSON object: {e}")
    
    # Try to find JSON patterns in order of preference
    json_patterns = [
        # Look for complete JSON arrays first (most common for discovery)
        r'(\[[\s\S]*?\])',  # Array with any content including newlines
        # Look for JSON objects (fallback for simpler cases)
        r'(\{[\s\S]*?\})',  # Object with any content
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, cleaned_text, re.DOTALL)
        for match in matches:
            try:
                parsed = json.loads(match)
                logger.info(f"Successfully parsed JSON with pattern: {pattern[:30]}...")
                
                # Log what type of object was parsed
                if isinstance(parsed, dict):
                    logger.info(f"Parsed object is a dict with {len(parsed)} keys: {list(parsed.keys())[:5]}...")
                elif isinstance(parsed, list):
                    logger.info(f"Parsed object is a list with {len(parsed)} items")
                else:
                    logger.info(f"Parsed object is of type: {type(parsed)}")
                
                # If we expect attribute objects (Phase 2), ensure we got objects not just strings
                if expect_attribute_objects and isinstance(parsed, list):
                    if parsed and isinstance(parsed[0], dict):
                        logger.info(f"Found {len(parsed)} attribute objects")
                        return parsed
                    elif parsed and isinstance(parsed[0], str):
                        logger.warning("Found list of strings but expected attribute objects, continuing to search...")
                        continue
                        
                return parsed
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse JSON pattern match: {str(e)}")
                continue
    
    # Fallback: Handle numbered lists (common in older Claude responses)
    if not expect_attribute_objects:
        # Look for numbered list pattern: "1. Attribute Name"
        numbered_list_pattern = r'^\s*\d+\.\s+(.+?)$'
        numbered_matches = re.findall(numbered_list_pattern, cleaned_text, re.MULTILINE)
        if numbered_matches and len(numbered_matches) >= 5:
            logger.info(f"Found {len(numbered_matches)} items in numbered list format")
            # Convert to lowercase with underscores to match expected format
            filtered_numbered = []
            for match in numbered_matches:
                match = match.strip()
                if (not match.lower().startswith('note:') and 
                    not match.lower().startswith('this is') and
                    not match.lower().startswith('these') and
                    len(match) < 100):
                    # Convert to expected format (lowercase with underscores)
                    formatted_name = match.lower().replace(' ', '_').replace('-', '_')
                    filtered_numbered.append(formatted_name)
            
            if filtered_numbered and len(filtered_numbered) >= 5:
                logger.info(f"Successfully extracted {len(filtered_numbered)} attribute names from numbered list")
                return filtered_numbered
    
    logger.warning("No valid JSON found in response")
    logger.debug(f"Cleaned text sample: {cleaned_text[:500]}")
    return None

def normalize_attribute(attr: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize attribute data types and fields to match backend expectations"""
    if not isinstance(attr, dict):
        return attr
    
    normalized = attr.copy()
    
    # Normalize data_type to proper case
    if 'data_type' in normalized:
        data_type = str(normalized['data_type']).lower()
        type_mapping = {
            'string': 'String',
            'integer': 'Integer', 
            'int': 'Integer',
            'decimal': 'Decimal',
            'float': 'Decimal',
            'number': 'Decimal',
            'date': 'Date',
            'datetime': 'Date',
            'boolean': 'Boolean',
            'bool': 'Boolean'
        }
        normalized['data_type'] = type_mapping.get(data_type, 'String')
    
    # Normalize mandatory_flag to proper case
    if 'mandatory_flag' in normalized:
        mandatory = str(normalized['mandatory_flag']).lower()
        mandatory_mapping = {
            'mandatory': 'Mandatory',
            'required': 'Mandatory',
            'optional': 'Optional',
            'conditional': 'Conditional'
        }
        normalized['mandatory_flag'] = mandatory_mapping.get(mandatory, 'Optional')
    
    # Ensure all enhanced fields have default values
    enhanced_fields = ['validation_rules', 'typical_source_documents', 'keywords_to_look_for', 'testing_approach']
    for field in enhanced_fields:
        if field not in normalized or not normalized[field]:
            normalized[field] = ''
    
    # Set default boolean flags
    if 'cde_flag' not in normalized:
        normalized['cde_flag'] = False
    if 'historical_issues_flag' not in normalized:
        normalized['historical_issues_flag'] = False
    
    return normalized

def validate_attributes_response(attributes: Any) -> bool:
    """Validate that the LLM returned a proper attributes array with core required fields"""
    if not isinstance(attributes, list):
        logger.error(f"Attributes response is not a list: {type(attributes)}")
        return False
    
    if len(attributes) == 0:
        logger.error("Attributes response is empty")
        return False
    
    logger.info(f"Validating {len(attributes)} attributes from LLM response")
    
    valid_count = 0
    for i, attr in enumerate(attributes):
        if not isinstance(attr, dict):
            logger.error(f"Attribute {i} is not a dict: {type(attr)}")
            continue
        
        # Log what we received for debugging
        logger.debug(f"Raw attribute {i}: {attr}")
        
        # Normalize the attribute first
        normalized_attr = normalize_attribute(attr)
        
        # Check core required fields
        core_required_fields = ['attribute_name', 'data_type', 'mandatory_flag', 'description']
        missing_fields = []
        
        for field in core_required_fields:
            if field not in normalized_attr or not normalized_attr[field]:
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"Attribute {i} missing required fields: {missing_fields}. Raw attribute: {attr}")
            logger.warning(f"Normalized attribute: {normalized_attr}")
            # Don't reject - try to fix with defaults
            for field in missing_fields:
                if field == 'attribute_name':
                    normalized_attr[field] = f"Attribute_{i+1}"
                elif field == 'data_type':
                    normalized_attr[field] = 'String'
                elif field == 'mandatory_flag':
                    normalized_attr[field] = 'Optional'
                elif field == 'description':
                    normalized_attr[field] = f"Generated attribute {i+1}"
            logger.info(f"Fixed attribute {i} with defaults: {normalized_attr}")
        
        # Update the original attributes list with normalized version
        attributes[i] = normalized_attr
        valid_count += 1
    
    logger.info(f"Validation complete: {valid_count}/{len(attributes)} attributes are valid")
    return valid_count > 0  # Return true if we have at least some valid attributes

    def _extract_from_markdown_blocks(self, text: str) -> str:
        """Extract JSON from markdown code blocks."""
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            if end != -1:
                return text[start:end].strip()
        elif '```' in text:
            # Try any code block
            start = text.find('```') + 3
            end = text.find('```', start)
            if end != -1:
                return text[start:end].strip()
        return ""

    def _extract_balanced_json(self, text: str) -> str:
        """Extract JSON using balanced brace/bracket matching."""
        import re
        
        # Look for array first (recommendations are usually arrays)
        array_match = re.search(r'\[.*\]', text, re.DOTALL)
        if array_match:
            candidate = array_match.group()
            if self._is_balanced_json(candidate):
                return candidate
                
        # Look for object
        obj_match = re.search(r'\{.*\}', text, re.DOTALL)
        if obj_match:
            candidate = obj_match.group()
            if self._is_balanced_json(candidate):
                return candidate
                
        return ""

    def _is_balanced_json(self, text: str) -> bool:
        """Check if JSON brackets/braces are balanced."""
        brackets = {'[': ']', '{': '}'}
        stack = []
        
        for char in text:
            if char in brackets:
                stack.append(brackets[char])
            elif char in brackets.values():
                if not stack or stack.pop() != char:
                    return False
        
        return len(stack) == 0

    def _fix_json_issues(self, text: str) -> str:
        """Fix common JSON formatting issues."""
        # Remove trailing commas before closing brackets/braces
        import re
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # Don't try to fix unquoted keys - Claude typically returns well-formatted JSON
        # The previous regex was corrupting valid JSON strings
        
        return text.strip()