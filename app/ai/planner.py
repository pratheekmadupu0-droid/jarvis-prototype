"""
JARVIS AI Planning & Multi-Step Execution Engine
Implements the core cycle: Listen -> Understand -> Plan -> Execute -> Verify -> Respond.
Integrates OpenAI / OpenRouter function calling with offline intent parsing fallback.
"""

from __future__ import annotations
import json
import re
from typing import Dict, Any, List, Optional, Callable
from openai import OpenAI

from app.config import Config, DESKTOP_DIR
from app.tools.registry import registry
from app.tools.base import ToolResult
from app.memory.memory_manager import memory_manager
from app.security.guardrails import SecurityGuardrails


class AIPlanner:
    """Orchestrates AI intent understanding, tool selection, multi-step execution, and verification."""

    def __init__(self):
        self.conversation_history: List[Dict[str, str]] = []
        self._init_client()

        # Step callback: callback(step_number, total_steps, description, status)
        self.on_step_update: Optional[Callable[[int, int, str, str], None]] = None
        self.on_state_change: Optional[Callable[[str], None]] = None

    def _init_client(self):
        api_key = Config.AI_API_KEY
        base_url = Config.AI_BASE_URL if Config.AI_BASE_URL else None
        if api_key:
            try:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            except Exception as e:
                print(f"[AIPlanner] Client init error: {e}")
                self.client = None
        else:
            self.client = None

    def plan_and_execute(self, user_prompt: str) -> Dict[str, Any]:
        """Full pipeline: Understand -> Plan -> Execute -> Verify -> Respond."""
        prompt = user_prompt.strip()
        if not prompt:
            return {"status": "failed", "response": "I didn't catch that. Please speak a command."}

        if self.on_state_change:
            self.on_state_change("Received")

        # Check offline intent matcher first for rapid zero-latency commands
        offline_match = self._match_offline_intent(prompt)
        if offline_match:
            return self._execute_plan(offline_match["steps"], prompt)

        # Use AI function calling if client is configured
        if self.client:
            try:
                if self.on_state_change:
                    self.on_state_change("Planning")

                tools = registry.get_openai_tools_schema()
                system_prompt = self._build_system_prompt()

                messages = [{"role": "system", "content": system_prompt}]
                # Append recent history
                messages.extend(self.conversation_history[-6:])
                messages.append({"role": "user", "content": prompt})

                # Call AI model
                response = self.client.chat.completions.create(
                    model=Config.AI_MODEL,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )

                choice = response.choices[0]
                message = choice.message

                # If tool calls were generated
                if message.tool_calls:
                    steps = []
                    for tc in message.tool_calls:
                        func_name = tc.function.name
                        try:
                            args = json.loads(tc.function.arguments)
                        except Exception:
                            args = {}
                        steps.append({"tool": func_name, "args": args, "description": f"Execute {func_name}"})

                    return self._execute_plan(steps, prompt)
                else:
                    # Natural conversational response
                    reply = message.content or "Task acknowledged."
                    self.conversation_history.append({"role": "user", "content": prompt})
                    self.conversation_history.append({"role": "assistant", "content": reply})
                    if self.on_state_change:
                        self.on_state_change("Completed")
                    return {"status": "completed", "response": reply, "steps_executed": []}

            except Exception as e:
                print(f"[AIPlanner] AI API error: {e}. Falling back to rule parser.")

        # Fallback to smart rule-based decomposition
        fallback_steps = self._decompose_fallback(prompt)
        if fallback_steps:
            return self._execute_plan(fallback_steps, prompt)

        return {
            "status": "completed",
            "response": f"I heard '{prompt}', but no matching action was required.",
            "steps_executed": []
        }

    def _execute_plan(self, steps: List[Dict[str, Any]], user_prompt: str) -> Dict[str, Any]:
        """Execute a sequence of planned steps with verification."""
        total_steps = len(steps)
        executed = []
        final_messages = []
        requires_confirmation = False
        confirmation_info = None

        if self.on_state_change:
            self.on_state_change("Executing")

        for idx, step in enumerate(steps, 1):
            if SecurityGuardrails.is_stopped():
                if self.on_state_change:
                    self.on_state_change("Cancelled")
                return {"status": "cancelled", "response": "Execution cancelled by emergency stop."}

            tool_name = step["tool"]
            args = step.get("args", {})
            desc = step.get("description", f"Running {tool_name}")

            if self.on_step_update:
                self.on_step_update(idx, total_steps, desc, "Executing")

            # Execute tool
            res: ToolResult = registry.execute_tool(tool_name, args)

            # Verification step
            status_str = "Completed" if res.success else "Failed"
            if res.requires_confirmation:
                status_str = "Awaiting confirmation"
                requires_confirmation = True
                confirmation_info = {
                    "tool": tool_name,
                    "prompt": res.confirmation_prompt,
                    "payload": res.confirmation_payload
                }

            if self.on_step_update:
                self.on_step_update(idx, total_steps, desc, status_str)

            executed.append({
                "step": idx,
                "tool": tool_name,
                "args": args,
                "success": res.success,
                "message": res.message,
                "data": res.data
            })

            final_messages.append(res.message)

            if not res.success and not res.requires_confirmation:
                # Stop if critical step failed
                break

        overall_status = "awaiting_confirmation" if requires_confirmation else ("completed" if all(e["success"] for e in executed) else "failed")
        if self.on_state_change:
            self.on_state_change(overall_status.capitalize())

        combined_response = "\n\n".join(final_messages)
        self.conversation_history.append({"role": "user", "content": user_prompt})
        self.conversation_history.append({"role": "assistant", "content": combined_response})

        return {
            "status": overall_status,
            "response": combined_response,
            "steps_executed": executed,
            "requires_confirmation": requires_confirmation,
            "confirmation_info": confirmation_info
        }

    def _match_offline_intent(self, text: str) -> Optional[Dict[str, Any]]:
        """Fast offline matcher for common direct commands."""
        lowered = text.lower().strip()

        # Folder creation (e.g. "create a folder named Gromighty on my desktop", "create folder Test", "make a new folder called Sample")
        m_folder = re.search(r"(?:create|make)\s+(?:a\s+|new\s+)*folder\s+(?:(?:named|called)\s+)?([a-zA-Z0-9_\-]+)", lowered)
        if m_folder:
            name = m_folder.group(1).strip()
            # Check for subfolders (e.g. "and create Clients, Projects inside it")
            subfolders = []
            m_subs = re.search(r"(?:and\s+create|with\s+(?:subfolders?|folders?))\s+([a-zA-Z0-9_,\s]+?)(?:\s+inside\s+it|$)", lowered)
            if m_subs:
                subs_raw = m_subs.group(1).replace("and", ",").replace(".", "")
                subfolders = [s.strip().capitalize() for s in subs_raw.split(",") if s.strip()]
            return {"steps": [{"tool": "create_folder", "args": {"path": name.capitalize(), "subfolders": subfolders}, "description": f"Create directory {name} on Desktop"}]}

        # Time queries
        if re.search(r"what('?s| is)? the (current )?time", lowered) or lowered in ("time", "what time is it"):
            # Check city
            m_city = re.search(r"\b(?:in|for|at)\b\s+([a-zA-Z\s]+?)(?:\?|$)", lowered)
            city = m_city.group(1).strip() if m_city else None
            return {"steps": [{"tool": "get_time", "args": {"city": city}, "description": "Check current time"}]}

        # Date queries
        if re.search(r"what('?s| is)? (today'?s )?date", lowered) or "what day is tomorrow" in lowered or "next monday" in lowered:
            target = "tomorrow" if "tomorrow" in lowered else ("next monday" if "next monday" in lowered else "today")
            return {"steps": [{"tool": "get_date", "args": {"relative_target": target}, "description": "Check date"}]}

        # Weather queries
        if "weather" in lowered or "temperature" in lowered or "will it rain" in lowered:
            m_city = re.search(r"\b(?:in|for|at)\b\s+([a-zA-Z\s]+?)(?:\s+today|\s+tomorrow|\?|$)", lowered)
            city = m_city.group(1).strip() if m_city else None
            target_day = "tomorrow" if "tomorrow" in lowered else "today"
            return {"steps": [{"tool": "get_weather", "args": {"city": city, "target_day": target_day}, "description": f"Fetch weather for {city or 'default city'}"}]}

        # News queries
        if "news" in lowered or "headlines" in lowered:
            topic = "technology"
            if "india" in lowered:
                topic = "India"
            elif "ai" in lowered or "artificial intelligence" in lowered:
                topic = "AI"
            elif "cybersecurity" in lowered:
                topic = "cybersecurity"
            return {"steps": [{"tool": "get_news", "args": {"query": topic}, "description": f"Fetch latest {topic} news"}]}

        # Timers
        m_timer = re.search(r"set (?:a )?timer for (\d+\s*(?:minutes?|seconds?|hours?))", lowered)
        if m_timer:
            dur = m_timer.group(1)
            return {"steps": [{"tool": "set_timer", "args": {"duration": dur}, "description": f"Set timer for {dur}"}]}

        # Cancel timer
        if "cancel" in lowered and ("timer" in lowered or "reminder" in lowered):
            m_cancel = re.search(r"cancel (?:my )?(.+)", lowered)
            ident = m_cancel.group(1).strip() if m_cancel else "timer"
            return {"steps": [{"tool": "cancel_reminder", "args": {"identifier": ident}, "description": f"Cancel {ident}"}]}

        # Pending reminders
        if "pending reminders" in lowered or "show reminders" in lowered or "my reminders" in lowered:
            return {"steps": [{"tool": "list_reminders", "args": {}, "description": "List all reminders"}]}

        # YouTube playback
        m_yt = re.search(r"(?:open|play|search)\s+youtube\s+(?:for\s+)?(.+)", lowered)
        if m_yt:
            query = m_yt.group(1).strip()
            return {"steps": [{"tool": "search_youtube", "args": {"query": query, "autoplay": True}, "description": f"Search and play YouTube: {query}"}]}

        # General YouTube open
        if lowered in ("open youtube", "youtube"):
            return {"steps": [{"tool": "launch_application", "args": {"app_name": "youtube"}, "description": "Open YouTube"}]}

        # WhatsApp Open
        if lowered in ("open whatsapp", "whatsapp"):
            return {"steps": [{"tool": "whatsapp_open", "args": {}, "description": "Open WhatsApp Desktop"}]}

        # WhatsApp Send Message
        m_wa = re.search(r"(?:send|message)\s+([a-zA-Z0-9_+]+)\s+(?:a\s+)?(?:whatsapp\s+)?(?:message\s+)?saying\s+(.+)", lowered)
        if not m_wa:
            m_wa = re.search(r"(?:send|message)\s+([a-zA-Z0-9_+]+)\s+that\s+(.+)", lowered)
        if m_wa:
            recipient = m_wa.group(1).strip()
            msg = m_wa.group(2).strip()
            return {"steps": [{"tool": "whatsapp_draft_message", "args": {"recipient": recipient, "message": msg}, "description": f"Draft WhatsApp to {recipient}"}]}

        # Gmail Open
        if lowered in ("open gmail", "gmail"):
            return {"steps": [{"tool": "launch_application", "args": {"app_name": "gmail"}, "description": "Open Gmail"}]}

        # Unread Emails
        if "unread emails" in lowered or "check emails" in lowered or "summarize my emails" in lowered:
            return {"steps": [{"tool": "gmail_unread_emails", "args": {"max_results": 5}, "description": "Check unread emails"}]}

        # Google Search
        m_google = re.search(r"(?:search\s+for\s+|search\s+)(.+?)\s+(?:on\s+|in\s+)?google", lowered)
        if not m_google:
            m_google = re.search(r"google\s+(.+)", lowered)
        if not m_google:
            m_google = re.search(r"search\s+google\s+for\s+(.+)", lowered)
        if m_google:
            import urllib.parse
            q = m_google.group(1).strip()
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(q)}"
            return {"steps": [{"tool": "open_url", "args": {"url": search_url}, "description": f"Search Google for {q}"}]}

        # Open Google / Chrome / Browser activities
        if lowered in (
            "open google chrome activities", "open chrome activities", "google chrome activities",
            "open google chrome", "open google", "google", "open chrome", "chrome",
            "open browser", "browser"
        ):
            return {"steps": [{"tool": "launch_application", "args": {"app_name": "chrome"}, "description": "Open Google Chrome"}]}

        # Open Application (general)
        if lowered in ("open application", "open applications", "launch application", "open app"):
            return {"steps": [{"tool": "launch_application", "args": {"app_name": "application"}, "description": "Launch Application"}]}

        # Open Folder (e.g. "open folder gromighty", "open desktop", "open downloads", "open documents")
        m_open_folder = re.search(r"open\s+(?:the\s+)?folder\s+(?:named\s+|called\s+)?([a-zA-Z0-9_\-\s]+)", lowered)
        if not m_open_folder:
            m_open_folder = re.search(r"open\s+([a-zA-Z0-9_\-]+)\s+folder", lowered)
        if not m_open_folder and lowered in ("open desktop", "open my desktop", "open downloads", "open documents"):
            folder_target = lowered.replace("open", "").strip()
            return {"steps": [{"tool": "open_folder", "args": {"folder_name": folder_target}, "description": f"Open {folder_target}"}]}
        if m_open_folder:
            fn = m_open_folder.group(1).strip()
            return {"steps": [{"tool": "open_folder", "args": {"folder_name": fn}, "description": f"Open folder {fn}"}]}

        # Check direct desktop folder match (e.g. user says "open gromighty")
        if lowered.startswith("open "):
            candidate = lowered[5:].strip()
            if candidate:
                desktop_candidates = [
                    DESKTOP_DIR / candidate,
                    DESKTOP_DIR / candidate.capitalize(),
                    DESKTOP_DIR / candidate.upper()
                ]
                for dc in desktop_candidates:
                    if dc.exists() and dc.is_dir():
                        return {"steps": [{"tool": "open_folder", "args": {"folder_name": dc.name}, "description": f"Open folder {dc.name}"}]}

        # Applications
        for app in ["chatgpt", "notepad", "calculator", "calc", "vscode", "vs code", "explorer", "file explorer", "chrome"]:
            if f"open {app}" in lowered:
                clean_app = "calculator" if app == "calc" else ("vscode" if app == "vs code" else ("explorer" if app == "file explorer" else app))
                return {"steps": [{"tool": "launch_application", "args": {"app_name": clean_app}, "description": f"Launch {clean_app}"}]}

        return None

    def _decompose_fallback(self, text: str) -> List[Dict[str, Any]]:
        """Decompose complex multi-step prompts when offline."""
        lowered = text.lower()
        steps = []

        # Example: "create a folder named Gromighty on my desktop and create Clients, Projects, and Finance inside it"
        m_gromighty = re.search(r"create (?:a )?folder named (\w+)(?: on my desktop)?(?: and create (.+) inside it)?", lowered)
        if m_gromighty:
            folder_name = m_gromighty.group(1)
            subs_raw = m_gromighty.group(2)
            subfolders = []
            if subs_raw:
                subs_raw = subs_raw.replace("and", ",").replace(".", "")
                subfolders = [s.strip().capitalize() for s in subs_raw.split(",") if s.strip()]
            steps.append({
                "tool": "create_folder",
                "args": {"path": f"Desktop/{folder_name.capitalize()}", "subfolders": subfolders},
                "description": f"Create directory {folder_name} on Desktop"
            })
            return steps

        # Example: "prepare my project workspace, open VS Code, create the frontend and backend folders, and add a README"
        if "workspace" in lowered or "project" in lowered and "frontend" in lowered:
            steps.append({
                "tool": "create_project_structure",
                "args": {"project_name": "Workspace", "folders": ["frontend", "backend", "docs"]},
                "description": "Initialize project directory"
            })
            steps.append({
                "tool": "launch_application",
                "args": {"app_name": "vscode"},
                "description": "Open VS Code"
            })
            return steps

        return steps

    def _build_system_prompt(self) -> str:
        memory_context = memory_manager.summarize_memory_context()
        return f"""You are JARVIS, an advanced, highly intelligent voice-controlled AI personal assistant for Windows.
Core principle: Listen -> Understand -> Plan -> Execute -> Verify -> Respond.

When a user asks you to perform tasks, use the appropriate tools to perform REAL actions.
Always verify the result and report the exact outcome truthfully.
Never hallucinate breaking news, timestamps, or task completions.

{memory_context}
"""


planner = AIPlanner()
