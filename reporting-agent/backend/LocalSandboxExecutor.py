import subprocess

class LocalSandboxExecutor:
    def __init__(self, clean_code, session_files):
        self.clean_code = clean_code
        self.session_files = session_files
        self.path = "/Users/sugahlot/workplace/amazon-bedrock-agentcore/amazon-bedrock-agentcore-samples/02-use-cases/text-to-python-ide/"
        # print(f"session files : {session_files}")
        self.save_session_files()

    def save_session_files(self):
        print(f"save_session_files")
        if self.session_files:
            print(f"📁 Saving {len(self.session_files)} files to Local sandbox...")

            for file_info in self.session_files:
                with open(file_info['filename'], "w") as file:
                    file.write(file_info['content'])
                    print(f"file saved {file}")


        with open("a.py", "w") as file:
            file.write(self.clean_code)
            print(f"py file saved {file}")


    def execute_code(self):

        result = subprocess.run(["python", "a.py"], capture_output=True, text=True)

        print(result)





