from planner import planner
from executor import Executor
from supervisor import Supervisor

def main():
    messages=[]
    
    user_input=input("Enter your task: ")
    messages.append({"role": "user","content": user_input})
    
    while True:
        
        planner_output=planner.generate_reply(messages)
        if planner_output["content"]=="terminate":
            break
        messages.append(planner_output)
        print("----Planner-----")
        print(planner_output)
        # print(messages)
        
        executor_output = Executor.generate_reply(messages)
        messages.append(executor_output)
        print("----Executor-----")
        print(executor_output)
        
        supervisor_feedback = Supervisor.generate_reply(messages)
        messages.append(supervisor_feedback)
        print("----Supervisor-----")
        print(supervisor_feedback)
        
        if  supervisor_feedback["content"]["is_terminate"]:
            break
    
    # final_ans=""
    print("\n\n")
    for i in range(-1,-len(messages)-1,-1):
      if messages[i]["role"]=="Executor":
        extracted_ans=messages[i]["content"]["extract"]
        break
    for i in range(-1,-len(messages)-1,-1):
      if messages[i]["role"]=="user":
        user_task=messages[i]["content"]
        break
    system_prompt='''
    You will be provided with extracted elements list containing various elements from various websites or same website.
    Based on the task provided to you ,which will be a web query for web automation,you need to give the answer using extracted elements list provided.
    It should contain final answer in a sentence form for the query provided and also the url corresponding to the answer using the extracted list.
    '''
    from openai import OpenAI

    client = OpenAI(
      base_url="https://openrouter.ai/api/v1",
      api_key="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",
    )
    
    completion = client.chat.completions.create(
            model="deepseek/deepseek-r1-0528-qwen3-8b:free",         
            messages=[ 
                    {"role": "system", "content": system_prompt},   
                    {"role": "user","content": f"Task{user_task}\n\nExtract list:{extracted_ans}"}
            ]
        )
    print(completion.choices[0].message.content)
# Find cheapest one way flight from Bangalore to delhi for 2 adults and 1 children on 28th october from google flights website
# Search for cheapest and reliable  pendrive with usb3.2 256gb storage on amazon
# Find me a cheapest harry potter and philosopher's stone novel from first 3 websites

if __name__ == "__main__":
    main()
