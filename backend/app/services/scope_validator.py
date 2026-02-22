import ipaddress
from dataclasses import dataclass


@dataclass
class ScopeValidationResult:
    is_valid: bool
    reason: str = ""


class ScopeValidator:
    """
    Validates whether a scan target falls within the authorized scope.
    Checked BEFORE every tool invocation.
    """

    def __init__(
        self,
        allowed_targets: list[dict],
        excluded_targets: list[dict] | None = None,
    ):
        self.allowed = allowed_targets
        self.excluded = excluded_targets or []

    def validate(self, target: str) -> ScopeValidationResult:
        """Check if a target is within scope."""
        # Check exclusions first
        for excl in self.excluded:
            if self._matches(target, excl):
                return ScopeValidationResult(
                    is_valid=False,
                    reason=f"Target '{target}' is explicitly excluded from scope",
                )

        # Check allowed
        for allowed in self.allowed:
            if self._matches(target, allowed):
                return ScopeValidationResult(is_valid=True)

        return ScopeValidationResult(
            is_valid=False,
            reason=f"Target '{target}' is not in the authorized scope",
        )

    def validate_multiple(self, targets: list[str]) -> dict[str, ScopeValidationResult]:
        """Validate multiple targets at once."""
        return {target: self.validate(target) for target in targets}

    def get_allowed_values(self) -> list[str]:
        """Return list of allowed target values for tool scope checking."""
        return [t["value"] for t in self.allowed if not self._is_excluded(t["value"])]

    def _is_excluded(self, value: str) -> bool:
        """Check if a value is explicitly excluded."""
        return any(excl["value"] == value for excl in self.excluded)

    def _matches(self, target: str, scope_entry: dict) -> bool:
        """Check if a target matches a scope entry."""
        scope_type = scope_entry.get("type", "")
        scope_value = scope_entry.get("value", "")

        if scope_type == "domain":
            # Exact match or subdomain match
            return target == scope_value or target.endswith(f".{scope_value}")

        elif scope_type == "ip":
            return target == scope_value

        elif scope_type == "ip_range":
            try:
                network = ipaddress.ip_network(scope_value, strict=False)
                ip = ipaddress.ip_address(target)
                return ip in network
            except ValueError:
                return False

        elif scope_type == "url":
            return target == scope_value or target.startswith(scope_value)

        return False


def build_scope_validator(scope_targets: list) -> ScopeValidator:
    """Build a ScopeValidator from a list of ScopeTarget ORM objects."""
    allowed = []
    excluded = []
    for st in scope_targets:
        entry = {"type": st.target_type, "value": st.target_value}
        if st.is_excluded:
            excluded.append(entry)
        else:
            allowed.append(entry)
    return ScopeValidator(allowed_targets=allowed, excluded_targets=excluded)
