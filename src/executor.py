from autogen import AssistantAgent
from playwright.sync_api import sync_playwright
from openai import OpenAI
from helper import client_from_config
import json
import traceback

system_prompt='''You are a DOM selector extraction assistant. 

You are an Accessibility-Aware Web Automation Agent.
Your job is to analyze a user task together with an accessibility tree (containing only role, name, description, and children) and decide what 
operation to perform and which element to target.

**Your Role

-Interpret the user's intent (e.g., click, type, select, read).
-Locate the best matching element in the accessibility tree.
-Provide a structured answer with reasoning.


**Input structure:
-Accessibilty tree of a webpage contains dictionaries having:
  role-It can be text,button,link,image,textbox,heading,tag,main,etc.
  name-It is the actual content of the role
  description:Description about the element
  readonly-It is either true or false which tells the element with the given role is interactive or only readable.
  value-The value of the element having the role as role&name as name given in accesbilty tree.

**Reasoning Plan:

-Parse the user task
-Identify the operation: click/open/navigate, type/enter/search, choose/select/check, read/get.
-Identify the target concept
-Infer candidate roles by operation
-Remember the date,no of entities selection is of type: radio,option or select.
 examples:
   Click/open/navigate → link, button, menuitem.
   Type/enter/search → textbox, searchbox, combobox,button.
   Choose/select/check → checkbox, radio, option,select. 
   Read/get info → heading, text.
   
-Match by text cues
-Reason about the user task and decide which should be the role,name or description and operation accordigly.
-First try exact match on name.
-If none, try substring/fuzzy match.
-If still none, look at description.
-Normalize text (ignore case/extra spaces).

-Return structured output
-Always return a JSON object with:
 example:
   {
  "action": "click | type | select | read",
  "target": {
    "role": "...",
    "name": "...",
    "description": "..."{if there*}
  },
  "reason": "Explain why this element matches the user task",
   }

**Rules:
-For date selection,no of people,entities selection,etc always click first.
VeryIMP:The selected action should not contain role as 'text leaf' as it cannot be interacted with,unless the task is of just read or extract,
        else for interaction u should look for 'textbox' instead. For elements with almost same name and meaning having both textleaf and textbox ,always select the textbox. 
IMP: If the selected action contains interacting with text leaf always prioritize textbox first ,if textbox not present do interact using textleaf*

Always output in proper JSON format only ,so it can be used afterwards using json.loads().
Strictly follow this format only in JSON.
Format:
 {
  "action": "click | type | select | read",
  "target": {
    "role": "...",
    "name": "...",
    "description": "..."{if there*}
  },
  "value":"..."{if any*}
  "reason": "Explain why this element matches the user task",
   }
        
Example1:
User Task:
"Find the cheapest phone and add it to cart, then proceed to checkout."

Accessibility tree snippet:
[{"role":"textbox","name":"Search"},{"role":"button","name":"Search"},{"role":"link","name":"Home"},{"role":"link","name":"Categories"},{"role":"link","name":"Phones"},{"role":"link","name":"Laptops"},{"role":"link","name":"Phone X – $899"},{"role":"link","name":"Phone Y – $499"},{"role":"link","name":"Phone Z – $750"},{"role":"button","name":"Add to Cart"},{"role":"button","name":"Wishlist"},{"role":"link","name":"Cart"},{"role":"button","name":"Checkout"}]

Model Output:
{
  "actions": [
    {
      "action": "click",
      "target": { "role": "link", "name": "Phone Y - $499" },
    },
    {
      "action": "click",
      "target": { "role": "button", "name": "Add to Cart" },
    },
    {
      "action": "click",
      "target": { "role": "link", "name": "Cart" },
    
    },
    {
      "action": "click",
      "target": { "role": "button", "name": "Checkout" },
    }
  ]
}


Example2:
User Task:
"Apply for the 'Software Engineer' position and upload resume with any input name,email number of your choice."

Accessibility Tree:
[{"role":"link","name":"Home"},{"role":"link","name":"Jobs"},{"role":"link","name":"About"},{"role":"textbox","name":"Search Jobs"},{"role":"button","name":"Search"},{"role":"link","name":"Software Engineer"},{"role":"link","name":"Data Scientist"},{"role":"link","name":"Product Manager"},{"role":"textbox","name":"Full Name"},{"role":"textbox","name":"Email"},{"role":"textbox","name":"Phone"},{"role":"textbox","name":"Resume Upload"},{"role":"button","name":"Submit Application"},{"role":"button","name":"Cancel"}]

Model Output:
{
  "actions": [
    {
      "action": "click",
      "target": { "role": "link", "name": "Software Engineer" },
    },
    {
      "action": "type",
      "target": { "role": "textbox", "name": "Full Name" },
      "value": "John Doe",
    },
    {
      "action": "type",
      "target": { "role": "textbox", "name": "Email" },
      "value": "john@example.com",
    },
    {
      "action": "type",
      "target": { "role": "textbox", "name": "Phone" },
      "value": "9876543210",
    },
    {
      "action": "upload",
      "target": { "role": "textbox", "name": "Resume Upload" },
      "value": "resume.pdf",
    },
    {
      "action": "click",
      "target": { "role": "button", "name": "Submit Application" },
    }
  ]
}


'''

extract=[]

class BrowserController:
  def __init__(self):
      self.playwright = sync_playwright().start()
      self.browser = self.playwright.firefox.launch(headless=False)
      self.page = self.browser.new_page()

  def goto(self, url: str):
      self.page.wait_for_timeout(4000)
      self.page.goto(url)

  def perform_action(self, action: dict,url:str):
      act = action["action"]
      target = action.get("target", {})
      role = target.get("role")
      name = target.get("name")
      if act == "type":
          option_value = action.get("value")
          if url=="https://www.bing.com"  or "https://bing.com":
              self.page.keyboard.type(option_value)
              self.page.keyboard.press("Enter")
              return
          # print("not gone")
          locator = self.page.get_by_role(role, name=name)
          locator.click(force=True)
          
          locator.wait_for(state="visible")
          self.page.keyboard.type(option_value)
      elif act == "click":
          locator = self.page.get_by_role(role, name=name).first
          locator.click(force=True)
          self.page.wait_for_timeout(5000)
        
      elif act=="read":
          option_value = action.get("value")
          generated={
              "link":option_value,
              "name":name
          }
          extract.append(generated)
          
      elif act in ["select", "choose", "check"]:
          locator = self.page.get_by_role(role, name=name)
          option_value = action.get("value")
          if(option_value):
              locator.select_option(option_value)
          else:
              locator.select_option(name)
          
  
  def accesibility_tree(self):
      snapshot =  self.page.accessibility.snapshot()
      
      with open("accessibility_tree.json", "w", encoding="utf-8") as f:
          json.dump(snapshot, f, ensure_ascii=False, indent=1)
  
  def get_url(self):
      # self.page.wait_for_timeout(5000)
      return self.page.url
  
  def get_ss(self,path:str):
     self.page.wait_for_timeout(3000)
     self.page.screenshot(path=path, full_page=True)
  def close(self):
      self.browser.close()
      self.playwright.stop()

controller = BrowserController()

def executor_generate(agent, messages, sender, config):
    
    user_task=""
    accessibility_tree=""
    url=""
    operation=""
    fill_text=""

    for i in range(-1,-len(messages)-1,-1):
      if messages[i]["role"]=="Executor":
        with open("accessibility_tree.json", "r", encoding="utf-8") as f:
            accessibility_tree = json.load(f)
        url=messages[i]["content"]["updated_url"]
        break
    
    for i in range(-1,-len(messages)-1,-1):
      if messages[i]["role"]=="Planner":
        raw_content = messages[i]["content"]
        if isinstance(raw_content, str):
            content = json.loads(raw_content)
        else :
            content = raw_content
        step_id = content.get("step_id")
        user_task = content.get("step")
        operation = content.get("operation")
        break
    
    for i in range(-1, -len(messages) - 1, -1):
      if messages[i]["role"] == "Planner":
          try:
              content = json.loads(messages[i]["content"])  # parse JSON string
          except json.JSONDecodeError as e:
              print("JSON decode error:", e, messages[i]["content"])
              continue
  
          details = content.get("details", {})
  
          if "url" in details:
              url = details["url"]
          if "text" in details:
              fill_text = details["text"]
  
          break  # stop at the most recent Planner step
    
    if operation=="navigate":
       controller.goto(url)
        # snapshot = page.accessibility.snapshot()
       controller.accesibility_tree()
        # browser.close()

       executor_feedback={
        "success_status":True,
        "error":False,
        # "updated_tree":new_tree,
        "step_id":step_id,
        "updated_url":url
       }

      #  print(messages)
      #  print("done")
       return True, {"role": agent.name, "content": executor_feedback}
    
    if fill_text!="":
       user_task=user_task + f"with text to type as {fill_text}"
    
    try:
        # print("started")
        cfg = config["config_list"][0]

        client = OpenAI(
            base_url=cfg["base_url"],   
            api_key=cfg["api_key"],
        )

        completion = client.chat.completions.create(
            model=cfg["model"],         
            messages=[ 
                    {"role": "system", "content": system_prompt},   
                    {"role": "user","content": f"User Task: {user_task}\nDOM:\n{json.dumps(accessibility_tree, ensure_ascii=False)}\n\nOutput:"}
            ]
        )
        # print(completion)
        # print("act")
        # if completion and completion.choices:
        #     choice = completion.choices[0]
        #     message = getattr(choice, "message", None)
        
        #     if message and message.get("content"):
        #         actions = message["content"]
        #     else:
        #         actions = "ERROR: Empty content from model"
        # else:
        #     actions = "ERROR: No choices in completion"
        actions = completion.choices[0].message.content
        print(actions)

        controller.get_ss("pre_ss.png")
        
        def execute_actions(url: str, actions: dict):
            # controller.goto(url)
            # controller.get_ss("pre_ss.png")
        
            if isinstance(actions, str):
                try:
                    actions = json.loads(actions, strict=False)
                except Exception as e:
                    return f"Failed to parse actions: {e}\n{traceback.format_exc()}"
        
            try:
                for step in actions.get("actions", []):
                    try:
                        controller.perform_action(step,url)
                    except Exception as e:
                        return f"Error while performing action {step}:\n{traceback.format_exc()}"
        
                return "All actions executed"
            except Exception as e:
                return f"Unexpected error:\n{traceback.format_exc()}"

        feedback=execute_actions(url,actions)
        if feedback=="All actions executed":
            success_fb=True
            Error_fb=False
        else:
            success_fb=False
            Error_fb=feedback
        
        controller.accesibility_tree()
        
        next_url=controller.get_url()
        controller.get_ss("post_ss.png")
        # controller.close()
        # print("here")
        executor_feedback={
            "step_id":step_id,
            "success_status":success_fb,
            "error":Error_fb,
            # "updated_tree":next_tree,
            "updated_url":next_url,
            "extract":extract
        }

        # print(messages)
        return True,{
        "role": agent.name,
        "content": executor_feedback
        }

    except Exception as e:
        return True, {
            "role": agent.name,
            "content": f"Executor generate failed: {e}\n{traceback.format_exc()}"
        }


Executor = AssistantAgent(
    name="Executor",
    llm_config= {
    "config_list": [
        {
            "model": "x-ai/grok-4-fast:free",  
            "api_key": "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",
            "base_url": "https://openrouter.ai/api/v1"
        }
    ]
    }
)
executor_llm_config=Executor.llm_config
Executor.register_reply(
    trigger=lambda sender: True,
    reply_func=executor_generate,
    config=executor_llm_config 
)
