# Pack author process

Short rules for changing this repo. Workhorse is the host; this repo is data
plus an operator-installed collector.

## Source URL namespace

Workhorse builds JSON source URLs as:

```
{hostBase}/workshop/{namespace ?? packId}/{path}
```

(`packSourceUrls` in Workhorse `src/lib/workshop-pack.ts`.)

On the live DGX Spark gateway the feed allowlist is **`/workshop/v0/feed`**.
Both packs here must set:

```json
"namespace": "v0",
"path": "feed",
"schema": "go7-workshop-feed/v0"
```

Do not default the namespace to the pack id (`box-monitor`) unless the
gateway actually serves that path. Confirm with a bearer GET before shipping:

| Path | Expected |
| --- | --- |
| `/workshop/v0/feed` | 200, schema `go7-workshop-feed/v0` |
| `/workshop/box-monitor/feed` | 404 on this host (wrong for packs) |
| `/healthz` | 200 |

Never invent that Spark failed when the path is wrong.

## Confirm-screen URLs

After Add pack / Update, Workhorse lists the exact URLs. They must equal
`https://<host>/workshop/v0/feed` (plus probe paths). If the confirm screen
shows `…/workshop/box-monitor/feed`, the pack is wrong — fix `namespace`, do
not ask the operator to remount the gateway.

## Collector binary

| Correct | Wrong |
| --- | --- |
| `~/.local/bin/workshop-feed.py` (this repo, ~523 lines) | `~/workloads/creative-llm/scripts/workshop-feed.py` (~219-line stub) |
| systemd `ExecStart=… %h/.local/bin/workshop-feed.py` | unit still pointing at the stub |

After deploy, `--print` (or `feed.json`) must include `job.live`,
`job.derived`, and `last8TokS` when training is live. The stub leaves Job as —.

## Release / tag cadence

1. Bump each changed pack's `version` in `pack.json`.
2. Update README path notes if sources moved.
3. Commit on `main`, push, tag `vX.Y.Z` matching the highest pack version you
   intend Workhorse to install, and create a GitHub release on that tag.
4. Workhorse `installFromRepo` picks the highest semver tag. A `sources`
   change forces re-confirm on the desk.

## Never-list

No start, stop, route, lease, SSH-from-desk, or write to the box from a pack.
No leftover rings, vendor meters, or history store. Labels and soak only.
