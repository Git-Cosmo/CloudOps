"""
Terraform Operations Utility

Handles all Terraform-specific operations including init, fmt, validate, plan, and apply.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, List
from .cli import run_command

logger = logging.getLogger(__name__)


class TerraformOperations:
    """Handles Terraform CLI operations"""

    def __init__(self, working_dir: Path):
        """
        Initialize Terraform operations.

        Args:
            working_dir: Directory containing Terraform configuration
        """
        self.working_dir = working_dir
        self.plan_file_path: Optional[Path] = None

    def init(self, backend_config: Optional[str] = None) -> None:
        """
        Run terraform init.

        Args:
            backend_config: Backend configuration as key=value pairs (one per line)
        """
        logger.info("Running terraform init...")

        cmd = ['terraform', 'init']

        # Add backend config if provided
        if backend_config:
            for line in backend_config.strip().split('\n'):
                line = line.strip()
                if line:
                    cmd.extend(['-backend-config', line])

        run_command(cmd, cwd=self.working_dir)
        logger.info("✓ Terraform initialized")

    def fmt(self, check: bool = True, auto_fix: bool = True) -> None:
        """
        Run terraform fmt.

        Args:
            check: Run in check mode
            auto_fix: Auto-fix formatting issues if check fails
        """
        logger.info("Running terraform fmt...")

        if check:
            result = run_command(
                ['terraform', 'fmt', '-check', '-recursive'],
                cwd=self.working_dir,
                check=False
            )

            if result.returncode != 0 and auto_fix:
                logger.warning("Terraform formatting issues detected, auto-fixing...")
                run_command(['terraform', 'fmt', '-recursive'], cwd=self.working_dir)
                logger.info("✓ Terraform formatted")
            elif result.returncode == 0:
                logger.info("✓ Terraform formatting check passed")
        else:
            run_command(['terraform', 'fmt', '-recursive'], cwd=self.working_dir)
            logger.info("✓ Terraform formatted")

    def validate(self) -> None:
        """Run terraform validate."""
        logger.info("Running terraform validate...")
        run_command(['terraform', 'validate'], cwd=self.working_dir)
        logger.info("✓ Terraform validation passed")

    def plan(self, tf_vars: Optional[str] = None,
             set_output_func: Optional[callable] = None) -> Tuple[bool, str]:
        """
        Run terraform plan.

        Args:
            tf_vars: Terraform variables as key=value pairs (one per line)
            set_output_func: Function to set GitHub Actions output

        Returns:
            Tuple of (has_changes, plan_output)
        """
        logger.info("Running terraform plan...")

        # Generate plan file
        self.plan_file_path = self.working_dir / 'tfplan'

        cmd = ['terraform', 'plan', '-out', str(self.plan_file_path), '-detailed-exitcode']

        # Add variables if provided
        if tf_vars:
            for line in tf_vars.strip().split('\n'):
                line = line.strip()
                if line and '=' in line:
                    cmd.extend(['-var', line])

        result = run_command(cmd, check=False, capture_output=True, cwd=self.working_dir)

        # Exit code 0 = no changes, 1 = error, 2 = changes present
        if result.returncode == 0:
            logger.info("✓ Terraform plan completed (no changes)")
            if set_output_func:
                set_output_func('plan_outcome', 'no-changes')
            return False, result.stdout
        elif result.returncode == 2:
            logger.info("✓ Terraform plan completed (changes detected)")
            if set_output_func:
                set_output_func('plan_outcome', 'changes')
            return True, result.stdout
        else:
            logger.error("✗ Terraform plan failed")
            if set_output_func:
                set_output_func('plan_outcome', 'failure')
            raise RuntimeError(f"Terraform plan failed: {result.stderr}")

    def apply(self, set_output_func: Optional[callable] = None) -> None:
        """
        Run terraform apply.

        Args:
            set_output_func: Function to set GitHub Actions output

        Raises:
            RuntimeError: If plan file not found or apply fails
        """
        logger.info("Running terraform apply...")

        if not self.plan_file_path or not self.plan_file_path.exists():
            raise RuntimeError("Plan file not found. Run terraform plan first.")

        # Apply the plan
        run_command(['terraform', 'apply', '-auto-approve', str(self.plan_file_path)],
                    cwd=self.working_dir)

        logger.info("✓ Terraform apply completed successfully")
        if set_output_func:
            set_output_func('apply_outcome', 'success')

    def get_plan_file_path(self) -> Optional[Path]:
        """
        Get the path to the generated plan file.

        Returns:
            Path to plan file or None
        """
        return self.plan_file_path
