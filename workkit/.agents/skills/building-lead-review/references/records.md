# 本地数据和交付

## 批次与断点

`queue.py` 生成 `local-data/<批次>/queue.json` 和 `audit.json`。批次来自文件内容及读表设置。保持文件和映射一致即可恢复原批次。每次完成一家或工具结果返回时，原子写入该批次的 `research.json`。正文不放查询日志。不同批次可从 `local-data/` 中读取历史报告和验证缓存，确认主体一致后再抄入新记录。

`research.json` 是用 lead_id 索引的 JSON 对象。每条记录有 status，取“保留”“排除”或“待查”。待查尚未完成。排除只允许 category 为“个人商家”“个人自用”“重复”“无可用线索”，重复用 duplicate_of 记原表行。没有主体证据的排除记录，在独立身份补查完成后填写 category。

保留记录字段见包内 examples/research.example.json。checks 对每个字段标记“已取得”“未确认”“待查”“不适用”。“未确认”用于完成合理搜索但无法确认的项。每条 evidence 记录 kind、value、source、source_type、retrieved_at、status、verified_at（适用时）。网页用 URL，询盘值用输入文件、表和单元格位置。以 ISO 日期或带时区时间写入。path 数组逐项记录查询意图、实际搜索式或页面 URL、时间、结果；仅供续跑，禁止导入结果表。

## Apollo 与电话

验证前按小写完整邮箱读取 `local-data/email-cache.json`。只将归属可信、无历史结果的地址列入明细，按预算和优先级确认批次。按可用 Apollo 工具规则告知确切地址数与最大额度并等待授权。每次提交立即保存 request_id、record_id 与邮箱映射、请求时间。续跑先取回已提交任务。结果按 record_id 对齐，保留原 provider、状态和取回时间。没有 Apollo 或未授权时先交付公开证据，邮箱标为待验证。只有 API 返回明确结果时才写验证状态。validated 是可收信信号，not_validated 写未确认。电话只做可得公开来源核对和格式检查。

## 输出

运行 `audit_export.py` 对账并导出三张 CSV。检查报告列出未完成标识，给 Codex 在本地补查。全批任务只有待查数和保留记录缺项数都为零才能声称完成。审批待定邮箱可先交付，写明状态。用同一批 CSV 生成 Excel，列顺序保持一致，设置表头筛选、冻结首行、电话及原始标识列按文本，白灰等距斑马纹，无等级高亮。保留来源与验证页，不在交付中列搜索路径、评级理由或过程。
