from strands import Agent, tool
from strands_tools import calculator # Import the calculator tool
import argparse
import json, sys
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel
from CodeExecutionAgent import CodeExecutionAgent
from AWSCredentials import AWSCredentials

app = BedrockAgentCoreApp()

# Create a custom tool 
@tool
def weather():
    """ Get weather """ # Dummy implementation
    return "sunny"

model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
aws_credentials = AWSCredentials()

model = BedrockModel(
    model_id=model_id,
)
agent = Agent(
    model=model,
    tools=[calculator, weather],
    system_prompt="You're a helpful assistant. You can do simple math calculation, and tell the weather."
)

codeExecutionAgent = CodeExecutionAgent(model, model_id, aws_credentials)

@app.entrypoint
def strands_agent_bedrock(payload):
    """
    Invoke the agent with a payload
    """
    user_input = payload.get("prompt")
    request_type = payload.get("request_type")
    if(request_type and request_type == "execute_python_code"):

        # code_executor_agent = codeExecutionAgent.get_agent()
        # codeExecutionAgent.execute_python_code()
        response  = codeExecutionAgent.execute_python_code(payload.get("code"), payload.get("session_files"))
        return response
        
    else:
        print("User input:", user_input)
        print("Payload:", payload)
        response = agent(user_input)
        return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()