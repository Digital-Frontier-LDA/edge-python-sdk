# Runbook — scoped GitHub App for the upstream-sync workflow

`.github/workflows/sync-upstream.yml` opens a PR when a newer `latitudesh-python-sdk`
release is detected. Opening a PR from a workflow requires a token that is allowed to
create pull requests. The org policy **"Allow GitHub Actions to create and approve pull
requests" is OFF** org-wide, and the per-repo toggle is overridden by it (the API returns
`409 Conflict` when you try to set it on the repo).

Rather than turn that control on for **every** repo in the org — which would also let any
workflow anywhere self-**approve** PRs — this workflow authenticates with a **GitHub App
scoped to this repository only**. This is the least-privilege option: org policy stays
locked, no other repo gains anything.

This is a **one-time** setup. Until it is done, the workflow fails fast at its
`Preflight — require the sync App credentials` step with a link back here.

---

## What you create

A GitHub App owned by the `Digital-Frontier-LDA` org, installed on **`edge-python-sdk`
only**, with exactly two repository permissions:

| Permission | Level | Why |
|---|---|---|
| Pull requests | Read and write | open the sync PR |
| Contents | Read and write | push the `sync/upstream-<v>` branch |

Nothing else. No org permissions, no account permissions, no webhook.

## Steps

1. **Create the App**
   `https://github.com/organizations/Digital-Frontier-LDA/settings/apps` → **New GitHub App**.
   - **Name:** `df-edge-sdk-sync` (any unique name)
   - **Homepage URL:** the repo URL is fine
   - **Webhook:** *uncheck* "Active" — this App is pull-only, it receives nothing
   - **Repository permissions:** set **Pull requests → Read and write** and
     **Contents → Read and write**. Leave everything else "No access".
   - **Where can this App be installed:** "Only on this account"
   - Create.

2. **Note the App ID** — shown on the App's settings page (a number). This becomes the
   `SYNC_APP_ID` secret.

3. **Generate a private key** — on the App page, "Private keys" → **Generate a private
   key**. A `.pem` downloads. Its full contents become the `SYNC_APP_PRIVATE_KEY` secret.

4. **Install the App on the repo** — App page → **Install App** → install into
   `Digital-Frontier-LDA` → **Only select repositories** → pick **`edge-python-sdk`** →
   Install.

5. **Set the two repo secrets**
   `https://github.com/Digital-Frontier-LDA/edge-python-sdk/settings/secrets/actions`, or:

   ```bash
   # App ID (the number from step 2)
   gh secret set SYNC_APP_ID --repo Digital-Frontier-LDA/edge-python-sdk --body '123456'

   # the whole .pem, newlines and all
   gh secret set SYNC_APP_PRIVATE_KEY --repo Digital-Frontier-LDA/edge-python-sdk < ~/Downloads/df-edge-sdk-sync.*.private-key.pem
   ```

6. **Verify** — trigger the workflow manually and watch it get past preflight:

   ```bash
   gh workflow run "Sync upstream" --repo Digital-Frontier-LDA/edge-python-sdk --ref main
   gh run watch "$(gh run list --repo Digital-Frontier-LDA/edge-python-sdk -w 'Sync upstream' -L1 --json databaseId -q '.[0].databaseId')"
   ```

   A green run either opens a `sync: bump upstream to <v>` PR, or reports "Already pinned
   to latest — no PR needed." Either is success. A red run at **Preflight** means a secret
   is unset; a red run at **Mint a scoped App token** means the App is not installed on
   this repo or the key is malformed.

## How the workflow uses it

```yaml
- name: Mint a scoped App token
  id: app-token
  uses: actions/create-github-app-token@…   # SHA-pinned
  with:
    app-id: ${{ secrets.SYNC_APP_ID }}
    private-key: ${{ secrets.SYNC_APP_PRIVATE_KEY }}

- uses: actions/checkout@…                    # SHA-pinned
  with:
    token: ${{ steps.app-token.outputs.token }}   # so `git push` is the App, not GITHUB_TOKEN
```

The minted token lives only for the run and is scoped to this repo's two permissions.
Checking out **with** it means the later `git push` is authenticated as the App, which is
also what allows CI to run on the resulting PR (pushes made with the default
`GITHUB_TOKEN` deliberately do not trigger `on: pull_request`).

## Rotating the key

Generate a new private key on the App page, update `SYNC_APP_PRIVATE_KEY`, then delete the
old key from the App. The App ID does not change.

## Why not just flip the org setting

It is reversible and would work, but it grants **create *and approve*** to every workflow
in every repo in the org — including the money-handling ones. Weakening org-wide
review-gate integrity to serve one dependency-bump sync is disproportionate. This App
buys the same capability for one repo and nothing else.
