---
name: xdoa-office-docs
description: Use xdoa for company office and IT knowledge retrieval, OA live lookups, and flow submission workflows. Use when users ask about office operations, VPN, network access, accounts, SSO, email, devices, assets, meeting rooms, office systems, internal tools, permissions, onboarding/offboarding, internal knowledge-base documents, or when they want to create, submit, test-submit, or verify a Flow/OA approval. If xdoa is missing, install it first and then continue.
---

# XDOA Office Docs

Use `xdoa` as the source of truth for company office and IT knowledge-base answers, as the live lookup tool for user-specific OA state, and as the command surface for OA flow submission.

## Step 0: Ensure `xdoa` is available

Do not stop and ask the user to install `xdoa` manually. Check first:

```bash
xdoa version
```

If `xdoa` is missing, install it yourself before continuing.

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

After installation, verify:

```bash
xdoa version
```

## What `xdoa` gives you after install

For this merged skill, the most relevant `xdoa` capabilities are:

- `xdoa doc query` / `xdoa doc view`
  - Search and read internal office and IT documents
- `xdoa auth status` / `xdoa auth login`
  - Check whether the required OA sub-system login is already present
- `xdoa flow search` / `xdoa flow form` / `xdoa flow build` / `xdoa flow submit`
  - Discover, inspect, build, and submit OA approval flows
- `xdoa flow get task`
  - Check todo, submit, cc, and completion state around a flow workflow
- `xdoa asset get` / `xdoa asset detail`
  - Check the current user's hardware and software assets
- `xdoa reserve get mine` / `xdoa reserve rooms`
  - Check personal meeting-room bookings or find available rooms
- `xdoa space search` / `xdoa space floor` / `xdoa space history`
  - Find where someone sits, inspect floor layouts, or inspect workstation history

Adjacent but less central for this skill:

- `xdoa okr get ...`
  - Useful when the user asks about OKR system access or profile information

## CLI usage notes

- Prefer the installed binary:

```bash
xdoa ...
```

- In a development checkout without the installed binary, use:

```bash
go run main.go ...
```

- Prefer `--json` when output will be filtered, parsed, or handed to another agent step.
- Keep human-readable summaries separate from machine payload files.

## Workflow A: document-backed office and IT answers

1. Search first:

```bash
rtk xdoa doc query "<keyword>" --json
```

2. Inspect the JSON search results before opening documents:
   - Judge relevance from `title_path` and `preview`
   - Skip any result whose title path, preview, URL, or tags suggest it is deprecated, especially content containing `已废弃`
   - Prefer current, specific documents over broad or weakly related results
   - If no useful non-deprecated result exists, say that the knowledge-base search did not find a reliable current document

3. Read selected documents:

```bash
rtk xdoa doc view "<doc_url_or_path>"
```

Use the `url` field returned by `doc query`; it may be a `/docs/...` path or a full URL.

4. Answer from the full document content:
   - Think through and organize the answer before responding
   - Give the practical action path first
   - Mention caveats only when they matter
   - If documents conflict, prefer the non-deprecated and more current-looking document, and state uncertainty briefly

## Workflow B: live OA lookups when the question is user-specific

When the user is not asking for general documentation, but for their current state, use `xdoa` directly.

Examples:

- "我有哪些资产" -> `xdoa asset get`
- "我预定了哪些会议室" -> `xdoa reserve get mine`
- "我坐哪" / "某某坐哪" -> `xdoa space search "<name>"`
- "A1-1F 工位图" -> `xdoa space floor A1-1F`
- "我还有哪些待办审批" -> `xdoa flow get task`

Use `--json` when the output needs to be processed or filtered further.

## Workflow C: flow submission and verification

Use this when the user wants to create, submit, test-submit, or verify a Flow/OA approval.

### Guardrails

- Do not inspect implementation code for this workflow unless the user explicitly asks.
- Read `docs/commands.md` if the command shape is uncertain.
- Keep human status and machine payloads separate. Do not paste logs into JSON payload files.
- Treat `commitToken` as sensitive and short-lived. Delete temporary payload files after submission.
- Do not submit from raw field IDs alone. Show a human-readable confirmation summary first and require explicit confirmation.

### Standard flow workflow

1. Get the flow ID from search output:

```bash
xdoa flow search "<flow name>"
```

Extract the segment after `/approval/` from the workflow URL.

2. Build the empty payload template:

```bash
xdoa flow build <flow_id>
```

3. Read the form fields and required flags:

```bash
xdoa flow form <flow_id> --json
```

4. Create a temporary `values.json` mapping field IDs to desired values.
   - Fill all required fields.
   - Leave optional upload fields empty unless the user supplied files.

5. Build the final payload:

```bash
xdoa flow build <flow_id> --values <values.json> > <payload.json>
```

6. Before submitting, show the user a clear confirmation summary that includes:
   - Flow name and flow ID
   - Each human-visible field label and value
   - Any optional fields left blank, especially upload fields
   - The exact submit command

7. Submit only after explicit confirmation:

```bash
xdoa flow submit <flow_id> --data-file <payload.json>
```

8. Verify the result by checking submissions:

```bash
xdoa flow get task -t submit --query="pageNum=1&pageSize=5&instanceStatus="
```

9. Delete temporary files containing `commitToken` or submitted values:

```bash
rm <values.json> <payload.json>
```

### Confirmation summary template

Use this shape before the final submit command:

```text
准备提交流程，请确认：

流程：<flow name>
Flow ID：<flow_id>

表单值：
- <字段名 1>：<值>
- <字段名 2>：<值>
- <可选字段>：<空/未填写>

将执行：
xdoa flow submit <flow_id> --data-file <payload.json>

请回复“确认提交”后我再提交。
```

### Success report

After submission, report only the important result:

- `POST flow 200` or the exact failure
- Approval title, status, approval code, time, and link from the latest `flow get task -t submit` output when available
- Whether temporary files were deleted

## Query guidance

- Use the user's wording as the first query
- If results are weak, retry with 1-2 focused variants, such as product name, system name, error keyword, or Chinese/English synonyms
- Do not answer from search snippets alone when a relevant document can be opened
- Do not expose raw JSON unless the user asks for it

## Response style for this skill

- Prefer concrete steps over policy summaries
- If the answer depends on a document, cite the document title/path in prose
- If no reliable current document is found, say so plainly instead of guessing
- If the answer needs a live OA lookup, perform it rather than just describing the command
- If the answer is really a flow execution request, switch to the flow workflow instead of treating it as a documentation question
