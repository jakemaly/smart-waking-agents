import argparse
import json
import sys
from typing import Dict, Any

from src.orchestration.config import print_config
from src.orchestration.graph import app as orchestrator_app


def run_orchestration(source: str, user_prompt: str, payload: Dict[str, Any]):
    """
    Executes the LangGraph orchestrator with the specified arguments.
    """
    print_config()
    
    initial_state = {
        "source": source,
        "user_prompt": user_prompt,
        "payload": payload,
        "messages": [],
        "errors": []
    }
    
    print(f"\n[CLI] Starting orchestration flow (Source: {source})...")
    
    try:
        final_state = orchestrator_app.invoke(initial_state)
        
        print("\n=== Execution Results ===")
        print(f"Status: {final_state.get('status', 'unknown').upper()}")
        print(f"Response:\n{final_state.get('response', '')}")
        
        errors = final_state.get("errors", [])
        if errors:
            print("\nWarnings/Errors:")
            for err in errors:
                print(f"- {err}")
        
        print("=========================")
        
        if final_state.get("status") == "failed":
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[CLI] Critical failure running orchestration: {e}", file=sys.stderr)
        sys.exit(2)


def main():
    parser = argparse.ArgumentParser(
        description="CLI Tool for the LangGraph Orchestration Framework Skeleton."
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Trigger sub-command")

    # Prompt trigger
    prompt_parser = subparsers.add_parser("prompt", help="Run a manual user prompt query")
    prompt_parser.add_argument("--text", required=True, type=str, help="Prompt query text")

    # Cron trigger
    cron_parser = subparsers.add_parser("cron", help="Simulate a periodic cron run")
    cron_parser.add_argument("--job-name", required=True, type=str, help="Name of cron job")
    cron_parser.add_argument("--metadata", type=str, default="{}", help="Optional JSON metadata dict")

    # Webhook hook trigger
    hook_parser = subparsers.add_parser("hook", help="Simulate a webhook trigger event")
    hook_parser.add_argument("--event", required=True, type=str, help="Event name / type")
    hook_parser.add_argument("--data", type=str, default="{}", help="Optional JSON event payload string")

    args = parser.parse_args()

    if args.command == "prompt":
        run_orchestration(
            source="prompt",
            user_prompt=args.text,
            payload={}
        )
    elif args.command == "cron":
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError:
            print("[CLI Error] --metadata must be a valid JSON object string", file=sys.stderr)
            sys.exit(1)
            
        payload = {"job_name": args.job_name, **metadata}
        run_orchestration(
            source="cron",
            user_prompt=f"Triggered cron job: {args.job_name}",
            payload=payload
        )
    elif args.command == "hook":
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print("[CLI Error] --data must be a valid JSON object string", file=sys.stderr)
            sys.exit(1)
            
        payload = {"event": args.event, "event_data": data}
        run_orchestration(
            source="hook",
            user_prompt=f"Triggered webhook event: {args.event}",
            payload=payload
        )


if __name__ == "__main__":
    main()
