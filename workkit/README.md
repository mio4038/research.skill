# 建材询盘背调工作包

用 Codex 整理玻璃马赛克、瓷砖、装饰板材（含 WPC/PVC）的海外询盘。保留所有能确认企业主体的线索，按 A–D 标记跟进优先级，并交付 Excel 与 CSV。

[打开下载页](https://mio4038.github.io/research.skill/) · [下载工作包](https://mio4038.github.io/research.skill/workkit.zip)

## 快速开始

1. 解压 ZIP。在 Codex 桌面版打开最里面的 `workkit` 文件夹，也就是包含 `.agents` 的那一层。克隆仓库的使用者可以直接打开仓库中的 `workkit/`。
2. 在新对话附上 XLSX 或 UTF-8 CSV 询盘表。建议包含公司名、国家、公司类型、联系人、邮箱、电话和需求。已有背调表可以一起提供。
3. 发送下面这条指令。初次使用可以把“整表”替换成“前十条”，先看交付格式。
4. 如需验证新增邮箱，在个人 Codex 环境连接获授权的 Apollo 账号，核对新增地址数量和最高费用后确认。已有可复用结果的地址会跳过。

> 使用 $building-lead-review 处理附件整表。先读已有证据和验证缓存，只补查缺项。按原表顺序逐家处理，核对官网和公开地址。完成时输出白灰 A–D 评级的 Excel 和 CSV。新增邮箱先给出验证清单和最高额度。

找不到 Skill 时，检查 `.agents/skills/building-lead-review/SKILL.md` 是否在打开的文件夹下面，并重新打开该文件夹或重启 Codex。具备联网搜索能力的 Codex 才能核查公开网页。脚本需要 Python 3.10 或更新版本，读取 XLSX 额外需要 openpyxl。可先用包内的 `examples/inquiries.csv` 试跑，无需 Apollo。

## 查询和交付

- 先剔除个人自用及确认的个人商家，并去重。使用名称、国家、原电话或域名补查主体。无法归属且没有可用线索的条目进入处理记录。能确认的企业继续查询，主营差异仅影响评级。
- 逐项核对主体、官网、主营、地址、常用社交平台、公开邮箱及电话、中国贸易证据。总机、注册地址、门店和邮寄地址按来源标注。公开未检出或未确认的字段用简短状态标示。
- **A** 有明确的相关采购、项目或进口证据。**B** 产品或渠道直接相关。**C** 主营较远但有相关需求线索。**D** 企业可核实，暂缺相关需求证据。
- Excel 和 CSV 包含客户名单、来源与验证、处理记录。客户名单采用白灰样式，显示结果和等级。来源页保存 URL、来源类型、获取时间及验证状态。查询路径保存在本地，用于续跑。

## 从另一台电脑续跑

复制原始输入表以及整个 `local-data/`，包括批次目录、`research.json`、`email-cache.json` 和已提交的 Apollo 请求记录。把它们放入新电脑解压后的工作包，再按原工作表和表头设置运行。登录和工具权限在接收方环境单独配置。公司内部资料只通过内部渠道搬迁，公开仓库和下载包使用虚构样例。

## 工作包内容

- `.agents/skills/building-lead-review/SKILL.md` 定义执行顺序。
- `references/research.md` 说明各字段搜索路径。 `references/records.md` 说明证据、验证与导出结构。
- `scripts/queue.py` 导入表格、预筛、去重。 `scripts/audit_export.py` 对账、提示未查字段并生成 CSV。
- `examples/` 提供虚构输入和一条结构化记录示例。

发布版从 GitHub Pages 的 `main` 分支根目录提供下载。更新工作包时，同步更新可下载的 `workkit.zip` 和版本号。部署设置见 [PAGES.md](https://github.com/mio4038/research.skill/blob/main/PAGES.md)。
