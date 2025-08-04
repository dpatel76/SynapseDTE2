from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.application.dtos.sla import (
    SLAConfigurationDTO, SLAConfigurationCreateDTO, SLAConfigurationUpdateDTO,
    EscalationRuleDTO, EscalationRuleCreateDTO, EscalationRuleUpdateDTO,
    SLAViolationDTO, SLAViolationSummaryDTO, ResolveViolationDTO,
    EscalationLogDTO, SLAConfigurationFilterDTO, EscalationRuleFilterDTO,
    SLAViolationFilterDTO
)
from app.application.use_cases.sla import (
    SLAUseCase, EscalationRuleUseCase, SLAViolationUseCase
)

router = APIRouter(prefix="/admin/sla", tags=["Admin - SLA"])

# SLA Configuration Endpoints

@router.get("/configurations", response_model=List[SLAConfigurationDTO])
async def get_sla_configurations(
    active_only: bool = Query(False, description="Filter for active configurations only"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve SLA configurations with optional filtering.
    
    Required roles: Admin, Data Executive, Test Executive
    """
    filter_dto = SLAConfigurationFilterDTO(
        active_only=active_only,
        skip=skip,
        limit=limit
    )
    return await SLAUseCase.get_sla_configurations(filter_dto, current_user, db)


@router.get("/configurations/{config_id}", response_model=SLAConfigurationDTO)
async def get_sla_configuration(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a specific SLA configuration by ID.
    
    Required roles: Admin, Data Executive, Test Executive
    """
    return await SLAUseCase.get_sla_configuration(config_id, current_user, db)


@router.post("/configurations", response_model=SLAConfigurationDTO)
async def create_sla_configuration(
    config_data: SLAConfigurationCreateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new SLA configuration.
    
    Required roles: Admin, Data Executive, Test Executive
    """
    return await SLAUseCase.create_sla_configuration(config_data, current_user, db)


@router.put("/configurations/{config_id}", response_model=SLAConfigurationDTO)
async def update_sla_configuration(
    config_id: int,
    config_data: SLAConfigurationUpdateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing SLA configuration.
    
    Required roles: Admin, Data Executive, Test Executive
    """
    return await SLAUseCase.update_sla_configuration(config_id, config_data, current_user, db)


@router.delete("/configurations/{config_id}")
async def delete_sla_configuration(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an SLA configuration (soft delete by marking inactive).
    
    Required roles: Admin, Data Executive, Test Executive
    """
    return await SLAUseCase.delete_sla_configuration(config_id, current_user, db)


# Escalation Rules Endpoints

@router.get("/escalation-rules", response_model=List[EscalationRuleDTO])
async def get_escalation_rules(
    sla_config_id: int = Query(None, description="Filter by SLA configuration ID"),
    active_only: bool = Query(False, description="Filter for active rules only"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve escalation rules with optional filtering.
    
    Required roles: Admin, Data Executive, Test Executive
    """
    filter_dto = EscalationRuleFilterDTO(
        sla_config_id=sla_config_id,
        active_only=active_only
    )
    return await EscalationRuleUseCase.get_escalation_rules(filter_dto, current_user, db)


@router.post("/escalation-rules", response_model=EscalationRuleDTO)
async def create_escalation_rule(
    rule_data: EscalationRuleCreateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new escalation rule.
    
    Required roles: Admin, Data Executive, Test Executive
    """
    return await EscalationRuleUseCase.create_escalation_rule(rule_data, current_user, db)


@router.put("/escalation-rules/{rule_id}", response_model=EscalationRuleDTO)
async def update_escalation_rule(
    rule_id: int,
    rule_data: EscalationRuleUpdateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing escalation rule.
    
    Required roles: Admin, Data Executive, Test Executive
    """
    return await EscalationRuleUseCase.update_escalation_rule(rule_id, rule_data, current_user, db)


@router.delete("/escalation-rules/{rule_id}")
async def delete_escalation_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an escalation rule (soft delete).
    
    Required roles: Admin, Data Executive, Test Executive
    """
    return await EscalationRuleUseCase.delete_escalation_rule(rule_id, current_user, db)


# SLA Violation Monitoring Endpoints

@router.get("/violations", response_model=List[SLAViolationDTO])
async def get_sla_violations(
    active_only: bool = Query(True, description="Filter for active violations only"),
    sla_type: str = Query(None, description="Filter by SLA type"),
    severity: str = Query(None, description="Filter by severity (critical, high, medium, low)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve SLA violations with optional filtering.
    
    Required roles: Admin, Data Executive, Test Executive, Report Owner Executive
    """
    filter_dto = SLAViolationFilterDTO(
        active_only=active_only,
        sla_type=sla_type,
        severity=severity,
        skip=skip,
        limit=limit
    )
    return await SLAViolationUseCase.get_sla_violations(filter_dto, current_user, db)


@router.get("/violations/summary", response_model=SLAViolationSummaryDTO)
async def get_sla_violations_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get summary statistics for SLA violations.
    
    Required roles: Admin, Data Executive, Test Executive, Report Owner Executive
    """
    return await SLAViolationUseCase.get_sla_violations_summary(current_user, db)


@router.post("/violations/{violation_id}/resolve")
async def resolve_sla_violation(
    violation_id: int,
    resolve_data: ResolveViolationDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually resolve an SLA violation.
    
    Required roles: Admin, Data Executive, Test Executive
    """
    return await SLAViolationUseCase.resolve_sla_violation(violation_id, resolve_data, current_user, db)


@router.get("/violations/{violation_id}/escalation-logs", response_model=List[EscalationLogDTO])
async def get_escalation_logs(
    violation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get escalation history for a specific violation.
    
    Required roles: Admin, Data Executive, Test Executive, Report Owner Executive
    """
    return await SLAViolationUseCase.get_escalation_logs(violation_id, current_user, db)