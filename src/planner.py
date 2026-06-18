from autogen import AssistantAgent
import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv
import os,json
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)


trial2="""You are a web automation task planner. You will receive tasks from the user. You will think step by step and break down the tasks into sequence of simple subtasks.
    Return only in this format:
    strictly a well-formatted JSON with 3 attributes.
    The attributes will be as follows,
    "step_id": This is an integer that represents the number of the step. It takes values starting from 1 and then increments for each step.
    "step": This is a string that contains the step that reflects the activity to be performed on the browser to complete the task given by the user. It should be short, to the point.
    "value": This is a string that contains the selectors required for the "step" to be performed. This can be a link or any field or any particular text to be typed to execute the step or any other relevant entity. This attribute only needs to be present when it can be inferred.
    If the user input explicitly or implicitly says to select "any" or "a random" item, assume the rule is to select the first available item in the list.
    Don't write any explanations or anything extra except each subtask. 
    Your output should be consistent everytime the same task appears.

    Example 1:
    Task = Find the price of Adidas shoes
    Output should be like,
    [
      {
        "step_id": 1,
        "step": "Navigate to Adidas website",
        "value": "https://www.adidas.com/"
      },
      {
        "step_id": 2,
        "step": "Input the search term 'shoes' in the search bar",
        "value": "shoes"
      },
      {
        "step_id": 3,
        "step": "click the 'search' button",
        "value": "search"
      },
      {
        "step_id": 4,
        "step": "Select 'first' pair of shoes",
        "value": "first"
      },
      {
        "step_id": 5,
        "step": "Identify their 'price'",
        "value": "price"
      }
    ]

    Example 2:
    Task = I want to subscribe to the Times of India newsletter with the email 'abc@gmail.com'.
    Output should be like,
    [
      {
        "step_id": 1,
        "step": "Navigate to Times of India website",
        "value": "https://timesofindia.indiatimes.com/"
      },
      {
        "step_id": 2,
        "step": "Input the 'email' address into the newsletter 'subscription' field",
        "value": "abc@gmail.com"
      },
      {
        "step_id": 3,
        "step": "Click the subscribe button",
        "value": "subscribe"
      }
    ]
    """
    
planner_system_prompt = """
You are an AI Planner agent in a multi-agent web automation system. You will receive tasks from the user and break them down into logically sequenced subtasks suitable for execution by a PlayWright Executor. A Supervisor provides feedback that you must use to continue, replan, or backtrack.

YOUR RESPONSIBILITIES:
    1. Break down a user query into step-by-step actions for web scraping and automation.
    2. Be aware of the accesbility tree provided in context.
    3. If no site is provided by the user, try to interpret the website from the brands etc. mentioned, if not found any clue then use a search engine (preferably precise link for the query on bing) and then extract the search results to extract first 5 related different site search links .
    4. Navigate* the links of the websites listed by the search engine one by one . 
    5. For each website:
        Focus only on the specific details requested in the user’s goal and generate the a good step plan .
        Do not open or plan for every individual product unless necessary.
    6. Always follow the above steps 3,4&5 don't plan randomly anything like click on first website in bing search results, operation must be to navigate  first search result in bing search and so on.
    7. Always remember after the task is finished on a particular website the plan should be to navigate to the next website,till all websites are visited ,instead of navigating to bing page and then navigate to next.
    8. Aggregate results across multiple sites for final comparison.
    9. Store results from each site in short-term memory for multi-site analysis.
    10. Generate only one step at a time and wait for Supervisor feedback before continuing.
    11. If a step fails, use Supervisor feedback to replan or backtrack.

CONTEXT PROVIDED:
- Current Site: {site_url}
- Accessibility Tree: {accessibility_tree}
- User Goal: {user_query}
- Step History: [{"step_id", "step", "operation", "target", "details"}]
- Supervisor Feedback: [{ "success_status", "reasoning","expected_vs_actual","is_terminate"}]

STEP REQUIREMENTS:
- Be specific and actionable (include URLs, exact text)
- One atomic action per step
- Playwright-compatible operations (like navigate, click, fill, extract, select)

OUTPUT FORMAT:
    - Strictly a JSON object (curly brackets) in single line.
    - If the user query requests "any" or "random" items, return details of all available items.
    - No explanations or extra text.
    - Only output the format given don't give any explanations or any extra text
    - Output must be consistent for repeated tasks.
{
    "step_id": integer,
    "step": "clear description of what to accomplish",
    "operation": "navigate|click|fill|extract|select",
    "target": "what element/content in the accessibility tree to interact with",
    "details": {
        "url": "for navigate operations",
        "text": "for fill operations",
        "data_type": ["for extract operations (price, title, link, etc.)"]
    }
}

EXAMPLES:
{"step_id": 1,"step": "Navigate to Amazon homepage","operation": "navigate","target": "Amazon main page","details": {"url": "https://amazon.com"}}

{"step_id": 2,"step": "Extract required product with minimum price, more ratings,reviews from search results ","operation": "extract","target": "first product","details": {"data_type": ["price"]}}
"""
def custom_generate(agent, messages, sender, config):
    model = config.get("model")
    # user_query = [m for m in messages if m["role"] == "user"][-1:]
    # supervisor_msg = [m for m in messages if m["role"] == "Supervisor"][-1:]
    user_messages = []
    for m in messages:
        if m["role"] == "user":
            user_messages.append(m)
    
    user_query=user_messages[-1]["content"]

    for i in range(-1,-len(messages)-1,-1):
      if messages[i]["role"]=="Supervisor":
        supervisor_msg=messages[i]["content"]
        supervisor_msg=str(supervisor_msg)
        # supervisor_msg="success: "+supervisor_msg
        # print(supervisor_msg)
        break

    terminate_cond=False
    planner_history = []
    for i in range(-1,-len(messages)-1,-1):
        if len(planner_history)==8:
          break
        if messages[i]["role"] == "Planner":
                content_dict = json.loads(messages[i]["content"])
                planner_history.append(content_dict)
    tree=""
    site=""
    with open("accessibility_tree.json", "r", encoding="utf-8") as f:
            if tree is not "":
              tree = json.load(f)
    # for i in range(-1,-len(messages)-1,-1):
    #   if messages[i]["role"]=="Executor":
    #     tree=messages[i]["updated_tree"]
    #     break
    for i in range(-1,-len(messages)-1,-1):
      if messages[i]["role"]=="Executor":
        terminate_cond=messages[i]["content"]["terminate"]
        site=messages[i]["content"]["updated_url"]
        break
    sup_fdb=False
    for i in range(-1,-len(messages)-1,-1):
      if messages[i]["role"]=="Supervisor": 
          sup_fdb=True
          context =f"""
          "site_url":{site},
          "accessibility_tree":{json.dumps(tree, ensure_ascii=False)},
          "step_history":{planner_history},
          "supervisor_feedback":{supervisor_msg}
    """
    if not sup_fdb:
        context =f"""
          "site_url":{site},
          "accessibility_tree":{json.dumps(tree, ensure_ascii=False)},
          "step_history":{planner_history},
    """
    if terminate_cond:
        return True,{"role":"Planner","content":"terminate"}
    # messages = user_query + [{"role":"assistant","content":context}]
    # cfg = config["config_list"][0]

    # client = OpenAI(
    #     base_url=cfg["base_url"],   
    #     api_key=cfg["api_key"],
    # )
    # completion = client.chat.completions.create(
    #     model=cfg["model"],         
    #     messages=[
            
    #             {"role": "system", "content": planner_system_prompt},   
    #             {"role":"assistant","content":context},
    #             {"role":"user","content":user_query}
            
    #     ]
    # )
    model = genai.GenerativeModel('gemini-2.5-flash') 

    response = model.generate_content(
        [
            planner_system_prompt,
            f"User Task: {user_query}\nContext:\n{context}\n\nOutput:"
        ]
    )
    actions=response.text
    actions = actions.strip()
    if actions.startswith("```"):
        actions = actions.split("```")[1]  # take inside block
    if actions.startswith("json"):
        actions = actions[4:].strip()
    # print(actions)
    # import ast,re
    # actions = completion.choices[0].message.content
    # # print(actions)
    # _, sep, after = actions.partition("</think>")
    # if sep:  
    #     clean_output = after.strip()
    # else:   
    #     clean_output = actions.strip()

# #     return clean_output
    # def safe_literal_eval(s: str):
    #   s = s.strip()
  
    #   # 1. Balance braces if count mismatch
    #   open_count = s.count("{")
    #   close_count = s.count("}")
    #   if open_count > close_count:
    #       # Add missing closing braces
    #       s += "}" * (open_count - close_count)
    #   elif close_count > open_count:
    #       # Too many, reduce to match
    #       s = re.sub(r'}+$', '}' * open_count, s)
  
    #   # 2. Try ast.literal_eval
    #   try:
    #       return ast.literal_eval(s)
    #   except Exception:
    #       # 3. Fallback: try JSON
    #       try:
    #           return json.loads(s)
    #       except Exception as e:
    #           raise ValueError(f"Failed to parse planner output: {s}\nError: {e}")
        
    # new_acts = safe_literal_eval(clean_output)

    # # print(new_acts)
    # if "details" in new_acts:
    #    if "url" in "details":
    #       urll=new_acts["details"]["url"]
    #       urll=urll+"/"
    #       new_acts["details"]["url"]=urll
    # # print(urll)
    # # print(new_acts)


    # p_actions=json.dumps(new_acts)
    # new_acts=json.loads()


    return True,{"role":"Planner","content":actions}


planner = AssistantAgent(
    name="planner",
    llm_config= {
    "config_list": [
        {
            "model": "qwen/qwen3-235b-a22b:free",  
            "api_key": "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",
            "base_url": "https://openrouter.ai/api/v1"
        }
    ]
    }
)

planner_llm_config=planner.llm_config
planner.register_reply(
    trigger=lambda sender: True,
    reply_func=custom_generate,
    config=planner_llm_config # Pass the config here
)



