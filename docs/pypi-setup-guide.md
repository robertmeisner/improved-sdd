# PyPI Publishing Setup Guide

This guide provides step-by-step instructions for configuring PyPI and TestPyPI accounts, API tokens, and GitHub repository settings for automated publishing.

## Prerequisites

- GitHub repository with admin access
- Email account for PyPI/TestPyPI registration
- Two-factor authentication app (recommended)

## Part 1: PyPI and TestPyPI Account Setup

### 1.1 Create TestPyPI Account

1. **Visit TestPyPI**: Go to [https://test.pypi.org/](https://test.pypi.org/)
2. **Register Account**: Click "Register" and create an account
3. **Verify Email**: Check your email and verify the account
4. **Enable 2FA** (Recommended): 
   - Go to Account Settings → Security
   - Set up Two-Factor Authentication

### 1.2 Create PyPI Account

1. **Visit PyPI**: Go to [https://pypi.org/](https://pypi.org/)
2. **Register Account**: Click "Register" and create an account
3. **Verify Email**: Check your email and verify the account  
4. **Enable 2FA** (Recommended):
   - Go to Account Settings → Security
   - Set up Two-Factor Authentication

## Part 2: API Token Creation

### 2.1 Create TestPyPI API Token

1. **Login to TestPyPI**: [https://test.pypi.org/](https://test.pypi.org/)
2. **Navigate to Account Settings**: Click your username → Account settings
3. **Go to API Tokens**: Click "API tokens" in the left sidebar
4. **Create New Token**:
   - Click "Add API token"
   - **Token name**: `improved-sdd-github-actions`
   - **Scope**: `Entire account` (or specific to improved-sdd project if it exists)
   - Click "Add token"
5. **Copy Token**: **IMPORTANT** - Copy the token immediately (starts with `pypi-`)
6. **Store Securely**: Save the token temporarily in a secure location

### 2.2 Create PyPI API Token

1. **Login to PyPI**: [https://pypi.org/](https://pypi.org/)
2. **Navigate to Account Settings**: Click your username → Account settings
3. **Go to API Tokens**: Click "API tokens" in the left sidebar
4. **Create New Token**:
   - Click "Add API token"
   - **Token name**: `improved-sdd-github-actions`
   - **Scope**: `Entire account` (or specific to improved-sdd project after first upload)
   - Click "Add token"
5. **Copy Token**: **IMPORTANT** - Copy the token immediately (starts with `pypi-`)
6. **Store Securely**: Save the token temporarily in a secure location

## Part 3: GitHub Repository Configuration

### 3.1 Add Repository Secrets

1. **Navigate to Repository**: Go to your GitHub repository
2. **Open Settings**: Click "Settings" tab
3. **Go to Secrets**: Click "Secrets and variables" → "Actions"
4. **Add TestPyPI Token**:
   - Click "New repository secret"
   - **Name**: `TEST_PYPI_API_TOKEN`
   - **Secret**: Paste the TestPyPI token (starts with `pypi-`)
   - Click "Add secret"
5. **Add PyPI Token**:
   - Click "New repository secret"
   - **Name**: `PYPI_API_TOKEN`
   - **Secret**: Paste the PyPI token (starts with `pypi-`)
   - Click "Add secret"

### 3.2 Configure GitHub Environments

**Important**: The primary purpose of GitHub environments is to organize deployments and apply protection rules. The Environment URL field is optional and purely for documentation purposes.

#### 3.2.1 Create TestPyPI Environment

1. **Go to Environments**: Settings → Environments
2. **Create Environment**:
   - Click "New environment"
   - **Name**: `testpypi`
   - Click "Configure environment"
3. **Configure Environment**:
   - **Environment URL** (Optional): `https://test.pypi.org/project/improved-sdd/`
     - *Note: This field may not be visible initially - it's optional for basic setup*
   - **Protection Rules**: Leave all unchecked (automatic deployment)
   - **Environment Secrets**: None needed (uses repository secrets)
   - **Deployment branches**: Leave default (All branches)
4. **Save Configuration**: Click "Save protection rules"

#### 3.2.2 Create PyPI Environment

1. **Create Environment**:
   - Click "New environment"
   - **Name**: `pypi`
   - Click "Configure environment"
2. **Configure Environment**:
   - **Environment URL** (Optional): `https://pypi.org/project/improved-sdd/`
     - *Note: This field may not be visible initially - it's optional for basic setup*
   - **Protection Rules** (Recommended for production):
     - ☐ **Required reviewers**: Add yourself for extra safety (optional)
     - ☐ **Wait timer**: 5 minutes (optional delay)
     - ✅ **Deployment branches**: Recommended - "Selected branches and tags"
       - Add rule: `v*.*.*` (version tags only)
   - **Environment Secrets**: None needed (uses repository secrets)
3. **Save Configuration**: Click "Save protection rules"

## Part 4: Verification and Testing

### 4.1 Verify Secret Configuration

1. **Check Secrets**: Go to Settings → Secrets and variables → Actions
2. **Verify Secrets Exist**:
   - ✅ `TEST_PYPI_API_TOKEN`
   - ✅ `PYPI_API_TOKEN`

### 4.2 Verify Environment Configuration

1. **Check Environments**: Go to Settings → Environments
2. **Verify Environments Exist**:
   - ✅ `testpypi` - No protection rules
   - ✅ `pypi` - With protection rules (optional)

### 4.3 Test Workflow Access

1. **Manual Workflow Test**: 
   - Go to Actions tab
   - Find "Publish to PyPI" workflow
   - Click "Run workflow" → Select branch → "Run workflow"
   - Verify it has access to secrets (workflow should start)

## Part 5: Security Best Practices

### 5.1 Token Security

- **Never commit tokens** to code or documentation
- **Use least-privilege tokens** - scope to specific projects when possible
- **Regular rotation** - Rotate tokens every 6-12 months
- **Monitor usage** - Check PyPI account for unexpected activity

### 5.2 Environment Protection

- **Use environment protection** for production PyPI publishing
- **Required reviewers** - Add team members for critical releases
- **Deployment branches** - Restrict to version tags only
- **Audit logs** - Regularly review deployment history

### 5.3 Token Rotation Procedure

When rotating tokens:

1. **Create new token** on PyPI/TestPyPI
2. **Update GitHub secret** with new token
3. **Test workflow** to ensure it works
4. **Revoke old token** on PyPI/TestPyPI
5. **Document rotation** in security logs

## Part 6: Troubleshooting

### Common Issues

#### Environment Configuration Issues
- **Issue**: Cannot find "Environment URL" field
- **Solution**: This field is optional and may not be visible in all GitHub configurations
- **Action**: Skip the URL field - it's not required for basic publishing functionality

#### Authentication Errors
- **Issue**: `Invalid API token`
- **Solution**: Verify token was copied correctly, check for extra spaces
- **Action**: Regenerate token if needed

#### Permission Errors  
- **Issue**: `User X does not have upload permissions`
- **Solution**: Ensure token has correct scope (entire account or specific project)
- **Action**: Create new token with broader scope

#### Environment Access Errors
- **Issue**: `Environment not found`
- **Solution**: Verify environment names match workflow configuration
- **Action**: Check environment names are exactly `testpypi` and `pypi`

#### Workflow Failure
- **Issue**: Workflow fails to access secrets
- **Solution**: Verify secrets exist with correct names
- **Action**: Check secret names match `TEST_PYPI_API_TOKEN` and `PYPI_API_TOKEN`

#### CI Workflow Dependencies
- **Issue**: Publishing blocked because CI workflows failed
- **Solution**: Fix CI issues first, or use manual override procedures
- **Action**: Follow manual override procedures below

### Manual Override Procedures

When CI workflows fail but you need to publish urgently, use these procedures:

#### Emergency Publishing (Use Sparingly)
1. **Manual Workflow Dispatch**:
   - Go to repository Actions tab
   - Select "Publish to PyPI" workflow  
   - Click "Run workflow"
   - Enable "dry_run" to test first without actual publishing
   - Select target environment (testpypi/pypi)

2. **CI Workflow Troubleshooting**:
   ```bash
   # Check workflow status (requires GitHub CLI)
   gh run list --workflow=ci.yml --limit=5
   
   # View specific workflow logs
   gh run view [run-id] --log
   
   # Re-run failed workflows
   gh run rerun [run-id] --failed
   ```

3. **Manual Package Upload** (Last Resort):
   ```bash
   # Build package locally
   python -m build
   
   # Test upload to TestPyPI first
   python -m twine upload --repository testpypi dist/*
   
   # Upload to PyPI (after testing)
   python -m twine upload dist/*
   ```

#### Timeout Handling
- **Issue**: CI workflows are stuck or running too long
- **Solution**: The publishing workflow has built-in timeout handling
- **Action**: Wait for automatic timeout, then investigate CI issues

#### Force Publishing Override
**Warning**: Only use this in emergency situations where CI is broken but code quality is verified through other means.

1. Edit the workflow file temporarily to skip CI dependencies
2. Use workflow_dispatch with manual approval
3. Revert workflow changes immediately after publishing

## Completion Checklist

- [ ] TestPyPI account created and verified
- [ ] PyPI account created and verified
- [ ] TestPyPI API token created and stored securely
- [ ] PyPI API token created and stored securely
- [ ] `TEST_PYPI_API_TOKEN` added to GitHub repository secrets
- [ ] `PYPI_API_TOKEN` added to GitHub repository secrets
- [ ] `testpypi` GitHub environment configured
- [ ] `pypi` GitHub environment configured (with protection rules)
- [ ] Manual workflow test completed successfully
- [ ] Security best practices documented and understood

## Next Steps

After completing this setup:
1. Test the publishing workflow with Task 1.3
2. Verify packages can be published to TestPyPI
3. Test the complete PyPI publishing flow
4. Set up monitoring and maintenance procedures

## Support

For issues with this setup:
- Check the troubleshooting section above
- Review GitHub Actions workflow logs
- Consult PyPI/TestPyPI documentation
- Contact repository maintainers