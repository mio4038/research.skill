"""Reconcile inquiry rows, identify unfinished research, and export review tables."""
import argparse
import csv
import json
import re
from pathlib import Path

FIELDS = {
    "name": "企业", "country": "国家/地区", "business": "主营",
    "customer_type": "客户类型", "website": "官网", "address": "地址",
    "contact": "联系人", "email": "邮箱", "phone": "电话",
    "social": "社交", "china_trade": "中国贸易",
}
STATUS = {"已取得", "未确认", "待查", "不适用"}
EXCLUSIONS = {"个人商家", "个人自用", "重复", "无可用线索"}
CONTACTS = {"email", "phone"}
EVIDENCE_FIELDS = ("kind", "value", "source", "source_type", "retrieved_at", "status", "verified_at")
NAMES = {"website": "官网", "address": "地址", "email": "邮箱", "phone": "电话"}

def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def text_cell(value):
    if isinstance(value, int):
        return value
    text = str(value or "")
    return "'" + text if re.match(r"^[\s]*[=+@\-]", text) else text

def write_csv(directory, name, header, rows):
    with (directory / (name + ".csv")).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows([text_cell(x) for x in row] for row in rows)

def render_field(record, key):
    state = record.get("checks", {}).get(key)
    if state == "已取得":
        return record.get(key) or "待查"
    if key == "china_trade" and state == "未确认" and record.get(key) == "公开范围未检出":
        return record[key]
    if state in {"未确认", "不适用"}:
        return state
    return "待查"

def export(batch, output):
    audit = load(batch / "audit.json")
    queue = load(batch / "queue.json")
    research = load(batch / "research.json") if (batch / "research.json").exists() else {}
    known = {row["lead_id"] for row in queue}
    if not isinstance(research, dict) or set(research) - known:
        raise ValueError("research.json 含不属于本批的 lead_id。")
    if len(audit) != len({row["row"] for row in audit}):
        raise ValueError("审计表原行号有重复。")
    original_rows = {row["row"] for row in audit}
    if known != {row["lead_id"] for row in audit if row["status"] == "待查"}:
        raise ValueError("待查清单与审计表不一致。")
    main, sources, decisions, gaps = [], [], [], []
    for raw in sorted(audit, key=lambda row: row["row"]):
        lead_id, row = raw["lead_id"], raw["row"]
        record = research.get(lead_id, {})
        base = [row, raw["company"], raw["country"]]
        if raw["status"] != "待查":
            decisions.append(base + [raw["status"], raw.get("duplicate_of", "")])
            continue
        disposition = record.get("status")
        if disposition == "排除" and record.get("category") in EXCLUSIONS:
            original = record.get("duplicate_of", "")
            if record["category"] != "重复" or (original in original_rows and original != row):
                decisions.append(base + [record["category"], original])
                continue
        if disposition != "保留":
            decisions.append(base + ["待查", ""])
            gaps.append({"lead_id": lead_id, "fields": ["主体或处理状态"]})
            continue
        company = str(record.get("name") or raw["company"])
        grade = record.get("grade")
        checks = record.get("checks", {})
        missing = [
            name for key, name in FIELDS.items()
            if checks.get(key) not in STATUS - {"待查"}
            or (checks.get(key) == "已取得" and not record.get(key))
        ]
        if not record.get("name") or checks.get("name") != "已取得":
            missing.append("企业身份")
        if grade not in ("A", "B", "C", "D"):
            missing.append("等级")
        evidence = record.get("evidence", [])
        covered = set()
        for item in evidence:
            kind = item.get("kind")
            essentials = ("kind", "value", "source", "source_type", "retrieved_at")
            if not all(item.get(key) for key in essentials):
                missing.append("证据字段")
                continue
            if kind in CONTACTS and not item.get("status"):
                missing.append(NAMES[kind] + "验证状态")
            if kind == "email" and item.get("status") in {"validated", "not_validated", "valid", "invalid", "accept_all", "unknown"} and not item.get("verified_at"):
                missing.append("邮箱验证结果时间")
            covered.add(kind)
            label = FIELDS.get(kind, kind)
            sources.append([row, company, label] + [item.get(k, "") for k in EVIDENCE_FIELDS[1:]])
        for key in ("name", "business", "website", "address", "email", "phone"):
            if checks.get(key) == "已取得" and key not in covered:
                missing.append(FIELDS[key] + "来源")
        if missing:
            gaps.append({"lead_id": lead_id, "fields": list(dict.fromkeys(missing))})
        main.append([row, company, render_field(record, "country"),
                     grade if grade in ("A", "B", "C", "D") else "待查",
                     *(render_field(record, k) for k in ("business", "customer_type", "website", "address")),
                     raw["need"], *(render_field(record, k) for k in ("contact", "email", "phone", "social", "china_trade")),
                     *(record.get(k, "") for k in ("owner", "follow_up", "feedback", "next_date"))])
    assert len(main) + len(decisions) == len(audit)
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output, "客户名单", ["原表行","企业","国家/地区","等级","主营","客户类型","官网","地址","原询盘需求","联系人","邮箱 / 状态","电话","社交","中国贸易","负责人","跟进状态","客户反馈","下次跟进日期"], main)
    write_csv(output, "来源与验证", ["原表行","企业","类别","内容","来源","来源类型","获取时间","状态","验证结果获取时间"], sources)
    write_csv(output, "处理记录", ["原表行","原线索","国家/地区","处理状态","重复主记录行"], decisions)
    report = {"rows": len(audit), "retained": len(main), "other": len(decisions), "unfinished": gaps}
    (batch / "completeness.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"rows": len(audit), "retained": len(main), "unfinished": len(gaps)}, ensure_ascii=False))
    return bool(gaps)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path)
    parser.add_argument("output", type=Path)
    cli = parser.parse_args()
    raise SystemExit(2 if export(cli.batch, cli.output) else 0)
