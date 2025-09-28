from planner import planner
from executor import Executor
from supervisor import Supervisor

def main():
    messages=[]
    
    user_input=input("Enter your task: ")
    messages.append({"role": "user","content": user_input})
    
    while True:
        
        planner_output=planner.generate_reply(messages)
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
    
    final_ans=""
    for i in range(-1,-len(messages)-1,-1):
      if messages[i]["role"]=="Executor":
        extracted_ans=messages[i]["content"]["extract"]
        break
    for ans in extracted_ans:
       final_ans+=ans["name"]+" "
    print("Desired answer:",final_ans)
# FInd cheapest flight from mumbai to delhi for 2 adults on 5th september from ixigo site
if __name__ == "__main__":
    main()

