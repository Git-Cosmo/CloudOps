#!/usr/bin/env python3
"""
CloudOps - Unified Terraform IaC Toolchain
Main entrypoint for the GitHub Action (Refactored)

This module provides the main orchestration logic using modular utilities.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple

# Import utility modules
from utils import (
    TerraformOperations,
    CloudAuth,
    GitHubIntegration,
    ToolInstaller
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class CloudOpsAction:
    """Main action orchestrator for CloudOps Terraform pipeline"""

    def __init__(self):
        """Initialize the action with environment variables"""
        self.github_workspace = os.getenv('GITHUB_WORKSPACE', os.getcwd())
        self.github_action_path = os.getenv('GITHUB_ACTION_PATH',
                                              os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Read inputs from environment
        self.tf_path = os.getenv('INPUT_TF_PATH', '').strip()
        self.tf_working_dir = os.getenv('INPUT_TF_WORKING_DIR', '').strip()
        self.cloud_provider = os.getenv('INPUT_CLOUD_PROVIDER', 'azure').strip().lower()
        self.tf_version = os.getenv('INPUT_TF_VERSION', 'latest').strip()
        self.gh_cli_version = os.getenv('INPUT_GH_CLI_VERSION', 'latest').strip()
        self.terraform_operation = os.getenv('INPUT_TERRAFORM_OPERATION', 'plan').strip().lower()

        # Cloud credentials
        self.azure_credentials = os.getenv('INPUT_AZURE_CREDENTIALS', '').strip()
        self.aws_access_key_id = os.getenv('INPUT_AWS_ACCESS_KEY_ID', '').strip()
        self.aws_secret_access_key = os.getenv('INPUT_AWS_SECRET_ACCESS_KEY', '').strip()
        self.aws_region = os.getenv('INPUT_AWS_REGION', 'us-east-1').strip()

        # Terraform configuration
        self.backend_config = os.getenv('INPUT_BACKEND_CONFIG', '').strip()
        self.tf_vars = os.getenv('INPUT_TF_VARS', '').strip()

        # Features
        self.enable_pr_comment = os.getenv('INPUT_ENABLE_PR_COMMENT', 'true').strip().lower() == 'true'
        self.enable_artifact_upload = os.getenv('INPUT_ENABLE_ARTIFACT_UPLOAD', 'true').strip().lower() == 'true'

        # GitHub context
        github_token = os.getenv('GITHUB_TOKEN', '').strip()
        github_repository = os.getenv('GITHUB_REPOSITORY', '').strip()
        github_event_name = os.getenv('GITHUB_EVENT_NAME', '').strip()
        github_ref = os.getenv('GITHUB_REF', '').strip()

        # Initialize GitHub integration
        self.github = GitHubIntegration(
            github_token,
            github_repository,
            github_event_name,
            github_ref
        )

        # Resolved values
        self.resolved_working_dir: Optional[Path] = None
        self.terraform: Optional[TerraformOperations] = None

    def validate_inputs(self) -> None:
        """Validate required inputs"""
        logger.info("Validating inputs...")

        if not self.tf_path:
            raise ValueError("tf_path is required")

        if self.cloud_provider not in ['azure', 'aws', 'multi']:
            raise ValueError(f"Invalid cloud_provider: {self.cloud_provider}. Must be: azure, aws, or multi")

        if self.terraform_operation not in ['plan', 'apply', 'plan-apply']:
            raise ValueError(f"Invalid terraform_operation: {self.terraform_operation}. "
                             "Must be: plan, apply, or plan-apply")

        logger.info("✓ Inputs validated successfully")
        logger.info(f"  - tf_path: {self.tf_path}")
        logger.info(f"  - cloud_provider: {self.cloud_provider}")
        logger.info(f"  - terraform_operation: {self.terraform_operation}")

    def resolve_working_directory(self) -> Path:
        """Resolve the Terraform working directory from tf_path"""
        logger.info("Resolving Terraform working directory...")

        # If tf_working_dir is explicitly provided, use it
        if self.tf_working_dir:
            working_dir = Path(self.github_workspace) / self.tf_working_dir
            logger.info(f"Using explicit tf_working_dir: {working_dir}")
        else:
            # Resolve from tf_path
            tf_path_full = Path(self.github_workspace) / self.tf_path

            if tf_path_full.is_dir():
                working_dir = tf_path_full
                logger.info(f"tf_path is directory: {working_dir}")
            elif tf_path_full.is_file():
                working_dir = tf_path_full.parent
                logger.info(f"tf_path is file, using parent directory: {working_dir}")
            else:
                raise ValueError(f"tf_path does not exist: {tf_path_full}")

        if not working_dir.exists():
            raise ValueError(f"Resolved working directory does not exist: {working_dir}")

        self.resolved_working_dir = working_dir
        self.github.set_output('tf_working_dir', str(working_dir.relative_to(self.github_workspace)))
        logger.info(f"✓ Working directory resolved: {working_dir}")

        return working_dir

    def install_toolchain(self) -> None:
        """Install required CLI tools"""
        logger.info("\n--- Installing Toolchain ---")

        # Install Terraform
        ToolInstaller.install_terraform(self.tf_version)

        # Install cloud provider CLIs
        if self.cloud_provider in ['azure', 'multi']:
            ToolInstaller.install_azure_cli()

        if self.cloud_provider in ['aws', 'multi']:
            ToolInstaller.install_aws_cli()

        # Install GitHub CLI
        ToolInstaller.install_github_cli(self.gh_cli_version)

    def configure_cloud_providers(self) -> None:
        """Configure cloud provider authentication"""
        logger.info("\n--- Configuring Cloud Providers ---")

        if self.cloud_provider in ['azure', 'multi']:
            CloudAuth.configure_azure(self.azure_credentials)

        if self.cloud_provider in ['aws', 'multi']:
            CloudAuth.configure_aws(
                self.aws_access_key_id,
                self.aws_secret_access_key,
                self.aws_region
            )

    def run_terraform_workflow(self) -> Tuple[bool, str]:
        """
        Run the Terraform workflow.

        Returns:
            Tuple of (has_changes, plan_output)
        """
        logger.info("\n--- Terraform Workflow ---")

        # Initialize Terraform operations
        self.terraform = TerraformOperations(self.resolved_working_dir)

        # Run Terraform commands
        self.terraform.init(self.backend_config)
        self.terraform.fmt(check=True, auto_fix=True)
        self.terraform.validate()

        # Plan
        has_changes, plan_output = self.terraform.plan(
            self.tf_vars,
            self.github.set_output
        )

        # Upload artifact
        if self.enable_artifact_upload:
            plan_file = self.terraform.get_plan_file_path()
            if plan_file:
                self.github.set_output('plan_artifact_path', str(plan_file))
                logger.info(f"✓ Plan artifact ready at: {plan_file}")

        # Post PR comment
        if has_changes:
            self.github.post_pr_comment(
                plan_output,
                self.resolved_working_dir,
                Path(self.github_workspace),
                self.enable_pr_comment
            )

        return has_changes, plan_output

    def apply_changes(self, has_changes: bool) -> None:
        """
        Apply Terraform changes if requested.

        Args:
            has_changes: Whether changes were detected in plan
        """
        if self.terraform_operation in ['apply', 'plan-apply'] and has_changes:
            logger.info("\n--- Applying Changes ---")
            self.terraform.apply(self.github.set_output)
        else:
            logger.info("Skipping apply (no changes or not requested)")
            self.github.set_output('apply_outcome', 'skipped')

    def format_plan_comment(self, plan_output: str) -> str:
        """
        Format plan output for PR comment (compatibility wrapper for tests).

        Args:
            plan_output: Terraform plan output

        Returns:
            Formatted markdown comment
        """
        return self.github._format_plan_comment(
            plan_output,
            self.resolved_working_dir,
            Path(self.github_workspace)
        )

    def set_output(self, name: str, value: str) -> None:
        """
        Set GitHub Actions output (compatibility wrapper for tests).

        Args:
            name: Output name
            value: Output value
        """
        self.github.set_output(name, value)

    def run(self) -> int:
        """Main execution flow"""
        try:
            logger.info("=" * 60)
            logger.info("CloudOps - Unified Terraform IaC Toolchain")
            logger.info("=" * 60)

            # Phase 1: Validate inputs
            self.validate_inputs()
            self.resolve_working_directory()

            # Phase 2: Install toolchain
            self.install_toolchain()

            # Phase 3: Configure cloud providers
            self.configure_cloud_providers()

            # Phase 4: Terraform workflow
            has_changes, plan_output = self.run_terraform_workflow()

            # Phase 5: Apply (if requested)
            self.apply_changes(has_changes)

            # Phase 6: Cleanup credentials
            CloudAuth.cleanup_credentials()

            # Summary
            logger.info("\n" + "=" * 60)
            logger.info("✓ CloudOps pipeline completed successfully")
            logger.info("=" * 60)

            self.github.create_success_summary(
                self.resolved_working_dir,
                Path(self.github_workspace),
                self.cloud_provider,
                self.terraform_operation,
                has_changes
            )

            return 0

        except Exception as e:
            logger.error(f"\n✗ Pipeline failed: {e}", exc_info=True)
            self.github.create_failure_summary(str(e))

            # Cleanup credentials even on failure
            try:
                CloudAuth.cleanup_credentials()
            except Exception:
                pass

            return 1


def main():
    """Entry point"""
    action = CloudOpsAction()
    sys.exit(action.run())


if __name__ == '__main__':
    main()
