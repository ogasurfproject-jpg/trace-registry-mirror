# TRACE Registry mirror (HORIZON SHIELD)

An independent mirror of [agentrust-io/trace-registry](https://github.com/agentrust-io/trace-registry), run by HORIZON SHIELD, The HORIZONs Co., Ltd., following the registry's [docs/mirroring.md](https://github.com/agentrust-io/trace-registry/blob/main/docs/mirroring.md). We have no relationship with OPAQUE Systems or AgenTrust beyond this mirror.

- **`main`** is a byte-for-byte replica of canonical `main`. It carries no commit of ours. Its head is at `https://api.github.com/repos/ogasurfproject-jpg/trace-registry-mirror/commits/main`.
- **`mirror-ops`** (this branch, the repository default) holds the sync job and the witness records.

## What runs

`.github/workflows/mirror.yml`, twice an hour:

1. **sync**: fast-forwards `main` from canonical and refuses when canonical no longer descends from what we hold (a possible history rewrite). On refusal the mirror stays where it was, so both heads remain as evidence, and the run fails.
2. **witness**: writes `witness/heads/YYYY/MM/<time>_<head>.json` when the head changed, or once a day when it did not, and stamps it with OpenTimestamps. The record lists the canonical head, our head, every registry NDJSON file at that head with its SHA-256, and each anchor line's Merkle root and signed MMR checkpoint (copied, not re-verified). Records are chained by `previous_record_sha256`.

## What the witness records add

The registry's own external receipt authenticates a checkpoint root but does not establish a witness time. A record here, once its `.ots` proof is upgraded, fixes the observed head and the checkpoint roots it lists in a Bitcoin block, a clock that neither the registry operator nor this mirror controls.

Check one yourself:

```bash
shasum -a 256 witness/heads/2026/10/<record>.json
ots verify witness/heads/2026/10/<record>.json.ots
```

A record does not establish that any signature in the registry is valid, that any Trust Record is true, or that every observer saw the same history.

## Contact

Security contact: `contact@the-horizons-innovation.com` (subject `[security]`), policy at https://shield.the-horizons-innovation.com/security/ and RFC 9116 file at https://shield.the-horizons-innovation.com/.well-known/security.txt. We commit to keeping this mirror running for at least 12 months from registration, or to removing our entry if we stop.
