from planner import planner
from executor import executor
from supervisor import supervisor

def main():
    messages=[]
    
    user_input=input("Enter your task: ")
    messages.append({"role": "user","content": user_input})
    
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
        
        supervisor_feedback = supervisor.generate_reply(messages=messages, sender=supervisor)
        messages.append(supervisor_feedback)
        print("----Supervisor-----")
        print(supervisor_feedback)
        print(messages,"\n\n")
        #if len(messages)>=6:
        #    del messages[-4]
        if  supervisor_feedback["content"]["is_terminate"]:
            break



if __name__ == "__main__":
    main()
