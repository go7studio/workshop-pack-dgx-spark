# Workshop pack · DGX Spark

Two read-only packs for the [Go7 Workhorse](https://github.com/go7studio/Go7-Workhorse)
Workshop rail, and the collector that feeds them.

| Pack | Paints |
| --- | --- |
| `box-monitor` | GPU %, watts, one writer, loaded models, infer probes, fence labels, and the training job: live step and last-8 rate from the log, the durable save, tokens toward target, hours to the token floor, the trainer's gate, abort flags |
| `job-log` | The tail of that job's log |

A pack is data. Nothing in this repo runs inside Workhorse. The collector runs
on the Spark, installed by you.

## Install the packs (desk)

Workhorse → Settings → Skills → Workshop → **Add pack** → paste
`https://github.com/go7studio/workshop-pack-dgx-spark`. Workhorse downloads
the highest tagged release, shows the exact URLs each pack will read, and asks
which Local Compute host to read through. Confirm. The rail appears.

Both packs read one document: `<host>/workshop/box-monitor/feed`. `job-log`
declares `namespace: box-monitor` so it reads the same file.

## Install the collector (Spark, operator only)

From an NVIDIA Sync terminal on the Spark, as the operator:

```sh
mkdir -p ~/.local/bin ~/.config/systemd/user
cp packs/box-monitor/collector/workshop-feed.py ~/.local/bin/
cp packs/box-monitor/collector/go7-workshop-feed.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now go7-workshop-feed.timer
python3 ~/.local/bin/workshop-feed.py --print | head -40
```

The collector writes `~/.local/share/go7-workshop/feed.json` every 30 s. A
failed run keeps the last valid file. It reads:

| Source | Path / command | Feed field |
| --- | --- | --- |
| Lease | `~/workloads/creative-llm/ACTIVE_GPU_JOB.json` | `job.lease` — kind, pid, yaml, startedUtc, `pidMatch` against `pgrep -f train_pretrain.py` |
| Live log | newest `~/workloads/creative-llm/logs/exclusive-probes/*.log`, `\r` → `\n` | `job.live` — last `[step]` line; `last8TokS` = Δtokens / Δelapsed over the last 480 s of step lines, first 60 s skipped |
| Durable | newest `checkpoints/**/latest.json` | `job.durable` — step, tokens, targets, `param_count`, losses, `job_complete`, `undertrained_flag`, run_name, savedAt |
| Box | `nvidia-smi` name / utilization / power | `gpuUtilPercent`, `powerWatts`, `job.gpuName`. UMA memory is N/A and never invented |
| Fence | `systemctl --user is-active` on the probe unit, `qwen38-sglang`, `bloom-v40-500m` | `exclusiveSidecar`, `job.fence` |

It also publishes `job.derived` (pct, remain, hours to floor, s/it, steps
ahead) so the desk only formats, and `job.flags`: `two-trainers`,
`qwen-up-during-train`, `gpu-idle` (0 % for 3 min with a trainer present),
`step-backwards`. Never published: the sidecar's whole-run tok/s and
`latest.json` `tokens_per_sec`. `max_steps` is not an ETA input.

`GO7_WORKSHOP_WORKLOAD` overrides `~/workloads/creative-llm`;
`GO7_WORKSHOP_FEED` overrides the output path.

## Serve the feed (gateway, operator only)

Add a read-only route on the Local Compute gateway that serves
`~/.local/share/go7-workshop/feed.json` at `/workshop/box-monitor/feed` for
the owner bearer. The probes (`/healthz`, `/readyz`, `/v1/models`) are the
gateway's own. Nothing here talks to NVIDIA Sync; the Dashboard is the
backdrop, not the score.

## What this never does

No start, stop, route, lease, SSH, or write. `trainNameMatchCount` is a count,
not a process list to act on. The flags are labels on the rail; the desk does
nothing about them.

## Releases

Workhorse installs the highest semver tag (`v1.2.3`). Cut a tag to ship a
change; a change to `sources` makes Workhorse ask users to confirm the pack
again. `contract` in `pack.json` is the Workhorse vocabulary major, not this
repo's version.
