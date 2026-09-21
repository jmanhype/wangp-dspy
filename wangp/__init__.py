"""Stable operator command-line surface for Wangp."""

__version__ = "0.1.0"
PROJECT_NAME = "wangp-dspy"
CONTENT_PLAN_SCHEMA = "wangp-dspy.content-plan/v1"
CLI_VERBS = ("brief", "doctor", "plan", "review", "status")
DOCTOR_PREFLIGHT_KINDS = (
    "ssh_reachable", "model_files", "disk_headroom", "gpu_state", "qc_available",
)
EXIT_CODES = {"success": 0, "input": 2, "doctor_failed": 3, "internal": 4}

__all__ = [
    "CLI_VERBS", "CONTENT_PLAN_SCHEMA", "DOCTOR_PREFLIGHT_KINDS", "EXIT_CODES",
    "PROJECT_NAME", "__version__",
]
