# Changelog

All notable changes to CloudOps will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial implementation of unified Terraform IaC toolchain
- GitHub Action with Python-based orchestrator
- Support for Azure and AWS cloud providers
- Multi-cloud deployment capability
- Automated toolchain installation:
  - Terraform with version pinning
  - Azure CLI
  - AWS CLI
  - GitHub CLI
- Complete Terraform workflow: `fmt → validate → plan → apply`
- PR integration with plan comment posting
- Plan artifact upload to GitHub Actions artifacts
- Embedded Azure AVM-style modules:
  - `virtual-network`: Virtual networks with subnets
  - `storage-account`: Storage accounts with security best practices
- Embedded AWS modules:
  - `vpc`: VPC with public/private subnets and NAT gateway
  - `s3-bucket`: S3 buckets with encryption and lifecycle policies
- Example Terraform configurations for Azure and AWS
- Example GitHub workflows for CI/CD
- Comprehensive documentation:
  - README with usage guide
  - Module documentation
  - Example READMEs with setup instructions
  - Contributing guidelines
  - MIT License

### Features

- Zero-setup toolchain installation
- Smart working directory resolution from `tf_path`
- Cloud credential configuration (Azure SP, AWS keys)
- Backend configuration support
- Terraform variable passing
- Structured logging and GitHub Actions summaries
- Security-first defaults (HTTPS-only, TLS 1.2+, blocked public access)

## [1.0.0] - TBD

Initial release.

[Unreleased]: https://github.com/Git-Cosmo/CloudOps/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Git-Cosmo/CloudOps/releases/tag/v1.0.0
