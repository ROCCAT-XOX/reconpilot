import hashlib


def compute_finding_fingerprint(
    target_host: str,
    target_port: int | None,
    target_url: str | None,
    cve_id: str | None,
    cwe_id: str | None,
    title: str,
) -> str:
    """
    Generate a SHA-256 fingerprint for deduplication.
    Findings with the same fingerprint are considered duplicates.
    """
    components = [
        target_host or "",
        str(target_port or ""),
        target_url or "",
        cve_id or "",
        cwe_id or "",
        title.lower().strip(),
    ]
    raw = "|".join(components)
    return hashlib.sha256(raw.encode()).hexdigest()
