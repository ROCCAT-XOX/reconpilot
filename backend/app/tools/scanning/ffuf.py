import json

from app.tools.base import BaseToolWrapper, ToolCategory, ToolResult, ToolStatus


class FfufWrapper(BaseToolWrapper):
    """Wrapper for ffuf web fuzzer."""

    @property
    def name(self) -> str:
        return "ffuf"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SCANNING

    def build_command(self, target: str, config: dict) -> list[str]:
        wordlist = config.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
        url = target if "FUZZ" in target else f"{target}/FUZZ"

        cmd = [
            "ffuf",
            "-u", url,
            "-w", wordlist,
            "-o", "/dev/stdout",
            "-of", "json",
            "-s",  # silent mode
        ]

        # Filter options
        if "mc" in config:
            cmd.extend(["-mc", config["mc"]])
        else:
            cmd.extend(["-mc", "200,204,301,302,307,401,403"])

        if "fc" in config:
            cmd.extend(["-fc", config["fc"]])

        if "fs" in config:
            cmd.extend(["-fs", str(config["fs"])])

        if "fw" in config:
            cmd.extend(["-fw", str(config["fw"])])

        # Performance
        threads = config.get("threads", 40)
        cmd.extend(["-t", str(threads)])

        rate = config.get("rate", 0)
        if rate > 0:
            cmd.extend(["-rate", str(rate)])

        # Extensions
        if "extensions" in config:
            cmd.extend(["-e", ",".join(config["extensions"])])

        # Recursion
        if config.get("recursive", False):
            cmd.extend(["-recursion", "-recursion-depth", str(config.get("recursion_depth", 2))])

        return cmd

    def parse_output(self, raw_output: str, target: str) -> ToolResult:
        result = ToolResult(
            tool_name=self.name,
            target=target,
            status=ToolStatus.COMPLETED,
            raw_output=raw_output,
        )

        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            if raw_output.strip():
                result.errors.append("Failed to parse ffuf JSON output")
            return result

        results = data.get("results", [])
        for entry in results:
            url = entry.get("url", "")
            status_code = entry.get("status", 0)
            length = entry.get("length", 0)
            words = entry.get("words", 0)
            lines = entry.get("lines", 0)
            input_val = entry.get("input", {}).get("FUZZ", "")
            redirect_location = entry.get("redirectlocation", "")

            severity = "info"
            if status_code == 200:
                severity = "low"
            if any(kw in input_val.lower() for kw in [
                "admin", "login", "dashboard", "config", "backup", ".env",
                "wp-admin", "phpmyadmin", ".git",
            ]):
                severity = "medium"

            title = f"Directory/file found: {input_val} [{status_code}]"
            description = (
                f"Found {url} (Status: {status_code}, "
                f"Size: {length} bytes, Words: {words}, Lines: {lines})"
            )
            if redirect_location:
                description += f" → Redirects to: {redirect_location}"

            result.findings.append({
                "title": title,
                "severity": severity,
                "target_host": target.split("//")[-1].split("/")[0] if "//" in target else target,
                "target_url": url,
                "description": description,
                "source_tool": "ffuf",
                "raw_evidence": {
                    "url": url,
                    "status": status_code,
                    "length": length,
                    "words": words,
                    "lines": lines,
                    "input": input_val,
                    "redirect": redirect_location,
                },
            })

        result.metadata = {
            "total_results": len(results),
            "target_url": target,
            "command_line": data.get("commandline", ""),
        }

        return result
