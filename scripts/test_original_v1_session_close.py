"""ORIGINAL-v1 session-close classification tests."""
from __future__ import annotations
import unittest

import original_v1_session_close as s


class SessionCloseTests(unittest.TestCase):
    def base(self):
        return {"expected_branch":"model","branch":"model","sync":"SYNCED_CLEAN","working_tree":"",
                "generated_status_current":True,"handoff_has_current_revision":True,
                "handoff_has_next_action":True,"partial_candidates":[],"local_blends":[]}

    def test_clean_synced_session_is_ready(self):
        status,blockers,actions=s.assess(self.base())
        self.assertEqual(status,"READY_TO_END_SESSION");self.assertEqual(blockers,[])

    def test_local_ahead_requires_push(self):
        info=self.base();info["sync"]="LOCAL_AHEAD_NEEDS_PUSH"
        status,blockers,actions=s.assess(info)
        self.assertEqual(status,"NEEDS_ATTENTION_BEFORE_ENDING")
        self.assertTrue(any("not been pushed" in x for x in blockers))

    def test_remote_ahead_requires_reconcile(self):
        info=self.base();info["sync"]="REMOTE_AHEAD"
        status,blockers,actions=s.assess(info)
        self.assertTrue(any("newer work" in x for x in blockers))

    def test_partial_verified_candidate_can_be_preserved(self):
        info=self.base();info["partial_candidates"]=[{"revision":"r30","manifest_exists":True,"blend_exists":True,
                                                       "blend_hash_matches":True,"handoff_mentions":True}]
        status,blockers,actions=s.assess(info)
        self.assertEqual(status,"PARTIAL_WORK_PRESERVED");self.assertEqual(blockers,[])

    def test_partial_missing_blend_blocks(self):
        info=self.base();info["partial_candidates"]=[{"revision":"r30","manifest_exists":True,"blend_exists":False,
                                                       "blend_hash_matches":False,"handoff_mentions":True}]
        status,blockers,actions=s.assess(info)
        self.assertEqual(status,"NEEDS_ATTENTION_BEFORE_ENDING")
        self.assertTrue(any("local partial Blend missing" in x for x in blockers))

    def test_dirty_tree_blocks(self):
        info=self.base();info["sync"]="SYNCED_DIRTY";info["working_tree"]=" M file"
        status,blockers,actions=s.assess(info)
        self.assertTrue(any("uncommitted" in x for x in blockers))

    def test_orphan_local_blend_blocks(self):
        info=self.base();info["local_blends"]=[{"revision":"r30","manifest_exists":False,"manifest_hash_matches":False}]
        status,blockers,actions=s.assess(info)
        self.assertTrue(any("lack matching" in x for x in blockers))

    def test_sync_classification(self):
        self.assertEqual(s.sync_classification("a","a",""),"SYNCED_CLEAN")
        self.assertEqual(s.sync_classification("b","a","",(0,2)),"LOCAL_AHEAD_NEEDS_PUSH")
        self.assertEqual(s.sync_classification("b","a","",(2,0)),"REMOTE_AHEAD")
        self.assertEqual(s.sync_classification("b","a","",(1,1)),"DIVERGED")


if __name__=="__main__":
    unittest.main()
