"""
Tool Installation Utility

Handles installation of Terraform, Azure CLI, AWS CLI, and GitHub CLI.
"""

import os
import logging
import platform
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Optional
from .cli import run_command, command_exists

logger = logging.getLogger(__name__)


class ToolInstaller:
    """Handles installation of required CLI tools"""

    @staticmethod
    def install_terraform(version: str = 'latest') -> None:
        """
        Install Terraform CLI.

        Args:
            version: Terraform version to install ('latest' or specific version)
        """
        logger.info(f"Installing Terraform (version: {version})...")

        # Check if terraform is already installed
        if command_exists('terraform'):
            result = subprocess.run(['terraform', 'version'],
                                    capture_output=True, text=True, check=False)
            if result.returncode == 0:
                installed_version = result.stdout.split()[1]
                logger.info(f"Terraform already installed: {installed_version}")
                if version == 'latest':
                    logger.info("Skipping installation (latest already available)")
                    return

        # Determine version to install
        if version == 'latest':
            version = ToolInstaller._get_latest_terraform_version()

        logger.info(f"Installing Terraform version: {version}")

        # Download and install
        system = platform.system().lower()
        arch = 'amd64' if platform.machine() in ['x86_64', 'AMD64'] else 'arm64'

        download_url = f"https://releases.hashicorp.com/terraform/{version}/terraform_{version}_{system}_{arch}.zip"

        install_dir = Path.home() / '.local' / 'bin'
        install_dir.mkdir(parents=True, exist_ok=True)

        import urllib.request

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

    @staticmethod
    def _get_latest_terraform_version() -> str:
        """
        Get the latest Terraform version from GitHub releases.

        Returns:
            Latest version string
        """
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
            return "1.9.0"

    @staticmethod
    def install_azure_cli() -> None:
        """Install Azure CLI."""
        logger.info("Installing Azure CLI...")

        # Check if az is already installed
        if command_exists('az'):
            logger.info("Azure CLI already installed")
            return

        # Install using curl method (works on Ubuntu)
        logger.info("Installing Azure CLI via apt...")
        commands = [
            ['sudo', 'apt-get', 'update'],
            ['sudo', 'apt-get', 'install', '-y', 'ca-certificates', 'curl',
             'apt-transport-https', 'lsb-release', 'gnupg'],
            ['bash', '-c', 'curl -sL https://packages.microsoft.com/keys/microsoft.asc | '
                           'gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null'],
            ['bash', '-c', 'AZ_REPO=$(lsb_release -cs) && '
                           'echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $AZ_REPO main" | '
                           'sudo tee /etc/apt/sources.list.d/azure-cli.list'],
            ['sudo', 'apt-get', 'update'],
            ['sudo', 'apt-get', 'install', '-y', 'azure-cli']
        ]

        for cmd in commands:
            try:
                subprocess.run(cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                logger.warning(f"Command failed: {' '.join(cmd)}")
                break

        # Verify installation
        if command_exists('az'):
            logger.info("✓ Azure CLI installed")
        else:
            logger.warning("Azure CLI installation could not be verified")

    @staticmethod
    def install_aws_cli() -> None:
        """Install AWS CLI."""
        logger.info("Installing AWS CLI...")

        # Check if aws is already installed
        if command_exists('aws'):
            logger.info("AWS CLI already installed")
            return

        logger.info("Installing AWS CLI v2...")

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
            logger.info("Extracting AWS CLI...")
            with zipfile.ZipFile(installer_zip, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)

            # Install
            logger.info("Installing AWS CLI...")
            subprocess.run([str(tmpdir / 'aws' / 'install')], check=True)

        # Verify
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        logger.info(f"✓ AWS CLI installed: {result.stdout.strip()}")

    @staticmethod
    def install_github_cli(version: str = 'latest') -> None:
        """
        Install GitHub CLI.

        Args:
            version: GitHub CLI version to install
        """
        logger.info(f"Installing GitHub CLI (version: {version})...")

        # Check if gh is already installed
        if command_exists('gh'):
            logger.info("GitHub CLI already installed")
            if version == 'latest':
                return

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
