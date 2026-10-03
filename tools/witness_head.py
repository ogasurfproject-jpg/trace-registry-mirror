#!/usr/bin/env python3
"""Record what this mirror observed of the TRACE Registry, as one canonical JSON file per observed head.

The record lists the canonical head, the mirror's head after the sync, every registry NDJSON file at that head with
its SHA-256, and for each anchor line its Merkle root and signed MMR checkpoint (copied, not re-verified). The
workflow then stamps the file with OpenTimestamps, so the head and the checkpoint roots it lists get a time fixed in
Bitcoin by a clock neither the registry operator nor this mirror controls.

A new record is written when the head changed since the last record, or when the last record is older than
--heartbeat-hours (a quiet registry still gets a dated observation). Otherwise nothing is written.
Prints the path of the new record, or nothing. Standard library only.
"""
import argparse, hashlib, json, os, subprocess, sys, datetime

SCHEMA = "hs-trace-registry-witness-v1"

def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True).stdout

def registry_files(repo):
    names = git(repo, "ls-tree", "-r", "--name-only", "HEAD", "--", "registry").decode().split()
    out = []
    for n in sorted(x for x in names if x.endswith(".ndjson")):
        raw = git(repo, "show", "HEAD:" + n)
        entries = []
        for i, line in enumerate(raw.decode("utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except ValueError:
                entries.append({"line": i, "parse_error": True, "line_sha256": hashlib.sha256(line.encode()).hexdigest()})
                continue
            c = e.get("mmr_checkpoint") or {}
            entries.append({"line": i, "ts": e.get("ts"), "merkle_root": e.get("merkle_root"), "leaf_count": e.get("leaf_count"),
                            "batch_id": e.get("batch_id"), "producer": e.get("producer"),
                            "mmr_size": c.get("mmr_size"), "mmr_root": c.get("root"), "mmr_key_id": c.get("key_id"),
                            "mmr_signature": c.get("signature")})
        out.append({"path": n, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "entries": entries})
    return out

def last_record(out_dir):
    best = None
    for root, _, files in os.walk(out_dir):
        for f in files:
            if f.endswith(".json") and (best is None or f > os.path.basename(best)):
                best = os.path.join(root, f)
    return best

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True, help="clone of the mirror's main, checked out at its head")
    ap.add_argument("--canonical-head", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--heartbeat-hours", type=float, default=24.0)
    a = ap.parse_args()
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    mirror_head = git(a.registry, "rev-parse", "HEAD").decode().strip()
    prev = last_record(a.out)
    if prev:
        p = json.load(open(prev, encoding="utf-8"))
        age_h = (now - datetime.datetime.fromisoformat(p["observed_at"].replace("Z", "+00:00"))).total_seconds() / 3600
        if p.get("canonical_head") == a.canonical_head and p.get("mirror_head") == mirror_head and age_h < a.heartbeat_hours:
            return 0
    files = registry_files(a.registry)
    listing = "".join("%s\0%s\n" % (f["path"], f["sha256"]) for f in files).encode("utf-8")
    rec = {
        "schema": SCHEMA,
        "witness": "HORIZON SHIELD, The HORIZONs Co., Ltd. (https://shield.the-horizons-innovation.com/security/)",
        "canonical": "https://github.com/agentrust-io/trace-registry",
        "observed_at": now.isoformat().replace("+00:00", "Z"),
        "canonical_head": a.canonical_head,
        "mirror_head": mirror_head,
        "heads_equal": a.canonical_head == mirror_head,
        "previous_record": os.path.relpath(prev, a.out) if prev else None,
        "previous_record_sha256": hashlib.sha256(open(prev, "rb").read()).hexdigest() if prev else None,
        "registry_files": files,
        "registry_listing_sha256": hashlib.sha256(listing).hexdigest(),
        "establishes": "these registry bytes, this canonical head and the checkpoint roots listed existed no later than the Bitcoin block in the OpenTimestamps proof next to this file",
        "does_not_establish": [
            "that any checkpoint signature or producer signature is valid; they are copied, not verified",
            "that any Trust Record is true; only that the registry held these bytes",
            "that every observer saw the same history; only what this mirror saw",
        ],
    }
    d = os.path.join(a.out, now.strftime("%Y"), now.strftime("%m"))
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "%s_%s.json" % (now.strftime("%Y%m%dT%H%M%SZ"), a.canonical_head[:12]))
    if os.path.exists(path):
        print("refusing to overwrite an existing record: " + path, file=sys.stderr)
        return 1
    with open(path, "wb") as fh:
        fh.write(canon(rec))
    print(path)
    return 0

if __name__ == "__main__":
    sys.exit(main())
