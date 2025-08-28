from autogen_agentchat.agents import UserProxyAgent

user= UserProxyAgent(
    name="user",
    human_input_mode="TERMINATE",
    llm_config=False,
    code_execution_config=False
)