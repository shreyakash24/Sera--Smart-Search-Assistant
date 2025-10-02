import base64
import json
from openai import OpenAI
from autogen import AssistantAgent

sys_prompt="""
You are a reasoning supervisor agent. 
Your job is to validate whether a given user interaction on a webpage 
was successful by analyzing the pre-action state and post-action state of the page.
Also by checking the previous sub tasks provided to you ,you will analyze them and decide if the main user task is done or not.

## Role
- You carefully compare the interactive elements (buttons, inputs, links, dialogs, etc.) 
  from the pre-action screenshot summary and the post-action screenshot summary.  
- You must determine if the intended action was executed correctly.  
- You provide structured reasoning and a clear final judgment. 
- You need to check the provided sub tasks/actions to you till now and also decide if the main user task is completed or no. 

## Input Structure
You will always receive the input in this JSON-like format:

{
  "action": "<The intended action in natural language. Example: 'Click the Login button'>",
  "pre_state": "<Summary of interactive elements before the action>",
  "post_state": "<Summary of interactive elements after the action>",
  "all_actions":"<A list of all the sub tasks done till now for the main task",
  "user_task":<the main user task for which we need the continue or termination of next step>
}

## Task
1. Read the `action` to understand what was supposed to happen.
2. If the action as to read or extract always give succes status as true since there would be no changes in Ui. 
2. Compare `pre_state` and `post_state` carefully.  
   - Look for the expected change (e.g., new popup,change in UI, form submitted, error message,navigated to new page,only change in current page by typing some information in input or slection of any elements).  
   - Look for missing or incorrect changes.
   - Sometimes the action is just to type something,clicking something or fill the details in the same page.
   - Reason about the action ,after performing what it can led to.
   - Not always the changes predicted will be as it is dont be very rigid with the prediction,some slight changes will work too "but not next to nothing" ,give success as false only if any major change to happen isnt there and you are confident about it.   
3. Give reasoning step by step.  
4. Conclude whether the task succeeded or failed. 
6. Reason about the main user task if completed or not with provided list of sub steps. 

## Output Format
Always respond in the following JSON format:
Don't output anything else than this format.
{
  "success": true/false,
  "reasoning": "<Step-by-step reasoning of what changed and why it indicates success or failure>",
  "expected_vs_actual": {
      "expected": "<What should have happened>",
      "actual": "<What actually happened>"
  },
  "is_terminate":true/false<user task completed or no>
}

## Important Rules
- If the action did produce the expected outcome and if there are slight considerable changes wrt the action performed, mark `"success": true`. 
- For subtask like extracting,reading from a webpage would have no change in UI so always give "success":True,but only terminate  if the main user task was completed or no,after extraction or reading?
- Be objective. Do not assume success unless the evidence clearly supports it.  
- Use precise reasoning, not vague statements.  
- Keep reasoning concise but logical. 
- Stick to the output format strictly dont output anything extra than the json output format explicitly mentioned.

"""
def encode_image(path: str, mime: str = "png") -> str:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{mime};base64,{b64}"

def analyze_image(image_path, prompt,client,model, mime: str = "png"):
    data_url = encode_image(image_path, mime)
    completion = client.chat.completions.create(
        model=model,
        temperature=0.5,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }
        ]
    )
    return completion.choices[0].message.content

def supervisor_generate(agent, messages, sender, config):
    for i in range(-1,-len(messages)-1,-1):
      if messages[i]["role"]=="user":
        user_task=messages[i]["content"]
        break
    
    for i in range(-1,-len(messages)-1,-1):
      if messages[i]["role"]=="Planner":
        content=json.loads(messages[i]["content"])
        sub_task=content["step"]
        operation=content["operation"]
        break
    
    if operation=="navigate":
       sup_feedback={
          "success": True,
          "reasoning": "navigated perfectly",
          "expected_vs_actual": {
              "expected": "navigation",
              "actual": "navigation"
          },
          "is_terminate":False
        }
       messages.append({
        "role": agent.name,
        "content": sup_feedback
        })
       return True,{
        "role": agent.name,
        "content": sup_feedback
        }
       

    all_actions=[]
    for i in range(-1,-len(messages)-1,-1):
      if messages[i]["role"]=="user":
         break
      if messages[i]["role"]=="Planner":
        content=json.loads(messages[i]["content"])
        all_actions.append(content["step"])
        break    
    
    all_actions.reverse()

    v_cfg = config["config_list"][0]
    t_cfg = config["config_list"][1]

    v_client = OpenAI(
            base_url=v_cfg["base_url"],   
            api_key=v_cfg["api_key"],
        )
    t_client = OpenAI(
            base_url=t_cfg["base_url"],   
            api_key=t_cfg["api_key"],
        )
    
    v_model=v_cfg["model"]
    t_model=t_cfg["model"]

    image1 = r"C:\Users\tanmay\OneDrive\Desktop\Autogen\pre_ss.png"
    image2 = r"C:\Users\tanmay\OneDrive\Desktop\Autogen\post_ss.png"

    prompt1 = "List all interactive elements visible on this webpage screenshot with the possible actions after interacting with them can led to."
    prompt2 = "Summarize this page what it is about and what all element it contains"

    pre_state=analyze_image(image1, prompt1,v_client,v_model, mime="png")
    post_state=analyze_image(image2, prompt2,v_client,v_model, mime="png")

    user_input = {
        "action": sub_task,
        "pre_state": pre_state,
        "post_state": post_state,
        "all_actions":all_actions,
        "user_task":user_task
    }

    completion = t_client.chat.completions.create(
        model=t_model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user","content":str(user_input)}
        ]
    )
    feedback=completion.choices[0].message.content
    dict_feedback=json.loads(feedback)
    messages.append({
        "role": agent.name,
        "content": dict_feedback
        })
    return True,{
        "role": agent.name,
        "content": dict_feedback
        }

Supervisor = AssistantAgent(
    name="Supervisor",
    llm_config={
        "config_list": [
            {
                "model": "google/gemma-3-27b-it:free",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": "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"
            },
            {
                "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": "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"
            }
        ]
    }
)

supervisor_llm_config=Supervisor.llm_config
Supervisor.register_reply(
    trigger=lambda sender: True,
    reply_func=supervisor_generate,
    config=supervisor_llm_config # Pass the config here
)

