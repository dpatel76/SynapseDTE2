"""
Activity State Management for SynapseDTE
Standardized activity states and transition rules
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime


class ActivityState(str, Enum):
    """Standardized activity states across all phases"""
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    REVISION_REQUESTED = "Revision Requested"


class ActivityType(str, Enum):
    """Types of activities in the workflow"""
    START_PHASE = "Start Phase"
    EXECUTE_ACTIVITY = "Execute Activity"
    TESTER_REVIEW = "Tester Review"
    REPORT_OWNER_APPROVAL = "Report Owner Approval"
    DATA_EXECUTIVE_ASSIGNMENT = "Data Executive Assignment"
    DATA_OWNER_ASSIGNMENT = "Data Owner Assignment"
    COMPLETE_PHASE = "Complete Phase"


# Standardized activity names for each phase
PHASE_ACTIVITIES = {
    "Planning": {
        "start": "Start Planning Phase",
        "activities": ["Generate Attributes", "Review Attributes"],
        "review": "Tester Review",
        "approval": "Report Owner Approval",
        "complete": "Complete Planning Phase"
    },
    "Data Profiling": {
        "start": "Start Data Profiling Phase",
        "activities": ["Generate Profiling Rules", "Apply Rules", "Analyze Results"],
        "review": "Tester Review",
        "approval": "Report Owner Approval",
        "complete": "Complete Data Profiling Phase"
    },
    "Scoping": {
        "start": "Start Scoping Phase",
        "activities": ["Generate Recommendations", "Apply Scoping"],
        "review": "Tester Review",
        "approval": "Report Owner Approval",
        "complete": "Complete Scoping Phase"
    },
    "Sample Selection": {
        "start": "Start Sample Selection Phase",
        "activities": ["Generate Sample Sets", "Validate Samples"],
        "review": "Tester Review",
        "approval": "Report Owner Approval",
        "complete": "Complete Sample Selection Phase"
    },
    "Data Provider Identification": {
        "start": "Start Data Provider Identification Phase",
        "activities": ["Identify LOBs", "Generate Assignments"],
        "assignment": "Data Executive Assignment",
        "provider_assignment": "Data Owner Assignment",
        "complete": "Complete Data Provider Identification Phase"
    },
    "Request for Information": {
        "start": "Start Request for Information Phase",
        "activities": ["Create RFI Requests", "Send RFIs", "Track Responses"],
        "review": "Tester Review",
        "complete": "Complete Request for Information Phase"
    },
    "Test Execution": {
        "start": "Start Test Execution Phase",
        "activities": ["Execute Tests", "Validate Results", "Document Findings"],
        "review": "Tester Review",
        "complete": "Complete Test Execution Phase"
    },
    "Observation Management": {
        "start": "Start Observation Management Phase",
        "activities": ["Create Observations", "Group Observations", "Rate Severity"],
        "review": "Tester Review",
        "approval": "Report Owner Approval",
        "complete": "Complete Observation Management Phase"
    }
}


# Activity transition rules
ACTIVITY_TRANSITIONS = {
    # Start Phase - Manual, Tester only
    "Start Phase": {
        "manual": True,
        "allowed_roles": ["Tester", "Test Manager"],
        "allowed_states": [ActivityState.NOT_STARTED],
        "next_state": ActivityState.IN_PROGRESS,
        "updates_phase_state": "In Progress",
        "auto_start_next": True
    },
    
    # Execute Activity - Auto-starts when previous completes
    "Execute Activity": {
        "manual": False,
        "trigger": "previous_complete",
        "allowed_states": [ActivityState.NOT_STARTED],
        "next_state": ActivityState.IN_PROGRESS,
        "auto_complete_on": ["all_tasks_done"]
    },
    
    # Tester Review - Auto-completes on submission
    "Tester Review": {
        "manual": False,
        "trigger": "submission",
        "allowed_states": [ActivityState.IN_PROGRESS],
        "next_state": ActivityState.COMPLETED,
        "auto_complete": True,
        "creates_submission": True
    },
    
    # Report Owner Approval - Auto-completes on decision
    "Report Owner Approval": {
        "manual": False,
        "trigger": "approval_decision",
        "allowed_states": [ActivityState.IN_PROGRESS],
        "next_state": ActivityState.COMPLETED,
        "auto_complete": True,
        "on_rejection": {
            "previous_activity_state": ActivityState.REVISION_REQUESTED,
            "phase_state": "In Progress"
        }
    },
    
    # Data Executive Assignment - Auto-completes when all LOBs assigned
    "Data Executive Assignment": {
        "manual": False,
        "trigger": "all_assignments_complete",
        "allowed_states": [ActivityState.IN_PROGRESS],
        "next_state": ActivityState.COMPLETED,
        "auto_complete": True,
        "validation": "check_all_lobs_assigned"
    },
    
    # Data Owner Assignment - Auto-completes when all providers assigned
    "Data Owner Assignment": {
        "manual": False,
        "trigger": "all_providers_assigned",
        "allowed_states": [ActivityState.IN_PROGRESS],
        "next_state": ActivityState.COMPLETED,
        "auto_complete": True,
        "validation": "check_all_providers_assigned"
    },
    
    # Complete Phase - Manual, Tester only
    "Complete Phase": {
        "manual": True,
        "allowed_roles": ["Tester", "Test Manager"],
        "allowed_states": [ActivityState.IN_PROGRESS],
        "next_state": ActivityState.COMPLETED,
        "updates_phase_state": "Completed",
        "validation": "check_all_activities_complete"
    }
}


# Activity dependencies within phases
ACTIVITY_DEPENDENCIES = {
    "Planning": [
        ("Start Planning Phase", None),
        ("Generate Attributes", "Start Planning Phase"),
        ("Review Attributes", "Generate Attributes"),
        ("Tester Review", "Review Attributes"),
        ("Report Owner Approval", "Tester Review"),
        ("Complete Planning Phase", "Report Owner Approval")
    ],
    "Data Profiling": [
        ("Start Data Profiling Phase", None),
        ("Generate Profiling Rules", "Start Data Profiling Phase"),
        ("Apply Rules", "Generate Profiling Rules"),
        ("Analyze Results", "Apply Rules"),
        ("Tester Review", "Analyze Results"),
        ("Report Owner Approval", "Tester Review"),
        ("Complete Data Profiling Phase", "Report Owner Approval")
    ],
    "Scoping": [
        ("Start Scoping Phase", None),
        ("Generate Recommendations", "Start Scoping Phase"),
        ("Apply Scoping", "Generate Recommendations"),
        ("Tester Review", "Apply Scoping"),
        ("Report Owner Approval", "Tester Review"),
        ("Complete Scoping Phase", "Report Owner Approval")
    ],
    "Sample Selection": [
        ("Start Sample Selection Phase", None),
        ("Generate Sample Sets", "Start Sample Selection Phase"),
        ("Validate Samples", "Generate Sample Sets"),
        ("Tester Review", "Validate Samples"),
        ("Report Owner Approval", "Tester Review"),
        ("Complete Sample Selection Phase", "Report Owner Approval")
    ],
    "Data Provider Identification": [
        ("Start Data Provider Identification Phase", None),
        ("Identify LOBs", "Start Data Provider Identification Phase"),
        ("Generate Assignments", "Identify LOBs"),
        ("Data Executive Assignment", "Generate Assignments"),
        ("Data Owner Assignment", "Data Executive Assignment"),
        ("Complete Data Provider Identification Phase", "Data Owner Assignment")
    ],
    "Request for Information": [
        ("Start Request for Information Phase", None),
        ("Create RFI Requests", "Start Request for Information Phase"),
        ("Send RFIs", "Create RFI Requests"),
        ("Track Responses", "Send RFIs"),
        ("Tester Review", "Track Responses"),
        ("Complete Request for Information Phase", "Tester Review")
    ],
    "Test Execution": [
        ("Start Test Execution Phase", None),
        ("Execute Tests", "Start Test Execution Phase"),
        ("Validate Results", "Execute Tests"),
        ("Document Findings", "Validate Results"),
        ("Tester Review", "Document Findings"),
        ("Complete Test Execution Phase", "Tester Review")
    ],
    "Observation Management": [
        ("Start Observation Management Phase", None),
        ("Create Observations", "Start Observation Management Phase"),
        ("Group Observations", "Create Observations"),
        ("Rate Severity", "Group Observations"),
        ("Tester Review", "Rate Severity"),
        ("Report Owner Approval", "Tester Review"),
        ("Complete Observation Management Phase", "Report Owner Approval")
    ]
}


class ActivityTransitionValidator:
    """Validates activity state transitions"""
    
    @staticmethod
    def can_transition(
        activity_name: str,
        current_state: ActivityState,
        target_state: ActivityState,
        user_role: str,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if an activity can transition to a new state
        
        Returns:
            (can_transition, error_message)
        """
        # Get transition rules
        activity_type = ActivityTransitionValidator._get_activity_type(activity_name)
        if not activity_type:
            return False, f"Unknown activity: {activity_name}"
        
        rules = ACTIVITY_TRANSITIONS.get(activity_type, {})
        
        # Check if transition is manual or automatic
        if rules.get("manual", False):
            # Check role permissions
            allowed_roles = rules.get("allowed_roles", [])
            if user_role not in allowed_roles:
                return False, f"Role {user_role} not allowed to transition {activity_name}"
        
        # Check current state
        allowed_states = rules.get("allowed_states", [])
        if current_state not in allowed_states:
            return False, f"Cannot transition from {current_state} state"
        
        # Check if target state matches expected
        expected_state = rules.get("next_state")
        if expected_state and target_state != expected_state:
            return False, f"Invalid target state. Expected {expected_state}, got {target_state}"
        
        # Run validation if specified
        validation_func = rules.get("validation")
        if validation_func and context:
            is_valid, error = ActivityTransitionValidator._run_validation(
                validation_func, context
            )
            if not is_valid:
                return False, error
        
        return True, None
    
    @staticmethod
    def _get_activity_type(activity_name: str) -> Optional[str]:
        """Map activity name to activity type"""
        # Check standard patterns
        if "Start" in activity_name and "Phase" in activity_name:
            return "Start Phase"
        elif "Complete" in activity_name and "Phase" in activity_name:
            return "Complete Phase"
        elif "Tester Review" in activity_name:
            return "Tester Review"
        elif "Report Owner Approval" in activity_name:
            return "Report Owner Approval"
        elif "Data Executive Assignment" in activity_name:
            return "Data Executive Assignment"
        elif "Data Owner Assignment" in activity_name:
            return "Data Owner Assignment"
        else:
            return "Execute Activity"
    
    @staticmethod
    def _run_validation(validation_func: str, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Run validation function"""
        if validation_func == "check_all_activities_complete":
            # Check if all activities in the phase are complete
            activities = context.get("phase_activities", [])
            incomplete = [a for a in activities if a["state"] != ActivityState.COMPLETED]
            if incomplete:
                return False, f"Activities not complete: {', '.join(a['name'] for a in incomplete)}"
        
        elif validation_func == "check_all_lobs_assigned":
            # Check if all LOBs have executive assignments
            lobs = context.get("lobs", [])
            unassigned = [l for l in lobs if not l.get("executive_assigned")]
            if unassigned:
                return False, f"LOBs not assigned: {', '.join(l['name'] for l in unassigned)}"
        
        elif validation_func == "check_all_providers_assigned":
            # Check if all required providers are assigned
            assignments = context.get("provider_assignments", [])
            unassigned = [a for a in assignments if not a.get("provider_assigned")]
            if unassigned:
                return False, f"Providers not assigned for {len(unassigned)} items"
        
        return True, None


class ActivityStateTracker:
    """Tracks activity states within a phase"""
    
    def __init__(self, phase_name: str):
        self.phase_name = phase_name
        self.activities = {}
        self._initialize_activities()
    
    def _initialize_activities(self):
        """Initialize activities for the phase"""
        phase_config = PHASE_ACTIVITIES.get(self.phase_name, {})
        dependencies = ACTIVITY_DEPENDENCIES.get(self.phase_name, [])
        
        # Create activity entries
        for activity_name, dependency in dependencies:
            self.activities[activity_name] = {
                "name": activity_name,
                "state": ActivityState.NOT_STARTED,
                "dependency": dependency,
                "started_at": None,
                "completed_at": None,
                "started_by": None,
                "completed_by": None
            }
    
    def get_next_activity(self) -> Optional[str]:
        """Get the next activity to be started"""
        for activity_name, activity_data in self.activities.items():
            if activity_data["state"] == ActivityState.NOT_STARTED:
                # Check if dependency is complete
                dependency = activity_data["dependency"]
                if not dependency or self.activities[dependency]["state"] == ActivityState.COMPLETED:
                    return activity_name
        return None
    
    def start_activity(self, activity_name: str, user_id: str) -> bool:
        """Start an activity"""
        if activity_name not in self.activities:
            return False
        
        activity = self.activities[activity_name]
        if activity["state"] != ActivityState.NOT_STARTED:
            return False
        
        activity["state"] = ActivityState.IN_PROGRESS
        activity["started_at"] = datetime.utcnow()
        activity["started_by"] = user_id
        return True
    
    def complete_activity(self, activity_name: str, user_id: str) -> bool:
        """Complete an activity"""
        if activity_name not in self.activities:
            return False
        
        activity = self.activities[activity_name]
        if activity["state"] != ActivityState.IN_PROGRESS:
            return False
        
        activity["state"] = ActivityState.COMPLETED
        activity["completed_at"] = datetime.utcnow()
        activity["completed_by"] = user_id
        return True
    
    def request_revision(self, activity_name: str) -> bool:
        """Mark activity for revision"""
        if activity_name not in self.activities:
            return False
        
        activity = self.activities[activity_name]
        activity["state"] = ActivityState.REVISION_REQUESTED
        return True
    
    def get_phase_progress(self) -> Dict[str, Any]:
        """Get overall phase progress"""
        total = len(self.activities)
        completed = sum(1 for a in self.activities.values() if a["state"] == ActivityState.COMPLETED)
        in_progress = sum(1 for a in self.activities.values() if a["state"] == ActivityState.IN_PROGRESS)
        
        return {
            "total_activities": total,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": total - completed - in_progress,
            "completion_percentage": (completed / total * 100) if total > 0 else 0,
            "current_activity": self.get_next_activity()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "phase_name": self.phase_name,
            "activities": self.activities,
            "progress": self.get_phase_progress()
        }
    
    def reset_activity_cascade(self, activity_name: str, user_id: str) -> List[str]:
        """
        Reset an activity and all its dependent activities
        Returns list of reset activity names
        """
        if activity_name not in self.activities:
            return []
        
        activity = self.activities[activity_name]
        if activity["state"] != ActivityState.COMPLETED:
            return []  # Can only reset completed activities
        
        # Find all activities that depend on this one (direct and indirect)
        activities_to_reset = self._get_dependent_activities(activity_name)
        activities_to_reset.insert(0, activity_name)  # Include the activity itself
        
        # Reset each activity in reverse order (dependents first)
        reset_activities = []
        for act_name in reversed(activities_to_reset):
            act = self.activities[act_name]
            if act["state"] == ActivityState.COMPLETED:
                act["state"] = ActivityState.IN_PROGRESS
                act["completed_at"] = None
                act["completed_by"] = None
                # Add reset metadata
                if "reset_history" not in act:
                    act["reset_history"] = []
                act["reset_history"].append({
                    "reset_at": datetime.utcnow(),
                    "reset_by": user_id,
                    "previous_completed_at": act.get("completed_at")
                })
                reset_activities.append(act_name)
        
        return reset_activities
    
    def _get_dependent_activities(self, activity_name: str) -> List[str]:
        """Get all activities that depend on the given activity"""
        dependents = []
        dependencies = ACTIVITY_DEPENDENCIES.get(self.phase_name, [])
        
        # Build dependency map
        dep_map = {name: dep for name, dep in dependencies}
        
        # Find all activities that have this activity in their dependency chain
        for act_name, dep in dep_map.items():
            if self._has_dependency(act_name, activity_name, dep_map):
                dependents.append(act_name)
        
        return dependents
    
    def _has_dependency(self, activity: str, target: str, dep_map: dict) -> bool:
        """Check if activity has target in its dependency chain"""
        current = dep_map.get(activity)
        while current:
            if current == target:
                return True
            current = dep_map.get(current)
        return False