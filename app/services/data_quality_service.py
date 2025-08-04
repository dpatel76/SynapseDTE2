"""
Data Quality Score Calculation Service

This service calculates composite Data Quality scores for attributes
based on profiling rule execution results.
"""

from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.data_profiling import ProfilingResult, ProfilingRule, ProfilingRuleType
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataQualityService:
    """Service for calculating composite Data Quality scores"""
    
    @staticmethod
    def _get_severity_weight(severity: str) -> float:
        """Get weight for rule severity"""
        severity_weights = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
        return severity_weights.get(severity.lower(), 0.6)
    
    @staticmethod
    def _get_rule_type_weight(rule_type: ProfilingRuleType) -> float:
        """Get weight for rule type"""
        type_weights = {
            ProfilingRuleType.COMPLETENESS: 1.0,
            ProfilingRuleType.VALIDITY: 0.9,
            ProfilingRuleType.ACCURACY: 1.0,
            ProfilingRuleType.CONSISTENCY: 0.8,
            ProfilingRuleType.UNIQUENESS: 0.7,
            ProfilingRuleType.REGULATORY: 1.0,
            ProfilingRuleType.TIMELINESS: 0.6
        }
        return type_weights.get(rule_type, 0.8)
    
    @classmethod
    async def calculate_composite_dq_score(
        cls,
        db: AsyncSession,
        cycle_id: int,
        report_id: int,
        attribute_id: int
    ) -> Dict[str, float]:
        """
        Calculate composite Data Quality score for an attribute
        
        Formula: Weighted average of pass rates across all approved rules
        Weight = severity_weight * rule_type_weight
        
        Args:
            db: Database session
            cycle_id: Test cycle ID
            report_id: Report ID  
            attribute_id: Attribute ID
            
        Returns:
            Dict with overall_quality_score, total_rules_executed, etc.
        """
        try:
            # Get profiling phase
            from app.models.workflow import WorkflowPhase
            phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Data Profiling"
                )
            )
            phase_result = await db.execute(phase_query)
            profiling_phase = phase_result.scalar_one_or_none()
            
            if not profiling_phase:
                logger.warning(f"No data profiling phase found for cycle {cycle_id}, report {report_id}")
                return {
                    "overall_quality_score": 0.0,
                    "total_rules_executed": 0,
                    "rules_passed": 0,
                    "rules_failed": 0,
                    "has_profiling_data": False
                }
            
            # Get all successful profiling results for this attribute
            results_query = select(ProfilingResult, ProfilingRule).join(
                ProfilingRule, ProfilingResult.rule_id == ProfilingRule.rule_id
            ).where(
                and_(
                    ProfilingResult.phase_id == profiling_phase.phase_id,
                    ProfilingResult.attribute_id == attribute_id,
                    ProfilingResult.execution_status == "success",
                    ProfilingRule.status == "APPROVED"  # Only use approved rules
                )
            )
            
            results = await db.execute(results_query)
            result_pairs = results.all()
            
            if not result_pairs:
                logger.info(f"No profiling results found for attribute {attribute_id}")
                return {
                    "overall_quality_score": 0.0,
                    "total_rules_executed": 0,
                    "rules_passed": 0,
                    "rules_failed": 0,
                    "has_profiling_data": False
                }
            
            # Calculate weighted composite score
            total_weighted_score = 0.0
            total_weight = 0.0
            rules_passed = 0
            rules_failed = 0
            
            # Track dimension scores for detailed breakdown
            dimension_scores = {
                ProfilingRuleType.COMPLETENESS: [],
                ProfilingRuleType.VALIDITY: [],
                ProfilingRuleType.ACCURACY: [],
                ProfilingRuleType.CONSISTENCY: [],
                ProfilingRuleType.UNIQUENESS: [],
                ProfilingRuleType.REGULATORY: [],
                ProfilingRuleType.TIMELINESS: []
            }
            
            for profiling_result, profiling_rule in result_pairs:
                # Calculate weights
                severity_weight = cls._get_severity_weight(profiling_result.severity or "medium")
                rule_type_weight = cls._get_rule_type_weight(profiling_rule.rule_type)
                total_rule_weight = severity_weight * rule_type_weight
                
                # Add to weighted score calculation
                rule_pass_rate = profiling_result.pass_rate or 0.0
                weighted_score = rule_pass_rate * total_rule_weight
                
                total_weighted_score += weighted_score
                total_weight += total_rule_weight
                
                # Track pass/fail by simple threshold
                if rule_pass_rate >= 80.0:  # 80% threshold for "passing"
                    rules_passed += 1
                else:
                    rules_failed += 1
                
                # Add to dimension breakdown
                dimension_scores[profiling_rule.rule_type].append(rule_pass_rate)
                
                logger.debug(f"Rule {profiling_rule.rule_name}: pass_rate={rule_pass_rate}%, "
                           f"severity={profiling_result.severity}, weight={total_rule_weight}")
            
            # Calculate final composite score
            if total_weight > 0:
                overall_quality_score = total_weighted_score / total_weight
            else:
                overall_quality_score = 0.0
            
            # Calculate dimension averages
            dimension_averages = {}
            for rule_type, scores in dimension_scores.items():
                if scores:
                    dimension_averages[f"{rule_type.value}_score"] = sum(scores) / len(scores)
                else:
                    dimension_averages[f"{rule_type.value}_score"] = 0.0
            
            result = {
                "overall_quality_score": round(overall_quality_score, 2),
                "total_rules_executed": len(result_pairs),
                "rules_passed": rules_passed,
                "rules_failed": rules_failed,
                "has_profiling_data": True,
                **dimension_averages
            }
            
            logger.info(f"Calculated DQ score for attribute {attribute_id}: "
                       f"{overall_quality_score:.2f}% ({len(result_pairs)} rules)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating DQ score for attribute {attribute_id}: {str(e)}")
            return {
                "overall_quality_score": 0.0,
                "total_rules_executed": 0,
                "rules_passed": 0,
                "rules_failed": 0,
                "has_profiling_data": False,
                "error": str(e)
            }
    
    @classmethod
    async def calculate_dq_scores_for_all_attributes(
        cls,
        db: AsyncSession,
        cycle_id: int,
        report_id: int,
        attribute_ids: List[int]
    ) -> Dict[int, Dict[str, float]]:
        """
        Calculate DQ scores for multiple attributes efficiently
        
        Args:
            db: Database session
            cycle_id: Test cycle ID
            report_id: Report ID
            attribute_ids: List of attribute IDs
            
        Returns:
            Dict mapping attribute_id to DQ score data
        """
        scores = {}
        
        for attribute_id in attribute_ids:
            score_data = await cls.calculate_composite_dq_score(
                db, cycle_id, report_id, attribute_id
            )
            scores[attribute_id] = score_data
        
        return scores
    
    @classmethod
    async def store_calculated_scores(
        cls,
        db: AsyncSession,
        cycle_id: int,
        report_id: int,
        scores: Dict[int, Dict[str, float]]
    ) -> None:
        """
        Store calculated DQ scores in the AttributeProfilingScore table
        
        Args:
            db: Database session
            cycle_id: Test cycle ID
            report_id: Report ID
            scores: Dict mapping attribute_id to score data
        """
        try:
            # Get profiling phase
            from app.models.workflow import WorkflowPhase
            phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Data Profiling"
                )
            )
            phase_result = await db.execute(phase_query)
            profiling_phase = phase_result.scalar_one_or_none()
            
            if not profiling_phase:
                logger.warning(f"No profiling phase found for cycle {cycle_id}, report {report_id}")
                return
            
            for attribute_id, score_data in scores.items():
                if not score_data.get("has_profiling_data", False):
                    continue
                    
                # Check if score already exists
                existing_query = select(AttributeProfilingScore).where(
                    and_(
                        AttributeProfilingScore.phase_id == profiling_phase.phase_id,
                        AttributeProfilingScore.attribute_id == attribute_id
                    )
                )
                existing_result = await db.execute(existing_query)
                existing_score = existing_result.scalar_one_or_none()
                
                if existing_score:
                    # Update existing score
                    existing_score.overall_quality_score = score_data["overall_quality_score"]
                    existing_score.total_rules_executed = score_data["total_rules_executed"]
                    existing_score.rules_passed = score_data["rules_passed"]
                    existing_score.rules_failed = score_data["rules_failed"]
                    existing_score.completeness_score = score_data.get("completeness_score", 0.0)
                    existing_score.validity_score = score_data.get("validity_score", 0.0)
                    existing_score.accuracy_score = score_data.get("accuracy_score", 0.0)
                    existing_score.consistency_score = score_data.get("consistency_score", 0.0)
                    existing_score.uniqueness_score = score_data.get("uniqueness_score", 0.0)
                    existing_score.calculated_at = func.now()
                else:
                    # Create new score record
                    new_score = AttributeProfilingScore(
                        phase_id=profiling_phase.phase_id,
                        attribute_id=attribute_id,
                        overall_quality_score=score_data["overall_quality_score"],
                        total_rules_executed=score_data["total_rules_executed"],
                        rules_passed=score_data["rules_passed"],
                        rules_failed=score_data["rules_failed"],
                        completeness_score=score_data.get("completeness_score", 0.0),
                        validity_score=score_data.get("validity_score", 0.0),
                        accuracy_score=score_data.get("accuracy_score", 0.0),
                        consistency_score=score_data.get("consistency_score", 0.0),
                        uniqueness_score=score_data.get("uniqueness_score", 0.0)
                    )
                    db.add(new_score)
            
            await db.commit()
            logger.info(f"Stored DQ scores for {len(scores)} attributes")
            
        except Exception as e:
            logger.error(f"Error storing DQ scores: {str(e)}")
            await db.rollback()
            raise