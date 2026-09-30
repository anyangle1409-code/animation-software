"""Validate the frozen provenance policy for the ORIGINAL v1 O1 scaffold generator."""

EXPECTED = {
    "schema_version": 1,
    "generator_path": "scripts/generate_original_v1_clean_scaffold.py",
    "pinned_profile_commit": "e6ef05b4312a1928cc6fbb71b92a94ceaff1cc62",
    "pinned_profile_blob_sha": "ee56a49bfb2e32530520fd1811ed9427460256bd",
    "pinned_mesh_algorithm_blob_sha": "0216035a6574a0b753f8716f49e603967923f68f",
    "pinned_clean_rig_commit": "287f72c6a6ac9b1dcd771946ef548d77a40b8ea1",
    "pinned_clean_rig_blob_sha": "5c0182ae6db57e8de99547aa96d80216105a36ba",
}


def validate_generator_policy(policy, committed_blob_sha, dirty=False):
    errors = []
    for key, expected in EXPECTED.items():
        if policy.get(key) != expected:
            errors.append(key.replace("_", " "))
    generator_blob = policy.get("generator_blob_sha")
    if not isinstance(generator_blob, str) or len(generator_blob) != 40:
        errors.append("generator blob sha")
    elif committed_blob_sha != generator_blob:
        errors.append("generator blob mismatch")
    if dirty:
        errors.append("generator working tree modified")
    return errors
