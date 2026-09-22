# Lil Mansions — California DRE License Verification

This project automatically retrieves the public California Department of Real Estate Licensee List, finds DRE license **01890136**, and publishes a small JSON file that can be displayed on the Lil Mansions GoDaddy website.

## What it does

- Runs automatically once per day.
- Downloads the official DRE Licensee List ZIP from the DRE data-file page.
- Finds license `01890136`.
- Extracts the license name, type, status, and expiration.
- Writes the result to `docs/license.json`.
- Commits changes only when the license data changes.

## Important

The DRE says its public license information represents its records and may not reflect pending licensing changes. The website should therefore include an official DRE verification link and should not claim that the site's copy is an independent government verification.

## Setup

1. Create a GitHub repository named `lilmansions-license-verification`.
2. Upload this project.
3. Enable GitHub Pages:
   - Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main`
   - Folder: `/docs`
4. Go to Actions → Update California DRE License → Run workflow.
5. Confirm `docs/license.json` was updated and contains a current `lastCheckedUtc`.
6. Your JSON URL will be:

   `https://YOUR-GITHUB-USERNAME.github.io/lilmansions-license-verification/license.json`

7. Paste the provided GoDaddy HTML embed into an HTML section on the Lil Mansions site and replace `YOUR-GITHUB-USERNAME` with your GitHub username.

## Official DRE lookup

https://www2.dre.ca.gov/PublicASP/pplinfo.asp?License_id=01890136
