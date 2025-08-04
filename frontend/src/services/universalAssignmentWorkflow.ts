/**
 * Universal Assignment Workflow Integration Service
 * 
 * This service integrates Universal Assignments with workflow phase transitions,
 * automatically creating assignments when phases change and handling workflow logic.
 */

import apiClient from '../api/client';
import { getPhaseAssignmentTypes, AssignmentTypeConfig } from '../config/universalAssignmentTypes';
import { toast } from 'react-hot-toast';

export interface WorkflowContext {
  cycleId: number;
  reportId: number;
  phase: string;
  userId: number;
  userRole: string;
  additionalData?: any;
}

export interface AssignmentCreationParams {
  assignmentType: string;
  cycleId: number;
  reportId: number;
  fromUserId?: number;
  toUserId?: number;
  toRole?: string;
  title: string;
  description?: string;
  priority: string;
  dueDate?: string;
  contextData?: any;
}

/**
 * Create assignments for a workflow phase transition
 */
export async function createPhaseTransitionAssignments(
  fromPhase: string,
  toPhase: string,
  context: WorkflowContext
): Promise<void> {
  try {
    // Get assignment types for the new phase
    const assignmentTypes = getPhaseAssignmentTypes(toPhase);
    
    // Filter assignment types based on user role
    const relevantAssignments = assignmentTypes.filter(type => 
      type.fromRole === context.userRole || type.autoAssign
    );
    
    // Create assignments
    for (const assignmentType of relevantAssignments) {
      await createAssignment({
        assignmentType: assignmentType.assignmentType,
        cycleId: context.cycleId,
        reportId: context.reportId,
        fromUserId: context.userId,
        toRole: assignmentType.toRole,
        title: assignmentType.title,
        description: assignmentType.description,
        priority: assignmentType.priority,
        dueDate: calculateDueDate(assignmentType.slaHours),
        contextData: {
          phase: toPhase,
          fromPhase,
          ...context.additionalData
        }
      });
    }
  } catch (error) {
    console.error('Error creating phase transition assignments:', error);
    throw error;
  }
}

/**
 * Create a single assignment
 */
export async function createAssignment(params: AssignmentCreationParams): Promise<any> {
  try {
    const payload = {
      assignment_type: params.assignmentType,
      from_role: params.contextData?.userRole || 'Tester',
      to_role: params.toRole,
      to_user_id: params.toUserId,
      title: params.title,
      description: params.description,
      task_instructions: params.description,
      context_type: 'Report',
      context_data: {
        cycle_id: Number(params.cycleId),  // Ensure it's a number
        report_id: Number(params.reportId),  // Ensure it's a number
        phase_name: params.contextData?.phase,
        ...params.contextData
      },
      priority: params.priority,
      due_date: params.dueDate,
      requires_approval: false,
      approval_role: null,
      assignment_metadata: params.contextData
    };
    
    console.log('Creating assignment with payload:', payload);
    
    const response = await apiClient.post('/universal-assignments/assignments', payload);
    
    console.log('Assignment created:', response.data);
    
    return response.data;
  } catch (error: any) {
    console.error('Error creating assignment:', error);
    console.error('Error response:', error.response?.data);
    throw error;
  }
}

/**
 * Handle assignment completion and trigger next assignments
 */
export async function handleAssignmentCompletion(
  assignmentId: string,
  completionData?: any
): Promise<void> {
  try {
    // Mark assignment as completed
    const response = await apiClient.post(
      `/universal-assignments/assignments/${assignmentId}/complete`,
      { completion_data: completionData }
    );
    
    const completedAssignment = response.data;
    
    // Check if this triggers any follow-up assignments
    const assignmentTypeConfig = getPhaseAssignmentTypes(completedAssignment.context_data?.phase || '');
    
    // Find dependent assignment types
    const dependentTypes = assignmentTypeConfig.filter(type => 
      type.autoAssign && type.fromRole === completedAssignment.to_role
    );
    
    // Create follow-up assignments
    for (const dependentType of dependentTypes) {
      await createAssignment({
        assignmentType: dependentType.assignmentType,
        cycleId: completedAssignment.cycle_id,
        reportId: completedAssignment.report_id,
        fromUserId: completedAssignment.to_user_id,
        toRole: dependentType.toRole,
        title: dependentType.title,
        description: dependentType.description,
        priority: dependentType.priority,
        dueDate: calculateDueDate(dependentType.slaHours),
        contextData: {
          ...completedAssignment.context_data,
          parentAssignmentId: assignmentId
        }
      });
    }
  } catch (error) {
    console.error('Error handling assignment completion:', error);
    throw error;
  }
}

/**
 * Check if user can proceed with workflow action based on assignments
 */
export async function canProceedWithWorkflow(
  phase: string,
  action: string,
  context: WorkflowContext
): Promise<boolean> {
  try {
    // Get active assignments for this phase
    const response = await apiClient.get('/universal-assignments/assignments', {
      params: {
        user_id: context.userId,
        phase,
        cycle_id: context.cycleId,
        report_id: context.reportId,
        status: 'assigned,acknowledged,in_progress'
      }
    });
    
    const activeAssignments = response.data || [];
    
    // Check if there are blocking assignments
    const blockingAssignments = activeAssignments.filter((assignment: any) => {
      const config = getAssignmentTypeConfig(assignment.assignment_type);
      return config?.priority === 'Critical' || config?.priority === 'Urgent';
    });
    
    if (blockingAssignments.length > 0) {
      toast.error(`Cannot proceed: ${blockingAssignments.length} critical assignments pending`);
      return false;
    }
    
    return true;
  } catch (error) {
    console.error('Error checking workflow permissions:', error);
    return false;
  }
}

/**
 * Get assignment type configuration helper
 */
function getAssignmentTypeConfig(assignmentType: string): AssignmentTypeConfig | undefined {
  // Get all phase configurations
  const allPhases = ['Planning', 'Scoping', 'Data Provider Identification', 'Sample Selection', 
                     'Request for Information', 'Test Execution', 'Observation Management', 'Finalize Test Report'];
  
  for (const phase of allPhases) {
    const phaseTypes = getPhaseAssignmentTypes(phase);
    const foundType = phaseTypes.find(t => t.assignmentType === assignmentType);
    if (foundType) return foundType;
  }
  return undefined;
}

/**
 * Calculate due date based on SLA hours
 */
function calculateDueDate(slaHours?: number): string | undefined {
  if (!slaHours) return undefined;
  
  const dueDate = new Date();
  dueDate.setHours(dueDate.getHours() + slaHours);
  return dueDate.toISOString();
}

/**
 * Integration hooks for workflow actions
 */
export const workflowHooks = {
  /**
   * Called when starting a phase
   */
  onPhaseStart: async (phase: string, context: WorkflowContext) => {
    const assignmentTypes = getPhaseAssignmentTypes(phase);
    const startAssignments = assignmentTypes.filter(type => 
      type.fromRole === context.userRole && type.assignmentType.includes('start')
    );
    
    for (const assignment of startAssignments) {
      await createAssignment({
        assignmentType: assignment.assignmentType,
        cycleId: context.cycleId,
        reportId: context.reportId,
        fromUserId: context.userId,
        toRole: assignment.toRole,
        title: assignment.title,
        description: assignment.description,
        priority: assignment.priority,
        dueDate: calculateDueDate(assignment.slaHours),
        contextData: { phase, action: 'phase_start' }
      });
    }
  },
  
  /**
   * Called when completing a phase
   */
  onPhaseComplete: async (phase: string, context: WorkflowContext) => {
    // Check for any pending critical assignments
    const canProceed = await canProceedWithWorkflow(phase, 'complete', context);
    if (!canProceed) {
      throw new Error('Cannot complete phase with pending assignments');
    }
  },
  
  /**
   * Called when submitting for approval
   */
  onSubmitForApproval: async (phase: string, context: WorkflowContext) => {
    console.log('onSubmitForApproval called with:', { phase, context });
    
    const assignmentTypes = getPhaseAssignmentTypes(phase);
    console.log('Assignment types for phase:', assignmentTypes);
    
    const approvalAssignments = assignmentTypes.filter(type => 
      (type.assignmentType.includes('approval') || type.assignmentType.includes('review')) &&
      type.fromRole === context.userRole
    );
    console.log('Filtered approval assignments:', approvalAssignments);
    console.log('Context user role:', context.userRole);
    
    for (const assignment of approvalAssignments) {
      console.log('Creating assignment:', assignment);
      try {
        await createAssignment({
          assignmentType: assignment.assignmentType,
          cycleId: context.cycleId,
          reportId: context.reportId,
          fromUserId: context.userId,
          toRole: assignment.toRole,
          title: assignment.title,
          description: assignment.description,
          priority: assignment.priority,
          dueDate: calculateDueDate(assignment.slaHours),
          contextData: { 
            phase, 
            action: 'submit_for_approval',
            ...context.additionalData 
          }
        });
        console.log('Assignment created successfully');
      } catch (error) {
        console.error('Error creating assignment:', error);
        throw error;
      }
    }
  },
};