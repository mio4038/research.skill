"""Build a reproducible queue without network calls."""
import argparse
import csv
import hashlib
import io
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ALIASES = {
    "company": ("公司名称", "公司名", "公司", "企业名称", "company name", "company"),
    "country": ("国家", "国家地区", "country"),
    "category": ("公司类型", "公司类型分类", "company type", "category"),
    "person": ("联系人", "姓名", "全名", "contact", "full name", "name"),
    "email": ("邮箱", "电子邮箱", "email"),
    "phone": ("电话", "手机号", "phone", "phone number"),
    "need": ("需求", "需要的产品说明", "采购需求", "询盘", "message", "need"),
}

def normalized(value):
    return re.sub(r"[\s_\W]+", "", unicodedata.normalize("NFKC", str(value)).casefold())

def rows_from(path, sheet):
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as source:
            return list(csv.reader(source))
    if path.suffix.lower() == ".xlsx":
        from openpyxl import load_workbook

        def read_values(source):
            workbook = load_workbook(source, read_only=True, data_only=True)
            try:
                page = workbook[sheet] if sheet else workbook.active
                return list(page.values)
            finally:
                workbook.close()

        try:
            return read_values(path)
        except TypeError as error:
            if "DataValidation.__init__()" not in str(error):
                raise
            # Some spreadsheet editors write validation attributes openpyxl
            # cannot parse. Drop those rules from an in-memory copy only.
            repaired = io.BytesIO()
            with zipfile.ZipFile(path) as original, zipfile.ZipFile(repaired, "w") as copy:
                for name in original.namelist():
                    content = original.read(name)
                    if re.fullmatch(r"xl/worksheets/[^/]+\.xml", name):
                        root = ET.fromstring(content)
                        for child in root.findall("{*}dataValidations"):
                            root.remove(child)
                        content = ET.tostring(root, encoding="utf-8")
                    copy.writestr(name, content)
            repaired.seek(0)
            return read_values(repaired)
    raise ValueError("请选择 CSV 或 XLSX。")

def mapping(headers, custom):
    names = [normalized(value or "") for value in headers]
    return {
        field: next((names.index(normalized(label)) for label in labels
                     if normalized(label) in names), None)
        for field, labels in {
            field: (custom[field],) if field in custom else labels
            for field, labels in ALIASES.items()
        }.items()
    }

def process(path, output, sheet, header, custom):
    rows = rows_from(path, sheet)
    choices = [header] if header else range(1, min(len(rows), 15) + 1)
    for first in choices:
        columns = mapping(rows[first - 1], custom)
        if all(columns[field] is not None for field in ("company", "category")):
            break
    else:
        raise ValueError("未找到公司和公司类型列。请用 --header 和 --columns 指定。")
    settings = json.dumps([sheet, first, columns], sort_keys=True).encode()
    batch = hashlib.sha256(path.read_bytes() + settings).hexdigest()[:20]
    folder = output / batch
    folder.mkdir(parents=True, exist_ok=True)
    seen = {}
    queue, audit = [], []
    for number, values in enumerate(rows[first:], first + 1):
        if not any(value not in ("", None) for value in values):
            continue
        row = {
            field: str(values[index]).strip() if index is not None and index < len(values)
            and values[index] is not None else ""
            for field, index in columns.items()
        }
        row.update(row=number, lead_id=f"{batch}:{number}")
        category = normalized(row["category"])
        if "homeowner" in category or category in ("个人自用", "自用业主"):
            audit.append({**row, "status": "个人自用"})
            continue
        if category in ("个人商家", "个体商户", "soleproprietor", "individualseller"):
            audit.append({**row, "status": "个人商家"})
            continue
        email = row["email"].casefold()
        phone = re.sub(r"^p:\s*", "", row["phone"], flags=re.I)
        digits = re.sub(r"\D", "", phone)
        phone_key = "+" + (digits[2:] if phone.startswith("00") else digits)
        keys = []
        if re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            keys.append(("email", email))
        if re.fullmatch(r"(?:\+|00)[0-9 ().-]+", phone) and 8 <= len(phone_key) - 1 <= 15:
            keys.append(("phone", phone_key))
        matches = {seen[key] for key in keys if key in seen}
        if len(matches) == 1:
            audit.append({**row, "status": "重复线索", "duplicate_of": matches.pop()})
            continue
        if len(matches) > 1:
            row["identity_note"] = "邮箱与电话对应不同前序记录，需人工核对"
        queue.append(row)
        for key in keys:
            seen.setdefault(key, number)
        audit.append({**row, "status": "待查"})
    for name, data in (("queue", queue), ("audit", audit)):
        target = folder / f"{name}.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(target)
    print(json.dumps({"folder": str(folder), "queued": len(queue), "rows": len(audit)}, ensure_ascii=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--sheet")
    parser.add_argument("--header", type=int)
    parser.add_argument("--columns", type=Path, help="JSON field-to-header mapping")
    args = parser.parse_args()
    custom = json.loads(args.columns.read_text(encoding="utf-8-sig")) if args.columns else {}
    process(args.input, args.output, args.sheet, args.header, custom)
