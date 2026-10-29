"""Install the local Windows Codex-to-Atom connection; preserve unrelated hooks/settings."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.main import init_config


def health(config):
    from urllib.parse import urlparse
    parsed=urlparse(config['endpoint'])
    if parsed.scheme!='http' or parsed.hostname!='127.0.0.1' or parsed.path!='/event':
        raise ValueError('Observer status must stay on the local loopback endpoint')
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    req=urllib.request.Request(config['endpoint'].removesuffix('/event')+'/status',headers={'Authorization':'Bearer '+config['token']})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(req,timeout=.5) as response:
        return json.load(response)


class CodexConfig:
    """Use Codex's installed protocol to list exact hooks and persist their reviewed hashes."""
    def __init__(self, executable, log):
        self.log=log.open('a',encoding='utf-8')
        self.process=subprocess.Popen([str(executable),'app-server','--stdio'],cwd=ROOT,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW)
        self.queue=queue.Queue();self.counter=0
        def read():
            for line in self.process.stdout:
                try:self.queue.put(json.loads(line))
                except ValueError:continue
        threading.Thread(target=read,daemon=True).start()
        self.call('initialize',dict(clientInfo=dict(name='atom-companion-setup',title='Atom companion setup',version='1.0'),
                                   capabilities=dict(experimentalApi=True,requestAttestation=False)))
        self.process.stdin.write(json.dumps(dict(method='initialized'))+'\n');self.process.stdin.flush()

    def call(self, method, params):
        self.counter+=1;ident=self.counter
        self.process.stdin.write(json.dumps(dict(id=ident,method=method,params=params))+'\n');self.process.stdin.flush()
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            try:msg=self.queue.get(timeout=max(.01,deadline-time.monotonic()))
            except queue.Empty:break
            if msg.get('id')==ident:
                if 'error' in msg:raise RuntimeError(method+': '+json.dumps(msg['error']))
                return msg.get('result')
        raise TimeoutError(method)

    def close(self):
        self.process.terminate()
        try:self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:self.process.kill();self.process.wait()
        self.log.close()


def register_hooks(python, codex_home, local, codex):
    path=codex_home/'hooks.json'
    before=path.read_bytes() if path.exists() else b'{"hooks":{}}'
    data=json.loads(before.decode('utf-8-sig'))
    groups=data.setdefault('hooks',{})
    command="& '"+str(python).replace("'","''")+"' '"+str(ROOT/'hooks/observe.py').replace("'","''")+"'"
    changed=False
    for event in ('UserPromptSubmit','PreToolUse','PermissionRequest','PostToolUse','Stop'):
        entries=groups.setdefault(event,[])
        if not any(h.get('command')==command for group in entries for h in group.get('hooks',[])):
            entries.append(dict(hooks=[dict(type='command',command=command,timeout=2,async_=True)]))
            entries[-1]['hooks'][0]['async']=entries[-1]['hooks'][0].pop('async_')
            changed=True
    if changed:
        backup=local/('hooks-before-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
        backup.write_bytes(before)
        if path.exists() and path.read_bytes()!=before:raise RuntimeError('Hooks changed concurrently; retry setup')
        temp=path.with_suffix('.atom-tmp');temp.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');os.replace(temp,path)
    client=CodexConfig(codex,local/'codex-config.log')
    try:
        listed=client.call('hooks/list',dict(cwds=[str(ROOT)]))
        ours=[h for entry in listed['data'] for h in entry['hooks'] if h.get('command')==command]
        assert len(ours)==5,'Codex did not load all five observer hooks'
        # Only our exact, reviewed observer command is trusted. Existing hook trust is untouched.
        edits=[dict(keyPath='hooks.state.'+json.dumps(h['key'])+'.trusted_hash',value=h['currentHash'],mergeStrategy='replace') for h in ours]
        client.call('config/batchWrite',dict(edits=edits,reloadUserConfig=True))
        listed=client.call('hooks/list',dict(cwds=[str(ROOT)]))
        ours=[h for entry in listed['data'] for h in entry['hooks'] if h.get('command')==command]
        assert len(ours)==5 and all(h['trustStatus']=='trusted' for h in ours),'Observer hook trust was not confirmed'
        return [dict(event=h['eventName'],trusted=h['trustStatus']=='trusted') for h in ours]
    finally:client.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',required=True)
    parser.add_argument('--codex-exe',type=Path,required=True)
    parser.add_argument('--no-startup',action='store_true')
    args=parser.parse_args()
    if os.name!='nt':parser.error('This installer is for Windows')
    from serial.tools import list_ports
    port=next((p for p in list_ports.comports() if p.device==args.port),None)
    if port is None or (port.vid,port.pid)!=(0x303A,0x1001):
        parser.error('Selected port is not the expected ESP32-S3 USB device')
    python=Path(sys.executable);pythonw=python.with_name('pythonw.exe')
    assert pythonw.is_file() and args.codex_exe.is_file()
    local=Path(os.environ['LOCALAPPDATA'])/'AtomCodexCompanion';local.mkdir(exist_ok=True)
    codex_home=Path(os.environ.get('CODEX_HOME',Path.home()/'.codex'))
    config_path=Path.home()/'.atom-companion/config.json'
    if not config_path.exists():init_config(config_path,52341)
    config=json.loads(config_path.read_text(encoding='utf-8'))
    command=[str(pythonw),'-u',str(ROOT/'hooks/run_companion.py'),'--port',args.port,'--codex-events','--log-file',str(local/'observer.log')]
    try:state=health(config)
    except OSError:
        process=subprocess.Popen(command,cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW,
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            if process.poll() is not None:raise RuntimeError('Companion exited; inspect the local observer.log')
            try:state=health(config);break
            except OSError:time.sleep(.2)
        else:raise RuntimeError('Companion did not start')
    if state.get('port') != args.port:
        raise RuntimeError('An existing companion owns a different port; stop that instance before switching devices')
    if not args.no_startup:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
            winreg.SetValueEx(key,'AtomCodexCompanion',0,winreg.REG_SZ,subprocess.list2cmdline(command))
    hooks=register_hooks(python,codex_home,local,args.codex_exe)
    result=dict(port=args.port,start_at_sign_in=not args.no_startup,observer=health(config),hooks=hooks)
    (local/'installation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
