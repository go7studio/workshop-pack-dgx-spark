# Workshop pack · DGX Spark

Two read-only packs for the [Go7 Workhorse](https://github.com/go7studio/Go7-Workhorse)
Workshop rail, and the collector that feeds them.

| Pack | Paints |
| --- | --- |
| `box-monitor` | GPU %, watts, one writer, loaded models, infer probes, fence labels, and the training job: live step and last-8 rate from the log, the durable save, tokens toward the 5 tok/param floor (then steps toward yaml max), hours to floor or yaml max, the trainer's gate, abort flags |
| `job-log` | The tail of that job's log |

A pack is data. Nothing in this repo runs inside Workhorse. The collector runs
on the Spark, installed by you.

## Install the packs (desk)

Workhorse → Settings → Skills → Workshop → **Add pack** → paste
`https://github.com/go7studio/workshop-pack-dgx-spark`. Workhorse downloads
the highest tagged release, shows the exact URLs each pack will read, and asks
which Local Compute host to read through. Confirm. The rail appears.

Both packs read one document: `<host>/workshop/v0/feed`. Each pack declares
`namespace: "v0"` with `path: "feed"` so Workhorse's `packSourceUrls` joins to
that gateway allowlist route. Schema stays `go7-workshop-feed/v0`.

The live Spark gateway answers `/workshop/v0/feed` today. It does **not**
serve `/workshop/box-monitor/feed` (404). Packs must match the gateway, not
the reverse.

## Install the collector (Spark, operator only)

From an NVIDIA Sync terminal (or SSH host `Go7-DGX-Spark`) on the Spark, as
the operator. Prefer the pack's 523-line collector at
`~/.local/bin/workshop-feed.py` — not the short stub under
`~/workloads/creative-llm/scripts/`.

```sh
mkdir -p ~/.local/bin ~/.config/systemd/user ~/.local/share/go7-workshop
cp packs/box-monitor/collector/workshop-feed.py ~/.local/bin/
chmod +x ~/.local/bin/workshop-feed.py
cp packs/box-monitor/collector/go7-workshop-feed.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now go7-workshop-feed.timer
systemctl --user start go7-workshop-feed.service
python3 ~/.local/bin/workshop-feed.py --print | head -60
```

The unit's `ExecStart` is `/usr/bin/python3 %h/.local/bin/workshop-feed.py`.
After install, `feed.json` must include `job.live`, `job.derived`, and
`job.live.last8TokS` (when the trainer is writing steps). A stub without those
fields leaves the Job card as —.

The collector writes `~/.local/share/go7-workshop/feed.json` every 30 s. A
failed run keeps the last valid file. It reads:

| Source | Path / command | Feed field |
| --- | --- | --- |
| Lease | `~/workloads/creative-llm/ACTIVE_GPU_JOB.json` | `job.lease` — kind, pid, yaml, startedUtc, `pidMatch` against `pgrep -f train_pretrain.py` |
| Live log | newest `~/workloads/creative-llm/logs/exclusive-probes/*.log`, `\r` → `\n` | `job.live` — last `[step]` line; `last8TokS` = Δtokens / Δelapsed over the last 480 s of step lines, first 60 s skipped |
| Durable | newest `checkpoints/**/latest.json` | `job.durable` — step, tokens, targets, `param_count`, losses, `job_complete`, `undertrained_flag`, run_name, savedAt |
| Box | `nvidia-smi` name / utilization / power | `gpuUtilPercent`, `powerWatts`, `job.gpuName`. UMA memory is N/A and never invented |
| Fence | `systemctl --user is-active` on the probe unit, `qwen38-sglang`, `bloom-v40-500m` | `exclusiveSidecar`, `job.fence` |

It also publishes `job.derived` so the desk only formats:

| Field | Meaning |
| --- | --- |
| `pctOfFloor` | 100 × live tokens / `target_tokens` (may exceed 100) |
| `pct` | that ratio clamped at 100 (do not use this as “job done”) |
| `floorMet` | live tokens ≥ 5 tok/param target |
| `hoursToFloor` | remain-to-floor / last-8; **0** after the floor |
| `hoursToMax` | remain steps to yaml `max_steps` / last-8 |
| `hoursEta` | `hoursToFloor` before the floor, `hoursToMax` after |

`job.flags` includes `two-trainers`, `qwen-up-during-train`, `gpu-idle`
(0 % for 3 min with a trainer present), `step-backwards`, and `past-floor`.
Top-level `tokPerParam` and `last8Toks` alias the **live** job row (not the
durable save). Never published: the sidecar's whole-run tok/s and
`latest.json` `tokens_per_sec`. Yaml `max_steps` is an ETA input only **after**
the floor; it is not the 5 tok/param finish.

`GO7_WORKSHOP_WORKLOAD` overrides `~/workloads/creative-llm`;
`GO7_WORKSHOP_FEED` overrides the output path.

## Serve the feed (gateway, operator only)

The Local Compute gateway on this box already serves
`~/.local/share/go7-workshop/feed.json` at `/workshop/v0/feed` for the owner
bearer. Packs declare `namespace: "v0"` to match. Do not re-point the gateway
to `/workshop/box-monitor/feed` to paper over a wrong pack path. The probes
(`/healthz`, `/readyz`, `/v1/models`) are the gateway's own. Nothing here
talks to NVIDIA Sync; the Dashboard is the backdrop, not the score.

## What this never does

No start, stop, route, lease, SSH, or write. `trainNameMatchCount` is a count,
not a process list to act on. The flags are labels on the rail; the desk does
nothing about them.

## Releases

Workhorse installs the highest semver tag (`v1.2.3`). Cut a tag to ship a
change; a change to `sources` makes Workhorse ask users to confirm the pack
again. `contract` in `pack.json` is the Workhorse vocabulary major, not this
repo's version.

Author rules (namespace join, confirm URLs, release cadence, never-list): see
[PROCESS.md](PROCESS.md).
