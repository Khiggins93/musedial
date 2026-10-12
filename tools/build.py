"""Build from committed resources; package only distributable flash segments."""
import hashlib,json,shutil,subprocess,zipfile
from pathlib import Path
from halloween_format import layout,validate_assets
ROOT=Path(__file__).resolve().parents[1]
def main():
    lock=json.loads((ROOT/'dependencies.lock.json').read_text())
    resources=(ROOT/'assets/halloween.bin').read_bytes();validate_assets(resources)
    if hashlib.sha256(resources).hexdigest()!=lock['assets_sha256']:raise RuntimeError('Resource checksum differs from lock file; update it explicitly after regeneration')
    build=ROOT/'build/firmware'
    # Remove developer home/build paths from __FILE__ and debug metadata.
    prefixes=dict([(str(ROOT),'/musedial'),(ROOT.as_posix(),'/musedial'),(str(Path.home()),'/builder'),(Path.home().as_posix(),'/builder')])
    maps=' '.join(f'"-ffile-prefix-map={path}={replacement}"' for path,replacement in prefixes.items())
    subprocess.run(['arduino-cli','compile','--fqbn',lock['fqbn'],'--libraries',str(ROOT/'vendor'),'--build-property','compiler.c.extra_flags='+maps,'--build-property','compiler.cpp.extra_flags='+maps,'--build-path',str(build),str(ROOT/'firmware/MuseDial')],check=True)
    if layout((build/'MuseDial.ino.partitions.bin').read_bytes())!='halloween':raise RuntimeError('Wrong partition map')
    app=(build/'MuseDial.ino.bin').read_bytes()
    if len(app)>0x330000:raise RuntimeError('Application exceeds its partition')
    release=ROOT/'dist'/('musedial-'+lock['version']);release.mkdir(parents=True,exist_ok=True)
    files={'bootloader.bin':(0,(build/'MuseDial.ino.bootloader.bin').read_bytes()),'partitions.bin':(0x8000,(build/'MuseDial.ino.partitions.bin').read_bytes()),'boot_app0.bin':(0xe000,(build/'MuseDial.ino.merged.bin').read_bytes()[0xe000:0x10000]),'application.bin':(0x10000,app),'halloween.bin':(0x340000,resources)}
    manifest={'version':lock['version'],'board':'M5Stack Dial','chip':'esp32s3','flash_bytes':8388608,'files':[]}
    for name,(offset,data) in files.items():
        (release/name).write_bytes(data)
        manifest['files'].append({'name':name,'offset':offset,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    (release/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for name in ['LICENSE','NOTICE','THIRD_PARTY_NOTICES.md','dependencies.lock.json']:shutil.copy2(ROOT/name,release/name)
    shutil.copytree(ROOT/'licenses',release/'licenses',dirs_exist_ok=True)
    shutil.copy2(ROOT/'docs/INSTALL.md',release/'INSTALL.md')
    shutil.copy2(ROOT/'docs/INSTALL.en.md',release/'INSTALL.en.md')
    (release/'tools').mkdir(exist_ok=True)
    for name in ['flash.py','halloween_format.py','requirements.txt']:shutil.copy2(ROOT/'tools'/name,release/'tools'/name)
    names=list(files)+['manifest.json','LICENSE','NOTICE','THIRD_PARTY_NOTICES.md','dependencies.lock.json','INSTALL.md','INSTALL.en.md']
    names += ['tools/'+name for name in ['flash.py','halloween_format.py','requirements.txt']]
    names += ['licenses/'+p.name for p in (ROOT/'licenses').iterdir() if p.is_file()]
    paths=sorted(release/name for name in names)
    (release/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(release).as_posix()+'\n' for p in paths))
    archive=Path(str(release)+'.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in paths+[release/'SHA256SUMS']:z.write(p,release.name+'/'+p.relative_to(release).as_posix())
    print('Release:',release.name,'application bytes:',len(app))
if __name__=='__main__':main()
