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

## Official DRE lookup

https://www2.dre.ca.gov/PublicASP/pplinfo.asp?License_id=01890136
