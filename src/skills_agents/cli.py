"""
Skills Agents CLI

Command-line interface for skill validation and management.
"""

import argparse
import logging
import sys
from pathlib import Path

from .validator import validate_skill, validate_skills
from .models import ValidationSeverity


logger = logging.getLogger(__name__)


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


def print_validation_result(result, skill_name: str, show_info: bool = False) -> bool:
    """Print validation result and return True if valid."""
    if result.is_valid:
        print(f"✓ {skill_name}: valid")
    else:
        print(f"✗ {skill_name}: invalid")

    # Print errors
    for issue in result.errors:
        field_info = f" [{issue.field}]" if issue.field else ""
        print(f"  ERROR{field_info}: {issue.message}")

    # Print warnings
    for issue in result.warnings:
        field_info = f" [{issue.field}]" if issue.field else ""
        print(f"  WARNING{field_info}: {issue.message}")

    # Print info (only if requested)
    if show_info:
        info_issues = [
            i for i in result.issues if i.severity == ValidationSeverity.INFO
        ]
        for issue in info_issues:
            field_info = f" [{issue.field}]" if issue.field else ""
            print(f"  INFO{field_info}: {issue.message}")

    return result.is_valid


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate skills command."""
    path = Path(args.path)

    if not path.exists():
        print(f"Error: Path does not exist: {path}", file=sys.stderr)
        return 1

    # Determine if it's a single skill or a directory of skills
    if path.is_file():
        # Assume it's a SKILL.md file
        skill_path = path.parent
    elif (path / "SKILL.md").exists():
        # It's a single skill directory
        skill_path = path
    else:
        # It's a directory containing multiple skills
        skill_path = None

    if skill_path:
        # Validate single skill
        result = validate_skill(skill_path, strict=args.strict)
        skill_name = skill_path.name
        is_valid = print_validation_result(result, skill_name, show_info=args.verbose)
        return 0 if is_valid else 1
    else:
        # Validate multiple skills
        results = validate_skills(path, strict=args.strict)

        if not results:
            print(f"No skills found in {path}")
            return 0

        all_valid = True
        valid_count = 0
        invalid_count = 0

        for result in results:
            skill_name = result.skill_path.name if result.skill_path else "unknown"
            is_valid = print_validation_result(
                result, skill_name, show_info=args.verbose
            )
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                all_valid = False

        # Print summary
        print()
        print(f"Summary: {valid_count} valid, {invalid_count} invalid")

        return 0 if all_valid else 1


def cmd_list(args: argparse.Namespace) -> int:
    """List discovered skills command."""
    from .discovery import discover_skills

    path = Path(args.path)

    if not path.exists():
        print(f"Error: Path does not exist: {path}", file=sys.stderr)
        return 1

    skills = discover_skills(path)

    if not skills:
        print(f"No skills found in {path}")
        return 0

    print(f"Found {len(skills)} skill(s):\n")

    for skill in skills:
        print(f"  {skill.name}")
        print(f"    Description: {skill.description[:80]}...")
        if skill.license:
            print(f"    License: {skill.license}")
        if skill.compatibility:
            print(f"    Compatibility: {skill.compatibility}")
        print()

    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="skills",
        description="Skills Agents CLI - validate and manage Agent Skills",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Default skills directory (examples directory relative to this module)
    default_skills_dir = str(Path(__file__).parent)

    # validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate skill(s) according to Agent Skills specification",
    )
    validate_parser.add_argument(
        "path",
        nargs="?",
        default=default_skills_dir,
        help=f"Path to skill directory or directory containing skills (default: {default_skills_dir})",
    )
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    validate_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show info messages"
    )
    validate_parser.set_defaults(func=cmd_validate)

    # list command
    list_parser = subparsers.add_parser(
        "list",
        help="List discovered skills",
    )
    list_parser.add_argument(
        "path",
        nargs="?",
        default=default_skills_dir,
        help=f"Path to directory containing skills (default: {default_skills_dir})",
    )
    list_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed information"
    )
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()

    setup_logging(getattr(args, "verbose", False))

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
