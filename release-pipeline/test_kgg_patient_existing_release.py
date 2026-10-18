"""Fail-closed contract for the additive existing-patient-PR release route."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ExistingPatientRelease(unittest.TestCase):
    def setUp(self):
        self.workflow = (ROOT / '.github/workflows/kgg-patient-gpt-preview-gate.yml').read_text(encoding='utf-8')
        self.assertIn('  merge-existing-patient-live:', self.workflow)
        self.job = self.workflow.split('  merge-existing-patient-live:', 1)[1]

    def test_existing_route_keeps_environment_approval(self):
        self.assertIn('    environment: patient-live', self.job)
        self.assertIn("inputs.mode == 'publish_patient_live' && inputs.existing_pr != ''", self.job)
        self.assertIn('[[ "$APPROVAL" == \'Zulassen\' ]]', self.job)
        self.assertNotIn('--admin', self.job)
        self.assertNotIn('--force', self.job)

    def test_exact_sha_and_same_repository_are_enforced(self):
        self.assertIn('[[ "$GITHUB_SHA" == "$EXPECTED_HEAD" ]]', self.job)
        self.assertIn("pr['head']['repo']['full_name']==os.environ['GITHUB_REPOSITORY']", self.job)
        self.assertIn("pr['head']['sha']==os.environ['EXPECTED_HEAD']", self.job)
        self.assertIn("pr['base']['ref']=='main'", self.job)
        self.assertIn('--match-head-commit "$EXPECTED_HEAD"', self.job)
        self.assertEqual(self.job.count('--required'), 2)

    def test_verification_is_bounded_and_checks_actual_client(self):
        self.assertIn('timeout-minutes: 15', self.job)
        self.assertIn('for attempt in {1..12}', self.job)
        self.assertIn('--max-time 10', self.job)
        self.assertIn('kgg_patient_live_version_smoke.js', self.job)
        self.assertIn('test "$ready" = true', self.job)

    def test_old_payload_route_remains_the_default(self):
        self.assertIn("  patient-gate:\n    if: inputs.existing_pr == ''", self.workflow)
        self.assertIn("  merge-patient-live:\n    if: inputs.mode == 'publish_patient_live' && inputs.existing_pr == ''", self.workflow)
        self.assertEqual(self.workflow.count('      existing_pr:'), 2)

    def test_both_release_routes_verify_local_update_before_merging(self):
        payload = self.workflow.split('  patient-gate:', 1)[1].split('  merge-patient-live:', 1)[0]
        regression = 'node --test release-pipeline/kgg_patient_live_version_smoke.test.cjs'
        smoke = 'node release-pipeline/kgg_patient_live_version_smoke.js'
        self.assertIn("      - name: Verify local stale-client update before release\n"
                      "        if: inputs.mode == 'publish_patient_live'", payload)
        for job, mutation in ((payload, 'gh pr create'), (self.job, 'gh pr merge')):
            with self.subTest(route=mutation):
                self.assertIn(regression, job)
                self.assertIn('--local-only', job)
                self.assertLess(job.index(regression), job.index(smoke))
                self.assertLess(job.index('--local-only'), job.index(mutation))
        self.assertIn("'${{ steps.gate.outputs.patient_version }}'", payload)
        self.assertIn('"$GITHUB_WORKSPACE/base" --local-only', payload)
        self.assertIn('"$PATIENT_VERSION"', self.job)
        self.assertIn('"$GITHUB_WORKSPACE" --local-only', self.job)

if __name__ == '__main__':
    unittest.main()
