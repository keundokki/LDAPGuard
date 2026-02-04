# Contributing to LDAPGuard

Thank you for your interest in contributing to LDAPGuard! This document provides guidelines for contributing to the project.

## Code of Conduct

Please be respectful and constructive in all interactions with the project and its community.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Environment details (OS, Podman/Docker version, etc.)

### Suggesting Features

Feature suggestions are welcome! Please create an issue with:
- A clear description of the feature
- Use cases and benefits
- Any implementation ideas

### Pull Requests

1. **Fork the repository** and create a new branch from `main`
2. **Make your changes** following the coding standards below
3. **Write tests** for new functionality
4. **Update documentation** as needed
5. **Commit your changes** with clear, descriptive messages
6. **Push to your fork** and submit a pull request

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/keundokki/LDAPGuard.git
   cd LDAPGuard
   ```

2. Set up environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Start development services:
   ```bash
   docker-compose up -d
   ```

4. Run tests:
   ```bash
   docker-compose exec api pytest
   ```

## Coding Standards

### Python

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Keep functions focused and concise
- Use meaningful variable names

### JavaScript

- Use ES6+ features
- Follow consistent indentation (2 spaces)
- Use descriptive variable names
- Add comments for complex logic

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Reference issues and PRs where appropriate
- Keep first line under 50 characters
- Provide detailed description if needed

## Testing

- Write unit tests for new functionality
- Ensure all tests pass before submitting PR
- Maintain or improve code coverage

## Documentation

- Update README.md for user-facing changes
- Update inline documentation for code changes
- Add examples for new features

## Questions?

Feel free to open an issue for any questions about contributing.

Thank you for contributing to LDAPGuard!
