"""
Report Generator for Enterprise Ingestion, Data Quality, and Multi-Source Reconciliation.
"""
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import json
from config.settings import REPORTS_DIR


class ReportGenerator:
    """Generates Markdown and HTML audit reports."""

    def __init__(self, reports_dir: Path = REPORTS_DIR):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_data_quality_report(self, profile: Dict[str, Any], validation_summary: Dict[str, Any], quality_metrics: Dict[str, Any]) -> str:
        """Create Comprehensive Data Quality Audit Report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_md_path = self.reports_dir / "DATA_QUALITY_AUDIT.md"
        report_html_path = self.reports_dir / "DATA_QUALITY_AUDIT.html"

        md = []
        md.append("# Enterprise Data Quality Audit Report")
        md.append(f"**Generated**: {timestamp} | **Dataset**: {profile.get('source_name', 'Source_A')}\n")

        md.append("## 1. Executive Quality Scorecard")
        md.append("| Quality Dimension | Metric Score | Benchmark Target | Status |")
        md.append("| --- | --- | --- | --- |")
        md.append(f"| **Composite Quality Index** | **{quality_metrics['composite_quality_score']}% (Grade: {quality_metrics['quality_grade']})** | > 90.0% | {'✅ PASSED' if quality_metrics['composite_quality_score'] >= 90 else '⚠️ ATTENTION'} |")
        md.append(f"| **Validity Rate** | {quality_metrics['validity_score']}% | > 98.0% | {'✅ PASSED' if quality_metrics['validity_score'] >= 98 else '⚠️ ATTENTION'} |")
        md.append(f"| **Completeness Rate** | {quality_metrics['completeness_score']}% | > 95.0% | {'✅ PASSED' if quality_metrics['completeness_score'] >= 95 else '⚠️ ATTENTION'} |")
        md.append(f"| **Uniqueness Rate** | {quality_metrics['uniqueness_score']}% | 100.0% | {'✅ PASSED' if quality_metrics['uniqueness_score'] == 100 else '⚠️ ATTENTION'} |\n")

        md.append("## 2. Ingestion & Validation Summary")
        md.append(f"- **Total Input Records**: {validation_summary['total_evaluated']:,}")
        md.append(f"- **Clean Records Accepted**: {validation_summary['passed_validation_count']:,} ({validation_summary['pass_rate_pct']}%)")
        md.append(f"- **Quarantined Records**: {validation_summary['quarantined_count']:,}")
        md.append(f"- **Income Handling Policy**: `{validation_summary['income_policy_applied']}`\n")

        md.append("### Rule Violation Breakdown")
        md.append("| Rule Code | Description | Violations Detected |")
        md.append("| --- | --- | --- |")
        for code, count in validation_summary.get("violation_counts", {}).items():
            md.append(f"| `{code}` | Automated business rule validation | {count} |")

        md.append("\n## 3. Detected Structural Anomalies")
        anomalies = profile.get("anomalies", [])
        if anomalies:
            md.append("| Column | Issue Flagged | Count | Details |")
            md.append("| --- | --- | --- | --- |")
            for a in anomalies:
                md.append(f"| `{a['column']}` | {a['issue']} | {a['count']} | `{a['examples']}` |")
        else:
            md.append("No structural anomalies detected.\n")

        md_content = "\n".join(md)
        with open(report_md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Generate standalone HTML version
        html_content = self._render_simple_html("Data Quality Audit Report", md_content)
        with open(report_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(report_md_path)

    def generate_reconciliation_report(self, recon_stats: Dict[str, Any]) -> str:
        """Create Multi-Source Entity Resolution & Reconciliation Report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_md_path = self.reports_dir / "RECONCILIATION_REPORT.md"
        report_html_path = self.reports_dir / "RECONCILIATION_REPORT.html"

        summary = recon_stats.get("reconciliation_summary", {})

        md = []
        md.append("# Enterprise Multi-Source Reconciliation Report")
        md.append(f"**Generated**: {timestamp} | **Reconciliation Scope**: Source A (Demographics) + Source B (CRM) + Source C (Sales)\n")

        md.append("## 1. Cross-Source Entity Coverage")
        md.append("| Source Metric | Count | Coverage % |")
        md.append("| --- | --- | --- |")
        md.append(f"| **Total Unified Customers (Golden Master)** | **{recon_stats['total_golden_records_created']:,}** | 100.0% |")
        md.append(f"| **Source A Demographics Records** | {summary.get('source_a_count', 0):,} | - |")
        md.append(f"| **Source B CRM Records** | {summary.get('source_b_count', 0):,} | - |")
        md.append(f"| **Matched Source A & Source B (Full Enrichment)** | {summary.get('matched_a_and_b_count', 0):,} | {recon_stats.get('crm_enrichment_rate_pct', 0)}% of Source A |")
        md.append(f"| **Customers with Transaction History (Source C)** | {summary.get('customers_with_transactions_count', 0):,} | {recon_stats.get('transaction_coverage_pct', 0)}% of Master |")
        md.append(f"| **Customers Only in CRM (Unmatched to Source A)** | {summary.get('only_in_source_b_count', 0):,} | - |")
        md.append(f"| **Total Conflicts & Variances Audited** | {recon_stats.get('total_conflicts_logged', 0):,} | Recorded in DB audit log |\n")

        md.append("## 2. Reconciliation Principles Applied")
        md.append("- **Entity Matching**: Joined on validated customer identifier (`customer_id`).")
        md.append("- **Contact Information**: Source B (CRM) established as primary authoritative source for email, phone, and name.")
        md.append("- **Demographic Truth**: Source A established as primary authoritative source for birth year, education, income, and family composition.")
        md.append("- **Financial Cross-Check**: Source C transaction sums compared against historical total spend from Source A, flagging significant delta variances.\n")

        md_content = "\n".join(md)
        with open(report_md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        html_content = self._render_simple_html("Multi-Source Reconciliation Report", md_content)
        with open(report_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(report_md_path)

    def _render_simple_html(self, title: str, markdown_text: str) -> str:
        """Convert markdown lines into a clean styled standalone HTML report."""
        lines = markdown_text.split("\n")
        body_elements = []
        in_table = False

        for line in lines:
            line_str = line.strip()
            if not line_str:
                if in_table:
                    body_elements.append("</tbody></table>")
                    in_table = False
                continue

            if line_str.startswith("# "):
                body_elements.append(f"<h1 style='color: #1a365d; border-bottom: 2px solid #2b6cb0; padding-bottom: 8px;'>{line_str[2:]}</h1>")
            elif line_str.startswith("## "):
                body_elements.append(f"<h2 style='color: #2c5282; margin-top: 24px;'>{line_str[3:]}</h2>")
            elif line_str.startswith("### "):
                body_elements.append(f"<h3 style='color: #2b6cb0; margin-top: 18px;'>{line_str[4:]}</h3>")
            elif line_str.startswith("|"):
                parts = [p.strip() for p in line_str.split("|")[1:-1]]
                if all(set(p).issubset({"-", " ", ":"}) for p in parts):
                    continue  # Separator row
                if not in_table:
                    in_table = True
                    headers = "".join(f"<th style='background-color: #ebf8ff; padding: 10px; border: 1px solid #cbd5e0; text-align: left;'>{p}</th>" for p in parts)
                    body_elements.append(f"<table style='width: 100%; border-collapse: collapse; margin: 16px 0;'><thead><tr>{headers}</tr></thead><tbody>")
                else:
                    cells = "".join(f"<td style='padding: 8px 10px; border: 1px solid #e2e8f0;'>{p}</td>" for p in parts)
                    body_elements.append(f"<tr>{cells}</tr>")
            elif line_str.startswith("- "):
                body_elements.append(f"<li style='margin-left: 20px; line-height: 1.6;'>{line_str[2:]}</li>")
            else:
                body_elements.append(f"<p style='line-height: 1.6; color: #4a5568;'>{line_str}</p>")

        if in_table:
            body_elements.append("</tbody></table>")

        body_html = "\n".join(body_elements)
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f7fafc; color: #2d3748; padding: 40px; margin: 0; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 36px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        code {{ background: #edf2f7; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        {body_html}
    </div>
</body>
</html>"""

