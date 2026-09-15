import hashlib
from pathlib import Path
import pytest
from services.director.wiring import assemble_media, MediaAssemblyError


def test_golden_concat_executes_on_renderer_host_and_verifies_bytes(tmp_path):
    paths=[tmp_path/'c1.mp4',tmp_path/'c2.mp4']
    for p in paths: p.write_bytes(p.name.encode())
    output=tmp_path/'assembled.mp4'
    class Host:
        target='3090'
        def __init__(self): self.calls=[]
        def map_path(self,p): return '/w/'+Path(p).name
        def makedirs(self,p): pass
        def run_probe(self,argv,timeout):
            self.calls.append(argv)
            if argv[0]=='sha256sum':
                data=b'assembled' if argv[-1].endswith('assembled.mp4') else Path(tmp_path/Path(argv[-1]).name).read_bytes()
                return 0, hashlib.sha256(data).hexdigest()+'  file\n', ''
            if argv==['ffmpeg','-version']: return 0,'ffmpeg version pinned-remote',''
            return 0,'',''
        def fetch_file(self,remote,local): Path(local).write_bytes(b'assembled')
    host=Host()
    result=assemble_media([str(p) for p in paths], str(output),host=host)
    assert result['execution_host']=='3090'
    assert result['ffmpeg_version']=='ffmpeg version pinned-remote'
    assert result['command']==[
        'ffmpeg','-y','-v','error','-i','/w/c1.mp4','-i','/w/c2.mp4',
        '-filter_complex','[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]',
        '-map','[v]','-map','[a]','-c:v','libx264','-crf','18','-c:a','aac','/w/assembled.mp4']
    assert output.read_bytes()==b'assembled'


def test_host_source_mismatch_refuses_before_concat(tmp_path):
    source=tmp_path/'source.mp4'; source.write_bytes(b'correct')
    class Host:
        def map_path(self,p): return '/w/'+Path(p).name
        def makedirs(self,p): pass
        def run_probe(self,argv,timeout):
            assert argv[0] != 'ffmpeg', 'must reject before concat'
            return 0, '0'*64+' file', ''
    with pytest.raises(MediaAssemblyError,match='source SHA256'):
        assemble_media([str(source)],str(tmp_path/'assembled.mp4'),host=Host())
