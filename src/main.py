#!/usr/bin/env python3
"""
CloudOps - Unified Terraform IaC Toolchain
Main entrypoint for the GitHub Action
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple

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
        self.github_action_path = os.getenv('GITHUB_ACTION_PATH', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
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
        self.github_token = os.getenv('GITHUB_TOKEN', '').strip()
        self.github_repository = os.getenv('GITHUB_REPOSITORY', '').strip()
        self.github_event_name = os.getenv('GITHUB_EVENT_NAME', '').strip()
        self.github_ref = os.getenv('GITHUB_REF', '').strip()
        
        # Resolved values
        self.resolved_working_dir: Optional[Path] = None
        self.plan_file_path: Optional[Path] = None
        
    def validate_inputs(self) -> None:
        """Validate required inputs"""
        logger.info("Validating inputs...")
        
        if not self.tf_path:
            raise ValueError("tf_path is required")
        
        if self.cloud_provider not in ['azure', 'aws', 'multi']:
            raise ValueError(f"Invalid cloud_provider: {self.cloud_provider}. Must be: azure, aws, or multi")
        
        if self.terraform_operation not in ['plan', 'apply', 'plan-apply']:
            raise ValueError(f"Invalid terraform_operation: {self.terraform_operation}. Must be: plan, apply, or plan-apply")
        
        logger.info(f"✓ Inputs validated successfully")
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
        self.set_output('tf_working_dir', str(working_dir.relative_to(self.github_workspace)))
        logger.info(f"✓ Working directory resolved: {working_dir}")
        
        return working_dir
    
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None, 
                   capture_output: bool = False, check: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command with logging"""
        cwd = cwd or self.resolved_working_dir
        cmd_str = ' '.join(cmd)
        logger.info(f"Running: {cmd_str}")
        logger.info(f"  in directory: {cwd}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                check=check
            )
            if capture_output and result.stdout:
                logger.debug(f"Output: {result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with exit code {e.returncode}")
            if e.stdout:
                logger.error(f"stdout: {e.stdout}")
            if e.stderr:
                logger.error(f"stderr: {e.stderr}")
            raise
    
    def install_terraform(self) -> None:
        """Install Terraform CLI"""
        logger.info(f"Installing Terraform (version: {self.tf_version})...")
        
        # Check if terraform is already installed
        try:
            result = subprocess.run(['terraform', 'version'], 
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                logger.info(f"Terraform already installed: {result.stdout.split()[1]}")
                if self.tf_version == 'latest':
                    logger.info("Skipping installation (latest already available)")
                    return
        except FileNotFoundError:
            pass
        
        # Determine version to install
        if self.tf_version == 'latest':
            version = self.get_latest_terraform_version()
        else:
            version = self.tf_version
        
        logger.info(f"Installing Terraform version: {version}")
        
        # Download and install
        import platform
        system = platform.system().lower()
        arch = 'amd64' if platform.machine() in ['x86_64', 'AMD64'] else 'arm64'
        
        download_url = f"https://releases.hashicorp.com/terraform/{version}/terraform_{version}_{system}_{arch}.zip"
        
        install_dir = Path.home() / '.local' / 'bin'
        install_dir.mkdir(parents=True, exist_ok=True)
        
        import urllib.request
        import zipfile
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / 'terraform.zip'
            logger.info(f"Downloading from: {download_url}")
            urllib.request.urlretrieve(download_url, zip_path)
            
            logger.info(f"Extracting to: {install_dir}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(install_dir)
        
        # Make executable
        terraform_bin = install_dir / 'terraform'
        terraform_bin.chmod(0o755)
        
        # Add to PATH
        current_path = os.environ.get('PATH', '')
        if str(install_dir) not in current_path:
            os.environ['PATH'] = f"{install_dir}:{current_path}"
            # Also set for GitHub Actions
            if github_path := os.getenv('GITHUB_PATH'):
                with open(github_path, 'a') as f:
                    f.write(f"{install_dir}\n")
        
        # Verify installation
        result = subprocess.run(['terraform', 'version'], capture_output=True, text=True)
        logger.info(f"✓ Terraform installed: {result.stdout.strip()}")
    
    def get_latest_terraform_version(self) -> str:
        """Get the latest Terraform version from HashiCorp releases"""
        logger.info("Fetching latest Terraform version...")
        try:
            import urllib.request
            import json
            
            url = "https://api.github.com/repos/hashicorp/terraform/releases/latest"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                version = data['tag_name'].lstrip('v')
                logger.info(f"Latest version: {version}")
                return version
        except Exception as e:
            logger.warning(f"Failed to fetch latest version: {e}. Using fallback version.")
            return "1.6.6"
    
    def install_azure_cli(self) -> None:
        """Install Azure CLI"""
        logger.info("Installing Azure CLI...")
        
        # Check if az is already installed
        try:
            result = subprocess.run(['az', 'version'], 
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                logger.info("Azure CLI already installed")
                return
        except FileNotFoundError:
            pass
        
        # Install using curl method (works on Ubuntu)
        logger.info("Installing Azure CLI via apt...")
        commands = [
            ['sudo', 'apt-get', 'update'],
            ['sudo', 'apt-get', 'install', '-y', 'ca-certificates', 'curl', 'apt-transport-https', 'lsb-release', 'gnupg'],
            ['bash', '-c', 'curl -sL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null'],
            ['bash', '-c', 'AZ_REPO=$(lsb_release -cs) && echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $AZ_REPO main" | sudo tee /etc/apt/sources.list.d/azure-cli.list'],
            ['sudo', 'apt-get', 'update'],
            ['sudo', 'apt-get', 'install', '-y', 'azure-cli']
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                logger.warning(f"Command failed: {' '.join(cmd)}")
                # Try alternative installation method
                break
        
        # Verify installation
        try:
            result = subprocess.run(['az', 'version'], capture_output=True, text=True, check=True)
            logger.info(f"✓ Azure CLI installed")
        except:
            logger.warning("Azure CLI installation could not be verified")
    
    def install_aws_cli(self) -> None:
        """Install AWS CLI"""
        logger.info("Installing AWS CLI...")
        
        # Check if aws is already installed
        try:
            result = subprocess.run(['aws', '--version'], 
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                logger.info("AWS CLI already installed")
                return
        except FileNotFoundError:
            pass
        
        logger.info("Installing AWS CLI v2...")
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Download AWS CLI installer
            import urllib.request
            installer_zip = tmpdir / "awscliv2.zip"
            logger.info("Downloading AWS CLI installer...")
            urllib.request.urlretrieve(
                "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip",
                installer_zip
            )
            
            # Extract
            import zipfile
            logger.info("Extracting AWS CLI...")
            with zipfile.ZipFile(installer_zip, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            
            # Install
            logger.info("Installing AWS CLI...")
            subprocess.run([str(tmpdir / 'aws' / 'install')], check=True)
        
        # Verify
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        logger.info(f"✓ AWS CLI installed: {result.stdout.strip()}")
    
    def install_github_cli(self) -> None:
        """Install GitHub CLI"""
        logger.info(f"Installing GitHub CLI (version: {self.gh_cli_version})...")
        
        # Check if gh is already installed
        try:
            result = subprocess.run(['gh', '--version'], 
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                logger.info(f"GitHub CLI already installed")
                if self.gh_cli_version == 'latest':
                    return
        except FileNotFoundError:
            pass
        
        # Install using apt
        logger.info("Installing GitHub CLI via apt...")
        commands = [
            ['sudo', 'apt-get', 'update'],
            ['sudo', 'apt-get', 'install', '-y', 'gh']
        ]
        
        for cmd in commands:
            subprocess.run(cmd, check=True, capture_output=True)
        
        # Verify
        result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
        logger.info(f"✓ GitHub CLI installed: {result.stdout.split()[2]}")
    
    def configure_azure_credentials(self) -> None:
        """Configure Azure authentication"""
        if not self.azure_credentials:
            logger.info("No Azure credentials provided, skipping Azure configuration")
            return
        
        logger.info("Configuring Azure credentials...")
        
        try:
            creds = json.loads(self.azure_credentials)
            
            # Login using service principal
            self.run_command([
                'az', 'login',
                '--service-principal',
                '--username', creds.get('clientId', ''),
                '--password', creds.get('clientSecret', ''),
                '--tenant', creds.get('tenantId', '')
            ])
            
            # Set subscription
            if subscription_id := creds.get('subscriptionId'):
                self.run_command(['az', 'account', 'set', '--subscription', subscription_id])
            
            # Export environment variables for Terraform
            os.environ['ARM_CLIENT_ID'] = creds.get('clientId', '')
            os.environ['ARM_CLIENT_SECRET'] = creds.get('clientSecret', '')
            os.environ['ARM_TENANT_ID'] = creds.get('tenantId', '')
            os.environ['ARM_SUBSCRIPTION_ID'] = creds.get('subscriptionId', '')
            
            logger.info("✓ Azure credentials configured")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Azure credentials JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to configure Azure credentials: {e}")
            raise
    
    def configure_aws_credentials(self) -> None:
        """Configure AWS authentication"""
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            logger.info("No AWS credentials provided, skipping AWS configuration")
            return
        
        logger.info("Configuring AWS credentials...")
        
        # Export environment variables for Terraform
        os.environ['AWS_ACCESS_KEY_ID'] = self.aws_access_key_id
        os.environ['AWS_SECRET_ACCESS_KEY'] = self.aws_secret_access_key
        os.environ['AWS_DEFAULT_REGION'] = self.aws_region
        
        # Also configure AWS CLI
        aws_dir = Path.home() / '.aws'
        aws_dir.mkdir(exist_ok=True)
        
        credentials_file = aws_dir / 'credentials'
        with open(credentials_file, 'w') as f:
            f.write('[default]\n')
            f.write(f'aws_access_key_id = {self.aws_access_key_id}\n')
            f.write(f'aws_secret_access_key = {self.aws_secret_access_key}\n')
        
        config_file = aws_dir / 'config'
        with open(config_file, 'w') as f:
            f.write('[default]\n')
            f.write(f'region = {self.aws_region}\n')
        
        logger.info("✓ AWS credentials configured")
    
    def terraform_init(self) -> None:
        """Run terraform init"""
        logger.info("Running terraform init...")
        
        cmd = ['terraform', 'init']
        
        # Add backend config if provided
        if self.backend_config:
            for line in self.backend_config.strip().split('\n'):
                line = line.strip()
                if line:
                    cmd.extend(['-backend-config', line])
        
        self.run_command(cmd)
        logger.info("✓ Terraform initialized")
    
    def terraform_fmt(self) -> None:
        """Run terraform fmt"""
        logger.info("Running terraform fmt...")
        
        result = self.run_command(
            ['terraform', 'fmt', '-check', '-recursive'],
            check=False
        )
        
        if result.returncode != 0:
            logger.warning("Terraform formatting issues detected, auto-fixing...")
            self.run_command(['terraform', 'fmt', '-recursive'])
            logger.info("✓ Terraform formatted")
        else:
            logger.info("✓ Terraform formatting check passed")
    
    def terraform_validate(self) -> None:
        """Run terraform validate"""
        logger.info("Running terraform validate...")
        
        self.run_command(['terraform', 'validate'])
        logger.info("✓ Terraform validation passed")
    
    def terraform_plan(self) -> Tuple[bool, str]:
        """Run terraform plan and return (has_changes, plan_output)"""
        logger.info("Running terraform plan...")
        
        # Generate plan file
        self.plan_file_path = self.resolved_working_dir / 'tfplan'
        
        cmd = ['terraform', 'plan', '-out', str(self.plan_file_path), '-detailed-exitcode']
        
        # Add variables if provided
        if self.tf_vars:
            for line in self.tf_vars.strip().split('\n'):
                line = line.strip()
                if line and '=' in line:
                    cmd.extend(['-var', line])
        
        result = self.run_command(cmd, check=False, capture_output=True)
        
        # Exit code 0 = no changes, 1 = error, 2 = changes present
        if result.returncode == 0:
            logger.info("✓ Terraform plan completed (no changes)")
            self.set_output('plan_outcome', 'no-changes')
            return False, result.stdout
        elif result.returncode == 2:
            logger.info("✓ Terraform plan completed (changes detected)")
            self.set_output('plan_outcome', 'changes')
            return True, result.stdout
        else:
            logger.error("✗ Terraform plan failed")
            self.set_output('plan_outcome', 'failure')
            raise RuntimeError(f"Terraform plan failed: {result.stderr}")
    
    def terraform_apply(self) -> None:
        """Run terraform apply"""
        logger.info("Running terraform apply...")
        
        if not self.plan_file_path or not self.plan_file_path.exists():
            raise RuntimeError("Plan file not found. Run terraform plan first.")
        
        # Apply the plan
        self.run_command(['terraform', 'apply', '-auto-approve', str(self.plan_file_path)])
        
        logger.info("✓ Terraform apply completed successfully")
        self.set_output('apply_outcome', 'success')
    
    def upload_plan_artifact(self) -> None:
        """Upload plan file as GitHub artifact"""
        if not self.enable_artifact_upload:
            logger.info("Artifact upload disabled, skipping")
            return
        
        if not self.plan_file_path or not self.plan_file_path.exists():
            logger.warning("Plan file not found, skipping artifact upload")
            return
        
        logger.info("Uploading plan artifact...")
        
        # Set output for artifact path
        self.set_output('plan_artifact_path', str(self.plan_file_path))
        
        # Note: Actual artifact upload is handled by GitHub Actions upload-artifact action
        # We just log the path here
        logger.info(f"✓ Plan artifact ready at: {self.plan_file_path}")
    
    def post_pr_comment(self, plan_output: str) -> None:
        """Post plan summary as PR comment"""
        if not self.enable_pr_comment:
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
        import re
        pr_number = None
        if match := re.search(r'refs/pull/(\d+)/merge', self.github_ref):
            pr_number = match.group(1)
        
        if not pr_number:
            logger.warning("Could not determine PR number, skipping comment")
            return
        
        # Create comment body
        comment = self.format_plan_comment(plan_output)
        
        # Post comment using gh CLI
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(comment)
            comment_file = f.name
        
        try:
            self.run_command([
                'gh', 'pr', 'comment', pr_number,
                '--body-file', comment_file,
                '--repo', self.github_repository
            ], cwd=Path(self.github_workspace))
            logger.info("✓ PR comment posted successfully")
        finally:
            Path(comment_file).unlink()
    
    def format_plan_comment(self, plan_output: str) -> str:
        """Format plan output for PR comment"""
        # Truncate if too long
        max_length = 65000  # GitHub comment limit
        if len(plan_output) > max_length:
            plan_output = plan_output[:max_length] + "\n\n... (output truncated)"
        
        comment = f"""## 🏗️ Terraform Plan Summary

<details>
<summary>📋 View Full Plan</summary>

```terraform
{plan_output}
```

</details>

---
*Powered by CloudOps Terraform Action*
*Working Directory: `{self.resolved_working_dir.relative_to(self.github_workspace)}`*
"""
        return comment
    
    def set_output(self, name: str, value: str) -> None:
        """Set GitHub Actions output"""
        if github_output := os.getenv('GITHUB_OUTPUT'):
            with open(github_output, 'a') as f:
                f.write(f"{name}={value}\n")
        logger.debug(f"Output set: {name}={value}")
    
    def add_step_summary(self, summary: str) -> None:
        """Add content to GitHub Actions step summary"""
        if github_step_summary := os.getenv('GITHUB_STEP_SUMMARY'):
            with open(github_step_summary, 'a') as f:
                f.write(f"{summary}\n")
    
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
            logger.info("\n--- Installing Toolchain ---")
            self.install_terraform()
            
            if self.cloud_provider in ['azure', 'multi']:
                self.install_azure_cli()
            
            if self.cloud_provider in ['aws', 'multi']:
                self.install_aws_cli()
            
            self.install_github_cli()
            
            # Phase 3: Configure cloud credentials
            logger.info("\n--- Configuring Cloud Providers ---")
            if self.cloud_provider in ['azure', 'multi']:
                self.configure_azure_credentials()
            
            if self.cloud_provider in ['aws', 'multi']:
                self.configure_aws_credentials()
            
            # Phase 4: Terraform workflow
            logger.info("\n--- Terraform Workflow ---")
            self.terraform_init()
            self.terraform_fmt()
            self.terraform_validate()
            
            # Plan
            has_changes, plan_output = self.terraform_plan()
            
            # Upload artifact
            self.upload_plan_artifact()
            
            # Post PR comment
            if has_changes:
                self.post_pr_comment(plan_output)
            
            # Apply (if requested and changes exist)
            if self.terraform_operation in ['apply', 'plan-apply'] and has_changes:
                logger.info("\n--- Applying Changes ---")
                self.terraform_apply()
            else:
                logger.info("Skipping apply (no changes or not requested)")
                self.set_output('apply_outcome', 'skipped')
            
            # Summary
            logger.info("\n" + "=" * 60)
            logger.info("✓ CloudOps pipeline completed successfully")
            logger.info("=" * 60)
            
            self.add_step_summary(f"""## ✅ CloudOps Pipeline Success

- **Working Directory**: `{self.resolved_working_dir.relative_to(self.github_workspace)}`
- **Cloud Provider**: `{self.cloud_provider}`
- **Operation**: `{self.terraform_operation}`
- **Changes Detected**: `{has_changes}`
""")
            
            return 0
            
        except Exception as e:
            logger.error(f"\n✗ Pipeline failed: {e}", exc_info=True)
            self.add_step_summary(f"""## ❌ CloudOps Pipeline Failed

**Error**: {str(e)}

See logs for details.
""")
            return 1


def main():
    """Entry point"""
    action = CloudOpsAction()
    sys.exit(action.run())


if __name__ == '__main__':
    main()
