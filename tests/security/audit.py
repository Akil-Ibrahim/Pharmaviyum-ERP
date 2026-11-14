"""
=============================================================================
PharmaViyum CRM - Security Audit Script
=============================================================================
This script performs automated security checks on the PharmaViyum codebase.

Checks performed:
    - Hardcoded secrets detection
    - SQL injection vulnerabilities
    - Insecure dependencies
    - CORS misconfigurations
    - Missing security headers
    - Debug mode in production

Usage:
    python tests/security/audit.py

    # With JSON output
    python tests/security/audit.py --output json > audit_report.json

    # With HTML output
    python tests/security/audit.py --output html > audit_report.html
=============================================================================
"""

import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List


@dataclass
class SecurityIssue:
    """Represents a security issue found during audit"""

    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str
    file: str
    line: int
    description: str
    recommendation: str
    code_snippet: str = ""


class SecurityAuditor:
    """Performs security audit on the codebase"""

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.issues: List[SecurityIssue] = []

        # Patterns to detect
        self.secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
            (r'secret_key\s*=\s*["\'][^"\']+["\']', "Hardcoded secret key"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token"),
            (r"BEGIN (RSA |EC |DSA )?PRIVATE KEY", "Private key in code"),
        ]

        self.sql_patterns = [
            (r'execute\s*\(\s*f["\']', "Potential SQL injection (f-string)"),
            (
                r'execute\s*\(\s*["\'].*%s',
                "Potential SQL injection (string formatting)",
            ),
            (
                r'execute\s*\(\s*["\'].*\.format',
                "Potential SQL injection (format method)",
            ),
        ]

        self.cors_patterns = [
            (r'allow_origins\s*=\s*\["\*"\]', "Wildcard CORS origin"),
            (r"allow_origins\s*=\s*\*", "Wildcard CORS origin"),
        ]

        self.debug_patterns = [
            (r"debug\s*=\s*True", "Debug mode enabled"),
            (r"DEBUG\s*=\s*True", "Debug mode enabled"),
        ]

    def audit(self) -> List[SecurityIssue]:
        """Run all security checks"""
        print("🔒 Starting Security Audit...")
        print(f"Root directory: {self.root_dir.absolute()}")
        print()

        # Scan Python files
        self._scan_python_files()

        # Scan configuration files
        self._scan_config_files()

        # Check dependencies
        self._check_dependencies()

        # Check Docker configuration
        self._check_docker_config()

        # Check environment files
        self._check_env_files()
        print()
        print(f"✅ Audit complete. Found {len(self.issues)} issues.")

        return self.issues

    def _scan_python_files(self):
        """Scan Python files for security issues"""
        print("📄 Scanning Python files...")

        python_files = list(self.root_dir.rglob("*.py"))

        # Exclude common directories
        exclude_dirs = {".venv", "venv", "node_modules", "__pycache__", ".git"}
        python_files = [
            f for f in python_files if not any(excl in f.parts for excl in exclude_dirs)
        ]

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                    for line_num, line in enumerate(lines, 1):
                        # Check for secrets
                        for pattern, description in self.secret_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                self.issues.append(
                                    SecurityIssue(
                                        severity="CRITICAL",
                                        category="Hardcoded Secret",
                                        file=str(file_path.relative_to(self.root_dir)),
                                        line=line_num,
                                        description=description,
                                        recommendation="Use environment variables or secret management tools",
                                        code_snippet=line.strip(),
                                    )
                                )

                        # Check for SQL injection
                        for pattern, description in self.sql_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                self.issues.append(
                                    SecurityIssue(
                                        severity="HIGH",
                                        category="SQL Injection",
                                        file=str(file_path.relative_to(self.root_dir)),
                                        line=line_num,
                                        description=description,
                                        recommendation="Use parameterized queries or ORM",
                                        code_snippet=line.strip(),
                                    )
                                )
                        # Check for CORS issues
                        for pattern, description in self.cors_patterns:
                            if re.search(pattern, line):
                                self.issues.append(
                                    SecurityIssue(
                                        severity="MEDIUM",
                                        category="CORS Misconfiguration",
                                        file=str(file_path.relative_to(self.root_dir)),
                                        line=line_num,
                                        description=description,
                                        recommendation="Specify explicit allowed origins",
                                        code_snippet=line.strip(),
                                    )
                                )

                        # Check for debug mode
                        for pattern, description in self.debug_patterns:
                            if re.search(pattern, line):
                                self.issues.append(
                                    SecurityIssue(
                                        severity="MEDIUM",
                                        category="Debug Mode",
                                        file=str(file_path.relative_to(self.root_dir)),
                                        line=line_num,
                                        description=description,
                                        recommendation="Disable debug mode in production",
                                        code_snippet=line.strip(),
                                    )
                                )
            except Exception as e:
                print(f"  ⚠️  Error scanning {file_path}: {e}")

    def _scan_config_files(self):
        """Scan configuration files"""
        print("⚙️  Scanning configuration files...")

        config_files = [
            "docker-compose.yml",
            "docker-compose.prod.yml",
            "Dockerfile",
            ".env",
            ".env.example",
        ]

        for config_file in config_files:
            file_path = self.root_dir / config_file
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                        # Check for default passwords
                        if re.search(
                            r'password\s*[:=]\s*["\']?(postgres|admin|password|123456)',
                            content,
                            re.IGNORECASE,
                        ):
                            self.issues.append(
                                SecurityIssue(
                                    severity="HIGH",
                                    category="Weak Password",
                                    file=config_file,
                                    line=0,
                                    description="Default or weak password detected",
                                    recommendation="Use strong, unique passwords",
                                )
                            )
                except Exception as e:
                    print(f"  ⚠️  Error scanning {config_file}: {e}")

    def _check_dependencies(self):
        """Check for known vulnerable dependencies"""
        print("📦 Checking dependencies...")

        pyproject_file = self.root_dir / "pyproject.toml"
        if pyproject_file.exists():
            try:
                import tomllib

                with open(pyproject_file, "rb") as f:
                    project_config = tomllib.load(f)

                dependencies = project_config.get("project", {}).get("dependencies", [])
                for line_num, dependency in enumerate(dependencies, 1):
                    # Treat exact pins and explicit lower bounds as constrained.
                    if "==" not in dependency and ">=" not in dependency:
                        self.issues.append(
                            SecurityIssue(
                                severity="LOW",
                                category="Dependency Management",
                                file="pyproject.toml",
                                line=line_num,
                                description=f"Dependency lacks an explicit version constraint: {dependency}",
                                recommendation="Add a compatible version constraint and refresh uv.lock",
                            )
                        )
            except Exception as e:
                print(f"  ⚠️  Error checking pyproject.toml dependencies: {e}")

    def _check_docker_config(self):
        """Check Docker configuration for security issues"""
        print("🐳 Checking Docker configuration...")

        dockerfile = self.root_dir / "Dockerfile"
        if dockerfile.exists():
            try:
                with open(dockerfile, "r", encoding="utf-8") as f:
                    content = f.read()

                    # Check for root user
                    if "USER root" in content and "USER appuser" not in content:
                        self.issues.append(
                            SecurityIssue(
                                severity="HIGH",
                                category="Docker Security",
                                file="Dockerfile",
                                line=0,
                                description="Container running as root user",
                                recommendation="Create and use non-root user",
                            )
                        )

                    # Check for latest tag
                    if "FROM python:latest" in content or "FROM python:3" in content:
                        self.issues.append(
                            SecurityIssue(
                                severity="LOW",
                                category="Docker Security",
                                file="Dockerfile",
                                line=0,
                                description="Using 'latest' or unpinned base image",
                                recommendation="Pin base image to specific version",
                            )
                        )
            except Exception as e:
                print(f"  ⚠️  Error checking Dockerfile: {e}")

    def _check_env_files(self):
        """Check .env files for security issues"""
        print("🔐 Checking environment files...")

        env_file = self.root_dir / ".env"
        if env_file.exists():
            self.issues.append(
                SecurityIssue(
                    severity="INFO",
                    category="Environment File",
                    file=".env",
                    line=0,
                    description=".env file exists in repository",
                    recommendation="Ensure .env is in .gitignore and not committed",
                )
            )

    def generate_report(self, output_format: str = "text") -> str:
        """Generate audit report"""
        if output_format == "json":
            return json.dumps(
                {
                    "timestamp": datetime.now().isoformat(),
                    "total_issues": len(self.issues),
                    "issues": [asdict(issue) for issue in self.issues],
                },
                indent=2,
            )

        elif output_format == "html":
            html = ["<html><head><title>Security Audit Report</title></head><body>"]
            html.append("<h1>Security Audit Report</h1>")
            html.append(f"<p>Generated: {datetime.now().isoformat()}</p>")
            html.append(f"<p>Total Issues: {len(self.issues)}</p>")
            html.append("<table border='1'>")
            html.append(
                "<tr><th>Severity</th><th>Category</th><th>File</th><th>Line</th><th>Description</th></tr>"
            )
            for issue in self.issues:
                html.append("<tr>")
                html.append(f"<td>{issue.severity}</td>")
                html.append(f"<td>{issue.category}</td>")
                html.append(f"<td>{issue.file}</td>")
                html.append(f"<td>{issue.line}</td>")
                html.append(f"<td>{issue.description}</td>")
                html.append("</tr>")

            html.append("</table></body></html>")
            return "\n".join(html)

        else:  # text
            lines = []
            lines.append("=" * 80)
            lines.append("SECURITY AUDIT REPORT")
            lines.append("=" * 80)
            lines.append(f"Generated: {datetime.now().isoformat()}")
            lines.append(f"Total Issues: {len(self.issues)}")
            lines.append("")

            # Group by severity
            by_severity = {}
            for issue in self.issues:
                by_severity.setdefault(issue.severity, []).append(issue)

            for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
                if severity in by_severity:
                    lines.append(f"\n{severity} ISSUES ({len(by_severity[severity])})")
                    lines.append("-" * 80)

                    for issue in by_severity[severity]:
                        lines.append(f"\n[{severity}] {issue.category}")
                        lines.append(f"File: {issue.file}:{issue.line}")
                        lines.append(f"Description: {issue.description}")
                        lines.append(f"Recommendation: {issue.recommendation}")
                        if issue.code_snippet:
                            lines.append(f"Code: {issue.code_snippet}")

            return "\n".join(lines)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Security Audit for PharmaViyum CRM")
    parser.add_argument(
        "--output",
        choices=["text", "json", "html"],
        default="text",
        help="Output format",
    )
    parser.add_argument("--root", default=".", help="Root directory to scan")

    args = parser.parse_args()

    auditor = SecurityAuditor(args.root)
    auditor.audit()

    report = auditor.generate_report(args.output)
    print(report)

    # Exit with error code if critical issues found
    critical_count = sum(1 for issue in auditor.issues if issue.severity == "CRITICAL")
    if critical_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
