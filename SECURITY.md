# Security Policy

## About this project

The NABU Hornet Dashboard is a volunteer project by CorrelAid, developed in
collaboration with NABU (Naturschutzbund Deutschland). It is not a commercial
product and does not fall under the EU Cyber Resilience Act (CRA) — this
policy exists as a good-practice baseline, not a compliance requirement.

## Supported versions

This project runs a single deployment (`prod`), tracked on the `main` branch.
Only the latest commit on `main` receives security fixes.

| Version         | Supported |
| --------------- | --------- |
| `main` (latest) | ✅        |
| older commits    | ❌        |

## Reporting a vulnerability

If you discover a security issue (e.g. exposed credentials, injection risk,
unauthenticated data exposure, dependency vulnerability), please **do not**
open a public GitHub issue.

Instead, report it privately via one of:

1. **GitHub Private Vulnerability Reporting** (preferred):
   Go to the repository's **Security** tab →
   **Report a vulnerability** at
   `https://github.com/VitaliiShevchuk2023/hornet-dashboard/security/advisories/new`
2. **Direct contact**: reach out to the repository maintainer
   (Vitalii Shevchuk) or CorrelAid IT (Jonas Stettner) directly via Slack.

Please include:
- A description of the issue and its potential impact
- Steps to reproduce (if applicable)
- Any relevant logs, screenshots, or affected file/endpoint

## Response expectations

This is a volunteer project maintained outside of working hours, so response
times are best-effort:

- **Acknowledgement:** within 5 business days
- **Initial assessment:** within 2 weeks
- **Fix or mitigation:** timeline depends on severity and volunteer
  availability; critical issues (e.g. data exposure, credential leaks) are
  prioritized

## Scope

In scope:
- The Streamlit application code (`streamlit_app.py`, `pages/`, `utils/`)
- The GBIF data sync job (`download_gbif.py`, Container Apps Job)
- Azure infrastructure defined in this repo's Terraform configuration
- Third-party dependencies listed in `requirements.txt`

Out of scope:
- The upstream GBIF API and NABU|naturgucker platform (report to GBIF/NABU
  directly)
- Social engineering or physical security

## Data sensitivity note

This dashboard displays **public, aggregate species-occurrence data** sourced
from GBIF. It does not process personal data, payment data, or credentials
belonging to end users. The main security concerns are around:
- Integrity of published observation data (see verified-data filter in
  `utils/gbif_loader.py`)
- Availability of the Azure-hosted service
- Supply-chain risk from Python dependencies (see SBOM below)

## Software Bill of Materials (SBOM)

An SBOM listing all Python dependencies and their versions can be generated
locally — see `scripts/generate_sbom.sh` in this repository. Regenerate it
whenever `requirements.txt` changes.
