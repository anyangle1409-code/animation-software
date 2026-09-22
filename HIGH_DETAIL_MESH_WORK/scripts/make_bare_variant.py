"""Detach the shorts mesh from a dressed candidate while preserving its body/rig bytes."""

import json
import struct
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
version = sys.argv[1] if len(sys.argv) > 1 else "v3"
source = root / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.glb"
target = root / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}_BARE.glb"
data = source.read_bytes()
json_length = struct.unpack_from("<I", data, 12)[0]
document = json.loads(data[20 : 20 + json_length])
binary_chunk = data[20 + json_length :]
shorts = [(index, node) for index, node in enumerate(document["nodes"]) if node.get("name") == "HomeGymPT_Shorts"]
assert len(shorts) == 1 and "mesh" in shorts[0][1]
del shorts[0][1]["mesh"]
new_json = json.dumps(document, separators=(",", ":")).encode()
new_json += b" " * (-len(new_json) % 4)
target.write_bytes(
    struct.pack("<III", 0x46546C67, 2, 20 + len(new_json) + len(binary_chunk))
    + struct.pack("<II", len(new_json), 0x4E4F534A)
    + new_json
    + binary_chunk
)
print(target)

