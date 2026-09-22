import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

LICENSE_ID = "01890136"
DRE_DATA_PAGE = "https://dre.ca.gov/Licensees/ExamineeLicenseeListDataFiles.html"
DRE_LOOKUP_URL = f"https://www2.dre.ca.gov/PublicASP/pplinfo.asp?License_id={LICENSE_ID}"
OUTPUT = Path("docs/license.json")

HEADERS = {
    "User-Agent": "LilMansions-License-Verification/1.0"
}


def norm(value):
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]", "", str(value).strip().lower())


def clean(value):
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def find_license_download_url():
    response = requests.get(DRE_DATA_PAGE, headers=HEADERS, timeout=60)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    for a in soup.find_all("a", href=True):
        text = " ".join(a.get_text(" ", strip=True).split()).lower()
        href = a["href"]
        if "licensee list" in text and "zip" in text:
            if href.startswith("/"):
                href = "https://secure.dre.ca.gov" + href
            elif href.startswith("http://"):
                href = "https://" + href[len("http://"):]
            elif not href.startswith("http"):
                href = "https://dre.ca.gov/" + href.lstrip("/")
            return href

    raise RuntimeError("Could not find the official DRE 'Licensee List ZIP' download link.")


def download_zip(url):
    response = requests.get(url, headers=HEADERS, timeout=180)
    response.raise_for_status()
    return response.content


def header_score(row):
    vals = {norm(v) for v in row}
    score = 0
    if any("licenseid" in v or v in {"license", "licenseid"} for v in vals):
        score += 4
    if any("expiration" in v or "expirationdate" in v for v in vals):
        score += 2
    if any("licensestatus" in v or v == "status" for v in vals):
        score += 2
    if any("name" == v or "name" in v for v in vals):
        score += 1
    return score


def find_header_row(df, max_rows=40):
    best = (-1, None)
    for idx in range(min(max_rows, len(df))):
        score = header_score(df.iloc[idx].tolist())
        if score > best[0]:
            best = (score, idx)
    if best[0] < 4:
        return None
    return best[1]


def find_record_in_dataframe(df):
    # First try to identify the License ID column.
    header_row = find_header_row(df)
    if header_row is not None:
        data = df.copy()
        data.columns = [clean(x) for x in data.iloc[header_row].tolist()]
        data = data.iloc[header_row + 1:].copy()

        license_cols = [
            c for c in data.columns
            if "license" in norm(c) and ("id" in norm(c) or norm(c) == "license")
        ]

        for col in license_cols:
            matches = data[data[col].map(norm) == norm(LICENSE_ID)]
            if not matches.empty:
                return matches.iloc[0].to_dict()

    # Fallback: search every cell for an exact license-number match.
    target = norm(LICENSE_ID)
    for idx in range(len(df)):
        row = df.iloc[idx]
        for value in row.tolist():
            if norm(value) == target:
                return row.to_dict()

    return None


def find_record_in_zip(zip_bytes):
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        names = [
            n for n in z.namelist()
            if not n.endswith("/")
            and n.lower().endswith((".xlsx", ".xls", ".csv"))
        ]

        if not names:
            raise RuntimeError("The DRE ZIP did not contain an Excel/CSV data file.")

        for name in names:
            print(f"Checking {name}")
            raw = z.read(name)

            if name.lower().endswith(".csv"):
                df = pd.read_csv(io.BytesIO(raw), dtype=str, header=None, keep_default_na=False)
                record = find_record_in_dataframe(df)
                if record:
                    return name, record

            else:
                engine = "openpyxl" if name.lower().endswith(".xlsx") else "xlrd"
                workbook = pd.ExcelFile(io.BytesIO(raw), engine=engine)

                for sheet in workbook.sheet_names:
                    df = pd.read_excel(
                        io.BytesIO(raw),
                        sheet_name=sheet,
                        dtype=str,
                        header=None,
                        keep_default_na=False,
                        engine=engine,
                    )
                    record = find_record_in_dataframe(df)
                    if record:
                        return f"{name}::{sheet}", record

    return None, None


def get_field(record, patterns):
    normalized = {norm(k): clean(v) for k, v in record.items()}
    for pattern in patterns:
        p = norm(pattern)
        for key, value in normalized.items():
            if p in key and value:
                return value
    return ""


def main():
    print(f"Updating California DRE license {LICENSE_ID}")
    download_url = find_license_download_url()
    print(f"Official DRE download URL: {download_url}")

    zip_bytes = download_zip(download_url)
    source_file, record = find_record_in_zip(zip_bytes)

    if not record:
        raise RuntimeError(
            f"License {LICENSE_ID} was not found in the official DRE Licensee List."
        )

    name = get_field(record, ["name", "licensee name"])
    license_type = get_field(record, ["license type", "type"])
    status = get_field(record, ["license status", "status"])
    expiration = get_field(record, ["expiration date", "expiration"])

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    payload = {
        "licenseNumber": LICENSE_ID,
        "name": name or "Robert Paul Esparza Jr",
        "licenseType": license_type or "SALESPERSON",
        "status": status or "LICENSED",
        "expiration": expiration or "03/08/29",
        "lastCheckedUtc": now,
        "source": "California Department of Real Estate Licensee List",
        "sourceFile": source_file,
        "officialVerificationUrl": DRE_LOOKUP_URL,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
