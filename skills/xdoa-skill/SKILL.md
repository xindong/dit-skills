---
name: xdoa-skill
description: Use for XDOA CLI setup, upgrade guidance, capability routing, and OA task execution planning. Trigger when users want to install or upgrade xdoa, understand what xdoa can do, decide which XDOA workflow to use, or handle company office and OA tasks through xdoa such as document lookup, personal OA lookups, and approval flows. Read the matching child reference file for CLI usage, doc workflows, or flow workflows before acting.
---

# XDOA-skill

Use this as the main entry skill for `xdoa`.

This main skill should stay lightweight. It is responsible for:

- ensuring `xdoa` is installed
- upgrading `xdoa` when `xdoa version` reports a newer release
- explaining the main `xdoa` capability areas
- deciding which child reference file to read next

Do not keep all detailed workflows in this file. Read only the child reference file that matches the current task.

## Step 0: Ensure `xdoa` is available

Check first:

```bash
xdoa version
```

If `xdoa` is missing, install it before continuing.

macOS / Linux:

```bash
bash <(curl -fsSL https://oa-cdn.oss-cn-shanghai.aliyuncs.com/downloads/install.sh)
```

Windows PowerShell:

```powershell
irm https://oa-cdn.oss-cn-shanghai.aliyuncs.com/downloads/install.ps1 | iex
```

Fallback when the install script is unavailable:

```bash
npm login --scope=@xindong --auth-type=legacy --registry=https://npm.pkg.github.com
npm install -g @xindong/oa-cli
```

Verify after install:

```bash
xdoa version
```

## Step 1: Upgrade when a newer version is available

If `xdoa version` reports that a newer version exists, do not continue on the old version by default. Re-run the install script to upgrade:

macOS / Linux:

```bash
bash <(curl -fsSL https://oa-cdn.oss-cn-shanghai.aliyuncs.com/downloads/install.sh)
```

Windows PowerShell:

```powershell
irm https://oa-cdn.oss-cn-shanghai.aliyuncs.com/downloads/install.ps1 | iex
```

Then verify again:

```bash
xdoa version
```

## Main capability areas

The main `xdoa` capability groups are:

- `auth`
  - login, status, me, logout
- `doc`
  - search and read internal office and IT documents
- `flow`
  - search flows, inspect forms, build payloads, submit approvals, inspect todo or submit state
- `reserve`
  - personal bookings, room search, room booking operations
- `asset`
  - personal asset list and asset detail
- `space`
  - seat lookup, floor maps, seat history
- `okr`
  - OKR-related GET queries

## Child reference routing

Read only the matching child reference file:

- For general CLI usage, auth behavior, command style, and common OA query patterns:
  - read `references/cli-skill.md`
- For internal office and IT document retrieval through `xdoa doc`:
  - read `references/doc-skill.md`
- For approval flow search, form inspection, payload building, submit, and verification:
  - read `references/flow-skill.md`

## Routing rules

- If the user asks how to install, upgrade, or validate `xdoa`, stay in this file unless detailed command usage is also needed
- If the user asks about auth behavior, common command usage, meeting rooms, assets, seats, OKR, or personal OA state, read `references/cli-skill.md`
- If the user asks for office policy, VPN, IT support, SSO, devices, permissions, onboarding/offboarding, or other internal documentation, read `references/doc-skill.md`
- If the user asks to find, fill, test-submit, submit, or verify an approval flow, read `references/flow-skill.md`

## Response style

- Prefer concise operational guidance
- Prefer direct execution over abstract explanation when the user wants an action
- Load only the minimum child reference needed for the task
