from typing import TypedDict, Dict, Any, List

class OrchestrationState(TypedDict):
    """
    Structured state representing the execution context of the orchestrator.
    """
    # Trigger source details
    source: str             # Trigger type: 'cron', 'hook', or 'prompt'
    payload: Dict[str, Any] # Raw JSON / input dictionary sent to the trigger
    user_prompt: str        # Extracted or provided main instruction / query
    
    # Internal agent/runner states
    messages: List[Dict[str, Any]] # Simulated or real message trace/conversation history
    next_step: str          # Routing directive: 'execute', 'finalize', or 'orchestrate'
    
    # Output results
    response: str           # Final summary / output string generated
    status: str             # Execution status: 'success', 'failed', 'running'
    errors: List[str]       # Any warnings or error messages caught during run
