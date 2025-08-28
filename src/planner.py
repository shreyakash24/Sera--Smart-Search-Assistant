from autogen_agentchat.agents import AssistantAgent
import os
import requests
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN=os.environ.get("HF_TOKEN4")
BASE_URL = "https://api-inference.huggingface.co/models/"

planner_system_prompt = """
You are an AI Planner agent in a multi-agent web automation system. You will receive tasks from the user and break them down into logically sequenced subtasks suitable for execution by a PlayWright Executor. A Supervisor provides feedback that you must use to continue, replan, or backtrack.

YOUR RESPONSIBILITIES:
    1. Break down a user query into step-by-step actions for web scraping and automation.
    2. If no site is provided by the user and you cannot interpret it, visit and search for the user's query in a search engine (preferably bing) and then visit the links of the websites listed by the search engine one by one. Scroll if needed.
    3. When on a particular website no need to access each product one by one unless its details are asked explicitly.
    4. Aggregate results across multiple sites for final comparison.
    5. Store results from each site in short-term memory for multi-site analysis.
    6. Generate only one step at a time and wait for Supervisor feedback before continuing.
    7. If a step fails, use Supervisor feedback to replan or backtrack.

CONTEXT PROVIDED:
- Current Site: {site_url}
- Accessibility Tree: {accessibility_tree}
- User Goal: {user_query}
- Step History: [{"step_id", "step", "operation", "target", "details"}]
- Supervisor Feedback: [{"step_id", "success_status", "error"}]

STEP REQUIREMENTS:
- Be specific and actionable (include URLs, exact text)
- One atomic action per step
- Playwright-compatible operations (like navigate, click, fill, extract, scroll, select)

OUTPUT FORMAT:
    - Strictly a JSON object (curly brackets) in single line.
    - If the user query requests "any" or "random" items, return details of all available items.
    - No explanations or extra text.
    - Output must be consistent for repeated tasks.
{
    "step_id": integer,
    "step": "clear description of what to accomplish",
    "operation": "navigate|click|fill|extract|scroll|select",
    "target": "what element/content in the accessibility tree to interact with",
    "details": {
        "url": "for navigate operations",
        "text": "for fill operations",
        "data_type": ["for extract operations (price, title, link, etc.)"]
    }
}

EXAMPLES:
{"step_id": 1,"step": "Navigate to Amazon homepage","operation": "navigate","target": "Amazon main page","details": {"url": "https://amazon.com"}}

{"step_id": 3,"step": "Extract price of first search result","operation": "extract","target": "first product","details": {"data_type": ["price"]}}
"""


def hf_chat(model: str, messages: list):
    url=f"{BASE_URL}{model}"
    headers={"Authorization":f"Bearer {HF_TOKEN}"}
    payload={
        "model": model,
        "messages": messages
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    
    full_output = result["choices"][0]["message"]["content"]
    _, sep, after = full_output.partition("</think>")
    if sep:  
        clean_output = after.strip()
    else:   
        clean_output = full_output.strip()

    return clean_output

def custom_generate(messages, config):
    model = config.get("model")
    user_query = [m for m in messages if m["role"] == "Supervisor" and "metadata" in m and "from_user" in m["metadata"] and m["metadata"]["from_user"]==True][-1:]
    system_msg = [{"role": "System", "content": planner_system_prompt}]
    supervisor_msg = [m for m in messages if m["role"] == "Supervisor" and "metadata" in m and "from_user" in m["metadata"] and m["metadata"]["from_user"]==False][-1:]
    planner_history = [m for m in messages if m["role"] == "Planner"][-10:]
    messages = system_msg + user_query + supervisor_msg + planner_history

    return hf_chat(model, messages)


planner= AssistantAgent(
    name="Planner",
    llm_config={
        "model": "Qwen/Qwen3-30B-A3B",
        "custom_generate": custom_generate,
        "temperature": 0,
    }
)