"""Safety tests for the whole-body anatomical issue ledger."""
import copy
import json
from pathlib import Path
import unittest

import original_v1_whole_body_issues as issues

ROOT = Path(__file__).resolve().parents[1]


class WholeBodyIssueTests(unittest.TestCase):
    def valid_issue(self):
        return {
            "id":"WB-AX-001",
            "region":"bilateral axilla",
            "severity":"Critical",
            "state":"Open",
            "candidate":{"revision":"r95","sha256":"8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd"},
            "reproduction":{"poses":["press_top"],"views":["three_quarter"],"description":"Visible in the exact production deformation path."},
            "evidence_paths":["ORIGINAL_V1_WORK/candidates/review/milestone_r95/milestone_press_top_three_quarter.png"],
            "human_evidence_ids":["HE-AX-002"],
            "evidence_gap": None,
            "defect":"Long membrane-like axillary wall and deep trench.",
            "acceptance":"Anterior and posterior folds remain distinct and volume-continuous through the elevation arc.",
            "closure_evidence":[]
        }

    def valid_ledger(self):
        return {"schema_version":1,"asset":"HomeGymPT_Male_ORIGINAL_v1","issues":[self.valid_issue()]}

    def test_live_ledger_is_valid_and_blocks(self):
        ledger=json.loads((ROOT/'ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json').read_text(encoding='utf-8'))
        self.assertEqual(issues.validate_ledger(ledger, ROOT), [])
        blockers=issues.blocking_issues(ledger)
        self.assertTrue(blockers)
        self.assertTrue(all(x['severity'] in ('Critical','High') for x in blockers))

    def test_ids_must_be_unique_and_stable(self):
        ledger=self.valid_ledger(); duplicate=copy.deepcopy(ledger['issues'][0]); ledger['issues'].append(duplicate)
        self.assertIn('duplicate issue id', '\n'.join(issues.validate_ledger(ledger)))
        ledger=self.valid_ledger(); ledger['issues'][0]['id']='shoulder-one'
        self.assertIn('invalid stable issue id', '\n'.join(issues.validate_ledger(ledger)))

    def test_severity_and_state_are_controlled(self):
        ledger=self.valid_ledger(); ledger['issues'][0]['severity']='Very bad'; ledger['issues'][0]['state']='Maybe'
        errors='\n'.join(issues.validate_ledger(ledger))
        self.assertIn('invalid severity', errors); self.assertIn('invalid state', errors)

    def test_reproduction_evidence_and_candidate_are_required(self):
        for field in ('reproduction','evidence_paths','candidate'):
            ledger=self.valid_ledger(); del ledger['issues'][0][field]
            self.assertIn('missing '+field, '\n'.join(issues.validate_ledger(ledger)), field)

    def test_open_in_progress_and_pending_review_high_issues_block(self):
        ledger=self.valid_ledger()
        for state in ('Open','In Progress','Pending Review'):
            ledger['issues'][0]['state']=state
            self.assertEqual([x['id'] for x in issues.blocking_issues(ledger)], ['WB-AX-001'])
        ledger['issues'][0]['state']='Fixed'
        self.assertEqual(issues.blocking_issues(ledger), [])

    def test_fixed_issue_requires_closure_evidence(self):
        ledger=self.valid_ledger(); ledger['issues'][0]['state']='Fixed'
        self.assertIn('Fixed requires closure_evidence', '\n'.join(issues.validate_ledger(ledger)))

    def test_missing_committed_evidence_is_rejected(self):
        ledger=self.valid_ledger(); ledger['issues'][0]['evidence_paths']=['not/a/real/file.png']
        self.assertIn('evidence path missing', '\n'.join(issues.validate_ledger(ledger, ROOT)))


if __name__ == '__main__':
    unittest.main()
