"""
GitHub Integration Utility

Handles GitHub Actions-specific operations like PR comments and step summaries.
"""

import os
import re
import logging
import tempfile
from pathlib import Path
from typing import Optional
from .cli import run_command

logger = logging.getLogger(__name__)


class GitHubIntegration:
    """Handles GitHub Actions integration features"""

    def __init__(self, github_token: str, github_repository: str,
                 github_event_name: str, github_ref: str):
        """
        Initialize GitHub integration.

        Args:
            github_token: GitHub authentication token
            github_repository: Repository in owner/repo format
            github_event_name: GitHub event that triggered the workflow
            github_ref: GitHub ref that triggered the workflow
        """
        self.github_token = github_token
        self.github_repository = github_repository
        self.github_event_name = github_event_name
        self.github_ref = github_ref

    def set_output(self, name: str, value: str) -> None:
        """
        Set GitHub Actions output.

        Args:
            name: Output name
            value: Output value
        """
        if github_output := os.getenv('GITHUB_OUTPUT'):
            with open(github_output, 'a') as f:
                f.write(f"{name}={value}\n")
        logger.debug(f"Output set: {name}={value}")

    def add_step_summary(self, summary: str) -> None:
        """
        Add content to GitHub Actions step summary.

        Args:
            summary: Markdown-formatted summary content
        """
        if github_step_summary := os.getenv('GITHUB_STEP_SUMMARY'):
            with open(github_step_summary, 'a') as f:
                f.write(f"{summary}\n")

    def post_pr_comment(self, plan_output: str, working_dir: Path,
                        workspace: Path, enabled: bool = True) -> None:
        """
        Post plan summary as PR comment.

        Args:
            plan_output: Terraform plan output
            working_dir: Terraform working directory
            workspace: GitHub workspace directory
            enabled: Whether PR comments are enabled
        """
        if not enabled:
            logger.info("PR comments disabled, skipping")
            return

        if self.github_event_name != 'pull_request':
            logger.info("Not a pull request event, skipping PR comment")
            return

        if not self.github_token:
            logger.warning("GITHUB_TOKEN not available, skipping PR comment")
            return

        logger.info("Posting plan summary to PR...")

        # Extract PR number from GITHUB_REF
        pr_number = self._extract_pr_number()

        if not pr_number:
            logger.warning("Could not determine PR number, skipping comment")
            return

        # Create comment body
        comment = self._format_plan_comment(plan_output, working_dir, workspace)

        # Post comment using gh CLI
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(comment)
            comment_file = f.name

        try:
            run_command([
                'gh', 'pr', 'comment', pr_number,
                '--body-file', comment_file,
                '--repo', self.github_repository
            ], cwd=workspace)
            logger.info("✓ PR comment posted successfully")
        finally:
            Path(comment_file).unlink()

    def _extract_pr_number(self) -> Optional[str]:
        """
        Extract PR number from GITHUB_REF.

        Returns:
            PR number as string or None
        """
        if match := re.search(r'refs/pull/(\d+)/merge', self.github_ref):
            return match.group(1)
        return None

    def _format_plan_comment(self, plan_output: str, working_dir: Path,
                             workspace: Path) -> str:
        """
        Format plan output for PR comment.

        Args:
            plan_output: Terraform plan output
            working_dir: Terraform working directory
            workspace: GitHub workspace directory

        Returns:
            Formatted markdown comment
        """
        # Truncate if too long
        max_length = 65000  # GitHub comment limit
        if len(plan_output) > max_length:
            plan_output = plan_output[:max_length] + "\n\n... (output truncated)"

        # Extract change summary from plan output
        change_summary = self._extract_change_summary(plan_output)

        relative_dir = working_dir.relative_to(workspace) if workspace in working_dir.parents else working_dir

        comment = f"""## 🏗️ Terraform Plan Summary

{change_summary}

<details>
<summary>📋 View Full Plan</summary>

```terraform
{plan_output}
```

</details>

---
*Powered by CloudOps Terraform Action*
*Working Directory: `{relative_dir}`*
"""
        return comment

    def _extract_change_summary(self, plan_output: str) -> str:
        """
        Extract change summary from Terraform plan output.

        Args:
            plan_output: Terraform plan output

        Returns:
            Markdown-formatted change summary
        """
        # Look for the plan summary line
        lines = plan_output.split('\n')
        for line in lines:
            if 'Plan:' in line:
                return f"**{line.strip()}**"
            elif 'No changes' in line and 'infrastructure' in line.lower():
                return "**No changes detected** - Your infrastructure matches the configuration."

        return "**Changes detected** - Review the full plan below."

    def create_success_summary(self, working_dir: Path, workspace: Path,
                               cloud_provider: str, operation: str,
                               has_changes: bool) -> None:
        """
        Create a success step summary.

        Args:
            working_dir: Terraform working directory
            workspace: GitHub workspace directory
            cloud_provider: Cloud provider used
            operation: Terraform operation performed
            has_changes: Whether changes were detected
        """
        relative_dir = working_dir.relative_to(workspace) if workspace in working_dir.parents else working_dir

        summary = f"""## ✅ CloudOps Pipeline Success

- **Working Directory**: `{relative_dir}`
- **Cloud Provider**: `{cloud_provider}`
- **Operation**: `{operation}`
- **Changes Detected**: `{has_changes}`
"""
        self.add_step_summary(summary)

    def create_failure_summary(self, error: str) -> None:
        """
        Create a failure step summary.

        Args:
            error: Error message
        """
        summary = f"""## ❌ CloudOps Pipeline Failed

**Error**: {error}

See logs for details.
"""
        self.add_step_summary(summary)
