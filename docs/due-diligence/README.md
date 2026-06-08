# 技術盡調資料包

> 產出 for 投資人技術盡調 (Technical Due Diligence)

## 目錄結構

```
docs/due-diligence/
├── README.md                  ← 本文件
├── 01-system-architecture.md  # 系統架構圖 + 模組邊界 + 資料流 + 部署拓撲
├── 02-api-specification.md    # API 規格 (REST + 外部 + 內部)
├── 03-test-report.md          # 測試報告 (76 tests, 91% coverage)
├── 04-security-scan.md        # 安全掃描 (Bandit + pip-audit + Django check)
├── 05-deployment-architecture.md  # 部署架構 (Railway + 災備)
├── 06-monitoring-sla.md       # 監控指標與 SLA
├── 07-data-compliance.md      # 資料授權/合規聲明 (PDPA)
├── screenshots/               # 關鍵截圖 (12 張)
│   ├── 01-home-page.png
│   ├── 02-search-trace-code.png
│   ├── 03-search-crop-name.png
│   ├── 05-health-check.png
│   ├── 06-mobile-home.png
│   ├── 07-admin-login.png
│   ├── 08-search-result-expanded.png
│   ├── 09-empty-query-error.png
│   ├── 10-no-results.png
│   ├── 11-skeleton-loading.png
│   └── 12-product-cards.png
├── videos/                    # Demo 錄影
│   ├── 01-happy-path.mp4
│   ├── 02-anomaly-demo.mp4
│   └── 03-api-docs.mp4
├── coverage_html/             # pytest-cov HTML 報告
└── bandit_report.json         # Bandit 掃描原始結果
```

## 關鍵數據摘要

| 指標 | 數值 |
|---|---|
| 測試通過率 | **76/76 (100%)** |
| Code Coverage | **91%** |
| 安全漏洞 (dep.) | **0** (pip-audit) |
| 安全議題 (code) | **0** (Bandit production code) |
| 外部資料源 | **7** (TAFT + 4 MOA + FDA + Gemini) |
| REST API 端點 | **4** (index, search, health, admin) |
| 部署平台 | Railway (Nixpacks + Gunicorn + PostgreSQL) |
| 排程器 | APScheduler (每週日 02:00 UTC sync) |

## 供投資人簡報使用

- **系統架構圖**: [01-system-architecture.md](01-system-architecture.md) 含 Mermaid 圖
- **API 規格**: [02-api-specification.md](02-api-specification.md)
- **測試報告**: [03-test-report.md](03-test-report.md)
- **安全報告**: [04-security-scan.md](04-security-scan.md)
- **部署架構**: [05-deployment-architecture.md](05-deployment-architecture.md)
- **監控 SLA**: [06-monitoring-sla.md](06-monitoring-sla.md)
- **資料合規**: [07-data-compliance.md](07-data-compliance.md)
