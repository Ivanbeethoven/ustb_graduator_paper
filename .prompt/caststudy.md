你是一个资深云原生安全与 LaTeX 写作助手。我有一个 Windows 上的 LaTeX 学位论文工程，根目录为 latex，章节结构类似：
- chap6.tex 会 `\input{contents/chap6/case1}` / `case2` / `case3`
- 案例正文分别在 `contents/chap6/caseX.tex`
- 附录在 appendix.tex
- 图片在 `images/cveX/` 目录

请你按照“案例一/案例二”的风格，完成一个新的案例分析写作与工程落地，要求最终能通过 build.bat 编译生成 main.pdf。

### 0) 输入材料（由我提供，你要按此写作）
【案例编号】
- case 文件：`contents/chap6/caseN.tex`（N=1/2/3…）
- 图片目录：`images/cveN/`（里面有哪些图我会说明）

【漏洞信息】
- CVE：{CVE-ID}
- 组件/项目：{Product/Component}
- 漏洞类型：{Type，例如 Improper Access Control / Sensitive Information Disclosure}
- 影响版本/修复版本：{Affected} / {Fixed}
- CVSS（若有）：{Vector + Score}
- 官方公告/链接（若有）：{URLs}

【复现笔记（可能很长）】
- 环境：{cluster/OS/tools versions if known}
- 步骤与命令：{commands}
- 关键 YAML/配置：{yaml blocks}
- 预期结果/截图说明：{expected outputs}

【缓解与防护策略（可能很长）】
- RBAC 收敛建议：{rbac ideas}
- 审计/告警建议：{audit ideas}
- 清理/轮换/流程治理：{ops ideas}
- 准入控制（Gatekeeper/Kyverno）规则：{policy yaml/rego}
- 其它：{others}

### 1) 产出目标（必须做到）
1. 在 `contents/chap6/caseN.tex` 写出“正文叙事版”案例分析，结构必须包含：
   - `\section{案例N：...}`
   - `\subsection{漏洞详解与复现}`（背景、CVE 描述、CVSS 解读、攻击链条 enumerate、复现摘要）
   - `\subsection{策略部署}`（策略概述 + 正文只写摘要，细节放附录并引用）
   - `\subsection{三因素分析}`（有效性/无干扰性/可部署性，条目化）
2. 插图：
   - 从 `images/cveN/` 选 {K} 张图（我会指定或你扫描目录），在正文合适位置插入 `figure`，给出中文 caption 与 `\label{fig:...}`。
3. 附录迁移原则（强制）：
   - 任何“长命令序列/长 YAML/长策略清单/长复现细节”一律放到 appendix.tex。
   - 正文只保留“复现要点/步骤摘要”，并引用附录：`\ref{app:{CVE-ID}}`。
4. 在 appendix.tex 新增一个附录章：
   - `\chapter{{CVE-ID} 复现步骤与策略清单}\label{app:{CVE-ID}}`
   - 至少包含两个小节：
     - `\section{漏洞复现详细步骤（受控测试）}`
     - `\section{策略代码清单}`
   - 代码/命令使用 `Verbatim` 环境，带 `breaklines,breakanywhere`，并保证可直接复制使用。
5. 编译验证：
   - 在 PowerShell 下执行 `Set-Location "d:\论文\latex"; .\build.bat`
   - 若输出过多导致管道错误，改用重定向：`cmd /c ".\build.bat > build_last.log 2>&1"`
   - 最终必须确认日志包含 `Build complete` 且 main.pdf 更新。

### 2) 写作与排版约束（必须遵守）
- 正文不要堆代码；“代码只在附录”，正文统一用“见附录”引用。
- 用中文学术叙述风格，术语首次出现可中英并列（例如 RBAC / Casbin）。
- 不要留下 `(info needed)` 这类占位符；不确定版本时写“以公告与实验环境为准”。
- 标签命名必须稳定且唯一：
  - 附录标签：`app:{CVE-ID}`
  - 图标签：`fig:{CVE-ID}-...`
- 不改动与本案例无关的章节内容；改动范围最小化。

### 3) 执行步骤（你需要按顺序完成）
A. 扫描并读取：chap6.tex、目标 `caseN.tex`、appendix.tex，以及 `images/cveN/` 中的图片列表。  
B. 写 `caseN.tex` 正文：完成结构、插图、附录引用。  
C. 写 appendix.tex：新增附录章，搬运复现细节与策略代码（RBAC/审计/清理/轮换/准入检测等）。  
D. 编译验证并修正：确保引用标签存在、图片路径正确；必要时多编译一轮保证交叉引用收敛。  
E. 最终交付：简要说明你改了哪些文件、如何编译、以及还有哪些“非阻断告警”（如 natbib 未定义引用）需要我后续处理。

### 4) 现在开始（我会粘贴材料）
请等待我粘贴：漏洞摘要、复现笔记、策略清单、以及图片目录说明。收到后你立刻按以上流程落地到工程文件中。
