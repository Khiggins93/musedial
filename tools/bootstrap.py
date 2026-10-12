"""Fetch the exact upstream libraries and apply the documented JPEG patch."""
import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LOCK=json.loads((ROOT/'dependencies.lock.json').read_text())
def run(*args):subprocess.run(args,check=True,cwd=ROOT)
def main():
    version=subprocess.check_output(['arduino-cli','version'],text=True)
    if f"Version: {LOCK['arduino_cli']} " not in version:raise RuntimeError('Install Arduino CLI '+LOCK['arduino_cli'])
    run('arduino-cli','core','update-index','--additional-urls','https://espressif.github.io/arduino-esp32/package_esp32_index.json')
    run('arduino-cli','core','install','esp32:esp32@'+LOCK['esp32_core'],'--additional-urls','https://espressif.github.io/arduino-esp32/package_esp32_index.json')
    for name,item in LOCK['libraries'].items():
        folder=ROOT/'vendor'/name
        if not folder.exists():
            folder.mkdir(parents=True)
            run('git','-C',str(folder),'init')
            run('git','-C',str(folder),'remote','add','origin',f'https://github.com/m5stack/{name}.git')
            run('git','-C',str(folder),'fetch','--depth','1','origin',item['commit'])
            run('git','-C',str(folder),'checkout','--detach','FETCH_HEAD')
        actual=subprocess.check_output(['git','-C',str(folder),'rev-parse','HEAD'],text=True).strip()
        if actual!=item['commit']:raise RuntimeError('Unexpected dependency checkout: '+name)
    path=ROOT/'vendor/M5GFX/src/lgfx/utility/lgfx_tjpgd.h'
    data=path.read_bytes(); old=b'#define JD_BAYER\t\t1\t/* Use bayer pattern table */';new=old.replace(b'\t1\t',b'\t0\t')
    if data.count(old)+data.count(new)!=1:raise RuntimeError('Unexpected JPEG decoder header')
    path.write_bytes(data.replace(old,new))
    print('Pinned dependencies ready; JPEG Bayer dithering disabled.')
if __name__=='__main__':main()
