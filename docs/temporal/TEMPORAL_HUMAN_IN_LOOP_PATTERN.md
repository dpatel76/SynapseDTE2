# Temporal Human-in-the-Loop Pattern

This document explains how to implement human-in-the-loop activities in Temporal workflows.

## Pattern Overview

For activities that require human interaction (reviews, approvals, uploads), we use Temporal's signal/query pattern:

1. **Activity starts and returns "awaiting" status**
2. **Workflow waits for a signal with the human input**
3. **Activity is called again with the input data**
4. **Activity processes the input and returns result**

## Example: Scoping Phase with Human Reviews

```python
@workflow.defn
class TestCycleWorkflow:
    def __init__(self):
        self.tester_review_complete = False
        self.tester_review_data = None
        self.report_owner_approval_complete = False
        self.report_owner_approval_data = None
    
    @workflow.signal
    async def tester_review_signal(self, review_data: Dict[str, Any]):
        """Signal sent when tester completes attribute review"""
        self.tester_review_data = review_data
        self.tester_review_complete = True
    
    @workflow.signal
    async def report_owner_approval_signal(self, approval_data: Dict[str, Any]):
        """Signal sent when report owner completes approval"""
        self.report_owner_approval_data = approval_data
        self.report_owner_approval_complete = True
    
    async def execute_scoping_phase(self, input_data):
        # Step 1: Start scoping phase
        result = await workflow.execute_activity(
            start_scoping_phase_activity,
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        # Step 2: Generate LLM recommendations
        llm_result = await workflow.execute_activity(
            generate_llm_recommendations_activity,
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy
        )
        
        # Step 3: Wait for tester review
        # First call returns "awaiting" status
        review_result = await workflow.execute_activity(
            tester_review_attributes_activity,
            args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Wait for tester to complete review (signal)
        await workflow.wait_condition(lambda: self.tester_review_complete)
        
        # Call activity again with review data
        review_result = await workflow.execute_activity(
            tester_review_attributes_activity,
            args=[
                input_data.cycle_id, 
                input_data.report_id, 
                input_data.user_id, 
                self.tester_review_data
            ],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Step 4: Wait for report owner approval
        if review_result['data'].get('requires_report_owner_approval'):
            # First call returns "awaiting" status
            approval_result = await workflow.execute_activity(
                report_owner_approval_activity,
                args=[input_data.cycle_id, input_data.report_id, input_data.user_id, None],
                start_to_close_timeout=timedelta(minutes=5)
            )
            
            # Wait for report owner approval (signal)
            await workflow.wait_condition(lambda: self.report_owner_approval_complete)
            
            # Call activity again with approval data
            approval_result = await workflow.execute_activity(
                report_owner_approval_activity,
                args=[
                    input_data.cycle_id,
                    input_data.report_id,
                    input_data.user_id,
                    self.report_owner_approval_data
                ],
                start_to_close_timeout=timedelta(minutes=5)
            )
        
        # Step 5: Complete scoping phase
        complete_result = await workflow.execute_activity(
            complete_scoping_phase_activity,
            args=[
                input_data.cycle_id,
                input_data.report_id,
                input_data.user_id,
                {
                    'llm_result': llm_result,
                    'review_result': review_result,
                    'approval_result': approval_result
                }
            ],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        return complete_result
```

## API Endpoint to Send Signals

```python
@router.post("/{cycle_id}/reports/{report_id}/tester-review")
async def submit_tester_review(
    cycle_id: int,
    report_id: int,
    review_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    temporal_client = Depends(get_temporal_client)
):
    """Submit tester review decisions to workflow"""
    
    # Get workflow handle
    workflow_id = f"test-cycle-{cycle_id}"
    handle = temporal_client.get_workflow_handle(workflow_id)
    
    # Send signal with review data
    await handle.signal(
        "tester_review_signal",
        {
            "attribute_decisions": review_data["decisions"],
            "reviewer_id": current_user.user_id,
            "reviewed_at": datetime.utcnow().isoformat()
        }
    )
    
    return {"message": "Review submitted successfully"}
```

## Benefits of This Pattern

1. **No Polling**: Workflow efficiently waits for signals
2. **State Preservation**: All state is preserved in the workflow
3. **Resilience**: If the worker crashes, workflow resumes from last state
4. **Visibility**: Can query workflow for current state
5. **Timeout Support**: Can add timeouts for human actions

## Query Support for UI

```python
@workflow.query
def get_current_phase_status(self) -> Dict[str, Any]:
    """Query to get current phase status for UI"""
    return {
        "current_phase": self.current_phase,
        "awaiting_action": self.get_awaiting_action(),
        "phase_progress": self.phase_progress
    }

@workflow.query  
def get_awaiting_action(self) -> Optional[str]:
    """Get what action the workflow is waiting for"""
    if self.current_phase == "Scoping":
        if not self.tester_review_complete:
            return "tester_review"
        elif not self.report_owner_approval_complete:
            return "report_owner_approval"
    return None
```

## Implementation Steps

1. **Update all activities** to support optional input data parameter
2. **Add signals** to workflow for each human interaction point
3. **Create API endpoints** to send signals when users complete actions
4. **Add queries** for UI to check workflow state
5. **Update UI** to poll queries and show appropriate screens

## Considerations

- **Timeouts**: Add reasonable timeouts for human actions
- **Reminders**: Use Temporal timers to send reminder notifications
- **Delegation**: Support reassigning tasks to other users
- **Audit Trail**: All signals are recorded in workflow history
- **Error Handling**: Handle cases where invalid data is signaled