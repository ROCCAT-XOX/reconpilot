import csv
import io
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path("/tmp/reconforge/reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class ReportGenerator:
    """Generate reports in various formats from findings data."""

    def __init__(self):
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=True,
        )

    def _prepare_context(self, project: dict, findings: list[dict], config: dict | None = None) -> dict:
        """Build template context from project and findings data."""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        tool_counts: dict[str, int] = {}

        for f in findings:
            sev = f.get("severity", "info")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            tool = f.get("source_tool", "unknown")
            tool_counts[tool] = tool_counts.get(tool, 0) + 1

        # Sort findings by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.get("severity", "info"), 5))

        # Top findings (critical + high)
        top_findings = [f for f in sorted_findings if f.get("severity") in ("critical", "high")][:10]

        return {
            "project": project,
            "findings": sorted_findings,
            "top_findings": top_findings,
            "total_findings": len(findings),
            "severity_counts": severity_counts,
            "tool_counts": tool_counts,
            "tools_used": list(tool_counts.keys()),
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "config": config or {},
        }

    async def generate_html(self, project: dict, findings: list[dict], config: dict | None = None) -> Path:
        """Generate an HTML report."""
        template_name = (config or {}).get("template", "executive_summary.html")
        template = self.jinja_env.get_template(template_name)
        context = self._prepare_context(project, findings, config)
        html_content = template.render(**context)

        output_path = OUTPUT_DIR / f"{project['id']}_{template_name.replace('.html', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        output_path.write_text(html_content, encoding="utf-8")
        logger.info(f"HTML report generated: {output_path}")
        return output_path

    async def generate_pdf(self, project: dict, findings: list[dict], config: dict | None = None) -> Path:
        """Generate a PDF report using WeasyPrint."""
        # First generate HTML
        html_path = await self.generate_html(project, findings, config)
        pdf_path = html_path.with_suffix(".pdf")

        try:
            from weasyprint import HTML
            HTML(filename=str(html_path)).write_pdf(str(pdf_path))
            logger.info(f"PDF report generated: {pdf_path}")
        except ImportError:
            logger.warning("WeasyPrint not installed, returning HTML instead")
            return html_path
        except Exception as e:
            logger.error(f"PDF generation failed: {e}, returning HTML")
            return html_path

        return pdf_path

    async def generate_json(self, project: dict, findings: list[dict], config: dict | None = None) -> Path:
        """Generate a JSON export of findings."""
        context = self._prepare_context(project, findings, config)
        export_data = {
            "project": project,
            "generated_at": context["generated_at"],
            "summary": {
                "total": context["total_findings"],
                "by_severity": context["severity_counts"],
                "by_tool": context["tool_counts"],
            },
            "findings": findings,
        }

        output_path = OUTPUT_DIR / f"{project['id']}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path.write_text(json.dumps(export_data, indent=2, default=str), encoding="utf-8")
        logger.info(f"JSON export generated: {output_path}")
        return output_path

    async def generate_csv(self, project: dict, findings: list[dict], config: dict | None = None) -> Path:
        """Generate a CSV export of findings."""
        output_path = OUTPUT_DIR / f"{project['id']}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        fieldnames = [
            "title", "severity", "status", "target_host", "target_port",
            "target_url", "source_tool", "cve_id", "cwe_id", "cvss_score",
            "description",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for f in findings:
                writer.writerow({k: f.get(k, "") for k in fieldnames})

        logger.info(f"CSV export generated: {output_path}")
        return output_path
