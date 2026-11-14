"""Build the native regression-test core from an existing trusted MDPro3 checkout.
Usage: python3 tools/build_mdpro3_test_core.py /path/to/MDPro3 /workspace/mdpro3-test
Requires git, gcc, g++; does not modify the checkout. Uses its exact HEAD sources.
"""
import concurrent.futures
import pathlib
import subprocess
import sys

repo=pathlib.Path(sys.argv[1]).resolve()
root=pathlib.Path(sys.argv[2]).resolve()
root.mkdir(parents=True,exist_ok=True)
print('MDPro3 HEAD:',subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip())
for folder in ['ocgcore','lua/src']:
    prefix='Tools/YGO Classes/'+folder+'/'
    names=subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD',prefix],cwd=repo,text=True).splitlines()
    if not names:
        raise RuntimeError('Missing bundled source: '+prefix)
    for name in names:
        path=root/name.removeprefix('Tools/YGO Classes/')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(subprocess.check_output(['git','show','HEAD:'+name],cwd=repo))
(root/'script.zip').write_bytes(subprocess.check_output(['git','show','HEAD:Data/script.zip'],cwd=repo))
out=root/'build'
out.mkdir(exist_ok=True)
sources=list((root/'ocgcore').glob('*.cpp'))+[p for p in (root/'lua/src').glob('*.c') if p.name not in ['lua.c','luac.c']]
def compile_source(path):
    cmd=['g++' if path.suffix=='.cpp' else 'gcc','-O1','-fPIC','-I'+str(root/'lua/src'),'-c',str(path),'-o',str(out/(path.name+'.o'))]
    if path.suffix=='.cpp':
        cmd.insert(1,'-std=c++17')
    subprocess.run(cmd,check=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(compile_source,sources))
subprocess.run(['g++','-shared','-o',str(out/'libocgcore.so'),*[str(out/(p.name+'.o')) for p in sources],'-ldl','-lm'],check=True)
print('Built:',out/'libocgcore.so')
