from planner import planner
from executor import executor
from supervisor import supervisor

def main():
    messages=[]
    
    user_input=input("Enter your task: ")
    messages.append({"role": "user","content": user_input})
    
    while True:
        
        planner_output=planner.generate_reply(messages)
        messages.append({"role": "Planner", "content": planner_output})
        print("----Planner-----")
        print(planner_output)
        
        executor_output = executor.generate_reply(messages)
        # messages.append({"role": "Executor", "content": executor_output})
        print("----Executor-----")
        print(executor_output)
        
        supervisor_feedback = supervisor.generate_reply(messages)
        # messages.append({"role": "Supervisor","content": supervisor_feedback})
        print("----Supervisor-----")
        print(supervisor_feedback)
        
        if "terminate" in supervisor_feedback["feedback"].lower():
            break



if __name__ == "__main__":
    main()
