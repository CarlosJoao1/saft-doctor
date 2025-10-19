import os,subprocess
class Submitter:
    def __init__(self): self.jar_path=os.getenv('FACTEMICLI_JAR_PATH','/opt/factemi/FACTEMICLI.jar'); self.timeout_ms=int(os.getenv('SUBMIT_TIMEOUT_MS','600000'))
    def submit(self,saft_path,at_user,at_pass):
        if not os.path.exists(self.jar_path): return False,f'FACTEMICLI.jar not found at {self.jar_path}'
        cmd=['java','-jar',self.jar_path,'-u',at_user,'-p',at_pass,'-f',saft_path]
        try:
            out=subprocess.run(cmd,capture_output=True,text=True,timeout=self.timeout_ms/1000)
            ok=(out.returncode==0); return ok, out.stdout if ok else (out.stdout+'\n'+out.stderr)
        except subprocess.TimeoutExpired:
            return False,'Submission timed out'
