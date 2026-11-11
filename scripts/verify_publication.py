"""Read a deployed checkpoint anonymously and verify every public download hash."""
import json
import subprocess
import sys
import time
from scripts import pipeline as p
from scripts import check_release


def verify(base):
    def get(relative):
        return subprocess.run(["curl", "--disable", "--silent", "--show-error", "--fail", "--retry", "2",
                               "--max-time", "40", base.rstrip('/')+'/'+relative], check=True, capture_output=True).stdout
    expected = (p.ROOT / 'dist/publication.json').read_bytes()
    for attempt in range(6):
        actual = get('publication.json')
        if actual == expected:
            break
        if attempt == 5:
            raise p.PipelineError('Deployed checkpoint does not match the validated publication')
        time.sleep(5)
    report = json.loads(actual)
    checked = 0
    for folder, pointer, derived in [('data', report['data_pointer'], False), ('analysis', report['analysis_pointer'], True)]:
        for name, path in check_release.pointer_files(pointer, derived).items():
            if p.digest(get(folder+'/'+path)) != pointer['files_sha256'][name]:
                raise p.PipelineError('Public download checksum mismatch: '+name)
            checked += 1
    if p.digest(get('title-audit.json')) != report['title_audit_sha256']:
        raise p.PipelineError('Public title audit checksum mismatch')
    print(json.dumps(dict(status='verified_public', url=base, downloads=checked,
                          source_snapshot_id=report['data_pointer']['snapshot_id'])))


if __name__ == '__main__':
    verify(sys.argv[1])
