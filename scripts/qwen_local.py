"""Local-deployment adapter. Standard-library only; no model downloads."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request

PROJECT = Path(os.environ.get('QWEN_IMAGE_PROJECT', str(Path.home() / 'Documents/QwenImage21')))
PYTHON = Path(os.environ.get('QWEN_IMAGE_PYTHON', str(Path.home() / 'Documents/MiniMaxH3/.venv/Scripts/python.exe')))
SERVER = 'http://127.0.0.1:8765'
PORTS = sorted(set(range(8188, 8196)) | {8765, 18290} | {int(x) for x in os.environ.get('QWEN_COMFY_PORTS', '').split(',') if x.strip()})


def queue_state(port):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f'http://127.0.0.1:{port}/queue', timeout=1) as response:
            queue = json.load(response)
        return {'port': port, 'running': len(queue['queue_running']), 'pending': len(queue['queue_pending'])}
    except (OSError, ValueError, KeyError) as exc:
        return {'port': port, 'available': False, 'error': type(exc).__name__}


def validate_runtime(image_count=1, prompt='validation', resolution=1024, seed=20261012):
    if not PYTHON.is_file():
        raise RuntimeError(f'Runtime Python not found: {PYTHON}')
    for relative in ['work/run_edit.py', 'extra_model_paths.yaml', 'workflows/community_edit_api.json', 'sources/turbo_model_index.json']:
        if not (PROJECT / relative).is_file():
            raise RuntimeError(f'Deployment file missing: {PROJECT / relative}')
    code = '''import json,sys
from pathlib import Path
project=Path(sys.argv[1]); sys.path.insert(0,str(project/'work'))
import run_edit
g=run_edit.graph_for('turbo',sys.argv[2],[f'validate_{i}.png' for i in range(int(sys.argv[3]))],int(sys.argv[4]),int(sys.argv[5]),'default','cpu','validate')
root=run_edit.model_root()
required=['diffusion_models/qwen_image_2.1_turbo_int8_convrot.safetensors','text_encoders/qwen3vl_8b_int8_convrot.safetensors','vae/qwen_image_2.1_vae_bf16.safetensors']
sizes=[7256787829,9350798360,675509688]
for p,size in zip(required,sizes):
    if not (root/p).is_file() or (root/p).stat().st_size!=size: raise RuntimeError(f'Missing or unexpected model size: {root/p}')
sigmas=[float(s.strip()) for s in g['15']['inputs']['sigmas'].split(',')]
if sigmas!=[1,0.978453,0.95418,0.926626,0.89508,0.845148,0.704534,0.414568,0]:raise RuntimeError('Unexpected Turbo sigmas')
print(json.dumps({'model_root':str(root),'model_bytes':sum(sizes),'images':int(sys.argv[3]),'steps':8,'cache':'cpu/default','graph_nodes':len(g)}))
'''
    checked = subprocess.run([str(PYTHON), '-X', 'utf8', '-c', code, str(PROJECT), prompt, str(image_count), str(resolution), str(seed)], capture_output=True, text=True, encoding='utf-8')
    if checked.returncode:
        raise RuntimeError(checked.stderr.strip() or checked.stdout.strip())
    return json.loads(checked.stdout)


def gpu_status():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=uuid,name,memory.used,utilization.gpu', '--format=csv,noheader'], capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else 'nvidia-smi failed'
    except (OSError, subprocess.TimeoutExpired):
        return 'nvidia-smi unavailable'


def lock_paths():
    return [str(p) for p in (Path.home()/'.codex/gpu-locks').glob('*.lock')]


def ensure_idle(queues, locks):
    busy = [q for q in queues if q.get('running', 0) or q.get('pending', 0)]
    if busy or locks:
        raise RuntimeError(f'GPU work or locks present; inspect owner before proceeding: queues={busy}, locks={locks}')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor',help='Read-only deployment and queue inspection')
    edit=sub.add_parser('edit',help='Edit via the existing Turbo runtime')
    edit.add_argument('--images',nargs='+',type=Path,required=True)
    edit.add_argument('--prompt-file',type=Path,required=True)
    edit.add_argument('--label',default='qwen_edit')
    edit.add_argument('--resolution',type=int,default=1024)
    edit.add_argument('--seed',type=int,default=20261012)
    edit.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    if args.command=='doctor':
        runtime=validate_runtime()
        print(json.dumps({'project':str(PROJECT),'python':str(PYTHON),'runtime':runtime,'queues':[queue_state(p) for p in PORTS],'gpu':gpu_status(),'locks':lock_paths()},ensure_ascii=False,indent=2))
        return 0
    if not 1<=len(args.images)<=10:
        parser.error('Use 1 to 10 images')
    if args.resolution<0 or args.resolution>4096 or args.resolution%32:
        parser.error('resolution must be 0..4096 in multiples of 32')
    for p in [*args.images,args.prompt_file]:
        if not p.is_file():parser.error(f'Input missing: {p}')
    prompt=args.prompt_file.read_text(encoding='utf-8-sig').strip()
    if not prompt:parser.error('Prompt is empty')
    checked=validate_runtime(len(args.images),prompt,args.resolution,args.seed)
    if args.dry_run:
        print(json.dumps({'submitted':False,'dry_run':True,'validated':checked},ensure_ascii=False,indent=2))
        return 0
    queues=[queue_state(p) for p in PORTS]
    ensure_idle(queues,lock_paths())
    service=next(q for q in queues if q['port']==8765)
    if service.get('available') is False:
        raise RuntimeError(f'Qwen service is not running at {SERVER}; start the existing launcher only when GPU is available.')
    command=[str(PYTHON),'-X','utf8',str(PROJECT/'work/run_edit.py'),'--images',*[str(p.resolve()) for p in args.images],'--prompt-file',str(args.prompt_file.resolve()),'--variant','turbo','--cache-device','cpu','--cache-dtype','default','--resolution',str(args.resolution),'--seed',str(args.seed),'--label',args.label,'--server',SERVER]
    return subprocess.call(command)


if __name__=='__main__':
    try:
        sys.exit(main())
    except (RuntimeError,OSError,ValueError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        sys.exit(1)
