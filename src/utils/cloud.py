"""
Cloud Provider Authentication Utility

Handles authentication and configuration for Azure and AWS.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional
from .cli import run_command

logger = logging.getLogger(__name__)


class CloudAuth:
    """Handles cloud provider authentication"""

    @staticmethod
    def configure_azure(credentials: str) -> None:
        """
        Configure Azure authentication.

        Args:
            credentials: Azure credentials JSON string

        Raises:
            ValueError: If credentials are invalid
            RuntimeError: If authentication fails
        """
        if not credentials:
            logger.info("No Azure credentials provided, skipping Azure configuration")
            return

        logger.info("Configuring Azure credentials...")

        try:
            creds = json.loads(credentials)

            # Login using service principal
            run_command([
                'az', 'login',
                '--service-principal',
                '--username', creds.get('clientId', ''),
                '--password', creds.get('clientSecret', ''),
                '--tenant', creds.get('tenantId', '')
            ])

            # Set subscription
            if subscription_id := creds.get('subscriptionId'):
                run_command(['az', 'account', 'set', '--subscription', subscription_id])

            # Export environment variables for Terraform
            os.environ['ARM_CLIENT_ID'] = creds.get('clientId', '')
            os.environ['ARM_CLIENT_SECRET'] = creds.get('clientSecret', '')
            os.environ['ARM_TENANT_ID'] = creds.get('tenantId', '')
            os.environ['ARM_SUBSCRIPTION_ID'] = creds.get('subscriptionId', '')

            logger.info("✓ Azure credentials configured")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Azure credentials JSON: {e}")
            raise ValueError("Invalid Azure credentials format") from e
        except Exception as e:
            logger.error(f"Failed to configure Azure credentials: {e}")
            raise RuntimeError("Azure authentication failed") from e

    @staticmethod
    def configure_aws(access_key_id: str, secret_access_key: str, region: str = 'us-east-1') -> None:
        """
        Configure AWS authentication.

        Args:
            access_key_id: AWS Access Key ID
            secret_access_key: AWS Secret Access Key
            region: AWS Region

        Raises:
            RuntimeError: If authentication fails
        """
        if not access_key_id or not secret_access_key:
            logger.info("No AWS credentials provided, skipping AWS configuration")
            return

        logger.info("Configuring AWS credentials...")

        # Export environment variables for Terraform
        os.environ['AWS_ACCESS_KEY_ID'] = access_key_id
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_access_key
        os.environ['AWS_DEFAULT_REGION'] = region

        # Also configure AWS CLI
        aws_dir = Path.home() / '.aws'
        aws_dir.mkdir(exist_ok=True)

        credentials_file = aws_dir / 'credentials'
        with open(credentials_file, 'w') as f:
            f.write('[default]\n')
            f.write(f'aws_access_key_id = {access_key_id}\n')
            f.write(f'aws_secret_access_key = {secret_access_key}\n')

        config_file = aws_dir / 'config'
        with open(config_file, 'w') as f:
            f.write('[default]\n')
            f.write(f'region = {region}\n')

        logger.info("✓ AWS credentials configured")

    @staticmethod
    def cleanup_credentials() -> None:
        """
        Clean up sensitive credentials from environment and filesystem.

        This should be called after Terraform operations are complete.
        """
        logger.info("Cleaning up credentials...")

        # Remove Azure environment variables
        for var in ['ARM_CLIENT_ID', 'ARM_CLIENT_SECRET', 'ARM_TENANT_ID', 'ARM_SUBSCRIPTION_ID']:
            os.environ.pop(var, None)

        # Remove AWS environment variables
        for var in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION']:
            os.environ.pop(var, None)

        # Remove AWS credential files
        aws_dir = Path.home() / '.aws'
        if aws_dir.exists():
            credentials_file = aws_dir / 'credentials'
            config_file = aws_dir / 'config'

            if credentials_file.exists():
                credentials_file.unlink()
            if config_file.exists():
                config_file.unlink()

        logger.info("✓ Credentials cleaned up")
