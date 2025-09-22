from planner import planner
from executor import Executor
from supervisor import Supervisor

def main():
    messages=[]
    
    user_input=input("Enter your task: ")
    messages.append({"role": "user","content": user_input})
    print(messages,"\n\n")
    while True:
        
        planner_output=planner.generate_reply(messages)
        messages.append(planner_output)
        print("----Planner-----")
        print(planner_output)
        
        print(messages,"\n\n")
        
        executor_output = Executor.generate_reply(messages)
        messages.append(executor_output)
        print("----Executor-----")
        print(executor_output)
        print(messages,"\n\n")
        
        supervisor_feedback = Supervisor.generate_reply(messages)
        messages.append(supervisor_feedback)
        print("----Supervisor-----")
        print(supervisor_feedback)
        print(messages,"\n\n")
        
        if  supervisor_feedback["content"]["is_terminate"]:
            break

# FInd cheapest flight from mumbai to delhi for 2 adults on 5th september

if __name__ == "__main__":
    main()

