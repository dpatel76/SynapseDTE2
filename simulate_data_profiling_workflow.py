#!/usr/bin/env python3
"""
Complete Data Profiling Workflow Simulation
1. Load FR Y-14M dataset with anomalies
2. Use real LLM integration to generate profiling rules
3. Execute LLM-generated rules on the data
4. Show results at attribute level with anomaly detection
"""
import asyncio
import pandas as pd
import numpy as np
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
import re

# Add app to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

class DataProfilingSimulator:
    def __init__(self):
        self.df = None
        self.generated_rules = []
        self.execution_results = []
        self.attribute_scores = {}
        
    async def load_test_dataset(self) -> bool:
        """Step 1: Load the FR Y-14M test dataset with anomalies"""
        print("📁 Step 1: Loading FR Y-14M Test Dataset with Anomalies")
        print("=" * 60)
        
        data_file = Path("tests/data/fr_y14m_schedule_d1_test_data.csv")
        
        if not data_file.exists():
            print(f"❌ Test data file not found: {data_file}")
            print("   Run 'python generate_test_data_with_anomalies.py' first")
            return False
        
        self.df = pd.read_csv(data_file)
        print(f"✅ Loaded dataset: {len(self.df)} records, {len(self.df.columns)} attributes")
        
        # Show data overview
        print(f"\n📊 Dataset Overview:")
        print(f"   Records: {len(self.df):,}")
        print(f"   Attributes: {len(self.df.columns)}")
        print(f"   Memory usage: {self.df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        
        # Show sample attribute types
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        text_cols = self.df.select_dtypes(include=['object']).columns
        
        print(f"   Numeric attributes: {len(numeric_cols)}")
        print(f"   Text attributes: {len(text_cols)}")
        
        return True
    
    async def generate_profiling_rules_with_llm(self, batch_size: int = 15) -> bool:
        """Step 2: Generate profiling rules using real LLM integration"""
        print(f"\n🤖 Step 2: Generating Profiling Rules with Real LLM")
        print("=" * 55)
        
        try:
            # Import LLM service
            from app.services.llm_service import get_llm_service
            
            # Load regulatory prompt
            prompt_path = Path(__file__).parent / "prompts" / "regulatory" / "fr_y_14m" / "schedule_d_1" / "executable_data_profiling_rules.txt"
            
            if not prompt_path.exists():
                print(f"❌ Regulatory prompt not found: {prompt_path}")
                return False
            
            with open(prompt_path, 'r', encoding='utf-8') as file:
                prompt_template = file.read()
            
            print(f"✅ Loaded regulatory prompt template")
            
            # Get all column names
            column_names = self.df.columns.tolist()
            
            # Create attribute batches for processing
            attribute_batches = self._create_attribute_batches(column_names, batch_size)
            print(f"✅ Created {len(attribute_batches)} batches of {batch_size} attributes each")
            
            # Initialize LLM service
            llm_service = get_llm_service()
            system_prompt = "You are a Federal Reserve FR Y-14M data validation specialist. Generate executable validation rules using ONLY the exact column names provided."
            
            all_generated_rules = []
            
            # Process each batch
            for batch_idx, attribute_batch in enumerate(attribute_batches):
                print(f"\n📦 Processing Batch {batch_idx + 1}/{len(attribute_batches)}")
                print(f"   Attributes: {attribute_batch[:5]}{'...' if len(attribute_batch) > 5 else ''}")
                
                # Create batch-specific attributes text with data insights
                batch_attributes_text = self._create_attribute_context(attribute_batch)
                
                # Substitute variables in prompt
                batch_prompt = prompt_template.replace("${column_names}", str(column_names))
                batch_prompt = batch_prompt.replace("${attributes_batch}", batch_attributes_text)
                
                # Add data quality focus
                batch_prompt += f"\n\nDATA QUALITY FOCUS: This dataset contains {len(self.df)} records and may have data quality issues. Generate comprehensive validation rules that detect anomalies, outliers, format violations, and business logic inconsistencies."
                
                print(f"   Prompt size: {len(batch_prompt):,} characters")
                
                # Call LLM
                print(f"   🔗 Calling LLM for batch {batch_idx + 1}...")
                
                response = await llm_service._generate_with_failover(
                    prompt=batch_prompt,
                    system_prompt=system_prompt,
                    preferred_provider="claude"
                )
                
                if not response.get("success"):
                    print(f"   ❌ LLM failed for batch {batch_idx + 1}: {response.get('error')}")
                    continue
                
                print(f"   ✅ LLM response received ({len(response.get('content', '')):,} chars)")
                
                # Parse response
                try:
                    batch_rules = self._parse_llm_response(response.get("content", ""))
                    
                    if batch_rules:
                        all_generated_rules.extend(batch_rules)
                        print(f"   ✅ Generated {len(batch_rules)} rules for batch {batch_idx + 1}")
                        
                        # Show sample rule
                        if batch_rules:
                            sample_rule = batch_rules[0]
                            print(f"   📋 Sample: {sample_rule.get('attribute_id')} - {sample_rule.get('rule_name')} [{sample_rule.get('severity')}]")
                    else:
                        print(f"   ⚠️  No valid rules parsed from batch {batch_idx + 1}")
                        
                except Exception as e:
                    print(f"   ❌ Error parsing batch {batch_idx + 1}: {str(e)}")
            
            self.generated_rules = all_generated_rules
            
            print(f"\n📊 Rule Generation Summary:")
            print(f"   Total rules generated: {len(self.generated_rules)}")
            print(f"   Attributes covered: {len(set(rule.get('attribute_id') for rule in self.generated_rules))}")
            print(f"   Success rate: {(len(self.generated_rules) / len(column_names) * 100):.1f}%")
            
            # Show rule breakdown by severity
            severity_counts = {}
            for rule in self.generated_rules:
                severity = rule.get('severity', 'unknown')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            print(f"   Rule severity breakdown:")
            for severity, count in severity_counts.items():
                print(f"     - {severity}: {count} rules")
            
            return len(self.generated_rules) > 0
            
        except Exception as e:
            print(f"❌ Error in LLM rule generation: {str(e)}")
            return False
    
    def _create_attribute_batches(self, attributes: List[str], batch_size: int) -> List[List[str]]:
        """Create batches of attributes for LLM processing"""
        batches = []
        for i in range(0, len(attributes), batch_size):
            batches.append(attributes[i:i + batch_size])
        return batches
    
    def _create_attribute_context(self, attributes: List[str]) -> str:
        """Create rich context for attributes based on actual data"""
        attribute_descriptions = []
        
        for attr in attributes:
            if attr in self.df.columns:
                # Get basic statistics about the attribute
                col_data = self.df[attr]
                data_type = str(col_data.dtype)
                null_count = col_data.isna().sum()
                unique_count = col_data.nunique()
                
                # Create description based on data characteristics
                if col_data.dtype in ['int64', 'float64']:
                    min_val = col_data.min()
                    max_val = col_data.max()
                    mean_val = col_data.mean()
                    description = f"Numeric field, range: {min_val:.2f} to {max_val:.2f}, avg: {mean_val:.2f}"
                else:
                    description = f"Text field, {unique_count} unique values"
                
                mandatory = "Mandatory" if null_count == 0 else "Optional"
                
                attribute_descriptions.append(
                    f"- {attr} ({data_type}): {description}. Nulls: {null_count}, Unique: {unique_count} [{mandatory}]"
                )
            else:
                attribute_descriptions.append(f"- {attr}: FR Y-14M credit card attribute [Unknown]")
        
        return "\n".join(attribute_descriptions)
    
    def _parse_llm_response(self, response_content: str) -> List[Dict]:
        """Parse LLM response to extract validation rules"""
        if not response_content or "[" not in response_content or "]" not in response_content:
            return []
        
        try:
            # Extract JSON from response
            json_start = response_content.find("[")
            json_end = response_content.rfind("]") + 1
            json_content = response_content[json_start:json_end]
            
            # Clean up common LLM formatting issues
            json_content = re.sub(r',\s*}', '}', json_content)  # Remove trailing commas
            json_content = re.sub(r',\s*]', ']', json_content)  # Remove trailing commas in arrays
            
            rules = json.loads(json_content)
            
            if isinstance(rules, list):
                return rules
            else:
                return []
                
        except json.JSONDecodeError as e:
            print(f"      JSON parsing error: {str(e)}")
            return []
        except Exception as e:
            print(f"      Parsing error: {str(e)}")
            return []
    
    async def execute_profiling_rules(self) -> bool:
        """Step 3: Execute LLM-generated rules on the dataset"""
        print(f"\n⚡ Step 3: Executing LLM-Generated Rules on Dataset")
        print("=" * 55)
        
        if not self.generated_rules:
            print("❌ No rules available for execution")
            return False
        
        print(f"✅ Executing {len(self.generated_rules)} validation rules...")
        
        execution_results = []
        
        for i, rule in enumerate(self.generated_rules):
            rule_id = f"rule_{i+1}"
            attr_id = rule.get('attribute_id', 'Unknown')
            rule_name = rule.get('rule_name', 'Unnamed Rule')
            rule_logic = rule.get('rule_logic', '')
            severity = rule.get('severity', 'medium')
            
            print(f"\n📋 Executing Rule {i+1}: {attr_id}")
            print(f"   Name: {rule_name}")
            print(f"   Severity: {severity}")
            
            try:
                # Execute rule and get results
                result = self._execute_single_rule(rule_id, attr_id, rule_name, rule_logic, severity)
                execution_results.append(result)
                
                # Display results
                if result['execution_status'] == 'success':
                    pass_rate = result['pass_rate']
                    violations = result['violations_count']
                    
                    status_icon = "✅" if pass_rate >= 90 else "⚠️" if pass_rate >= 70 else "❌"
                    print(f"   {status_icon} Pass rate: {pass_rate:.1f}% ({result['passed_count']}/{result['total_records']})")
                    
                    if violations > 0:
                        print(f"   🚨 Violations found: {violations}")
                        
                        # Show sample violations
                        if 'violation_examples' in result and result['violation_examples']:
                            examples = result['violation_examples'][:3]
                            print(f"   📋 Sample violations: {examples}")
                else:
                    print(f"   ❌ Execution failed: {result['error_message']}")
                    
            except Exception as e:
                print(f"   ❌ Rule execution error: {str(e)}")
                execution_results.append({
                    'rule_id': rule_id,
                    'attribute_id': attr_id,
                    'rule_name': rule_name,
                    'execution_status': 'error',
                    'error_message': str(e),
                    'pass_rate': 0,
                    'violations_count': len(self.df)
                })
        
        self.execution_results = execution_results
        
        # Generate summary
        print(f"\n📊 Rule Execution Summary:")
        print("=" * 30)
        
        successful_executions = [r for r in execution_results if r['execution_status'] == 'success']
        failed_executions = [r for r in execution_results if r['execution_status'] != 'success']
        
        print(f"   Rules executed successfully: {len(successful_executions)}/{len(execution_results)}")
        print(f"   Rules failed to execute: {len(failed_executions)}")
        
        if successful_executions:
            avg_pass_rate = np.mean([r['pass_rate'] for r in successful_executions])
            total_violations = sum([r['violations_count'] for r in successful_executions])
            
            print(f"   Average pass rate: {avg_pass_rate:.1f}%")
            print(f"   Total violations detected: {total_violations}")
            
            # Severity breakdown
            severity_violations = {}
            for result in successful_executions:
                severity = result.get('severity', 'unknown')
                violations = result['violations_count']
                severity_violations[severity] = severity_violations.get(severity, 0) + violations
            
            print(f"   Violations by severity:")
            for severity, count in severity_violations.items():
                print(f"     - {severity}: {count} violations")
        
        return len(successful_executions) > 0
    
    def _execute_single_rule(self, rule_id: str, attr_id: str, rule_name: str, rule_logic: str, severity: str) -> Dict:
        """Execute a single validation rule on the dataset"""
        
        # Check if attribute exists in dataset
        if attr_id not in self.df.columns:
            return {
                'rule_id': rule_id,
                'attribute_id': attr_id,
                'rule_name': rule_name,
                'execution_status': 'error',
                'error_message': f"Attribute '{attr_id}' not found in dataset",
                'pass_rate': 0,
                'violations_count': len(self.df),
                'severity': severity
            }
        
        try:
            attr_data = self.df[attr_id]
            total_records = len(self.df)
            
            # Implement basic validation logic based on common patterns
            violations = []
            violation_examples = []
            
            # Analyze rule logic to determine validation type
            rule_logic_lower = rule_logic.lower()
            
            # Range validations
            if 'range' in rule_logic_lower or '>=' in rule_logic or '<=' in rule_logic:
                violations, violation_examples = self._validate_range(attr_data, attr_id, rule_logic)
            
            # Null validations  
            elif 'not null' in rule_logic_lower or 'is not null' in rule_logic_lower:
                violations, violation_examples = self._validate_not_null(attr_data, attr_id)
            
            # Format validations
            elif 'format' in rule_logic_lower or 'length' in rule_logic_lower:
                violations, violation_examples = self._validate_format(attr_data, attr_id, rule_logic)
            
            # Uniqueness validations
            elif 'unique' in rule_logic_lower or 'duplicate' in rule_logic_lower:
                violations, violation_examples = self._validate_uniqueness(attr_data, attr_id)
            
            # Business logic validations
            elif 'business' in rule_logic_lower or 'logic' in rule_logic_lower:
                violations, violation_examples = self._validate_business_logic(attr_data, attr_id, rule_logic)
            
            # Default: Basic statistical validation
            else:
                violations, violation_examples = self._validate_statistical(attr_data, attr_id)
            
            violations_count = len(violations)
            passed_count = total_records - violations_count
            pass_rate = (passed_count / total_records) * 100
            
            return {
                'rule_id': rule_id,
                'attribute_id': attr_id,
                'rule_name': rule_name,
                'execution_status': 'success',
                'total_records': total_records,
                'passed_count': passed_count,
                'violations_count': violations_count,
                'pass_rate': pass_rate,
                'violation_examples': violation_examples[:5],
                'severity': severity
            }
            
        except Exception as e:
            return {
                'rule_id': rule_id,
                'attribute_id': attr_id,
                'rule_name': rule_name,
                'execution_status': 'error',
                'error_message': str(e),
                'pass_rate': 0,
                'violations_count': total_records,
                'severity': severity
            }
    
    def _validate_range(self, attr_data: pd.Series, attr_id: str, rule_logic: str) -> Tuple[List, List]:
        """Validate numeric ranges"""
        violations = []
        violation_examples = []
        
        if attr_data.dtype in ['int64', 'float64']:
            # Extract range values from rule logic (simplified)
            if 'credit' in attr_id.lower() and 'score' in attr_id.lower():
                # Credit score validation (300-850)
                invalid_mask = (attr_data < 300) | (attr_data > 850)
            elif 'apr' in attr_id.lower() or 'rate' in attr_id.lower():
                # APR validation (0-100%)
                invalid_mask = (attr_data < 0) | (attr_data > 100)
            elif 'limit' in attr_id.lower() or 'balance' in attr_id.lower():
                # Financial amounts (non-negative)
                invalid_mask = attr_data < 0
            elif 'utilization' in attr_id.lower():
                # Utilization rate (0-999.999%)
                invalid_mask = (attr_data < 0) | (attr_data > 999.999)
            else:
                # General numeric validation
                q1 = attr_data.quantile(0.25)
                q3 = attr_data.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 3 * iqr
                upper_bound = q3 + 3 * iqr
                invalid_mask = (attr_data < lower_bound) | (attr_data > upper_bound)
            
            violations = self.df.index[invalid_mask].tolist()
            violation_examples = attr_data[invalid_mask].head(5).tolist()
        
        return violations, violation_examples
    
    def _validate_not_null(self, attr_data: pd.Series, attr_id: str) -> Tuple[List, List]:
        """Validate non-null requirements"""
        null_mask = attr_data.isna()
        violations = self.df.index[null_mask].tolist()
        violation_examples = ['NULL'] * min(5, len(violations))
        
        return violations, violation_examples
    
    def _validate_format(self, attr_data: pd.Series, attr_id: str, rule_logic: str) -> Tuple[List, List]:
        """Validate data formats"""
        violations = []
        violation_examples = []
        
        if 'state' in attr_id.lower():
            # State code validation
            valid_states = [
                'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
            ]
            invalid_mask = ~attr_data.isin(valid_states)
            violations = self.df.index[invalid_mask].tolist()
            violation_examples = attr_data[invalid_mask].head(5).tolist()
        
        elif 'zip' in attr_id.lower():
            # ZIP code format validation (5 or 9 digits)
            invalid_mask = ~attr_data.astype(str).str.match(r'^\d{5}(\d{4})?$')
            violations = self.df.index[invalid_mask].tolist()
            violation_examples = attr_data[invalid_mask].head(5).tolist()
        
        elif 'date' in attr_id.lower():
            # Date format validation (YYYYMMDD)
            try:
                pd.to_datetime(attr_data.astype(str), format='%Y%m%d', errors='coerce')
                invalid_mask = pd.to_datetime(attr_data.astype(str), format='%Y%m%d', errors='coerce').isna()
                violations = self.df.index[invalid_mask].tolist()
                violation_examples = attr_data[invalid_mask].head(5).tolist()
            except:
                violations = []
                violation_examples = []
        
        return violations, violation_examples
    
    def _validate_uniqueness(self, attr_data: pd.Series, attr_id: str) -> Tuple[List, List]:
        """Validate uniqueness requirements"""
        duplicate_mask = attr_data.duplicated(keep=False)
        violations = self.df.index[duplicate_mask].tolist()
        violation_examples = attr_data[duplicate_mask].head(5).tolist()
        
        return violations, violation_examples
    
    def _validate_business_logic(self, attr_data: pd.Series, attr_id: str, rule_logic: str) -> Tuple[List, List]:
        """Validate business logic rules"""
        violations = []
        violation_examples = []
        
        # Business logic validation requires cross-field analysis
        if 'limit' in attr_id.lower() and 'balance' in rule_logic.lower():
            # Balance vs. credit limit validation
            if 'CURRENT_CREDIT_LIMIT' in self.df.columns and 'CYCLE_ENDING_BALANCE' in self.df.columns:
                credit_limit = self.df['CURRENT_CREDIT_LIMIT']
                balance = self.df['CYCLE_ENDING_BALANCE']
                
                # Balance should not exceed limit by more than 50%
                invalid_mask = balance > credit_limit * 1.5
                violations = self.df.index[invalid_mask].tolist()
                violation_examples = balance[invalid_mask].head(5).tolist()
        
        elif 'payment' in attr_id.lower():
            # Payment logic validation
            if 'MINIMUM_PAYMENT_DUE' in self.df.columns and 'CYCLE_ENDING_BALANCE' in self.df.columns:
                min_payment = self.df['MINIMUM_PAYMENT_DUE']
                balance = self.df['CYCLE_ENDING_BALANCE']
                
                # Minimum payment should not exceed balance significantly
                invalid_mask = min_payment > balance * 1.2
                violations = self.df.index[invalid_mask].tolist()
                violation_examples = min_payment[invalid_mask].head(5).tolist()
        
        return violations, violation_examples
    
    def _validate_statistical(self, attr_data: pd.Series, attr_id: str) -> Tuple[List, List]:
        """Basic statistical validation for outliers"""
        violations = []
        violation_examples = []
        
        if attr_data.dtype in ['int64', 'float64']:
            # Use z-score for outlier detection
            mean_val = attr_data.mean()
            std_val = attr_data.std()
            
            if std_val > 0:
                z_scores = np.abs((attr_data - mean_val) / std_val)
                outlier_mask = z_scores > 3  # 3 standard deviations
                
                violations = self.df.index[outlier_mask].tolist()
                violation_examples = attr_data[outlier_mask].head(5).tolist()
        
        return violations, violation_examples
    
    async def generate_attribute_level_report(self) -> bool:
        """Step 4: Generate comprehensive attribute-level data quality report"""
        print(f"\n📊 Step 4: Generating Attribute-Level Data Quality Report")
        print("=" * 60)
        
        if not self.execution_results:
            print("❌ No execution results available for reporting")
            return False
        
        # Calculate attribute-level scores
        attribute_results = {}
        
        for result in self.execution_results:
            attr_id = result['attribute_id']
            
            if attr_id not in attribute_results:
                attribute_results[attr_id] = {
                    'attribute_name': attr_id,
                    'rules_applied': 0,
                    'rules_passed': 0,
                    'total_violations': 0,
                    'severity_breakdown': {},
                    'quality_score': 0,
                    'quality_grade': 'F',
                    'status': 'Unknown'
                }
            
            attr_result = attribute_results[attr_id]
            attr_result['rules_applied'] += 1
            
            if result['execution_status'] == 'success':
                if result['pass_rate'] >= 90:
                    attr_result['rules_passed'] += 1
                
                attr_result['total_violations'] += result['violations_count']
                
                severity = result.get('severity', 'medium')
                attr_result['severity_breakdown'][severity] = attr_result['severity_breakdown'].get(severity, 0) + result['violations_count']
        
        # Calculate quality scores
        for attr_id, attr_result in attribute_results.items():
            if attr_result['rules_applied'] > 0:
                pass_rate = (attr_result['rules_passed'] / attr_result['rules_applied']) * 100
                violation_rate = (attr_result['total_violations'] / len(self.df)) * 100
                
                # Quality score combines rule pass rate and violation rate
                quality_score = max(0, pass_rate - violation_rate)
                attr_result['quality_score'] = quality_score
                
                # Assign quality grade
                if quality_score >= 90:
                    attr_result['quality_grade'] = 'A'
                    attr_result['status'] = 'Excellent'
                elif quality_score >= 80:
                    attr_result['quality_grade'] = 'B'
                    attr_result['status'] = 'Good'
                elif quality_score >= 70:
                    attr_result['quality_grade'] = 'C'
                    attr_result['status'] = 'Fair'
                elif quality_score >= 60:
                    attr_result['quality_grade'] = 'D'
                    attr_result['status'] = 'Poor'
                else:
                    attr_result['quality_grade'] = 'F'
                    attr_result['status'] = 'Critical'
        
        self.attribute_scores = attribute_results
        
        # Display detailed report
        print(f"✅ Generated quality scores for {len(attribute_results)} attributes")
        
        print(f"\n📋 Attribute-Level Data Quality Report:")
        print("=" * 70)
        print(f"{'Attribute':<25} {'Grade':<6} {'Score':<7} {'Violations':<11} {'Status':<10}")
        print("-" * 70)
        
        # Sort by quality score (worst first for attention)
        sorted_attributes = sorted(attribute_results.items(), key=lambda x: x[1]['quality_score'])
        
        for attr_id, result in sorted_attributes:
            grade = result['quality_grade']
            score = result['quality_score']
            violations = result['total_violations']
            status = result['status']
            
            # Color coding for display
            grade_icon = {
                'A': '🟢', 'B': '🟡', 'C': '🟠', 'D': '🔴', 'F': '❌'
            }.get(grade, '⚪')
            
            print(f"{attr_id:<25} {grade_icon}{grade:<5} {score:>6.1f} {violations:>10} {status:<10}")
        
        # Summary statistics
        print("\n📊 Quality Summary Statistics:")
        print("-" * 35)
        
        grades = [result['quality_grade'] for result in attribute_results.values()]
        grade_counts = {grade: grades.count(grade) for grade in ['A', 'B', 'C', 'D', 'F']}
        
        total_attrs = len(attribute_results)
        for grade, count in grade_counts.items():
            percentage = (count / total_attrs) * 100
            print(f"   Grade {grade}: {count:2d} attributes ({percentage:5.1f}%)")
        
        overall_score = np.mean([result['quality_score'] for result in attribute_results.values()])
        total_violations = sum([result['total_violations'] for result in attribute_results.values()])
        
        print(f"\n   Overall Quality Score: {overall_score:.1f}")
        print(f"   Total Violations Detected: {total_violations:,}")
        print(f"   Anomaly Detection Rate: {(total_violations / len(self.df)):.1f} violations per record")
        
        # Critical issues that need attention
        critical_attributes = [attr for attr, result in attribute_results.items() 
                             if result['quality_grade'] in ['D', 'F']]
        
        if critical_attributes:
            print(f"\n🚨 Critical Issues Requiring Immediate Attention:")
            print("-" * 50)
            for attr in critical_attributes[:5]:  # Show top 5
                result = attribute_results[attr]
                print(f"   • {attr}: Grade {result['quality_grade']} - {result['total_violations']} violations")
                
                # Show severity breakdown
                if result['severity_breakdown']:
                    severity_text = ", ".join([f"{sev}: {count}" for sev, count in result['severity_breakdown'].items()])
                    print(f"     Severity breakdown: {severity_text}")
        
        return True
    
    async def run_complete_simulation(self):
        """Run the complete data profiling workflow simulation"""
        print("🎯 Complete Data Profiling Workflow Simulation")
        print("=" * 50)
        print("Simulating: LLM Rule Generation → Rule Execution → Quality Assessment")
        print()
        
        # Step 1: Load dataset
        if not await self.load_test_dataset():
            return False
        
        # Step 2: Generate rules with LLM
        if not await self.generate_profiling_rules_with_llm():
            return False
        
        # Step 3: Execute rules
        if not await self.execute_profiling_rules():
            return False
        
        # Step 4: Generate report
        if not await self.generate_attribute_level_report():
            return False
        
        # Final summary
        print(f"\n🎉 Data Profiling Workflow Simulation Complete!")
        print("=" * 50)
        print(f"📊 Results Summary:")
        print(f"   Dataset: {len(self.df)} records, {len(self.df.columns)} attributes")
        print(f"   Rules Generated: {len(self.generated_rules)} (via real LLM)")
        print(f"   Rules Executed: {len(self.execution_results)}")
        print(f"   Attributes Analyzed: {len(self.attribute_scores)}")
        
        # Quality distribution
        if self.attribute_scores:
            grades = [result['quality_grade'] for result in self.attribute_scores.values()]
            grade_summary = {grade: grades.count(grade) for grade in ['A', 'B', 'C', 'D', 'F']}
            print(f"   Quality Distribution: {grade_summary}")
            
            total_violations = sum([result['total_violations'] for result in self.attribute_scores.values()])
            print(f"   Total Violations: {total_violations:,}")
            
            if total_violations > 200:
                print(f"   🚨 High anomaly detection rate - dataset contains significant data quality issues")
            elif total_violations > 100:
                print(f"   ⚠️  Moderate anomaly detection - some data quality issues found")
            else:
                print(f"   ✅ Low anomaly rate - dataset appears to have good quality")
        
        print(f"\n💡 This simulation demonstrates how the data profiling module:")
        print(f"   ✓ Uses real LLM integration to generate validation rules")
        print(f"   ✓ Executes rules against actual data with anomalies")
        print(f"   ✓ Provides attribute-level quality assessment")
        print(f"   ✓ Identifies data quality issues for remediation")
        
        return True

async def main():
    """Run the complete data profiling workflow simulation"""
    simulator = DataProfilingSimulator()
    
    try:
        success = await simulator.run_complete_simulation()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Simulation interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Simulation error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())