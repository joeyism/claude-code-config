# Publishing to PyPI

This guide walks you through publishing `claude-code-config` to PyPI.

## Prerequisites

1. **PyPI Account**: Create an account at https://pypi.org/account/register/
2. **API Token**: Generate an API token at https://pypi.org/manage/account/token/
3. **Build Tools**: Install required packages

```bash
pip install build twine
```

## Pre-Publishing Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` with new version
- [ ] Run tests: `pytest tests/`
- [ ] Format code: `black claude_config_manager/`
- [ ] Lint code: `ruff check claude_config_manager/`
- [ ] Update GitHub repository URL in `pyproject.toml` and `README.md`
- [ ] Update author email in `pyproject.toml`
- [ ] Test installation locally
- [ ] Review README.md

## Building the Package

1. **Clean previous builds**:
```bash
rm -rf dist/ build/ *.egg-info
```

2. **Build the package**:
```bash
python3 -m build
```

This creates two files in `dist/`:
- `claude-code-config-X.Y.Z.tar.gz` (source distribution)
- `claude_config_manager-X.Y.Z-py3-none-any.whl` (wheel distribution)

## Testing the Build

Test the package locally before uploading:

```bash
# Create a test virtual environment
python3 -m venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from the built wheel
pip install dist/claude_config_manager-*.whl

# Test the installation
claude-config --version
ccm --version

# Deactivate and remove test environment
deactivate
rm -rf test-env
```

## Publishing to Test PyPI (Recommended First)

Test PyPI is a separate instance for testing packages before publishing to the main PyPI.

1. **Create Test PyPI account**: https://test.pypi.org/account/register/

2. **Upload to Test PyPI**:
```bash
python3 -m twine upload --repository testpypi dist/*
```

3. **Test installation from Test PyPI**:
```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps claude-code-config
```

## Publishing to PyPI

Once you've tested everything:

```bash
python3 -m twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your API token (starts with `pypi-`)

## Post-Publishing

1. **Verify the upload**: Visit https://pypi.org/project/claude-code-config/

2. **Test installation**:
```bash
pip install claude-code-config
```

3. **Create a GitHub release**:
   - Go to your repository's releases page
   - Click "Create a new release"
   - Tag: `v0.1.0` (matching your version)
   - Title: "Release 0.1.0"
   - Description: Copy from CHANGELOG.md
   - Publish release

4. **Announce**:
   - Share on social media
   - Post in relevant communities
   - Update documentation

## Updating the Package

For subsequent releases:

1. Make your changes
2. Update version number in `pyproject.toml` (follow [Semantic Versioning](https://semver.org/)):
   - MAJOR version (X.0.0): Incompatible API changes
   - MINOR version (0.X.0): New functionality, backwards compatible
   - PATCH version (0.0.X): Backwards compatible bug fixes
3. Update `CHANGELOG.md`
4. Repeat the building and publishing steps

## Using GitHub Repository URL

Before publishing, update these files with your actual GitHub username:

**pyproject.toml**:
```toml
[project.urls]
Homepage = "https://github.com/YOUR_USERNAME/claude-code-config"
Repository = "https://github.com/YOUR_USERNAME/claude-code-config"
Issues = "https://github.com/YOUR_USERNAME/claude-code-config/issues"
```

**README.md**:
Replace all instances of `joeyism` with your actual GitHub username.

## Troubleshooting

### "File already exists" error
- You cannot overwrite a published version
- Increment the version number and rebuild

### Import errors after installation
- Check that `__init__.py` exports are correct
- Verify package structure with `python3 -m build --sdist` and inspect the tarball

### Missing dependencies
- Ensure all dependencies are listed in `pyproject.toml`
- Test in a fresh virtual environment

## Automation with GitHub Actions (Optional)

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.x'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

Add your PyPI API token as a GitHub secret named `PYPI_API_TOKEN`.

## Support

If you encounter issues during publishing, refer to:
- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Twine Documentation](https://twine.readthedocs.io/)
