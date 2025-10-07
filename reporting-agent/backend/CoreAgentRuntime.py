from bedrock_agentcore_starter_toolkit import Runtime
from AWSCredentials import AWSCredentials
from boto3.session import Session
import os
import json
import boto3

class CoreAgentRuntime:

    def __init__(self, awsCredentials, botoSession=None):
        self.awsCredentials = awsCredentials
        self.botoSession = botoSession
        self.agentcore_runtime = Runtime()
        self.resposne = None

    def configure(self, entry_point, requirements_txt):

        print("Configiure.....Begin")
        response = self.agentcore_runtime.configure(
            entrypoint=entry_point,
            auto_create_execution_role=True,
            auto_create_ecr=True,
            requirements_file=requirements_txt,
            region=self.awsCredentials.aws_region,
            agent_name="strands_reporting_agent")
        self.response = response

        print("Configiure.....End")

    def launch(self):
        print("launch.....Begin")
        launch_result = self.agentcore_runtime.launch(auto_update_on_conflict = True)
        status_response = self.agentcore_runtime.status()
        status = status_response.endpoint['status']
        end_status = ['READY', 'CREATE_FAILED', 'DELETE_FAILED', 'UPDATE_FAILED']
        while status not in end_status:
            time.sleep(10)
            status_response = self.agentcore_runtime.status()
            status = status_response.endpoint['status']
            print(status)
        print("launch.....End")
        status
    
    def process_stream_events(self, events):
        """
        Recursively processes an iterable of events to find trace or chunk data.
        """
        final_answer = ""
        for event in events:
            if 'chunk' in event:
                data = event['chunk']['bytes']
                text_content = data.decode('utf-8')
                final_answer += text_content
                print(text_content, end="", flush=True)

            elif 'trace' in event:
                logger.info(json.dumps(event['trace'], indent=2))
                trace_payload = event['trace'].get('payload', {})
                if 'text' in trace_payload:
                    final_answer = trace_payload['text']
            
            elif 'stream' in event:
                logger.info("Encountered nested 'stream' key. Descending into nested stream...")
                # Recursively call the function for the nested stream
                nested_answer = process_stream_events(event['stream'])
                final_answer += nested_answer

            else:
                logger.warning("Received an unknown event type: %s", event)
        
        return final_answer

    def process_event(self, event):
        result = event.get("result", {})
                    
        if result.get("isError", False):
            error_content = result.get("content", [{}])
            error_text = error_content[0].get("text", "Unknown error") if error_content else "Unknown error"
            print(f"❌ Direct execution error: {error_text}")
            return f"Error: {error_text}", []
                    
        # Extract structured content
        structured_content = result.get("structuredContent", {})
        stdout = structured_content.get("stdout", "")
        stderr = structured_content.get("stderr", "")
                    
        if stdout:
            output_parts.append(stdout)
            full_stdout += stdout
            print(f"📤 Direct stdout captured: {len(stdout)} characters")
        if stderr:
            output_parts.append(f"Errors: {stderr}")
            print(f"⚠️  Direct stderr: {stderr}")
            
        # Combine output
        final_output = "\n".join(output_parts) if output_parts else "Code executed successfully"
                
        # Extract images directly from full stdout
        images = extract_image_data(full_stdout)
                
        # Clean the output for display (remove image binary but keep analysis text)
        display_output = clean_output_for_display(final_output)
                
        print(f"✅ Direct execution completed:")
        print(f"   Output length: {len(final_output)} :: {final_output}")
        print(f"   Display output length: {len(display_output)}:: {display_output}")
        print(f"   Images extracted: {len(images)}")
                
        return display_output, images

    def test(self):
        print("test.....Begin")
        print("=============================================================")
        invoke_response = self.agentcore_runtime.invoke({"prompt": "How is the weather now?"})
        response_text = invoke_response['response'][0]
        print({"prompt": "How is the weather now . 1?"})
        print(f"Response: {response_text}")
        print("=============================================================")

        prepared_code = """
a = 3
b = 8
print(f"Sum of a & b is {a + b}")
        """
        execution_prompt = f"""Execute this Python code using the execute_python_code tool:

        ```python
        {prepared_code}
        ```

    Use the tool to run the code and return the complete output."""
        '''
        invoke_response = self.agentcore_runtime.invoke({"prompt": execution_prompt,
            "request_type": "execute_python_code",
            "code": prepared_code,
            "session_files": None
        })
        response_text = invoke_response['response'][0]
        print({"prompt": "How is the weather today?"})
        print(f"Response: {response_text}")
        '''
        aws_credentials = AWSCredentials();
        print(f"===={aws_credentials.aws_access_key}::{aws_credentials.aws_secret_key}::{aws_credentials.aws_region}")
        session = boto3.Session(
                aws_access_key_id = aws_credentials.aws_access_key,
                aws_secret_access_key = aws_credentials.aws_secret_key,
                region_name = aws_credentials.aws_region
            )

        agent_core_client = session.client('bedrock-agentcore')
        payload = json.dumps({
            "request_type": "execute_python_code",
            "code": prepared_code,
            "session_files": None
        }).encode()

        response = agent_core_client.invoke_agent_runtime(
            agentRuntimeArn="arn:aws:bedrock-agentcore:us-east-1:101494236755:runtime/strands_reporting_agent-0APBjJ9dYp",
            payload = payload
        )

        # final_answer = self.process_stream_events(response['response'])
        # print(f"\n\nFinal assembled answer: {final_answer}")

        print(response)
            
        print("=============================================================")

        print("test.....End")


if __name__ == "__main__":
    
    coreAgentRuntime = CoreAgentRuntime(AWSCredentials())
    coreAgentRuntime.configure("agent_core_runtime.py", "requirements.txt")
    coreAgentRuntime.launch()
    coreAgentRuntime.test()
   

