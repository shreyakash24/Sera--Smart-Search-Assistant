from autogen import AssistantAgent
from playwright.sync_api import sync_playwright
from openai import OpenAI
import json,json5
import traceback
from dotenv import load_dotenv
import os,json
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

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
-First try exact match on name and reason if the subtask actually satisfies with selecting a particular element.
-If none, look at description and see if by description the correct element can be inferred for performing the action.
-Normalize text (ignore case/extra spaces).
-Do not pick any element candidate by your own only choose from accesbility tree provided.
-ALWAYS RETURN A VALID JSON STRUCTURE.
-NEVER OMIT OR CUT OFF A FIELD.
-DO NOT TRUNCATE THE LINK VALUE OR NAME.
-ALSO IF LINK IS A ROLE PROVIDE IT'S VALUE TOO WHICH IS A LINK.(ALWAYS PROVIDE ENTIRE LINK VALUE DONT TRUNCATE)
-DO NOT OUTPUT YOUR THINKING ,OR ANY EXTRA PART EXCEPT THE STRUCTURED JSON OUTPUT.
-THE EXTRACTED LINK IF ANY SHOULD BE EXTRACTED AS IT IS FROM THE TREE PROVIDED, DONT MISS OR ADD ANY CHARACTER SYMBOL.
-IF AN ACTION IS TO TYPE,FILL THE OUTPUT MUST ONLY CONTAIN "TYPE" AS THE ONLY ACTION ,NO NEED TO HAVE "CLICK" ACTION NEXT TO ENTER OR EXECUTE THE TYPED QUERY AS TYPE IS ENTERED SUCCESFULLY.

-Return structured output
-Always return a JSON object with:
 example:
   {
  "action": "click | type | select | read",
  "target": {
    "role": "...",
    "name": "...",
    "description": "..."[if there*]
  },
  "value":"..."[if any*],
  "reason": "Explain why this element matches the user task"
   }

**Rules:
-IF THE ACTION IS OF "TYPE", IT MEANS THE ACTION HAS ALREADY BEEN EXECUTED BY TYPING INTO THE ELEMENT AND CLICKING THE SEARCH OR ANY OTHER ELEMENT THAT EXECUTES THE TYPED QUERY, SO THERE IS NO NEED TO SPECIFY ANY ADDITIONAL CLICK ACTION AFTER TYPING TO EXECUTE THE QUERY.
-For date selection,no of people,entities selection,etc always click first.
-DO NOT TRUNCATE THE LINK VALUE OR NAME.
-THE STRUCTURE OF RESPONSE SHOULD NOT BE BROKEN, DONT BE CARELESS,DONT MISS THE DOUBLE QUOTES,COMMAS,FORMAT AS IT'S IMPORTANT.
-Always give the entire role,name,value as given in accessibility tree for the candidate element selected for action.
VeryIMP:The selected action should not contain role as 'text leaf' as it cannot be interacted with,unless the task is of just read or extract,
        else for interaction u should look for 'textbox' instead. For elements with almost same name and meaning having both textleaf and textbox ,always select the textbox. 
IMP: If the selected action contains interacting with text leaf always prioritize textbox first ,if textbox not present do interact using textleaf*

-THE BELOW FORMAT MUST NOT BE BROKEN BY ANY CHANCE
-Always output in proper JSON format only ,so it can be used afterwards using json.loads().
-DO NOT GIVE RESPONSE WITH back ticks (``` json ).
-Strictly follow this format only in JSON,giving a list of actions always*even if an individual action.
-THE EXTRACTED LINK IF ANY SHOULD BE EXTRACTED AS IT IS FROM THE TREE PROVIDED, DONT MISS OR ADD ANY CHARACTER SYMBOL.
-THE VALUE KEY IF PRESENT IT SHOULD NOT BE NESTED IN TARGET KEY BUT AS A SEPERATE KEY OUTSIDE TARGET AS SPECIFIED IN FORMAT.
Format:
 {
  "actions":[
  {
  "action": "click | type | select | read",
  "target": {
    "role": "...",
    "name": "...",
    "description": "..."{if there*}
  },
  "value":"..."{if any*},
  "reason": "Explain why this element matches the user task"
   },
   {another action if more than 1}
    ]
  }
       

Example:
User Task:
"Apply for the 'Software Engineer' position and upload resume with any input name,email number of your choice."

Accessibility Tree:
[{"role":"link","name":"Home"},{"role":"link","name":"Jobs"},{"role":"link","name":"About"},{"role":"textbox","name":"Search Jobs"},{"role":"button","name":"Search"},{"role":"link","name":"Software Engineer"},{"role":"link","name":"Data Scientist"},{"role":"link","name":"Product Manager"},{"role":"textbox","name":"Full Name"},{"role":"textbox","name":"Email"},{"role":"textbox","name":"Phone"},{"role":"textbox","name":"Resume Upload"},{"role":"button","name":"Submit Application"},{"role":"button","name":"Cancel"}]

Model Output:
{
  "actions": [
    {
      "action": "click",
      "target": { 
        "role": "link",
        "name": "Software Engineer"
         }
    },
    {
      "action": "type",
      "target": { 
        "role": "textbox",
        "name": "Full Name"
          },
      "value": "John Doe"
    },
    {
      "action": "type",
      "target": {
        "role": "textbox",
        "name": "Email" 
        },
      "value": "john@example.com"
    },
    {
      "action": "type",
      "target": {
        "role": "textbox",
        "name": "Phone" 
        },
      "value": "9876543210"
    },
    {
      "action": "upload",
      "target": { 
      "role": "textbox",
       "name": "Resume Upload"
         },
      "value": "resume.pdf"
    },
    {
      "action": "click",
      "target": {
        "role": "button",
        "name": "Submit Application"
          }
    }
  ]
}


'''

extract=[]
inner_list=[]
extract_links=[]
count=0
first_time=True
single_website=True
initial_navigate=True
class BrowserController:
  def __init__(self):
        self.playwright = None
        self.browser = None

  def start(self):
      if not self.playwright:
          self.playwright = sync_playwright().start()
          self.browser = self.playwright.firefox.launch(headless=False)
          self.context =  self.browser.new_context()
          self.page = self.context.new_page()
#   def __init__(self):
#       self.playwright = sync_playwright().start()
#       self.browser = self.playwright.firefox.launch(headless=False)
#       self.context =  self.browser.new_context()
#       self.page = self.context.new_page()

  def goto(self, url: str):
      self.page.goto(url,wait_until="load")
      self.page.wait_for_timeout(5000)

  def bing_search(self,query, num_results=5):
      headers = {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
      }
      url = query
      response = requests.get(url, headers=headers)
      soup = BeautifulSoup(response.text, "html.parser")
  
      links = []
      for item in soup.select("li.b_algo h2 a"):
          link = item.get("href")
          if link and link.startswith("http"):
              links.append(link)
          if len(links) >= num_results:
              break
  
      return links

  def perform_action(self, action: dict,url:str):
      act = action["action"]
      target = action.get("target", {})
      role = target.get("role")
      name = target.get("name")
      if act == "type":
          print("gone to type")
          option_value = action.get("value")
          if url.rstrip('/') in ["https://www.bing.com", "https://bing.com"]:
              self.page.keyboard.type(option_value)
              self.page.keyboard.press("Enter")
              return
          # print("not gone")
          print("type")
          locator = self.page.get_by_role(role, name=name)
          print("locator got")
          locator.click(force=True)
          print("clicked")
        #   locator.wait_for(state="visible")
          self.page.wait_for_timeout(2000)
          self.page.keyboard.type(option_value)
          self.page.keyboard.press("Enter")
      elif act == "click":
          locator = self.page.get_by_role(role, name=name).first
          if role=="link":
              with self.page.expect_popup() as popup_info:
                  locator.click(force=True)
              self.page = popup_info.value
              self.page.wait_for_load_state()
          else:
              locator.click(force=True)
          self.page.wait_for_timeout(5000)
        
      elif act=="read":
          option_value = action.get("value")
          generated={
              "link":option_value,
              "name":name,
              "url":url
          }
          inner_list.append(generated)
      
          
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
controller.start()

def executor_generate(agent, messages, sender, config):
    global initial_navigate,count,first_time,extract,inner_list,extract_links,single_website
    user_task=""
    accessibility_tree=""
    url=""
    operation=""
    fill_text=""

    for i in range(-1,-len(messages)-1,-1):
      if messages[i]["role"]=="Executor":
        with open("accessibility_tree.json", "r", encoding="utf-8") as f:
            accessibility_tree = json.load(f)
            print("tree taken")
        url=messages[i]["content"]["updated_url"]
        break
      
    for i in range(-1,-len(messages)-1,-1):
      if messages[i]["role"]=="user":
        user_task=messages[i]["content"]
        raw_content=messages[i+1]["content"]
        if isinstance(raw_content, str):
            content = json.loads(raw_content)
        else :
            content = raw_content
        target=content.get("target")
    
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
          content = json.loads(messages[i]["content"])  
          details = content.get("details", {})
  
          if "url" in details:
              url = details["url"]
          if "text" in details:
              fill_text = details["text"]
  
          break  
    
    if operation=="navigate" and initial_navigate==True :
       controller.goto(url)
       controller.accesibility_tree()
        # browser.close()

       executor_feedback={
        "success_status":True,
        "error":False,
        "step_id":step_id,
        "updated_url":url,
        "terminate":False,
        "extract":extract
       }

       initial_navigate=False
       return True, {"role": agent.name, "content": executor_feedback}
    
    if operation == "navigate" and initial_navigate == False:
      print("In extract links part-- ")
  
      if extract_links and count < len(extract_links):
          print("count:", count)
          new_link = extract_links[count]
          print("new link:", new_link)
          count += 1
  
          controller.goto(new_link)
          controller.accesibility_tree()
  
          executor_feedback = {
              "success_status": True,
              "error": False,
              "step_id": step_id,
              "updated_url": new_link,
              "terminate":False,
              "extract":extract
          }
          return True, {"role": agent.name, "content": executor_feedback}
      else:
          print("No more links left in extract_links.")
          new_link=controller.get_url()
          executor_feedback = {
              "success_status": True,
              "error": False,
              "step_id": step_id,
              "updated_url": new_link,
              "terminate":True,
              "extract":extract
          }
          return True, {"role": agent.name, "content": executor_feedback}


    if fill_text!="":
       user_task=user_task + f"with text to type as {fill_text}"
    
    try:
        # print("started")
        # cfg = config["config_list"][0]

        # client = OpenAI(
        #     base_url=cfg["base_url"],   
        #     api_key=cfg["api_key"],
        # )

        # completion = client.chat.completions.create(
        #     model=cfg["model"],         
        #     messages=[ 
        #             {"role": "system", "content": system_prompt},   
        #             {"role": "user","content": f"User Task: {user_task}\nDOM:\n{json.dumps(accessibility_tree, ensure_ascii=False)}\n\nOutput:"}
        #     ],
        #     max_tokens=cfg["max_tokens"]
        # )

        # actions = completion.choices[0].message.content
        # _, sep, after = actions.partition("</think>")
        # if sep:  
        #     clean_output = after.strip()
        # else:   
        #     clean_output = actions.strip()
        # actions=clean_output
        # print(actions)
        model = genai.GenerativeModel('gemini-2.5-flash') 

        response = model.generate_content(
            [
                system_prompt,
                f"User Task: {user_task}\nDOM:\n{json.dumps(accessibility_tree, ensure_ascii=False)}\n\nOutput:"
             ],
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=25000
            )
        )
        actions=response.text
        actions = actions.strip()
        if actions.startswith("```"):
            actions = actions.split("```")[1]  # take inside block
        if actions.startswith("json"):
            actions = actions[4:].strip()
        print(actions)

        controller.get_ss("pre_ss.png")
        
        def execute_actions(url: str, actions: dict):
            global first_time, extract_links
            if isinstance(actions, str):
                
                try:
                    actions = json5.loads(actions)
                    if first_time and target!="default" and url not in ["https://www.bing.com/", "https://bing.com/","https://www.bing.com", "https://bing.com"]:
                        link=controller.get_url()
                        print(link)
                        extract_links= controller.bing_search(link)
                        print(extract_links)
                        first_time=False
                        return "All actions executed"

                except Exception as e:
                    return f"Failed to parse actions: {e}\n{traceback.format_exc()}"
        
            try:
                for step in actions.get("actions", []):
                    try:
                        print("gone")
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

        if inner_list:
            extract.append(inner_list.copy())

        # if inner_list:
        #     if first_time==True and step_id<=4:
        #         first_time = False
        #         extract_links = inner_list.copy()   # now extract_links is a list-of-dicts (not [[...]])
        #         print("extracted search results and not displaying in extract")
        #         # print(extract_links)
                
        

        executor_feedback={
            "step_id":step_id,
            "success_status":success_fb,
            "error":Error_fb,
            # "updated_tree":next_tree,
            "updated_url":next_url,
            "extract":extract,
            "terminate":False
        }
        inner_list.clear()
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
            "model": "qwen/qwen3-235b-a22b:free",  
            "api_key": "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",
            "base_url": "https://openrouter.ai/api/v1",
            "max_tokens": 15000
        }
    ]
    }
)
executor_llm_config=Executor.llm_config
Executor.register_reply(
    trigger=lambda sender: True,
    reply_func=executor_generate,
    config=executor_llm_config # Pass the config here
)
