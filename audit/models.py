"""
Data models for audit test results and reports.

Uses Pydantic v2 for validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TestStatus(str, Enum):
    """Test result status codes."""

    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    SKIP = "SKIP"


class EvidenceType(str, Enum):
    """Types of evidence that can be collected."""

    FILE = "file"
    API = "api"
    MEASUREMENT = "measurement"
    ERROR = "error"


class TestResult(BaseModel):
    """Result of a single audit test execution."""

    name: str = Field(description="Test name")
    status: TestStatus = Field(description="Test outcome")
    duration_ms: float = Field(description="Execution time in milliseconds")
    evidence_refs: list[str] = Field(
        default_factory=list, description="Paths to evidence files"
    )
    error_msg: Optional[str] = Field(
        default=None, description="Error message if test failed"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Test execution time"
    )


class AuditReport(BaseModel):
    """Summary report for audit phase execution."""

    phase: str = Field(description="Phase identifier (e.g., '02-auzoom-core')")
    tests_run: int = Field(description="Total tests executed")
    passed: int = Field(description="Tests that passed")
    failed: int = Field(description="Tests that failed")
    partial: int = Field(description="Tests with partial success")
    skipped: int = Field(default=0, description="Tests that were skipped")
    evidence_dir: str = Field(description="Path to evidence directory")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Report generation time"
    )
    results: list[TestResult] = Field(
        default_factory=list, description="Individual test results"
    )
