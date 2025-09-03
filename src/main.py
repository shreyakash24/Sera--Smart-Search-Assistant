# from planner import planner
# from executor import executor
# from supervisor import supervisor

# def main():
#     messages=[]
    
#     user_input=input("Enter your task: ")
#     messages.append({"role": "user","content": user_input})
    
#     while True:
#         print(messages,"\n\n")
#         planner_output=planner.generate_reply(messages=messages, sender=supervisor)
#         messages.append({"role": "planner", "content":planner_output})
#         print("----Planner-----")
#         print(planner_output)
#         print(messages,"\n\n")
#         executor_output = executor.generate_reply(messages=messages, sender=supervisor)
#         messages.append(executor_output)
#         print("----Executor-----")
#         print(executor_output)
#         print(messages,"\n\n")
#         supervisor_feedback = supervisor.generate_reply(messages=messages, sender=supervisor)
#         messages.append({"role": "supervisor", "content":supervisor_feedback})
#         print("----Supervisor-----")
#         print(supervisor_feedback)
        
#         if "true" in supervisor_feedback["is_terminate"].lower():
#             break



# if __name__ == "__main__":
#     main()

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

# FInd cheapest flight from mumbai to delhi for 2 adults on 5th september

if __name__ == "__main__":
    main()
