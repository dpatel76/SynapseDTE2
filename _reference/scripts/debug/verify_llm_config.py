#!/usr/bin/env python3
"""
Verify LLM Regulation Mapping and Batch Configuration
This script verifies:
1. All regulation mappings have corresponding prompt files
2. Batch sizes are properly configured for each operation
3. Special handling rules are working correctly
4. Prompt templates can be loaded successfully
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.llm_config import (
    LLMConfiguration, LLMProvider, LLMOperation,
    RegulationPromptMapping, get_llm_config
)
from app.core.prompt_manager import PromptManager, get_prompt_manager


def verify_regulation_mappings() -> Tuple[bool, List[str]]:
    """Verify all regulation mappings have corresponding prompt files"""
    errors = []
    prompt_manager = get_prompt_manager()
    
    print("\n=== Verifying Regulation Mappings ===")
    
    for regulation, config in RegulationPromptMapping.REGULATION_MAPPING.items():
        print(f"\nRegulation: {regulation}")
        print(f"  Normalized name: {config['normalized_name']}")
        
        # Check if regulation directory exists
        reg_dir = Path("prompts/regulatory") / config['normalized_name']
        if not reg_dir.exists():
            errors.append(f"Missing directory for {regulation}: {reg_dir}")
            print(f"  ❌ Directory not found: {reg_dir}")
            continue
        else:
            print(f"  ✓ Directory exists: {reg_dir}")
        
        # Check common prompts
        common_dir = reg_dir / config.get('default_prompts', 'common')
        if not common_dir.exists():
            errors.append(f"Missing common prompts directory for {regulation}: {common_dir}")
            print(f"  ❌ Common prompts directory not found: {common_dir}")
        else:
            print(f"  ✓ Common prompts directory exists: {common_dir}")
        
        # Check schedule-specific prompts
        for schedule, schedule_dir in config.get('schedules', {}).items():
            schedule_path = reg_dir / schedule_dir
            if not schedule_path.exists():
                errors.append(f"Missing schedule directory for {regulation} {schedule}: {schedule_path}")
                print(f"  ❌ Schedule directory not found: {schedule} -> {schedule_path}")
            else:
                print(f"  ✓ Schedule directory exists: {schedule} -> {schedule_path}")
                
                # Check for required prompt files
                required_prompts = [
                    'attribute_discovery.txt',
                    'attribute_batch_details.txt',
                    'scoping_recommendations.txt',
                    'testing_approach.txt'
                ]
                
                for prompt_file in required_prompts:
                    prompt_path = schedule_path / prompt_file
                    if not prompt_path.exists():
                        print(f"    ⚠️  Missing prompt file: {prompt_file}")
                    else:
                        print(f"    ✓ Found prompt file: {prompt_file}")
    
    return len(errors) == 0, errors


def verify_batch_configurations() -> Tuple[bool, List[str]]:
    """Verify batch size configurations"""
    errors = []
    config = get_llm_config()
    
    print("\n=== Verifying Batch Configurations ===")
    
    # Test Claude batch sizes
    print("\nClaude Batch Sizes:")
    for operation in LLMOperation:
        try:
            default_size = config.get_batch_size(LLMProvider.CLAUDE, operation, "default")
            speed_size = config.get_batch_size(LLMProvider.CLAUDE, operation, "speed")
            quality_size = config.get_batch_size(LLMProvider.CLAUDE, operation, "quality")
            
            print(f"  {operation.value}:")
            print(f"    Default: {default_size}, Speed: {speed_size}, Quality: {quality_size}")
            
            # Verify constraints
            batch_config = LLMConfiguration.CLAUDE_BATCH_SIZES.get(operation)
            if batch_config:
                if not (batch_config.min_size <= default_size <= batch_config.max_size):
                    errors.append(f"Claude {operation}: default size {default_size} out of bounds")
                if quality_size > speed_size:
                    errors.append(f"Claude {operation}: quality size > speed size")
        except Exception as e:
            errors.append(f"Error getting Claude batch size for {operation}: {str(e)}")
    
    # Test Gemini batch sizes
    print("\nGemini Batch Sizes:")
    for operation in LLMOperation:
        try:
            default_size = config.get_batch_size(LLMProvider.GEMINI, operation, "default")
            speed_size = config.get_batch_size(LLMProvider.GEMINI, operation, "speed")
            quality_size = config.get_batch_size(LLMProvider.GEMINI, operation, "quality")
            
            print(f"  {operation.value}:")
            print(f"    Default: {default_size}, Speed: {speed_size}, Quality: {quality_size}")
            
            # Verify constraints
            batch_config = LLMConfiguration.GEMINI_BATCH_SIZES.get(operation)
            if batch_config:
                if not (batch_config.min_size <= default_size <= batch_config.max_size):
                    errors.append(f"Gemini {operation}: default size {default_size} out of bounds")
                if quality_size > speed_size:
                    errors.append(f"Gemini {operation}: quality size > speed size")
        except Exception as e:
            errors.append(f"Error getting Gemini batch size for {operation}: {str(e)}")
    
    return len(errors) == 0, errors


def verify_prompt_loading() -> Tuple[bool, List[str]]:
    """Verify prompt templates can be loaded"""
    errors = []
    prompt_manager = get_prompt_manager()
    
    print("\n=== Verifying Prompt Loading ===")
    
    # Test loading regulatory prompts
    test_cases = [
        ("FR Y-14M", "Schedule D.1", "attribute_discovery"),
        ("FR Y-14M", "Schedule A.1", "scoping_recommendations"),
        ("FR Y-14Q", None, "attribute_discovery"),
        ("CCAR", "Schedule 1A", "testing_approach"),
        (None, None, "attribute_discovery"),  # Generic prompt
    ]
    
    for regulation, schedule, prompt_type in test_cases:
        try:
            prompt_path = RegulationPromptMapping.get_prompt_path(regulation, schedule, prompt_type)
            print(f"\nTesting: {regulation or 'Generic'} - {schedule or 'Common'} - {prompt_type}")
            print(f"  Expected path: {prompt_path}")
            
            # Try to load the prompt
            template = prompt_manager.load_prompt_template(prompt_type, regulation, schedule)
            if template:
                print(f"  ✓ Prompt loaded successfully")
            else:
                errors.append(f"Failed to load prompt: {regulation} - {schedule} - {prompt_type}")
                print(f"  ❌ Failed to load prompt")
        except Exception as e:
            errors.append(f"Error loading prompt {regulation} - {schedule} - {prompt_type}: {str(e)}")
            print(f"  ❌ Error: {str(e)}")
    
    return len(errors) == 0, errors


def verify_special_handling() -> Tuple[bool, List[str]]:
    """Verify special handling configurations"""
    errors = []
    
    print("\n=== Verifying Special Handling Rules ===")
    
    # Check special handling configurations
    test_cases = [
        ("FR Y-14M", "Schedule D.1"),
        ("FR Y-14M", "Schedule A.1"),
        ("FR Y-14Q", None),
    ]
    
    for regulation, schedule in test_cases:
        special = RegulationPromptMapping.get_special_handling(regulation, schedule)
        print(f"\n{regulation} - {schedule or 'Common'}:")
        if special:
            print(f"  Special handling: {json.dumps(special, indent=4)}")
            
            # Verify special handling rules make sense
            if 'preferred_provider' in special:
                provider = special['preferred_provider']
                if provider not in ['claude', 'gemini']:
                    errors.append(f"Invalid provider in special handling: {provider}")
        else:
            print(f"  No special handling")
    
    return len(errors) == 0, errors


def verify_dynamic_batch_sizing() -> Tuple[bool, List[str]]:
    """Verify dynamic batch sizing logic"""
    errors = []
    config = get_llm_config()
    
    print("\n=== Verifying Dynamic Batch Sizing ===")
    
    test_scenarios = [
        # (provider, operation, input_size, complexity, expected_range)
        (LLMProvider.CLAUDE, LLMOperation.ATTRIBUTE_DISCOVERY, 50, "low", (10, 30)),
        (LLMProvider.CLAUDE, LLMOperation.ATTRIBUTE_DISCOVERY, 500, "medium", (10, 20)),
        (LLMProvider.CLAUDE, LLMOperation.ATTRIBUTE_DISCOVERY, 2000, "high", (5, 15)),
        (LLMProvider.GEMINI, LLMOperation.ATTRIBUTE_DETAILS, 100, "low", (80, 150)),
        (LLMProvider.GEMINI, LLMOperation.ATTRIBUTE_DETAILS, 1500, "high", (40, 80)),
    ]
    
    for provider, operation, input_size, complexity, expected_range in test_scenarios:
        batch_size = config.get_dynamic_batch_size(provider, operation, input_size, complexity)
        print(f"\n{provider.value} - {operation.value}:")
        print(f"  Input size: {input_size}, Complexity: {complexity}")
        print(f"  Dynamic batch size: {batch_size}")
        print(f"  Expected range: {expected_range}")
        
        if not (expected_range[0] <= batch_size <= expected_range[1]):
            errors.append(
                f"Dynamic batch size {batch_size} outside expected range "
                f"{expected_range} for {provider.value} {operation.value}"
            )
            print(f"  ❌ Outside expected range!")
        else:
            print(f"  ✓ Within expected range")
    
    return len(errors) == 0, errors


def main():
    """Run all verification checks"""
    print("LLM Configuration Verification Script")
    print("=" * 50)
    
    all_passed = True
    all_errors = []
    
    # Run all verification checks
    checks = [
        ("Regulation Mappings", verify_regulation_mappings),
        ("Batch Configurations", verify_batch_configurations),
        ("Prompt Loading", verify_prompt_loading),
        ("Special Handling", verify_special_handling),
        ("Dynamic Batch Sizing", verify_dynamic_batch_sizing),
    ]
    
    for check_name, check_func in checks:
        passed, errors = check_func()
        if not passed:
            all_passed = False
            all_errors.extend(errors)
    
    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    
    if all_passed:
        print("✅ All checks passed!")
    else:
        print(f"❌ Found {len(all_errors)} errors:")
        for error in all_errors:
            print(f"  - {error}")
    
    # Recommendations
    print("\n" + "=" * 50)
    print("RECOMMENDATIONS")
    print("=" * 50)
    
    if not all_passed:
        print("1. Fix missing prompt directories and files")
        print("2. Verify batch size configurations are within bounds")
        print("3. Ensure all regulation mappings are correct")
        print("4. Test prompt loading for all regulations")
    else:
        print("1. Consider adding more regulation types as needed")
        print("2. Monitor batch size performance in production")
        print("3. Add unit tests for regulation mapping")
        print("4. Document any new special handling rules")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())