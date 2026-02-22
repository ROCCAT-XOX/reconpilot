from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import asyncio
import subprocess
import logging
import time

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    RECON = "recon"
    DISCOVERY = "discovery"
    SCANNING = "scanning"
    EXPLOITATION = "exploitation"
    WEB_ANALYSIS = "web_analysis"
    INFRASTRUCTURE = "infrastructure"


class ToolStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ToolResult:
    """Unified result format for all tools."""
    tool_name: str
    target: str
    status: ToolStatus
    raw_output: str = ""
    raw_output_path: str | None = None
    findings: list[dict[str, Any]] = field(default_factory=list)
    hosts: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


class BaseToolWrapper(ABC):
    """
    Abstract base class for all tool wrappers.

    Each wrapper must implement:
    - name: Unique tool name
    - category: Tool category
    - build_command(): Build the CLI command
    - parse_output(): Parse tool output into ToolResult
    """

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        ...

    @abstractmethod
    def build_command(self, target: str, config: dict) -> list[str]:
        ...

    @abstractmethod
    def parse_output(self, raw_output: str, target: str) -> ToolResult:
        ...

    def is_available(self) -> bool:
        """Check if the tool is installed on the system."""
        try:
            subprocess.run(
                [self.name, "--version"],
                capture_output=True,
                timeout=10,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def run(
        self,
        target: str,
        config: dict | None = None,
        timeout: int = 3600,
        scope_targets: list[str] | None = None,
    ) -> ToolResult:
        """Execute the tool and return normalized results."""
        config = config or {}

        if scope_targets and not self._validate_scope(target, scope_targets):
            return ToolResult(
                tool_name=self.name,
                target=target,
                status=ToolStatus.FAILED,
                errors=[f"Target '{target}' is outside defined scope"],
            )

        command = self.build_command(target, config)
        logger.info(f"[{self.name}] Executing: {' '.join(command)}")

        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            duration = time.time() - start_time

            raw_output = stdout.decode("utf-8", errors="replace")
            result = self.parse_output(raw_output, target)
            result.duration_seconds = duration

            if process.returncode != 0 and stderr:
                result.errors.append(stderr.decode("utf-8", errors="replace"))

            return result

        except asyncio.TimeoutError:
            return ToolResult(
                tool_name=self.name,
                target=target,
                status=ToolStatus.TIMEOUT,
                errors=[f"Tool timed out after {timeout} seconds"],
                duration_seconds=timeout,
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                target=target,
                status=ToolStatus.FAILED,
                errors=[str(e)],
                duration_seconds=time.time() - start_time,
            )

    def _validate_scope(self, target: str, scope_targets: list[str]) -> bool:
        """Check if target is within the defined scope."""
        import ipaddress

        for scope in scope_targets:
            if target == scope:
                return True
            if target.endswith(f".{scope}"):
                return True
            try:
                network = ipaddress.ip_network(scope, strict=False)
                ip = ipaddress.ip_address(target)
                if ip in network:
                    return True
            except ValueError:
                continue
        return False
