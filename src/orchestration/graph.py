import json
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.orchestration.state import OrchestrationState
from src.orchestration.config import (
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    OPENAI_MODEL_NAME,
    IS_MOCK_MODE
)

# ----------------------------------------------------
# Node Definitions
# ----------------------------------------------------

def parse_input_node(state: OrchestrationState) -> Dict[str, Any]:
    """
    Parses incoming triggers, sets default prompts if missing, 
    and initializes execution status.
    """
    source = state.get("source", "prompt")
    payload = state.get("payload") or {}
    user_prompt = state.get("user_prompt") or ""
    
    # If this was triggered by a cron and we don't have a prompt, synthesize one
    if source == "cron" and not user_prompt:
        job_name = payload.get("job_name", "unnamed_cron")
        user_prompt = f"Executing cron tasks for job: {job_name}"
    
    # If triggered by a webhook/hook and we don't have a prompt, synthesize one
    if source == "hook" and not user_prompt:
        event = payload.get("event", "generic_event")
        user_prompt = f"Processing webhook hook event: {event}"
        
    print(f"[Node: parse_input] Source: {source} | Prompt: '{user_prompt}'")
    
    return {
        "user_prompt": user_prompt,
        "messages": [
            {"role": "system", "content": f"Initialized workflow triggered by '{source}'."}
        ],
        "status": "running",
        "errors": []
    }

def agent_orchestrator_node(state: OrchestrationState) -> Dict[str, Any]:
    """
    Core brain of the orchestrator. Evaluates the prompt/context and 
    determines whether to run system actions or generate the final response.
    """
    source = state["source"]
    payload = state.get("payload") or {}
    user_prompt = state["user_prompt"]
    messages = state.get("messages") or []
    
    print(f"[Node: agent_orchestrator] Evaluating next steps...")
    
    if IS_MOCK_MODE:
        # Mock LLM Logic
        print("[agent_orchestrator] Running in Mock/Simulated LLM mode.")
        
        # Decide if we need to perform an action first
        # We simulate a workflow where if it is a hook/cron, we do a simulation action first.
        has_executed_action = any(m.get("content", "").startswith("Executed action:") for m in messages)
        
        if (source in ["cron", "hook"]) and not has_executed_action:
            # Route to action execution node
            next_step = "execute"
            response = ""
            new_message = {
                "role": "assistant",
                "content": f"Need to execute simulated action for source '{source}' with payload {json.dumps(payload)}."
            }
        else:
            # Finalize immediately
            next_step = "finalize"
            response = f"Simulated success response for prompt: '{user_prompt}' (triggered by {source})."
            new_message = {
                "role": "assistant",
                "content": response
            }
    else:
        # Real OpenAI Compatible API Logic
        print(f"[agent_orchestrator] Calling OpenAI-compatible model: {OPENAI_MODEL_NAME} at {OPENAI_API_BASE}")
        try:
            # Initialize client
            llm = ChatOpenAI(
                openai_api_base=OPENAI_API_BASE,
                openai_api_key=OPENAI_API_KEY,
                model_name=OPENAI_MODEL_NAME,
                temperature=0.2
            )
            
            # Format chat context
            system_instruction = (
                "You are a short orchestration agent. Your job is to process incoming requests (crons, webhooks, or prompts). "
                "Respond directly if it is a standard prompt. "
                "If it's a cron/hook request, explain what was triggered and output 'ACTION_NEEDED: <description>' if "
                "an action needs execution, otherwise summarize the trigger status."
            )
            
            chat_messages = [SystemMessage(content=system_instruction)]
            for m in messages:
                if m["role"] == "system":
                    chat_messages.append(SystemMessage(content=m["content"]))
                elif m["role"] == "assistant":
                    chat_messages.append(SystemMessage(content=m["content"])) # treat assistant steps as context
            
            chat_messages.append(HumanMessage(content=f"Trigger Source: {source}\nPayload: {json.dumps(payload)}\nPrompt: {user_prompt}"))
            
            res = llm.invoke(chat_messages)
            llm_content = str(res.content)
            
            new_message = {"role": "assistant", "content": llm_content}
            
            if "ACTION_NEEDED" in llm_content:
                next_step = "execute"
                response = ""
            else:
                next_step = "finalize"
                response = llm_content
                
        except Exception as e:
            error_msg = f"LLM Invocation error: {str(e)}"
            print(f"[agent_orchestrator] Error: {error_msg}")
            return {
                "status": "failed",
                "errors": state.get("errors", []) + [error_msg],
                "next_step": "finalize",
                "response": "Orchestration failed due to LLM invocation error."
            }
            
    updated_messages = messages + [new_message]
    return {
        "messages": updated_messages,
        "next_step": next_step,
        "response": response
    }

def action_executor_node(state: OrchestrationState) -> Dict[str, Any]:
    """
    Executes mock system actions / simulated hooks/crons processes.
    In a full implementation, this could call DBs, external APIs, or other agents.
    """
    source = state["source"]
    payload = state.get("payload") or {}
    messages = state.get("messages") or []
    
    print(f"[Node: action_executor] Executing operations for {source}...")
    
    # Simulate processing work
    action_details = f"Processed {source} payload elements: {list(payload.keys())}"
    execution_log = f"Executed action: {action_details}. All systems normal."
    
    print(f"[action_executor] Run completed: {execution_log}")
    
    updated_messages = messages + [
        {"role": "system", "content": execution_log}
    ]
    
    # Once action is run, return to orchestrator to determine final response
    return {
        "messages": updated_messages,
        "next_step": "orchestrate"
    }

def finalize_response_node(state: OrchestrationState) -> Dict[str, Any]:
    """
    Wraps up the final execution state, sets status and return messages.
    """
    response = state.get("response") or ""
    errors = state.get("errors") or []
    
    print(f"[Node: finalize_response] Wrapping up orchestration state.")
    
    # If response is empty (e.g. from action executor without final output), summarize the logs
    if not response:
        messages = state.get("messages") or []
        last_assistant_msg = next((m["content"] for m in reversed(messages) if m["role"] == "assistant"), "")
        response = last_assistant_msg or "Orchestration workflow completed successfully."
        
    status = "failed" if errors else "success"
    
    return {
        "status": status,
        "response": response
    }

# ----------------------------------------------------
# Router Logic
# ----------------------------------------------------

def router_condition(state: OrchestrationState) -> str:
    """
    Determines transition edge from orchestrator.
    """
    return state.get("next_step", "finalize")

# ----------------------------------------------------
# Build the Graph
# ----------------------------------------------------

workflow = StateGraph(OrchestrationState)

# Add Nodes
workflow.add_node("parse_input", parse_input_node)
workflow.add_node("agent_orchestrator", agent_orchestrator_node)
workflow.add_node("action_executor", action_executor_node)
workflow.add_node("finalize_response", finalize_response_node)

# Set Entry Point
workflow.set_entry_point("parse_input")

# Define Transitions
workflow.add_edge("parse_input", "agent_orchestrator")

# Conditional Routing from orchestrator
workflow.add_conditional_edges(
    "agent_orchestrator",
    router_condition,
    {
        "execute": "action_executor",
        "orchestrate": "agent_orchestrator",
        "finalize": "finalize_response"
    }
)

# Return path from action_executor to orchestrator
workflow.add_edge("action_executor", "agent_orchestrator")

# End edge
workflow.add_edge("finalize_response", END)

# Compile Graph (Stateless: no checkpoint saver needed)
app = workflow.compile()
