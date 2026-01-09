"""AuZoom CLI commands."""

import sys
import click
from pathlib import Path


@click.group()
def main():
    """AuZoom - Multi-resolution code navigation for AI agents."""
    pass


@main.command()
@click.option('--scope', type=click.Choice(['file', 'directory', 'project']), default='project', help='Validation scope')
@click.argument('path', default='.', type=click.Path(exists=True))
def validate(scope, path):
    """Validate code structure compliance.

    Checks for:
    - Functions/methods ≤50 lines
    - Modules ≤250 lines
    - Directories ≤7 files
    """
    from .core.validator import CodeValidator

    validator = CodeValidator()
    path = str(Path(path).resolve())

    if scope == "file":
        violations = validator.validate_file(path)
    elif scope == "directory":
        violations = validator.validate_directory(path)
    else:  # project
        violations = validator.validate_project(path)

    report = validator.format_report(violations)
    click.echo(report)

    if any(v.severity == "error" for v in violations):
        sys.exit(1)


if __name__ == "__main__":
    main()
