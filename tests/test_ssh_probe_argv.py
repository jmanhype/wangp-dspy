"""Exercise OpenSSH's shell-command semantics, not an argv-preserving fake."""
import subprocess
from pathlib import Path

from host.render_host import SshHost


def test_probe_preserves_spaces_quotes_and_shell_metacharacters(tmp_path):
    path = tmp_path / "Grandma's voice $(touch BAD) ; still one file.mp4"
    path.write_bytes(b'native')
    calls=[]
    def ssh_shell(argv, **kwargs):
        calls.append(argv)
        # OpenSSH joins everything after the target, then the remote shell
        # parses it. Emulate that transport rather than calling cp directly.
        target_index=argv.index('test-host')
        command=' '.join(argv[target_index+1:])
        return subprocess.Popen(['sh','-c',command], cwd=tmp_path, **kwargs)
    host=SshHost(target='test-host', wgp_root='/w', pull_root=str(tmp_path/'pull'), sp=ssh_shell)
    target=tmp_path/'Copied native file.mp4'
    rc,out,err=host.run_probe(['cp',str(path),str(target)])
    assert rc==0, err
    assert target.read_bytes()==b'native'
    assert not (tmp_path/'BAD').exists()
    assert len(calls[0][calls[0].index('test-host')+1:])==1


def test_prebuilt_single_shell_command_keeps_legacy_contract(tmp_path):
    def ssh_shell(argv, **kwargs):
        return subprocess.Popen(['sh','-c',argv[-1]], **kwargs)
    host=SshHost(target='test-host', wgp_root='/w', pull_root=str(tmp_path/'pull'), sp=ssh_shell)
    assert host.run_probe(['printf launched'])[1]=='launched'
