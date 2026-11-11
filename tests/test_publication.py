"""Publication failure preservation and audited expanded cohort contracts."""
from datetime import date
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts import pipeline as p
from scripts import publication
from scripts import title_audit
from scripts import analysis


class PublicationTests(unittest.TestCase):
    def test_failed_acquisition_preserves_both_active_pointers_and_records_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ['data/current.json', 'analysis/current.json', 'dist/title-audit.json', 'dist/publication.json']:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p.ROOT / name, path)
            original = {name: (root / name).read_bytes() for name in ['data/current.json', 'analysis/current.json']}
            with patch.object(publication.c, 'create', side_effect=p.PipelineError('upstream unavailable')):
                with self.assertRaisesRegex(p.PipelineError, 'unavailable'):
                    publication.refresh(root, date(2026, 11, 11))
            for name, content in original.items():
                self.assertEqual((root / name).read_bytes(), content)
            latest = p.read_json(root / 'dist/publication.json')['history'][0]
            self.assertEqual(latest['status'], 'failed_retained_last_good')
            self.assertIn('upstream unavailable', latest['message'])

    def test_live_audit_covers_the_exact_cohort_and_preserves_known_warnings(self):
        audit = title_audit.verify(p.ROOT)
        self.assertEqual(len(audit['series']), 20)
        spider = next(s for s in audit['series'] if s['series_id'] == 'spider-man')
        self.assertIn('configured_title_is_redirect', spider['flags'])
        self.assertNotEqual(spider['canonical_article'], spider['configured_article'])

    def test_groups_partition_identical_target_predictions(self):
        pointer = p.read_json(p.ROOT / 'analysis/current.json')
        result = p.read_json(p.ROOT / 'analysis' / pointer['files']['analysis.json'])
        groups = result['benchmark']['release_groups']
        self.assertEqual(groups['original_launch']['scored_days'], 810)
        self.assertEqual(groups['console_rerelease']['scored_days'], 45)
        self.assertEqual(sum(g['scored_days'] for g in groups.values()), result['benchmark']['pooled']['scored_days'])
        self.assertEqual(len(result['events']), 26)


if __name__ == '__main__':
    unittest.main()
