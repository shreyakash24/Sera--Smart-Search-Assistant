from planner import planner
from executor import executor
from supervisor import supervisor

def main():
    messages=[]
    
    user_input=input("Enter your task: ")
    messages.append({"role": "user","content": user_input})
    
    while True:
        
        planner_output=planner.generate_reply(messages=messages, sender=supervisor)
        messages.append(planner_output)
        print("----Planner-----")
        print(planner_output)
        
        executor_output = executor.generate_reply(messages=messages, sender=supervisor)
        messages.append(executor_output)
        print("----Executor-----")
        print(executor_output)
        
        supervisor_feedback = supervisor.generate_reply(messages=messages, sender=supervisor)
        messages.append(supervisor_feedback)
        print("----Supervisor-----")
        print(supervisor_feedback)
        
        if "true" in supervisor_feedback["is_terminate"].lower():
            break



if __name__ == "__main__":
    main()
