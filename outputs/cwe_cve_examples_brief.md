# 关键 CWE 与 CVE 示例（精简版）

说明：选取 4 个与权限提升分析最相关且高频的 CWE，并为每个 CWE 给出 1 个样本内代表性 CVE。

## CWE-863 — Incorrect Authorization（授权不当）

- CVE：CVE-2019-11247
- 组件/软件：Kubernetes
- 成因映射：安全逻辑缺陷/2.1 访问控制缺陷
- 摘要：The Kubernetes kube-apiserver mistakenly allows access to a cluster-scoped custom resource if the request is made as if the resource were namespaced. Authorizations for the resource accessed in this manner are enforced using roles and role …

## CWE-269 — Improper Access Control (Generic)（权限/访问控制管理不当）

- CVE：CVE-2022-29179
- 组件/软件：Cilium
- 成因映射：配置错误/1.1 权限配置过宽
- 摘要：Cilium is open source software for providing and securing network connectivity and loadbalancing between application workloads. Prior to versions 1.9.16, 1.10.11, and 1.11.15, if an attacker is able to perform a container escape of a contai…

## CWE-22 — Improper Limitation of a Pathname to a Restricted Directory（路径遍历）

- CVE：CVE-2022-24730
- 组件/软件：Argo CD
- 成因映射：代码注入/4.2 路径遍历
- 摘要：Argo CD is a declarative, GitOps continuous delivery tool for Kubernetes. Argo CD starting with version 1.3.0 but before versions 2.1.11, 2.2.6, and 2.3.0 is vulnerable to a path traversal bug, compounded by an improper access control bug, …

## CWE-287 — Improper Authentication（认证不当）

- CVE：CVE-2022-29165
- 组件/软件：Argo CD
- 成因映射：安全逻辑缺陷/2.2 身份验证绕过
- 摘要：Argo CD is a declarative, GitOps continuous delivery tool for Kubernetes. A critical vulnerability has been discovered in Argo CD starting with version 1.4.0 and prior to versions 2.1.15, 2.2.9, and 2.3.4 which would allow unauthenticated u…

