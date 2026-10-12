"""Verified installation with mandatory local backup; identity-bound full restore."""
import argparse,hashlib,json,subprocess,sys,uuid,time
from pathlib import Path
from datetime import datetime,timezone,timedelta
from halloween_format import layout,validate_assets
SEGMENTS={'bootloader.bin':(0,0x8000),'partitions.bin':(0x8000,3072),'boot_app0.bin':(0xe000,8192),'application.bin':(0x10000,0x330000),'halloween.bin':(0x340000,3*1024*1024)}
def sha(data):return hashlib.sha256(data).hexdigest()
def validate_release(folder):
    folder=Path(folder);m=json.loads((folder/'manifest.json').read_text())
    if (m.get('board'),m.get('chip'),m.get('flash_bytes'))!=('M5Stack Dial','esp32s3',8388608):raise ValueError('Unsupported target')
    rows=m.get('files',[])
    if len(rows)!=len(SEGMENTS) or {x.get('name') for x in rows}!=set(SEGMENTS):raise ValueError('Unexpected segments')
    for row in rows:
        offset,limit=SEGMENTS[row['name']];data=(folder/row['name']).read_bytes()
        if row['offset']!=offset or not 0<len(data)<=limit or row['bytes']!=len(data) or sha(data)!=row['sha256']:raise ValueError('Invalid segment: '+row['name'])
    if layout((folder/'partitions.bin').read_bytes())!='halloween':raise ValueError('Unsupported layout')
    if (folder/'boot_app0.bin').stat().st_size!=8192:raise ValueError('Invalid OTA initialization')
    validate_assets((folder/'halloween.bin').read_bytes())
    return m
def validate_backup(folder,mac):
    folder=Path(folder);m=json.loads((folder/'backup.json').read_text());data=(folder/'flash.bin').read_bytes()
    if m.get('mac')!=mac or m.get('chip')!='esp32s3' or m.get('bytes')!=8388608:raise ValueError('Backup belongs to another device or target')
    if len(data)!=8388608 or sha(data)!=m.get('sha256'):raise ValueError('Corrupt backup')
    return m
def connect(port):
    from esptool.targets.esp32s3 import ESP32S3ROM
    rom=ESP32S3ROM(port,115200)
    try:
        rom.connect()
        if rom.get_secure_boot_enabled() or rom.get_flash_encryption_enabled():raise ValueError('Secure boot/encrypted flash is unsupported')
        mac=':'.join(f'{v:02x}' for v in rom.read_mac())
        stub=rom.run_stub();stub.flash_spi_attach(0)
        if ((stub.flash_id()>>16)&255)!=23:raise ValueError('Expected 8 MiB flash; confirm the board model')
        stub.flash_set_parameters(8388608)
        stub.change_baud(460800)
        return stub,mac
    except BaseException:
        rom._port.close();raise
def read_backup(stub,mac,port):
    """Reconnect only into the loader on transient USB failure; never write flash."""
    data=bytearray()
    try:
        # One flash sector per read bounds native USB/JTAG receive bursts.
        for offset in range(0,8388608,4096):
            for attempt in range(4):
                try:
                    chunk=stub.read_flash(offset,4096)
                    # esptool.read_flash already verifies each returned chunk's MD5.
                    if len(chunk)!=4096:raise RuntimeError('Incomplete backup chunk')
                    break
                except Exception:
                    print(f'Backup retry at {offset:#x}, attempt {attempt+1}/4',flush=True)
                    stub._port.close()
                    if attempt==3:raise
                    time.sleep(.5);stub,connected_mac=connect(port)
                    if connected_mac!=mac:raise ValueError('Device changed during backup')
            data.extend(chunk)
            if len(data)%65536==0:print('Verified backup bytes:',len(data),flush=True)
        if hashlib.md5(data).hexdigest()!=stub.flash_md5sum(0,len(data)):raise RuntimeError('Device backup digest mismatch')
        return data
    finally:stub._port.close()
def backup(stub,mac,base,port):
    stamp=datetime.now(timezone(timedelta(hours=-5)))
    folder=Path(base)/(stamp.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8]);folder.mkdir(parents=True,exist_ok=False)
    data=read_backup(stub,mac,port)
    (folder/'flash.bin').write_bytes(data)
    m={'chip':'esp32s3','mac':mac,'bytes':len(data),'sha256':sha(data),'created_bogota':stamp.isoformat()}
    (folder/'backup.json').write_text(json.dumps(m,indent=2))
    validate_backup(folder,mac)
    print('Verified LOCAL backup (keep private):',folder,flush=True)
    return folder
def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    verify=sub.add_parser('verify');verify.add_argument('--release',type=Path,required=True)
    install=sub.add_parser('install');install.add_argument('--release',type=Path,required=True);install.add_argument('--device',choices=['m5stack-dial'],required=True)
    restore=sub.add_parser('restore');restore.add_argument('--backup',type=Path,required=True)
    for p in (install,restore):p.add_argument('--port',required=True);p.add_argument('--backups',type=Path,default=Path('backups'))
    a=parser.parse_args()
    if a.action in ('install','verify'):manifest=validate_release(a.release)
    if a.action=='verify':print('Release hashes, bounds and resources verified');return
    stub,mac=connect(a.port)
    try:
        if a.action=='restore':validate_backup(a.backup,mac)
        backup(stub,mac,a.backups,a.port)
    finally:stub._port.close()
    command=[sys.executable,'-m','esptool','--chip','esp32s3','--port',a.port,'--baud','115200','write-flash']
    if a.action=='restore':command+=['0x0',str(a.backup/'flash.bin')]
    else:
        for row in sorted(manifest['files'],key=lambda x:x['offset']):command += [hex(row['offset']),str(a.release/row['name'])]
    subprocess.run(command,check=True)
    print('Flash write verified. Allow startup to finish before opening diagnostics.')
if __name__=='__main__':main()
