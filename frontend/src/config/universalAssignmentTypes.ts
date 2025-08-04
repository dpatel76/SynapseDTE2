/**
 * Universal Assignment Types Configuration
 * 
 * This configuration maps workflow phases to their specific assignment types,
 * defining the role-to-role interactions and assignments for each phase.
 */

export interface AssignmentTypeConfig {
  assignmentType: string;
  fromRole: string;
  toRole: string;
  title: string;
  description: string;
  priority: 'Critical' | 'Urgent' | 'High' | 'Medium' | 'Low';
  slaHours?: number;
  autoAssign?: boolean;
  requiresAcknowledgement?: boolean;
  allowReassignment?: boolean;
}

export interface PhaseAssignmentConfig {
  phase: string;
  assignmentTypes: AssignmentTypeConfig[];
}

export const UNIVERSAL_ASSIGNMENT_TYPES: PhaseAssignmentConfig[] = [
  {
    phase: 'Planning',
    assignmentTypes: [
      {
        assignmentType: 'Phase Review',
        fromRole: 'Tester',
        toRole: 'Test Executive',
        title: 'Review Planning Phase',
        description: 'Review and approve the generated test attributes for the planning phase',
        priority: 'High',
        slaHours: 24,
        requiresAcknowledgement: true,
        allowReassignment: true,
      },
      {
        assignmentType: 'Additional Data Required',
        fromRole: 'Test Executive',
        toRole: 'Tester',
        title: 'Revise Planning Attributes',
        description: 'Revise the test attributes based on feedback',
        priority: 'Urgent',
        slaHours: 12,
        requiresAcknowledgement: true,
        allowReassignment: false,
      },
    ],
  },
  {
    phase: 'Scoping',
    assignmentTypes: [
      {
        assignmentType: 'Scoping Approval',
        fromRole: 'Tester',
        toRole: 'Test Executive',
        title: 'Review Scoping Submission',
        description: 'Review and approve the scoping decisions for testing',
        priority: 'High',
        slaHours: 24,
        requiresAcknowledgement: true,
        allowReassignment: true,
      },
      {
        assignmentType: 'Scoping Approval',
        fromRole: 'Test Executive',
        toRole: 'Report Owner',
        title: 'Approve Scoping Decisions',
        description: 'Final approval of scoping decisions before proceeding',
        priority: 'High',
        slaHours: 48,
        requiresAcknowledgement: true,
        allowReassignment: false,
      },
    ],
  },
  {
    phase: 'Data Owner Identification',
    assignmentTypes: [
      {
        assignmentType: 'LOB Assignment',
        fromRole: 'Tester',
        toRole: 'Data Executive',
        title: 'Assign LOB to Attributes',
        description: 'Review and assign appropriate LOBs to test attributes',
        priority: 'High',
        slaHours: 48,
        requiresAcknowledgement: true,
        allowReassignment: true,
      },
      {
        assignmentType: 'Role Assignment',
        fromRole: 'Data Executive',
        toRole: 'Data Owner',
        title: 'Data Owner Assignment',
        description: 'You have been assigned as the data owner for specific attributes',
        priority: 'High',
        slaHours: 24,
        requiresAcknowledgement: true,
        allowReassignment: false,
        autoAssign: true,
      },
    ],
  },
  {
    phase: 'Request Info',
    assignmentTypes: [
      {
        assignmentType: 'Information Request',
        fromRole: 'Tester',
        toRole: 'Data Owner',
        title: 'Provide Documentation',
        description: 'Provide supporting documentation for assigned test cases',
        priority: 'High',
        slaHours: 72,
        requiresAcknowledgement: true,
        allowReassignment: false,
      },
      {
        assignmentType: 'Document Review',
        fromRole: 'Data Owner',
        toRole: 'Tester',
        title: 'Review Documentation',
        description: 'Documentation has been submitted for review',
        priority: 'Medium',
        slaHours: 24,
        requiresAcknowledgement: false,
        allowReassignment: false,
        autoAssign: true,
      },
      {
        assignmentType: 'Additional Data Required',
        fromRole: 'Tester',
        toRole: 'Data Owner',
        title: 'Revise Documentation',
        description: 'Additional information or corrections needed for documentation',
        priority: 'Urgent',
        slaHours: 24,
        requiresAcknowledgement: true,
        allowReassignment: false,
      },
    ],
  },
  {
    phase: 'Test Execution',
    assignmentTypes: [
      {
        assignmentType: 'Test Execution Review',
        fromRole: 'Test Executive',
        toRole: 'Tester',
        title: 'Execute Test Cases',
        description: 'Execute assigned test cases and document results',
        priority: 'High',
        slaHours: 120,
        requiresAcknowledgement: true,
        allowReassignment: true,
      },
      {
        assignmentType: 'Test Execution Review',
        fromRole: 'Tester',
        toRole: 'Test Executive',
        title: 'Review Test Results',
        description: 'Review completed test execution results',
        priority: 'Medium',
        slaHours: 48,
        requiresAcknowledgement: false,
        allowReassignment: true,
      },
      {
        assignmentType: 'Clarification Required',
        fromRole: 'Tester',
        toRole: 'Data Owner',
        title: 'Clarification Needed',
        description: 'Additional clarification required for test execution',
        priority: 'Urgent',
        slaHours: 24,
        requiresAcknowledgement: true,
        allowReassignment: false,
      },
    ],
  },
  {
    phase: 'Observation Management',
    assignmentTypes: [
      {
        assignmentType: 'Observation Approval',
        fromRole: 'Tester',
        toRole: 'Test Executive',
        title: 'Review Observations',
        description: 'Review and approve created observations',
        priority: 'High',
        slaHours: 48,
        requiresAcknowledgement: true,
        allowReassignment: true,
      },
      {
        assignmentType: 'Risk Assessment',
        fromRole: 'Test Executive',
        toRole: 'Report Owner',
        title: 'Rate Observations',
        description: 'Provide risk rating for observations',
        priority: 'High',
        slaHours: 72,
        requiresAcknowledgement: true,
        allowReassignment: false,
      },
      {
        assignmentType: 'Clarification Required',
        fromRole: 'Data Owner',
        toRole: 'Tester',
        title: 'Clarification Response',
        description: 'Response to clarification request',
        priority: 'High',
        slaHours: 24,
        requiresAcknowledgement: false,
        allowReassignment: false,
        autoAssign: true,
      },
      {
        assignmentType: 'Observation Approval',
        fromRole: 'Report Owner',
        toRole: 'Report Executive',
        title: 'Approve Observations',
        description: 'Executive approval required for high-risk observations',
        priority: 'Critical',
        slaHours: 48,
        requiresAcknowledgement: true,
        allowReassignment: false,
      },
    ],
  },
  {
    phase: 'Finalize Test Report',
    assignmentTypes: [
      {
        assignmentType: 'Report Approval',
        fromRole: 'Tester',
        toRole: 'Test Executive',
        title: 'Review Draft Report',
        description: 'Review the generated test report draft',
        priority: 'High',
        slaHours: 48,
        requiresAcknowledgement: true,
        allowReassignment: true,
      },
      {
        assignmentType: 'Report Approval',
        fromRole: 'Test Executive',
        toRole: 'Report Owner',
        title: 'Approve Test Report',
        description: 'Approve the final test report',
        priority: 'High',
        slaHours: 72,
        requiresAcknowledgement: true,
        allowReassignment: false,
      },
      {
        assignmentType: 'Report Approval',
        fromRole: 'Report Owner',
        toRole: 'Report Executive',
        title: 'Executive Report Approval',
        description: 'Executive approval for final test report',
        priority: 'Critical',
        slaHours: 96,
        requiresAcknowledgement: true,
        allowReassignment: false,
      },
    ],
  },
];

/**
 * Get assignment types for a specific phase
 */
export function getPhaseAssignmentTypes(phase: string): AssignmentTypeConfig[] {
  const phaseConfig = UNIVERSAL_ASSIGNMENT_TYPES.find(p => p.phase === phase);
  return phaseConfig?.assignmentTypes || [];
}

/**
 * Get assignment type by type string
 */
export function getAssignmentTypeConfig(assignmentType: string): AssignmentTypeConfig | undefined {
  for (const phaseConfig of UNIVERSAL_ASSIGNMENT_TYPES) {
    const typeConfig = phaseConfig.assignmentTypes.find(t => t.assignmentType === assignmentType);
    if (typeConfig) {
      return typeConfig;
    }
  }
  return undefined;
}

/**
 * Check if an assignment type allows reassignment
 */
export function canReassign(assignmentType: string): boolean {
  const config = getAssignmentTypeConfig(assignmentType);
  return config?.allowReassignment || false;
}

/**
 * Get SLA hours for an assignment type
 */
export function getSLAHours(assignmentType: string): number {
  const config = getAssignmentTypeConfig(assignmentType);
  return config?.slaHours || 48; // Default 48 hours
}

/**
 * Check if assignment requires acknowledgement
 */
export function requiresAcknowledgement(assignmentType: string): boolean {
  const config = getAssignmentTypeConfig(assignmentType);
  return config?.requiresAcknowledgement !== false; // Default true
}