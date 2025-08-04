from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, delete
from fastapi import HTTPException, status

from app.models.user import User
from app.models.sla import SLAConfiguration, SLAEscalationRule, SLAViolationTracking, EscalationEmailLog
from app.models.report import Report
from app.application.dtos.sla import (
    SLAConfigurationCreateDTO, SLAConfigurationUpdateDTO, SLAConfigurationDTO,
    EscalationRuleCreateDTO, EscalationRuleUpdateDTO, EscalationRuleDTO,
    SLAViolationDTO, SLAViolationSummaryDTO, ResolveViolationDTO,
    EscalationLogDTO, SLAConfigurationFilterDTO, EscalationRuleFilterDTO,
    SLAViolationFilterDTO
)


class SLAUseCase:
    """Use cases for SLA management"""
    
    @staticmethod
    async def get_sla_configurations(
        filter_dto: SLAConfigurationFilterDTO,
        current_user: User,
        db: AsyncSession
    ) -> List[SLAConfigurationDTO]:
        """Retrieve SLA configurations with optional filtering"""
        # Check permissions
        if current_user.role not in ["Admin", "Data Executive", "Test Executive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view SLA configurations"
            )
        
        stmt = select(SLAConfiguration)
        
        if filter_dto.active_only:
            stmt = stmt.where(SLAConfiguration.is_active == True)
        
        stmt = stmt.offset(filter_dto.skip).limit(filter_dto.limit)
        result = await db.execute(stmt)
        configurations = result.scalars().all()
        
        return [SLAConfigurationDTO.model_validate(config) for config in configurations]
    
    @staticmethod
    async def get_sla_configuration(
        config_id: int,
        current_user: User,
        db: AsyncSession
    ) -> SLAConfigurationDTO:
        """Retrieve a specific SLA configuration by ID"""
        if current_user.role not in ["Admin", "Data Executive", "Test Executive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        stmt = select(SLAConfiguration).where(SLAConfiguration.sla_config_id == config_id)
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SLA configuration not found"
            )
        
        return SLAConfigurationDTO.model_validate(config)
    
    @staticmethod
    async def create_sla_configuration(
        config_dto: SLAConfigurationCreateDTO,
        current_user: User,
        db: AsyncSession
    ) -> SLAConfigurationDTO:
        """Create a new SLA configuration"""
        if current_user.role not in ["Admin", "Data Executive", "Test Executive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create SLA configurations"
            )
        
        # Check if configuration already exists for this SLA type
        stmt = select(SLAConfiguration).where(SLAConfiguration.sla_type == config_dto.sla_type)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SLA configuration already exists for type: {config_dto.sla_type}"
            )
        
        # Create new configuration
        db_config = SLAConfiguration(
            **config_dto.model_dump(),
            created_by=current_user.user_id
        )
        
        db.add(db_config)
        await db.commit()
        await db.refresh(db_config)
        
        return SLAConfigurationDTO.model_validate(db_config)
    
    @staticmethod
    async def update_sla_configuration(
        config_id: int,
        config_dto: SLAConfigurationUpdateDTO,
        current_user: User,
        db: AsyncSession
    ) -> SLAConfigurationDTO:
        """Update an existing SLA configuration"""
        if current_user.role not in ["Admin", "Data Executive", "Test Executive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update SLA configurations"
            )
        
        stmt = select(SLAConfiguration).where(SLAConfiguration.sla_config_id == config_id)
        result = await db.execute(stmt)
        db_config = result.scalar_one_or_none()
        
        if not db_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SLA configuration not found"
            )
        
        # Update fields
        update_data = config_dto.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_config, field, value)
        
        db_config.updated_by = current_user.user_id
        
        await db.commit()
        await db.refresh(db_config)
        
        return SLAConfigurationDTO.model_validate(db_config)
    
    @staticmethod
    async def delete_sla_configuration(
        config_id: int,
        current_user: User,
        db: AsyncSession
    ) -> dict:
        """Delete an SLA configuration (soft delete)"""
        if current_user.role not in ["Admin", "Data Executive", "Test Executive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete SLA configurations"
            )
        
        stmt = select(SLAConfiguration).where(SLAConfiguration.sla_config_id == config_id)
        result = await db.execute(stmt)
        db_config = result.scalar_one_or_none()
        
        if not db_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SLA configuration not found"
            )
        
        # Check if configuration is being used
        violations_stmt = select(func.count(SLAViolationTracking.violation_id)).where(
            and_(
                SLAViolationTracking.sla_config_id == config_id,
                SLAViolationTracking.is_resolved == False
            )
        )
        violations_result = await db.execute(violations_stmt)
        active_violations = violations_result.scalar()
        
        if active_violations > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete SLA configuration with active violations"
            )
        
        # Soft delete by marking inactive
        db_config.is_active = False
        db_config.updated_by = current_user.user_id
        
        await db.commit()
        
        return {"message": "SLA configuration deleted successfully"}


class EscalationRuleUseCase:
    """Use cases for escalation rule management"""
    
    @staticmethod
    async def get_escalation_rules(
        filter_dto: EscalationRuleFilterDTO,
        current_user: User,
        db: AsyncSession
    ) -> List[EscalationRuleDTO]:
        """Retrieve escalation rules with optional filtering"""
        if current_user.role not in ["Admin", "Data Executive", "Test Executive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        stmt = select(SLAEscalationRule)
        
        if filter_dto.sla_config_id:
            stmt = stmt.where(SLAEscalationRule.sla_config_id == filter_dto.sla_config_id)
        
        if filter_dto.active_only:
            stmt = stmt.where(SLAEscalationRule.is_active == True)
        
        stmt = stmt.order_by(
            SLAEscalationRule.sla_config_id,
            SLAEscalationRule.escalation_order
        )
        
        result = await db.execute(stmt)
        rules = result.scalars().all()
        
        return [EscalationRuleDTO.model_validate(rule) for rule in rules]
    
    @staticmethod
    async def create_escalation_rule(
        rule_dto: EscalationRuleCreateDTO,
        current_user: User,
        db: AsyncSession
    ) -> EscalationRuleDTO:
        """Create a new escalation rule"""
        if current_user.role not in ["Admin", "Data Executive", "Test Executive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Verify SLA configuration exists
        sla_stmt = select(SLAConfiguration).where(SLAConfiguration.sla_config_id == rule_dto.sla_config_id)
        sla_result = await db.execute(sla_stmt)
        sla_config = sla_result.scalar_one_or_none()
        
        if not sla_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SLA configuration not found"
            )
        
        # Check for duplicate escalation order
        existing_stmt = select(SLAEscalationRule).where(
            and_(
                SLAEscalationRule.sla_config_id == rule_dto.sla_config_id,
                SLAEscalationRule.escalation_order == rule_dto.escalation_order,
                SLAEscalationRule.is_active == True
            )
        )
        existing_result = await db.execute(existing_stmt)
        existing_rule = existing_result.scalar_one_or_none()
        
        if existing_rule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Escalation rule with order {rule_dto.escalation_order} already exists"
            )
        
        # Create new rule
        db_rule = SLAEscalationRule(
            **rule_dto.model_dump(),
            created_by=current_user.user_id
        )
        
        db.add(db_rule)
        await db.commit()
        await db.refresh(db_rule)
        
        return EscalationRuleDTO.model_validate(db_rule)
    
    @staticmethod
    async def update_escalation_rule(
        rule_id: int,
        rule_dto: EscalationRuleUpdateDTO,
        current_user: User,
        db: AsyncSession
    ) -> EscalationRuleDTO:
        """Update an existing escalation rule"""
        if current_user.role not in ["Admin", "Data Executive", "Test Executive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        stmt = select(SLAEscalationRule).where(SLAEscalationRule.escalation_rule_id == rule_id)
        result = await db.execute(stmt)
        db_rule = result.scalar_one_or_none()
        
        if not db_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Escalation rule not found"
            )
        
        # Update fields
        update_data = rule_dto.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_rule, field, value)
        
        db_rule.updated_by = current_user.user_id
        
        await db.commit()
        await db.refresh(db_rule)
        
        return EscalationRuleDTO.model_validate(db_rule)
    
    @staticmethod
    async def delete_escalation_rule(
        rule_id: int,
        current_user: User,
        db: AsyncSession
    ) -> dict:
        """Delete an escalation rule (soft delete)"""
        if current_user.role not in ["Admin", "Data Executive", "Test Executive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        stmt = select(SLAEscalationRule).where(SLAEscalationRule.escalation_rule_id == rule_id)
        result = await db.execute(stmt)
        db_rule = result.scalar_one_or_none()
        
        if not db_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Escalation rule not found"
            )
        
        # Soft delete by marking inactive
        db_rule.is_active = False
        db_rule.updated_by = current_user.user_id
        
        await db.commit()
        
        return {"message": "Escalation rule deleted successfully"}


class SLAViolationUseCase:
    """Use cases for SLA violation monitoring"""
    
    @staticmethod
    async def get_sla_violations(
        filter_dto: SLAViolationFilterDTO,
        current_user: User,
        db: AsyncSession
    ) -> List[SLAViolationDTO]:
        """Retrieve SLA violations with optional filtering"""
        if current_user.role not in ["Admin", "Data Executive", "Test Executive", "Report Owner Executive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Base query with joins to get report name and SLA type
        stmt = select(
            SLAViolationTracking,
            Report.report_name,
            SLAConfiguration.sla_type
        ).join(
            Report,
            SLAViolationTracking.report_id == Report.report_id
        ).join(
            SLAConfiguration,
            SLAViolationTracking.sla_config_id == SLAConfiguration.sla_config_id
        )
        
        if filter_dto.active_only:
            stmt = stmt.where(SLAViolationTracking.is_violated == True)
        
        if filter_dto.sla_type:
            stmt = stmt.where(SLAConfiguration.sla_type == filter_dto.sla_type)
        
        # Apply severity filter based on violation hours
        if filter_dto.severity:
            if filter_dto.severity == "critical":
                stmt = stmt.where(SLAViolationTracking.violation_hours > 72)
            elif filter_dto.severity == "high":
                stmt = stmt.where(
                    and_(
                        SLAViolationTracking.violation_hours > 48,
                        SLAViolationTracking.violation_hours <= 72
                    )
                )
            elif filter_dto.severity == "medium":
                stmt = stmt.where(
                    and_(
                        SLAViolationTracking.violation_hours > 24,
                        SLAViolationTracking.violation_hours <= 48
                    )
                )
            elif filter_dto.severity == "low":
                stmt = stmt.where(SLAViolationTracking.violation_hours <= 24)
        
        stmt = stmt.order_by(
            desc(SLAViolationTracking.violation_hours)
        ).offset(filter_dto.skip).limit(filter_dto.limit)
        
        result = await db.execute(stmt)
        violations_with_data = result.all()
        
        # Format response
        violations = []
        for violation, report_name, sla_type in violations_with_data:
            violation_dto = SLAViolationDTO(
                violation_id=violation.violation_id,
                report_name=report_name,
                sla_type=sla_type,
                started_at=violation.started_at,
                due_date=violation.due_date,
                is_violated=violation.is_violated,
                violation_hours=violation.violation_hours,
                current_escalation_level=violation.current_escalation_level.value if violation.current_escalation_level else None,
                escalation_count=violation.escalation_count,
                is_resolved=violation.is_resolved,
                resolved_at=violation.resolved_at,
                resolution_notes=violation.resolution_notes
            )
            violations.append(violation_dto)
        
        return violations
    
    @staticmethod
    async def get_sla_violations_summary(
        current_user: User,
        db: AsyncSession
    ) -> SLAViolationSummaryDTO:
        """Get summary statistics for SLA violations"""
        if current_user.role not in ["Admin", "Data Executive", "Test Executive", "Report Owner Executive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Count total violations
        total_stmt = select(func.count(SLAViolationTracking.violation_id)).where(
            SLAViolationTracking.is_violated == True
        )
        total_result = await db.execute(total_stmt)
        total_violations = total_result.scalar()
        
        # Count by severity
        critical_stmt = select(func.count(SLAViolationTracking.violation_id)).where(
            and_(
                SLAViolationTracking.is_violated == True,
                SLAViolationTracking.violation_hours > 72
            )
        )
        critical_result = await db.execute(critical_stmt)
        critical_count = critical_result.scalar()
        
        high_stmt = select(func.count(SLAViolationTracking.violation_id)).where(
            and_(
                SLAViolationTracking.is_violated == True,
                SLAViolationTracking.violation_hours > 48,
                SLAViolationTracking.violation_hours <= 72
            )
        )
        high_result = await db.execute(high_stmt)
        high_count = high_result.scalar()
        
        medium_stmt = select(func.count(SLAViolationTracking.violation_id)).where(
            and_(
                SLAViolationTracking.is_violated == True,
                SLAViolationTracking.violation_hours > 24,
                SLAViolationTracking.violation_hours <= 48
            )
        )
        medium_result = await db.execute(medium_stmt)
        medium_count = medium_result.scalar()
        
        low_stmt = select(func.count(SLAViolationTracking.violation_id)).where(
            and_(
                SLAViolationTracking.is_violated == True,
                SLAViolationTracking.violation_hours <= 24
            )
        )
        low_result = await db.execute(low_stmt)
        low_count = low_result.scalar()
        
        # Count by SLA type
        sla_type_stmt = select(
            SLAConfiguration.sla_type,
            func.count(SLAViolationTracking.violation_id)
        ).join(
            SLAConfiguration,
            SLAViolationTracking.sla_config_id == SLAConfiguration.sla_config_id
        ).where(
            SLAViolationTracking.is_violated == True
        ).group_by(
            SLAConfiguration.sla_type
        )
        
        sla_type_result = await db.execute(sla_type_stmt)
        sla_type_counts = dict(sla_type_result.all())
        
        return SLAViolationSummaryDTO(
            total_violations=total_violations,
            by_severity={
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            },
            by_sla_type=sla_type_counts
        )
    
    @staticmethod
    async def resolve_sla_violation(
        violation_id: int,
        resolve_dto: ResolveViolationDTO,
        current_user: User,
        db: AsyncSession
    ) -> dict:
        """Manually resolve an SLA violation"""
        if current_user.role not in ["Admin", "Data Executive", "Test Executive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        stmt = select(SLAViolationTracking).where(SLAViolationTracking.violation_id == violation_id)
        result = await db.execute(stmt)
        violation = result.scalar_one_or_none()
        
        if not violation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SLA violation not found"
            )
        
        if violation.is_resolved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SLA violation is already resolved"
            )
        
        # Resolve violation
        violation.is_resolved = True
        violation.resolved_at = func.now()
        if resolve_dto.resolution_notes:
            violation.resolution_notes = resolve_dto.resolution_notes
        
        await db.commit()
        
        return {"message": "SLA violation resolved successfully"}
    
    @staticmethod
    async def get_escalation_logs(
        violation_id: int,
        current_user: User,
        db: AsyncSession
    ) -> List[EscalationLogDTO]:
        """Get escalation history for a specific violation"""
        if current_user.role not in ["Admin", "Data Executive", "Test Executive", "Report Owner Executive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        stmt = select(EscalationEmailLog).where(
            EscalationEmailLog.sla_violation_id == violation_id
        ).order_by(
            desc(EscalationEmailLog.sent_at)
        )
        
        result = await db.execute(stmt)
        logs = result.scalars().all()
        
        return [EscalationLogDTO.model_validate(log) for log in logs]