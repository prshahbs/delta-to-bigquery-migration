# Contributing to Delta to BigQuery Migration Tool

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## 🎯 How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/YOUR-USERNAME/delta-to-bigquery-migration/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, Spark version)
   - Error messages and logs

### Suggesting Enhancements

1. Check existing [Issues](https://github.com/YOUR-USERNAME/delta-to-bigquery-migration/issues) and [Discussions](https://github.com/YOUR-USERNAME/delta-to-bigquery-migration/discussions)
2. Create a new issue with:
   - Clear description of the enhancement
   - Use cases and benefits
   - Possible implementation approach

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test your changes thoroughly
5. Commit with clear messages (`git commit -m 'Add amazing feature'`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 🧪 Testing

Before submitting a PR:

```bash
# Test with sample data
cd test_data
python create_sample_delta_tables.py
cd ..

# Run migration test
./scripts/full_migration_workflow.sh

# Verify results
bq query "SELECT COUNT(*) FROM \`project.analytics.customers\`"
```

## 📝 Code Style

### Python
- Follow PEP 8
- Use meaningful variable names
- Add docstrings to functions
- Include type hints where appropriate

### Bash
- Use shellcheck for linting
- Add comments for complex logic
- Use meaningful variable names in CAPS

### Documentation
- Update README.md for new features
- Add examples for new functionality
- Keep documentation clear and concise

## 🏗️ Development Setup

```bash
# Clone repository
git clone https://github.com/YOUR-USERNAME/delta-to-bigquery-migration.git
cd delta-to-bigquery-migration

# Install dependencies
pip install -r requirements.txt
pip install -r test_data/requirements_test.txt

# Make scripts executable
chmod +x scripts/*.sh
```

## 📋 Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] Documentation updated (if needed)
- [ ] Tests added/updated (if needed)
- [ ] All tests pass
- [ ] Commit messages are clear
- [ ] PR description explains changes

## 🎯 Areas for Contribution

### High Priority
- Support for more Delta Lake features (CDC, time travel)
- Performance optimizations
- Additional data type mappings
- Better error handling

### Medium Priority
- Support for other cloud platforms (AWS, Azure)
- Integration with workflow orchestrators (Airflow, Prefect)
- Monitoring and alerting improvements
- Cost optimization features

### Documentation
- More examples and use cases
- Video tutorials
- Best practices guide
- FAQ section

## 🐛 Bug Fix Process

1. Create issue describing the bug
2. Fork and create fix branch
3. Write test that reproduces bug
4. Fix the bug
5. Verify test passes
6. Submit PR referencing issue

## ✨ Feature Development Process

1. Discuss feature in issue or discussion
2. Get feedback from maintainers
3. Fork and create feature branch
4. Implement feature
5. Add tests and documentation
6. Submit PR

## 📢 Communication

- Use GitHub Issues for bugs and features
- Use GitHub Discussions for questions and ideas
- Be respectful and constructive
- Follow the Code of Conduct

## 🏆 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in relevant documentation

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙋 Questions?

Feel free to:
- Open a discussion
- Create an issue
- Reach out to maintainers

Thank you for contributing! 🎉
