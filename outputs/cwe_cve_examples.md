# CWE 名称解释与 CVE 示例（自动抽取）

说明：从 `分类漏洞.csv` 的 CWE 标签与 `raw_results.csv` 的摘要字段抽取。

## CWE-863 — Incorrect Authorization

| CVE | 组件/软件 | 成因(一级/二级) | 摘要(截断) |
|---|---|---|---|
| CVE-2019-11247 | Kubernetes | 安全逻辑缺陷/2.1 访问控制缺陷 | The Kubernetes kube-apiserver mistakenly allows access to a cluster-scoped custom resource if the request is made as if the resource were namespaced. Authorizat… |
| CVE-2021-43858 | MinIO | 安全逻辑缺陷/2.3 授权验证不完善 | MinIO is a Kubernetes native application for cloud storage. Prior to version `RELEASE.202  2021-12-27T07-23-18Z`, a malicious client can hand-craft an HTTP API … |

## CWE-269 — Improper Access Control (Generic)

| CVE | 组件/软件 | 成因(一级/二级) | 摘要(截断) |
|---|---|---|---|
| CVE-2021-43858 | MinIO | 安全逻辑缺陷/2.3 授权验证不完善 | MinIO is a Kubernetes native application for cloud storage. Prior to version `RELEASE.202  2021-12-27T07-23-18Z`, a malicious client can hand-craft an HTTP API … |
| CVE-2022-29179 | Cilium | 配置错误/1.1 权限配置过宽 | Cilium is open source software for providing and securing network connectivity and loadbalancing between application workloads. Prior to versions 1.9.16, 1.10.1… |

## CWE-200 — Exposure of Sensitive Information to an Unauthorized Actor

| CVE | 组件/软件 | 成因(一级/二级) | 摘要(截断) |
|---|---|---|---|
| CVE-2018-5256 | CoreOS Tectonic | 配置错误/1.3 默认不安全配置 | CoreOS Tectonic 1.7.x before 1.7.9-tectonic.4 and 1.8.x before 1.8.4-tectonic.3 mounts a direct proxy to the kubernetes cluster at /api/kubernetes/ which is acc… |
| CVE-2019-3869 | Tower | 敏感信息泄露/3.3 配置暴露敏感信息 | When running Tower before 3.4.3 on OpenShift or Kubernetes, application credentials are exposed to playbook job runs via environment variables. A malicious user… |

## CWE-20 — Improper Input Validation

| CVE | 组件/软件 | 成因(一级/二级) | 摘要(截断) |
|---|---|---|---|
| CVE-2019-11247 | Kubernetes | 安全逻辑缺陷/2.1 访问控制缺陷 | The Kubernetes kube-apiserver mistakenly allows access to a cluster-scoped custom resource if the request is made as if the resource were namespaced. Authorizat… |
| CVE-2023-3676 | Kubernetes Windows | 安全逻辑缺陷/2.3 授权验证不完善 | A security issue was discovered in Kubernetes where a user that can create pods on Windows nodes may be able to escalate to admin privileges on those nodes. Kub… |

## CWE-22 — Improper Limitation of a Pathname to a Restricted Directory

| CVE | 组件/软件 | 成因(一级/二级) | 摘要(截断) |
|---|---|---|---|
| CVE-2022-24730 | Argo CD | 代码注入/4.2 路径遍历 | Argo CD is a declarative, GitOps continuous delivery tool for Kubernetes. Argo CD starting with version 1.3.0 but before versions 2.1.11, 2.2.6, and 2.3.0 is vu… |
| CVE-2022-24877 | Flux | 代码注入/4.2 路径遍历 | Flux is an open and extensible continuous delivery solution for Kubernetes. Path Traversal in the kustomize-controller via a malicious `kustomization.yaml` allo… |

## CWE-287 — Improper Authentication

| CVE | 组件/软件 | 成因(一级/二级) | 摘要(截断) |
|---|---|---|---|
| CVE-2022-23652 | capsule-proxy | 安全逻辑缺陷/2.4 输入验证不足 | capsule-proxy is a reverse proxy for Capsule Operator which provides multi-tenancy in Kubernetes. In versions prior to 0.2.1 an attacker with a proper authentic… |
| CVE-2022-29165 | Argo CD | 安全逻辑缺陷/2.2 身份验证绕过 | Argo CD is a declarative, GitOps continuous delivery tool for Kubernetes. A critical vulnerability has been discovered in Argo CD starting with version 1.4.0 an… |

