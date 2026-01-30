# Contributing to OpenClaw Skill: AllStar Link Control

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Code of Conduct

- Be respectful and constructive
- Focus on what is best for the community
- Show empathy towards other community members

## How to Contribute

### Reporting Bugs

Before submitting a bug report:
1. Check existing issues to avoid duplicates
2. Collect information about your setup (ASL version, Python version, OS)
3. Include steps to reproduce the bug

When creating a bug report, include:
- Clear, descriptive title
- Detailed steps to reproduce
- Expected vs actual behavior
- System information
- Relevant logs (sanitize credentials!)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:
- Use a clear, descriptive title
- Provide detailed description of the proposed functionality
- Explain why this enhancement would be useful
- Include examples if applicable

### Pull Requests

1. Fork the repo and create your branch from `main`
2. Make your changes
3. Test your changes thoroughly
4. Update documentation if needed
5. Ensure code follows the existing style
6. Submit a pull request

#### Pull Request Guidelines

- One feature/fix per PR
- Include tests if applicable
- Update CHANGELOG.md
- Reference related issues
- Clear commit messages

## Development Setup

### Backend (Pi)

```bash
# Clone repo
git clone https://github.com/KJ5IRQ/openclaw-skill-asl3.git
cd openclaw-skill-asl3/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit config
cp config.yaml.example config.yaml
nano config.yaml

# Run locally
python3 asl_agent.py
```

### Skill (Windows)

Install Moltbot/Clawdbot and copy skill files to appropriate locations.

## Testing

Before submitting:
- Test all API endpoints
- Verify PowerShell functions work
- Check Telegram integration
- Test on clean ASL3 installation if possible
- Sanitize all credentials from logs

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Keep functions focused and small

### PowerShell
- Use approved verbs (Get-, Set-, etc.)
- Include parameter descriptions
- Add examples in comments

### Documentation
- Use clear, concise language
- Include code examples
- Update relevant docs when changing features

## Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Reference issues and pull requests
- First line: brief summary (50 chars or less)
- Detailed description in body if needed

Examples:
```
Fix connection timeout issue (#42)

Add support for EchoLink nodes

Update installation docs for Debian 13
```

## Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation only
- `refactor/description` - Code refactoring

## Release Process

1. Update version in relevant files
2. Update CHANGELOG.md
3. Create GitHub release
4. Tag with version number (v1.0.0)

## Questions?

Open a GitHub Discussion or create an issue with the "question" label.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
