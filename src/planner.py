# from autogen import AssistantAgent
# import os
# import json
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()
# HF_TOKEN=os.environ.get("HF_TOKEN4")
# BASE_URL = "https://api-inference.huggingface.co/models/"

# trial1="""You are a web automation task planner. You will receive tasks from the user. You will think step by step and break down the tasks into sequence of simple subtasks.
#     Return only in this format:
#     strictly a well-formatted JSON with 3 attributes.
#     The attributes will be as follows,
#     "step_id": This is an integer that represents the number of the step. It takes values starting from 1 and then increments for each step.
#     "step": This is a string that contains the step that reflects the activity to be performed on the browser to complete the task given by the user. It should be short, to the point.
#     "value": This is a string that contains the specific name of the objects in "step" required for it to be performed. This attribute only needs to be present when the names are mentioned explicitly or can be inferred.
#     Don't write any explanations or anything extra except the JSON for each step.
#     Your output should be consistent everytime the same task appears."""
    
# trial2="""You are a web automation task planner. You will receive tasks from the user. You will think step by step and break down the tasks into sequence of simple subtasks.
#     Return only in this format:
#     strictly a well-formatted JSON with 3 attributes.
#     The attributes will be as follows,
#     "step_id": This is an integer that represents the number of the step. It takes values starting from 1 and then increments for each step.
#     "step": This is a string that contains the step that reflects the activity to be performed on the browser to complete the task given by the user. It should be short, to the point.
#     "value": This is a string that contains the selectors required for the "step" to be performed. This can be a link or any field or any particular text to be typed to execute the step or any other relevant entity. This attribute only needs to be present when it can be inferred.
#     If the user input explicitly or implicitly says to select "any" or "a random" item, assume the rule is to select the first available item in the list.
#     Don't write any explanations or anything extra except each subtask.
#     Your output should be consistent everytime the same task appears.

#     Example 1:
#     Task = Find the price of Adidas shoes
#     Output should be like,
#     [
#       {
#         "step_id": 1,
#         "step": "Navigate to Adidas website",
#         "value": "https://www.adidas.com/"
#       },
#       {
#         "step_id": 2,
#         "step": "Input the search term 'shoes' in the search bar",
#         "value": "shoes"
#       },
#       {
#         "step_id": 3,
#         "step": "click the 'search' button",
#         "value": "search"
#       },
#       {
#         "step_id": 4,
#         "step": "Select 'first' pair of shoes",
#         "value": "first"
#       },
#       {
#         "step_id": 5,
#         "step": "Identify their 'price'",
#         "value": "price"
#       }
#     ]

#     Example 2:
#     Task = I want to subscribe to the Times of India newsletter with the email 'abc@gmail.com'.
#     Output should be like,
#     [
#       {
#         "step_id": 1,
#         "step": "Navigate to Times of India website",
#         "value": "https://timesofindia.indiatimes.com/"
#       },
#       {
#         "step_id": 2,
#         "step": "Input the 'email' address into the newsletter 'subscription' field",
#         "value": "abc@gmail.com"
#       },
#       {
#         "step_id": 3,
#         "step": "Click the subscribe button",
#         "value": "subscribe"
#       }
#     ]
#     """
    
# planner_system_prompt = """
# You are an AI Planner agent in a multi-agent web automation system. You will receive tasks from the user and break them down into logically sequenced subtasks suitable for execution by a PlayWright Executor. A Supervisor provides feedback that you must use to continue, replan, or backtrack. You have to generate the next step by assesing all the context provided.

# YOUR RESPONSIBILITIES:
#     1. Break down a user query into step-by-step actions for web scraping and automation.
#     2. If no url is provided by the user and if you do not find any clue then use a search engine (give a direct link for the query on preferably bing) and then visit the links of the websites listed by the search engine one by one. Scroll if needed.
#     3. When on a particular website no need to access each product one by one unless its details are asked explicitly.
#     4. Aggregate results across multiple sites for final comparison.
#     5. Store results from each site in short-term memory for multi-site analysis.
#     6. Generate ONLY ONE STEP AT A TIME and wait for Supervisor feedback before continuing.
#     7. If a step fails, use Supervisor feedback to replan or backtrack.

# CONTEXT PROVIDED:
# - Current Site: {site_url}
# - Accessibility Tree: {accessibility_tree}
# - User Goal: {user_query}
# - Step History: [{"step_id", "step", "operation", "target", "details"}]
# - Supervisor Feedback: [{"step_id", "success_status", "error"}]

# STEP REQUIREMENTS:
# - Be specific and actionable (include URLs, exact text)
# - One atomic action per step
# - Playwright-compatible operations (like navigate, click, fill, extract, scroll, select)

# OUTPUT FORMAT:
#     - Strictly a JSON object (curly brackets) in single line.
#     - If the user query requests "any" or "random" items, return details of all available items.
#     - No explanations or extra text.
#     - Output must be consistent for repeated tasks.
# {
#     "step_id": integer,
#     "step": "clear description of what to accomplish",
#     "operation": "navigate|click|fill|extract|scroll|select",
#     "target": "what element/content in the accessibility tree to interact with",
#     "details": {
#         "url": "for navigate operations",
#         "text": "for fill operations",
#         "data_type": ["for extract operations (price, title, link, etc.)"]
#     }
# }

# EXAMPLES:
# {"step_id": 1,"step": "Navigate to Amazon homepage","operation": "navigate","target": "Amazon main page","details": {"url": "https://amazon.com/"}}

# {"step_id": 3,"step": "Extract price of first search result","operation": "extract","target": "first product","details": {"data_type": ["price"]}}
# """


# # def model_call(model: str, messages: list):
# #     url=f"{BASE_URL}{model}"
# #     headers={"Authorization":f"Bearer {HF_TOKEN}"}
# #     payload={
# #         "model": model,
# #         "messages": messages
# #     }
# #     response = requests.post(url, headers=headers, json=payload)
# #     response.raise_for_status()
# #     result = response.json()
    
# #     full_output = result["choices"][0]["message"]["content"]
# #     _, sep, after = full_output.partition("</think>")
# #     if sep:  
# #         clean_output = after.strip()
# #     else:   
# #         clean_output = full_output.strip()

# #     return clean_output

# def model_call(model: str, messages: list):
#     client = OpenAI(
#         base_url=model["base_url"],   
#         api_key=model["api_key"],
#     )
#     completion = client.chat.completions.create(
#         model=model["model"],         
#         messages=messages
#     )
#     full_output = completion.choices[0].message.content
#     _, sep, after = full_output.partition("</think>")
#     if sep:  
#         clean_output = after.strip()
#     else:   
#         clean_output = full_output.strip()

#     return {"role": "planner", "content": clean_output}

# def custom_generate(recipient, messages, sender, config):
#     model = config["config_list"][0]
#     user_query = [m for m in messages if m["role"] == "user"][-1:]
#     supervisor_msg = [m for m in messages if m["role"] == "Supervisor"][-1:]
#     planner_history = []
#     for i in range(-1,-len(messages)-1,-1):
#         if len(planner_history)==8:
#           break
#         if messages[i]["role"] == "Planner":
#                 content_dict = json.loads(messages[i]["content"])
#                 planner_history.append(content_dict)
#     tree=""
#     site=""
#     for i in range(-1,-len(messages)-1,-1):
#       if messages[i]["role"]=="Executor":
#         tree=messages[i]["updated_tree"]
#         break
#     for i in range(-1,-len(messages)-1,-1):
#       if "details" in messages[i] and messages[i]["details"].get("url"):
#         site=messages[i]["details"]["url"]
#         break    
#     context =f"""
#           "site_url":{site},
#           "accessibility_tree":{tree},
#           "step_history":{planner_history},
#           "supervisor_feedback":{supervisor_msg}
#     """
#     messages = user_query + [{"role":"assistant","content":context}]
#     return model_call(model, messages)

# planner_llm_config = {
#     "model": "Qwen/Qwen3-30B-A3B",
#     "custom_generate": custom_generate,
#     "temperature": 0,
# }      
# planner= AssistantAgent(
#     name="Planner",
#     model_client=client_from_config(planner_llm_config),
#     system_message=planner_system_prompt
# )

# planner = AssistantAgent(
#     name="planner",
#     system_message=planner_system_prompt,
#     llm_config= {
#     "config_list": [{
#             "model": "qwen/qwen3-30b-a3b:free",  
#             "api_key": "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",
#             "base_url": "https://openrouter.ai/api/v1"
#         }],
#     "temperature": 0
#     }
# )
# planner.register_reply(
#     reply_func=custom_generate,
#     position=1,
#     trigger="*"
# )

# from autogen import AssistantAgent
# from helper import client_from_config
# import os
# import json
# import requests
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()
# HF_TOKEN=os.environ.get("HF_TOKEN4")
# BASE_URL = "https://api-inference.huggingface.co/models/"

# trial1="""You are a web automation task planner. You will receive tasks from the user. You will think step by step and break down the tasks into sequence of simple subtasks.
#     Return only in this format:
#     strictly a well-formatted JSON with 3 attributes.
#     The attributes will be as follows,
#     "step_id": This is an integer that represents the number of the step. It takes values starting from 1 and then increments for each step.
#     "step": This is a string that contains the step that reflects the activity to be performed on the browser to complete the task given by the user. It should be short, to the point.
#     "value": This is a string that contains the specific name of the objects in "step" required for it to be performed. This attribute only needs to be present when the names are mentioned explicitly or can be inferred.
#     Don't write any explanations or anything extra except the JSON for each step.
#     Your output should be consistent everytime the same task appears."""
    
# trial2="""You are a web automation task planner. You will receive tasks from the user. You will think step by step and break down the tasks into sequence of simple subtasks.
#     Return only in this format:
#     strictly a well-formatted JSON with 3 attributes.
#     The attributes will be as follows,
#     "step_id": This is an integer that represents the number of the step. It takes values starting from 1 and then increments for each step.
#     "step": This is a string that contains the step that reflects the activity to be performed on the browser to complete the task given by the user. It should be short, to the point.
#     "value": This is a string that contains the selectors required for the "step" to be performed. This can be a link or any field or any particular text to be typed to execute the step or any other relevant entity. This attribute only needs to be present when it can be inferred.
#     If the user input explicitly or implicitly says to select "any" or "a random" item, assume the rule is to select the first available item in the list.
#     Don't write any explanations or anything extra except each subtask.
#     Your output should be consistent everytime the same task appears.

#     Example 1:
#     Task = Find the price of Adidas shoes
#     Output should be like,
#     [
#       {
#         "step_id": 1,
#         "step": "Navigate to Adidas website",
#         "value": "https://www.adidas.com/"
#       },
#       {
#         "step_id": 2,
#         "step": "Input the search term 'shoes' in the search bar",
#         "value": "shoes"
#       },
#       {
#         "step_id": 3,
#         "step": "click the 'search' button",
#         "value": "search"
#       },
#       {
#         "step_id": 4,
#         "step": "Select 'first' pair of shoes",
#         "value": "first"
#       },
#       {
#         "step_id": 5,
#         "step": "Identify their 'price'",
#         "value": "price"
#       }
#     ]

#     Example 2:
#     Task = I want to subscribe to the Times of India newsletter with the email 'abc@gmail.com'.
#     Output should be like,
#     [
#       {
#         "step_id": 1,
#         "step": "Navigate to Times of India website",
#         "value": "https://timesofindia.indiatimes.com/"
#       },
#       {
#         "step_id": 2,
#         "step": "Input the 'email' address into the newsletter 'subscription' field",
#         "value": "abc@gmail.com"
#       },
#       {
#         "step_id": 3,
#         "step": "Click the subscribe button",
#         "value": "subscribe"
#       }
#     ]
#     """
    
# planner_system_prompt = """
# You are an AI Planner agent in a multi-agent web automation system. You will receive tasks from the user and break them down into logically sequenced subtasks suitable for execution by a PlayWright Executor. A Supervisor provides feedback that you must use to continue, replan, or backtrack.

# YOUR RESPONSIBILITIES:
#     1. Break down a user query into step-by-step actions for web scraping and automation.
#     2. If no site is provided by the user, try to interpret the website from the brands etc. mentioned, if not found any clue then use a search engine (preferably precise link for the query on bing) and then visit the links of the websites listed by the search engine one by one. Scroll if needed.
#     3. When on a particular website no need to access each product one by one unless its details are asked explicitly.
#     4. Aggregate results across multiple sites for final comparison.
#     5. Store results from each site in short-term memory for multi-site analysis.
#     6. Generate only one step at a time and wait for Supervisor feedback before continuing.
#     7. If a step fails, use Supervisor feedback to replan or backtrack.

# CONTEXT PROVIDED:
# - Current Site: {site_url}
# - Accessibility Tree: {accessibility_tree}
# - User Goal: {user_query}
# - Step History: [{"step_id", "step", "operation", "target", "details"}]
# - Supervisor Feedback: [{"step_id", "success_status", "error"}]

# STEP REQUIREMENTS:
# - Be specific and actionable (include URLs, exact text)
# - One atomic action per step
# - Playwright-compatible operations (like navigate, click, fill, extract, scroll, select)

# OUTPUT FORMAT:
#     - Strictly a JSON object (curly brackets) in single line.
#     - If the user query requests "any" or "random" items, return details of all available items.
#     - No explanations or extra text.
#     - Output must be consistent for repeated tasks.
# {
#     "step_id": integer,
#     "step": "clear description of what to accomplish",
#     "operation": "navigate|click|fill|extract|scroll|select",
#     "target": "what element/content in the accessibility tree to interact with",
#     "details": {
#         "url": "for navigate operations",
#         "text": "for fill operations",
#         "data_type": ["for extract operations (price, title, link, etc.)"]
#     }
# }

# EXAMPLES:
# {"step_id": 1,"step": "Navigate to Amazon homepage","operation": "navigate","target": "Amazon main page","details": {"url": "https://amazon.com"}}

# {"step_id": 3,"step": "Extract price of first search result","operation": "extract","target": "first product","details": {"data_type": ["price"]}}
# """




# def custom_generate(messages, config):
#     model = config.get("model")
#     user_query = [m for m in messages if m["role"] == "user"][-1:]
#     supervisor_msg = [m for m in messages if m["role"] == "Supervisor"][-1:]
#     planner_history = []
#     for i in range(-1,-len(messages)-1,-1):
#         if len(planner_history)==8:
#           break
#         if messages[i]["role"] == "Planner":
#                 content_dict = json.loads(messages[i]["content"])
#                 planner_history.append(content_dict)
#     tree=""
#     site=""
#     for i in range(-1,-len(messages)-1,-1):
#       if messages[i]["role"]=="Executor":
#         tree=messages[i]["updated_tree"]
#         break
#     for i in range(-1,-len(messages)-1,-1):
#       if "details" in messages[i] and messages[i]["details"].get("url"):
#         site=messages[i]["details"]["url"]
#         break    
#     context =f"""
#           "site_url":{site},
#           "accessibility_tree":{tree},
#           "step_history":{planner_history},
#           "supervisor_feedback":{supervisor_msg}
#     """
#     messages = user_query + [{"role":"assistant","content":context}]
#     cfg = config["config_list"][0]

#     client = OpenAI(
#         base_url=cfg["base_url"],   
#         api_key=cfg["api_key"],
#     )
#     completion = client.chat.completions.create(
#         model=cfg["model"],         
#         messages=[
#             { 
#                 {"role": "system", "content": planner_system_prompt},   
#                 {"role":"assistant","content":context},
#                 {"role":"user","content":user_query}
#             }
#         ]
#     )
#     actions = completion.choices[0].message.content
#     return actions


# planner = AssistantAgent(
#     name="planner",
#     llm_config= {
#     "config_list": [
#         {
#             "model": "qwen/qwen3-30b-a3b:free",  
#             "api_key": "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",
#             "base_url": "https://openrouter.ai/api/v1"
#         }
#     ],
#     "custom_generate":custom_generate
#     }
# )

# from autogen import AssistantAgent
# import os
# import json
# import requests
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()
# HF_TOKEN=os.environ.get("HF_TOKEN4")
# BASE_URL = "https://api-inference.huggingface.co/models/"

# trial1="""You are a web automation task planner. You will receive tasks from the user. You will think step by step and break down the tasks into sequence of simple subtasks.
#     Return only in this format:
#     strictly a well-formatted JSON with 3 attributes.
#     The attributes will be as follows,
#     "step_id": This is an integer that represents the number of the step. It takes values starting from 1 and then increments for each step.
#     "step": This is a string that contains the step that reflects the activity to be performed on the browser to complete the task given by the user. It should be short, to the point.
#     "value": This is a string that contains the specific name of the objects in "step" required for it to be performed. This attribute only needs to be present when the names are mentioned explicitly or can be inferred.
#     Don't write any explanations or anything extra except the JSON for each step.
#     Your output should be consistent everytime the same task appears."""
    
# trial2="""You are a web automation task planner. You will receive tasks from the user. You will think step by step and break down the tasks into sequence of simple subtasks.
#     Return only in this format:
#     strictly a well-formatted JSON with 3 attributes.
#     The attributes will be as follows,
#     "step_id": This is an integer that represents the number of the step. It takes values starting from 1 and then increments for each step.
#     "step": This is a string that contains the step that reflects the activity to be performed on the browser to complete the task given by the user. It should be short, to the point.
#     "value": This is a string that contains the selectors required for the "step" to be performed. This can be a link or any field or any particular text to be typed to execute the step or any other relevant entity. This attribute only needs to be present when it can be inferred.
#     If the user input explicitly or implicitly says to select "any" or "a random" item, assume the rule is to select the first available item in the list.
#     Don't write any explanations or anything extra except each subtask.
#     Your output should be consistent everytime the same task appears.

#     Example 1:
#     Task = Find the price of Adidas shoes
#     Output should be like,
#     [
#       {
#         "step_id": 1,
#         "step": "Navigate to Adidas website",
#         "value": "https://www.adidas.com/"
#       },
#       {
#         "step_id": 2,
#         "step": "Input the search term 'shoes' in the search bar",
#         "value": "shoes"
#       },
#       {
#         "step_id": 3,
#         "step": "click the 'search' button",
#         "value": "search"
#       },
#       {
#         "step_id": 4,
#         "step": "Select 'first' pair of shoes",
#         "value": "first"
#       },
#       {
#         "step_id": 5,
#         "step": "Identify their 'price'",
#         "value": "price"
#       }
#     ]

#     Example 2:
#     Task = I want to subscribe to the Times of India newsletter with the email 'abc@gmail.com'.
#     Output should be like,
#     [
#       {
#         "step_id": 1,
#         "step": "Navigate to Times of India website",
#         "value": "https://timesofindia.indiatimes.com/"
#       },
#       {
#         "step_id": 2,
#         "step": "Input the 'email' address into the newsletter 'subscription' field",
#         "value": "abc@gmail.com"
#       },
#       {
#         "step_id": 3,
#         "step": "Click the subscribe button",
#         "value": "subscribe"
#       }
#     ]
#     """
    
# planner_system_prompt = """
# You are an AI Planner agent in a multi-agent web automation system. You will receive tasks from the user and break them down into logically sequenced subtasks suitable for execution by a PlayWright Executor. A Supervisor provides feedback that you must use to continue, replan, or backtrack.

# YOUR RESPONSIBILITIES:
#     1. Break down a user query into step-by-step actions for web scraping and automation.
#     2. If no site is provided by the user, try to interpret the website from the brands etc. mentioned, if not found any clue then use a search engine (preferably precise link for the query on bing) and then visit the links of the websites listed by the search engine one by one. Scroll if needed.
#     3. When on a particular website no need to access each product one by one unless its details are asked explicitly.
#     4. Aggregate results across multiple sites for final comparison.
#     5. Store results from each site in short-term memory for multi-site analysis.
#     6. Generate only one step at a time and wait for Supervisor feedback before continuing.
#     7. If a step fails, use Supervisor feedback to replan or backtrack.

# CONTEXT PROVIDED:
# - Current Site: {site_url}
# - Accessibility Tree: {accessibility_tree}
# - User Goal: {user_query}
# - Step History: [{"step_id", "step", "operation", "target", "details"}]
# - Supervisor Feedback: [{"success":True/False, "reasoning","expected_vs_actual","is_terminate"}]

# STEP REQUIREMENTS:
# - Be specific and actionable (include URLs, exact text)
# - One atomic action per step
# - Playwright-compatible operations (like navigate, click, fill, extract, scroll, select)

# OUTPUT FORMAT:
#     - Strictly a JSON object (curly brackets) in single line.
#     - If the user query requests "any" or "random" items, return details of all available items.
#     - No explanations or extra text.
#     - Output must be consistent for repeated tasks.
# {
#     "step_id": integer,
#     "step": "clear description of what to accomplish",
#     "operation": "navigate|click|fill|extract|scroll|select",
#     "target": "what element/content in the accessibility tree to interact with",
#     "details": {
#         "url": "for navigate operations",
#         "text": "for fill operations",
#         "data_type": ["for extract operations (price, title, link, etc.)"]
#     }
# }

# EXAMPLES:
# {"step_id": 1,"step": "Navigate to Amazon homepage","operation": "navigate","target": "Amazon main page","details": {"url": "https://amazon.com"}}

# {"step_id": 3,"step": "Extract price of first search result","operation": "extract","target": "first product","details": {"data_type": ["price"]}}
# """




# def custom_generate(agent, messages, sender, config):
#     model = config.get("model")
#     user_query = [m for m in messages if m["role"] == "user"][-1:]
#     supervisor_msg = [m for m in messages if m["role"] == "Supervisor"][-1:]
#     planner_history = []
#     for i in range(-1,-len(messages)-1,-1):
#         if len(planner_history)==8:
#           break
#         if messages[i]["role"] == "Planner":
#                 content_dict = json.loads(messages[i]["content"])
#                 planner_history.append(content_dict)
#     tree=""
#     site=""
#     '''for i in range(-1,-len(messages)-1,-1):
#       if messages[i]["role"]=="Executor":
#         tree=messages[i]["updated_tree"]
#         break'''
#     file = open("src/accessibility_tree.json", "r")
#     tree=file.read()  
#     file.close()
#     for i in range(-1,-len(messages)-1,-1):
#       if "details" in messages[i] and messages[i]["details"].get("updated_url"):
#         site=messages[i]["details"]["updated_url"]
#         break    
#     context =f"""
#           "site_url":{site},
#           "accessibility_tree":{tree},
#           "step_history":{planner_history},
#           "supervisor_feedback":{supervisor_msg}
#     """
#     # messages = user_query + [{"role":"assistant","content":context}]
#     cfg = config["config_list"][0]

#     client = OpenAI(
#         base_url=cfg["base_url"],   
#         api_key=cfg["api_key"],
#     )
#     completion = client.chat.completions.create(
#         model=cfg["model"],         
#         messages=[
            
#                 {"role": "system", "content": planner_system_prompt},   
#                 {"role":"assistant","content":context},
#                 {"role":"user","content":user_query}
            
#         ]
#     )
#     import ast
#     actions = completion.choices[0].message.content
#     new_acts = ast.literal_eval(actions)
#     # print(new_acts)
#     if "details" in new_acts and "url" in "details":
#        urll=new_acts["details"]["url"]
#        urll=urll+"/"
#        new_acts["details"]["url"]=urll
#     # print(urll)
#     # print(new_acts)


#     p_actions=json.dumps(new_acts)
#     # new_acts=json.loads()

#     return True,{"role":"Planner","content":p_actions}


# planner = AssistantAgent(
#     name="planner",
#     llm_config= {
#     "config_list": [
#         {
#             "model": "qwen/qwen3-30b-a3b:free",  
#             "api_key": "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",
#             "base_url": "https://openrouter.ai/api/v1"
#         }
#     ]
#     }
# )

# planner_llm_config=planner.llm_config
# planner.register_reply(
#     trigger=lambda sender: True,
#     reply_func=custom_generate,
#     config=planner_llm_config # Pass the config here
# )

from autogen import AssistantAgent
from helper import client_from_config
import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN=os.environ.get("HF_TOKEN4")
BASE_URL = "https://api-inference.huggingface.co/models/"

trial1="""You are a web automation task planner. You will receive tasks from the user. You will think step by step and break down the tasks into sequence of simple subtasks.
    Return only in this format:
    strictly a well-formatted JSON with 3 attributes.
    The attributes will be as follows,
    "step_id": This is an integer that represents the number of the step. It takes values starting from 1 and then increments for each step.
    "step": This is a string that contains the step that reflects the activity to be performed on the browser to complete the task given by the user. It should be short, to the point.
    "value": This is a string that contains the specific name of the objects in "step" required for it to be performed. This attribute only needs to be present when the names are mentioned explicitly or can be inferred.
    Don't write any explanations or anything extra except the JSON for each step.
    Your output should be consistent everytime the same task appears."""
    
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
    2. If no site is provided by the user, try to interpret the website from the brands etc. mentioned, if not found any clue then use a search engine (preferably precise link for the query on bing) and then visit the links of the websites listed by the search engine one by one. Scroll if needed.
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
        supervisor_msg=messages[i]["content"]["success"]
        supervisor_msg=str(supervisor_msg)
        supervisor_msg="success: "+supervisor_msg
        break

      
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
    
    # messages = user_query + [{"role":"assistant","content":context}]
    cfg = config["config_list"][0]

    client = OpenAI(
        base_url=cfg["base_url"],   
        api_key=cfg["api_key"],
    )
    completion = client.chat.completions.create(
        model=cfg["model"],         
        messages=[
            
                {"role": "system", "content": planner_system_prompt},   
                {"role":"assistant","content":context},
                {"role":"user","content":user_query}
            
        ]
    )
    import ast
    actions = completion.choices[0].message.content
    _, sep, after = actions.partition("</think>")
    if sep:  
        clean_output = after.strip()
    else:   
        clean_output = actions.strip()

# #     return clean_output
    new_acts = ast.literal_eval(clean_output)
    print(new_acts)
    if "details" in new_acts:
       if "url" in "details":
          urll=new_acts["details"]["url"]
          urll=urll+"/"
          new_acts["details"]["url"]=urll
    # print(urll)
    # print(new_acts)


    p_actions=json.dumps(new_acts)
    # new_acts=json.loads()

    return True,{"role":"Planner","content":p_actions}


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



