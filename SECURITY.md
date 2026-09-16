# Security policy

TraceOne processes model responses locally and does not require API credentials for
offline scoring. The optional collectors invoke the locally installed Codex CLI and
write raw responses under the git-ignored `data/live/` directory.

Before publishing collected data, use `scripts/export_public_data.py`; it removes
local task IDs and stderr logs. Review the export manually because future runtimes
may add fields that this version does not know about.

Use GitHub's **Report a vulnerability** form when it is enabled. Otherwise, open a
minimal issue asking the maintainer for a private contact channel; do not include raw
logs, credentials, model responses, or exploit details in that issue.
