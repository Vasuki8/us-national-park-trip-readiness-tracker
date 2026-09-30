"""Construct a synthetic private bundle through the real archive/export path."""
import json
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from history_fixtures import snapshot, next_snapshot, notice, T0, T1
from tracker.history_store import HistoryStore
from tracker.preview import prepare_bundle

def main():
    output_parent = Path(sys.argv[1])  # The caller owns and removes this private temporary directory.
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)/'archive'; store = HistoryStore(root)
        first = snapshot([notice('a'),notice('b')]); store.append(first)
        changed = notice('a',now=T1,title='Preview-only synthetic notice',description='Synthetic evidence <script>window.previewInjected=1</script>')
        changed['observed_first_at'] = T0
        store.append(next_snapshot(first,records=[changed]))
        for code,status in [('romo','failed'),('yell','quarantined')]:
            old = snapshot(code=code); store.append(old); store.append(next_snapshot(old,status=status))
        store.append(snapshot([],code='zion'))
        (root/'pending.json').write_text('{"private":"PREVIEW_PENDING_SENTINEL"}')
        output = prepare_bundle(root, output_parent/'bundles', data_kind='synthetic')
        print(json.dumps({'bundle_file': str(output)}))

if __name__ == '__main__': main()
