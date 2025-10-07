from strands import Agent, tool
from bedrock_agentcore.tools.code_interpreter_client import code_session
import argparse
import json, sys

class CodeExecutionAgent: 

    def __init__(self, model, model_id, aws_credentials): 
        self.executor_type = "agentcore"
        self.model = model
        self.model_id = model_id
        self.SYSTEM_PROMPT = f"""You are a helpful AI assistant powered by {self.model_id} that validates all answers through code execution.

VALIDATION PRINCIPLES:
1. When making claims about code, algorithms, or calculations - write code to verify them
2. Use execute_python_code to test mathematical calculations, algorithms, and logic
3. Create test scripts to validate your understanding before giving answers
4. Always show your work with actual code execution
5. If uncertain, explicitly state limitations and validate what you can

APPROACH:
- If asked about a programming concept, implement it in code to demonstrate
- If asked for calculations, compute them programmatically AND show the code
- If implementing algorithms, include test cases to prove correctness
- Document your validation process for transparency
- The sandbox maintains state between executions, so you can refer to previous results

TOOL AVAILABLE:
- execute_python_code: Run Python code and see output

RESPONSE FORMAT: The execute_python_code tool returns execution results including stdout, stderr, and any errors."""    

        self.agent = None
        self.aws_credentials = aws_credentials

    def get_agent(self):
        if self.agent is None:
            self.agent = Agent(
                model=self.model,
                tools=[self.execute_python_code],
                system_prompt=self.SYSTEM_PROMPT
        )

        return self.agent
    

    def extract_python_code_from_prompt(self, input_text: str) -> str:
        """Extract clean Python code from markdown-formatted prompts or raw code"""
        import re
        
        # If the input contains markdown code blocks, extract the Python code
        if '```python' in input_text or '```' in input_text:
            # Pattern to match Python code blocks
            patterns = [
                r'```python\s*\n(.*?)\n```',  # ```python ... ```
                r'```\s*\n(.*?)\n```',       # ``` ... ```
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, input_text, re.DOTALL)
                if matches:
                    # Return the first match (the actual Python code)
                    clean_code = matches[0].strip()
                    print(f"🔧 Extracted Python code from markdown block")
                    return clean_code
        
        # If no markdown blocks found, check if it's a prompt with code
        if 'Execute this Python code' in input_text or 'python code' in input_text.lower():
            # Try to extract code after common prompt phrases
            lines = input_text.split('\n')
            code_lines = []
            in_code_section = False
            
            for line in lines:
                # Skip prompt text and markdown
                if any(phrase in line.lower() for phrase in [
                    'execute this python code', 'python code', 'use the tool', 
                    'return the complete output', '```'
                ]):
                    continue
                
                # If line looks like Python code, include it
                if line.strip() and (
                    line.startswith('import ') or 
                    line.startswith('from ') or
                    line.startswith('def ') or
                    line.startswith('class ') or
                    line.startswith('if ') or
                    line.startswith('for ') or
                    line.startswith('while ') or
                    line.startswith('try:') or
                    line.startswith('with ') or
                    '=' in line or
                    line.startswith('print(') or
                    line.startswith('    ')  # Indented line
                ):
                    in_code_section = True
                    code_lines.append(line)
                elif in_code_section and line.strip() == '':
                    code_lines.append(line)  # Keep empty lines within code
                elif in_code_section and not line.strip():
                    continue
                elif in_code_section:
                    # If we were in code section and hit non-code, we might be done
                    break
            
            if code_lines:
                clean_code = '\n'.join(code_lines).strip()
                print(f"🔧 Extracted Python code from prompt text")
                sys.stdout.flush()
                return clean_code
        
        # If no special formatting detected, return as-is (assume it's already clean code)
        print(f"🔧 Using input as-is (no markdown formatting detected)")
        sys.stdout.flush()
        return input_text.strip()


    def extract_image_data(self, execution_result: str):
        """Extract base64 image data from execution results - fixed for AgentCore format"""
        try:
            import re
            import base64
            
            images = []
            
            print(f"🔍 Image extraction - Input length: {len(execution_result)}")
            print(f"🔍 Contains IMAGE_DATA: {'IMAGE_DATA:' in execution_result}")
            
            if 'IMAGE_DATA:' in execution_result:
                # Find all IMAGE_DATA: patterns in the text
                # AgentCore puts the full base64 string in stdout, so we need a greedy pattern
                pattern = r'IMAGE_DATA:([A-Za-z0-9+/=\n\r\s]+?)(?=\n[A-Za-z]|\nBase64|\n$|$)'
                matches = re.findall(pattern, execution_result, re.MULTILINE | re.DOTALL)
                
                print(f"🔍 Regex matches found: {len(matches)}")
                
                for i, match in enumerate(matches):
                    try:
                        # Clean up the base64 string - remove all whitespace and newlines
                        clean_match = re.sub(r'[\s\n\r]', '', match)
                        
                        print(f"🔍 Match {i+1} - Original length: {len(match)}, Clean length: {len(clean_match)}")
                        print(f"🔍 Match {i+1} - Starts with: {clean_match[:50]}...")
                        
                        # Must be reasonable length for an image (at least 1KB when decoded)
                        if len(clean_match) > 1000:
                            # Validate it's valid base64 and can be decoded
                            decoded = base64.b64decode(clean_match)
                            print(f"🔍 Match {i+1} - Decoded length: {len(decoded)} bytes")
                            
                            # Check if it looks like a PNG (starts with PNG signature)
                            if decoded.startswith(b'\x89PNG\r\n\x1a\n'):
                                images.append({
                                    'format': 'png',
                                    'data': clean_match,
                                    'source': 'agentcore_stdout'
                                })
                                print(f"✅ Match {i+1} - Valid PNG image extracted")
                            # Also check for JPEG signatures
                            elif decoded.startswith(b'\xff\xd8\xff'):
                                images.append({
                                    'format': 'jpeg',
                                    'data': clean_match,
                                    'source': 'agentcore_stdout'
                                })
                                print(f"✅ Match {i+1} - Valid JPEG image extracted")
                            else:
                                print(f"⚠️  Match {i+1} - Invalid image signature")
                        else:
                            print(f"⚠️  Match {i+1} - Too short to be valid image")
                    except Exception as e:
                        print(f"❌ Match {i+1} - Extraction error: {e}")
                        continue
            
            print(f"🎯 Final result: {len(images)} images extracted")
            return images
            
        except Exception as e:
            print(f"❌ Image extraction error: {e}")
            return []

    def clean_output_for_display(self, output: str) -> str:
        """Clean output for display by removing image binary data while preserving analysis text"""
        if not output:
            return output
        
        # If output contains IMAGE_DATA, extract everything except the binary
        if 'IMAGE_DATA:' in output:
            parts = output.split('IMAGE_DATA:')
            cleaned_parts = []
            
            # Add the part before IMAGE_DATA
            if parts[0].strip():
                cleaned_parts.append(parts[0].strip())
            
            # Process parts after IMAGE_DATA
            for i in range(1, len(parts)):
                # Split on newline to separate binary from any following text
                lines = parts[i].split('\n', 1)
                if len(lines) > 1:
                    # Skip the binary line, keep any text after it
                    remaining_text = lines[1].strip()
                    if remaining_text and not remaining_text.startswith(('iVBOR', '/9j/', 'data:')):
                        cleaned_parts.append(remaining_text)
            
            if cleaned_parts:
                result = '\n\n'.join(cleaned_parts)
                print(f"🧹 Cleaned output: removed image binary, kept {len(result)} chars of text")
                return result
            else:
                return "Code executed successfully - chart generated"
        
        return output

        def process_event(self, response):
            # Process response directly without Strands-Agents truncation
            try: 
                output_parts = []
                full_stdout = ""
                
                print(f"response:: {response}")
                sys.stdout.flush()

                for event in response["stream"]:
                    print(f"Event:: {event}")
                    sys.stdout.flush()

                    result = event.get("result", {})

                    print(f"Result:: {result}")
                    sys.stdout.flush()
                    
                    if result.get("isError", False):
                        error_content = result.get("content", [{}])
                        error_text = error_content[0].get("text", "Unknown error") if error_content else "Unknown error"
                        print(f"61. ❌ Direct execution error: {error_text}")
                        sys.stdout.flush()
                        return f"Error: {error_text}", []
                    
                    # Extract structured content
                    structured_content = result.get("structuredContent", {})
                    stdout = structured_content.get("stdout", "")
                    stderr = structured_content.get("stderr", "")
                    
                    if stdout:
                        output_parts.append(stdout)
                        full_stdout += stdout
                        print(f"6.2 📤 Direct stdout captured: {len(stdout)} characters")
                        sys.stdout.flush()
                    if stderr:
                        output_parts.append(f"Errors: {stderr}")
                        print(f"6.3 ⚠️  Direct stderr: {stderr}")
                        sys.stdout.flush()
                
                # Combine output
                final_output = "\n".join(output_parts) if output_parts else "Code executed successfully"
                
                # Extract images directly from full stdout
                images = self.extract_image_data(full_stdout)
                
                # Clean the output for display (remove image binary but keep analysis text)
                display_output = self.clean_output_for_display(final_output)
                
                print(f"✅ Direct execution completed:")
                print(f"   Output length: {len(final_output)}")
                print(f"   Display output length: {len(display_output)}")
                print(f"   Images extracted: {len(images)}")
                sys.stdout.flush()
                
                return display_output, images
            except Exception as e:
                print(f"Exception: {e}")
                sys.stdout.flush()



    @tool
    def execute_python_code(self, code: str, session_files: list = None) -> tuple[str, list]:
        """Execute code"""
        try:
            print(f"\n🎨 Code  execution")
            print(f"📝 Code length: {len(code)} characters")
            
            # Clean the code to remove any markdown formatting
            clean_code = self.extract_python_code_from_prompt(code)
            print(f"🔧 Clean code length: {len(clean_code)} characters")
            print("1. ====================================")
            sys.stdout.flush()

            
            with code_session(self.aws_credentials.aws_region) as code_client:
                # Upload files to sandbox if provided
                if session_files:
                    print(f"📁 2. Uploading......{len(session_files)} files to sandbox...")
                    sys.stdout.flush()
 
                    files_data = []
                    file_metadata = []
                    for file_info in session_files:
                        print(f"📁 3. Uploading......{file_info} files to sandbox...")
                        sys.stdout.flush()
                   
                        files_data.append({
                            "path": file_info['filename'],
                            "text": file_info['content']
                        })

                        print(f"📁 31. Uploaded to files_data......{files_data} files to sandbox...")
                        sys.stdout.flush()

                        print(f"📁 4. Uploading......{file_info['filename']}: {len(file_info['content'])} files to sandbox...")
                        sys.stdout.flush()

                        file_metadata.append({
                            "name": file_info['filename'],
                            "length": len(file_info['content'])
                        })
                    
                    
                    print(f"41. upload Started===================================={file_metadata}")
                    sys.stdout.flush()
                    
                    # Upload files using writeFiles tool
                    upload_response = code_client.invoke("writeFiles", {"content": files_data})

                    print(f"41. upload Ended===================================={file_metadata}")
                    sys.stdout.flush()

                    for event in upload_response["stream"]:
                        result = event.get("result", {})
                        if result.get("isError", False):
                            error_content = result.get("content", [{}])
                            error_text = error_content[0].get("text", "Unknown error") if error_content else "Unknown error"
                            print(f"5. ❌ File upload error: {error_text}")
                            sys.stdout.flush()
                            return f"File upload failed: {error_text}", []
                        else:
                            content = result.get("content", [])
                            for item in content:
                                if item.get("type") == "text":
                                    print(f"5. ✅ File upload: {item.get('text', '')}")
                                    sys.stdout.flush()
                
                print(f"51. Execute Start ====================================")
                sys.stdout.flush()
                # Execute the cleaned code
                response = code_client.invoke("executeCode", {
                    "code": clean_code,
                    "language": "python",
                    "clearContext": False
                })
                print(f"52. Execute Ended===================================={response}")
                sys.stdout.flush()
            
            # Process response directly without Strands-Agents truncation
            output_parts = []
            full_stdout = ""
            
            for event in response["stream"]:
                result = event.get("result", {})
                
                if result.get("isError", False):
                    error_content = result.get("content", [{}])
                    error_text = error_content[0].get("text", "Unknown error") if error_content else "Unknown error"
                    print(f"61. ❌ Direct execution error: {error_text}")
                    sys.stdout.flush()
                    return f"Error: {error_text}", []
                
                # Extract structured content
                structured_content = result.get("structuredContent", {})
                stdout = structured_content.get("stdout", "")
                stderr = structured_content.get("stderr", "")
                
                if stdout:
                    output_parts.append(stdout)
                    full_stdout += stdout
                    print(f"6.2 📤 Direct stdout captured: {len(stdout)} characters")
                    sys.stdout.flush()
                if stderr:
                    output_parts.append(f"Errors: {stderr}")
                    print(f"6.3 ⚠️  Direct stderr: {stderr}")
                    sys.stdout.flush()
            
            # Combine output
            final_output = "\n".join(output_parts) if output_parts else "Code executed successfully"
            
            # Extract images directly from full stdout
            images = self.extract_image_data(full_stdout)
            
            # Clean the output for display (remove image binary but keep analysis text)
            display_output = self.clean_output_for_display(final_output)
            
            print(f"✅ Direct execution completed:")
            sys.stdout.flush()
            print(f"   Output length: {len(final_output)}")
            sys.stdout.flush()
            print(f"   Display output length: {len(display_output)}")
            sys.stdout.flush()
            print(f"   Images extracted: {len(images)}")
            sys.stdout.flush()
            
            return response
            
            
        except Exception as e:
            print(f"❌ Direct AgentCore execution failed: {str(e)}")
            import traceback
            print(f"📋 Traceback: {traceback.format_exc()}")
            return f"Direct execution failed: {str(e)}", []
            sys.stdout.flush()

