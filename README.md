# github-to-gdrive

A GitHub Composite Action that automatically syncs Markdown documents from GitHub repositories to Google Drive as Google Docs, triggered by pushes to the main branch.

## Overview

- **Trigger**: Push to the main branch (or manual run)
- **Configuration**: Repository-to-folder mapping managed via a Google Spreadsheet
- **Output format**: Markdown → Google Docs (ready to read directly in Google Drive)

## Setup

### 1. Create a Google Service Account

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/) (or use an existing one)
2. Go to "APIs & Services" → "Library" and enable the following two APIs:
   - **Google Drive API**
   - **Google Sheets API**
3. Go to "APIs & Services" → "Credentials" → "Create Service Account"
4. After creating the service account, go to the "Keys" tab → "Add Key" → "JSON" to download the key file

> ⚠️ **Principle of least privilege**: Grant only the minimum required permissions to the Service Account.
> Do **not** grant owner access to the entire Drive.
> The action only requires **Viewer** on the spreadsheet and **Editor** on each target Drive folder.

### 2. Prepare the Google Spreadsheet

1. Create a new spreadsheet
2. Add a header row (optional)
3. Enter mapping data from row 2 onwards:

| Column A: GitHub Repo URL | Column B: GDrive Folder Name (reference) | Column C: GDrive Folder ID | Column D: Sync File Pattern | Column E: Enabled |
|---|---|---|---|---|
| https://github.com/org/project-a | Project A Manual | 1BxiMVs...（last part of folder URL） | README.md,docs/*.md | TRUE |

> **How to get the Folder ID**: Open the folder in Google Drive in your browser. The string at the end of the URL is the folder ID.
> Example: `https://drive.google.com/drive/folders/`**`1BxiMVs0XRA5nFMdKvBd`** ← this part

4. Share the spreadsheet with the service account email (e.g., `xxx@yyy.iam.gserviceaccount.com`) as a **Viewer** (read-only access is sufficient)
5. Share each target folder with the same service account as an **Editor**

### 3. Configure Each Target Repository

#### GitHub Secrets

In the target repository, go to "Settings" → "Secrets and variables" → "Actions" and add:

| Secret Name | Value |
|---|---|
| `GOOGLE_CREDENTIALS` | The full contents of the downloaded Service Account JSON key file |
| `GDRIVE_SPREADSHEET_ID` | The spreadsheet ID (the string between `/d/` and `/edit` in the spreadsheet URL) |

> **How to get the Spreadsheet ID**: Check the spreadsheet URL.
> `https://docs.google.com/spreadsheets/d/`**`1BxiMVs0XRA5nFMdKv`**`/edit` ← the bold part is the ID

> `GDRIVE_SPREADSHEET_ID` is the same value across all repositories.

#### Add the Workflow File

Copy `workflow-template.yml` from this repository to `.github/workflows/sync-to-gdrive.yml` in the target repository:

```bash
mkdir -p .github/workflows
curl -o .github/workflows/sync-to-gdrive.yml \
  https://raw.githubusercontent.com/ga-t-nishimura/github-to-gdrive/main/workflow-template.yml
git add .github/workflows/sync-to-gdrive.yml
git commit -m "ci: add Google Drive sync workflow"
git push
```

### 4. Verify

Go to the "Actions" tab in GitHub → "Sync docs to Google Drive" → "Run workflow" to trigger a manual run.
If the log shows `Done. X file(s) synced to Google Drive folder '...'`, the setup is complete.

---

## Security

### Minimum Permissions for the Service Account

Grant the Service Account **only** the following permissions (no Drive-wide access required):

- Mapping spreadsheet → **Viewer** (read-only)
- Each target Drive folder → **Editor** (required for file creation and updates)

### Key Rotation

It is recommended to periodically rotate the Service Account key registered as `GOOGLE_CREDENTIALS`:

1. Add a new key to the service account in Google Cloud Console
2. Update the `GOOGLE_CREDENTIALS` secret in all target repositories with the new key
3. Delete the old key in Google Cloud Console

### Version Pinning (recommended for production)

The `workflow-template.yml` references `@main` by default. For production use, pin to a tag or SHA:

```yaml
- uses: ga-t-nishimura/github-to-gdrive@v1  # pinned to a tag
```

---

## Cost

### Essentially Free

| Component | Cost | Notes |
|---|---|---|
| Google Sheets API | **Free** | Read frequency stays well below the API limit (100 req/100 sec) |
| Google Drive API | **Free** | Document uploads fit within the free tier |
| Google Cloud Service Account | **Free** | Drive & Sheets APIs require no billing |
| Google Drive Storage | **Free (effectively)** | Converted Docs are only a few KB to tens of KB |

### Note: GitHub Actions Usage (for private repositories)

| Plan | Free Monthly Minutes | Overage Cost |
|---|---|---|
| GitHub Free | 2,000 min/month | $0.008/min |
| GitHub Team | 3,000 min/month | $0.008/min |

- One sync run: ~1–2 minutes
- Estimate: 10 repos × 5 pushes/day = ~500–1,000 min/month → **likely within the free tier**
- **Public repositories are completely free with no limits**

**Conclusion**: Essentially free to operate.

---

## Sync File Pattern Syntax

| Pattern | Target Files |
|---|---|
| `README.md` | Only the root-level README.md |
| `docs/*.md` | All .md files directly under the docs folder |
| `README.md,docs/*.md` | Combination of the above two |
| `**/*.md` | All .md files in all folders |

> **Google Doc naming**: Files in subdirectories are saved with their path included in the name (e.g., `docs / guide`) to prevent naming conflicts.
