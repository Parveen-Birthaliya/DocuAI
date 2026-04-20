# Contributing to DocuAI

We welcome contributions from the community! This document provides guidelines and instructions for contributing to DocuAI.

## Code of Conduct

Please be respectful and constructive in all interactions with other contributors and maintainers.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/docuai.git
   cd docuai
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov black flake8
   ```

5. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) conventions
- Use type hints where appropriate
- Write descriptive docstrings using Google-style format
- Maximum line length: 100 characters

### Code Formatting

```bash
# Format code with black
black src/ tests/

# Check code style with flake8
flake8 src/ tests/
```

### Testing

- Write tests for new features
- Ensure all tests pass before submitting PR

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=src tests/
```

### Documentation

- Update docstrings for modified functions/classes
- Update README.md if adding new features
- Add examples for complex functionality
- Document any breaking changes

## Submitting Changes

1. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Submit a Pull Request**:
   - Use a clear, descriptive title
   - Reference any related issues
   - Provide a detailed description of changes
   - Include screenshots/examples if relevant

3. **Code Review**:
   - Address feedback from reviewers
   - Keep discussions professional and constructive

## Project Structure

```
docuai/
├── src/
│   ├── blog1_audit/           # Corpus audit stage
│   ├── blog2_parsing/         # Format parsing stage
│   ├── blog3_cleaning/        # Text cleaning stage
│   ├── blog4_extraction/      # Knowledge extraction
│   ├── blog5_dedup/           # Deduplication
│   ├── blog6_embedding/       # Embedding & retrieval
│   ├── blog7_rag/             # RAG interfaces
│   ├── utils/                 # Shared utilities
│   └── config.py              # Configuration
├── tests/                     # Test suite
├── docs/                      # Documentation
├── data/                      # Data directory
├── pipeline.py                # Main orchestrator
├── requirements.txt           # Dependencies
└── setup.py                   # Package setup
```

## Areas for Contribution

### High Priority

- [ ] LLM integration (OpenAI, HuggingFace, Ollama)
- [ ] Performance optimization
- [ ] Additional file format support
- [ ] Query result re-ranking

### Medium Priority

- [ ] Multi-language support
- [ ] Database integrations
- [ ] Advanced retrieval strategies
- [ ] Conversation management

### Low Priority

- [ ] UI improvements
- [ ] Additional metrics/analytics
- [ ] Documentation improvements

## Reporting Issues

When reporting a bug:

1. **Check existing issues** to avoid duplicates
2. **Describe the issue clearly**:
   - What you tried
   - What happened
   - What you expected
   - Error messages/logs
3. **Include system information**:
   - OS and Python version
   - DocuAI version
   - Relevant dependencies
4. **Provide a minimal reproduction**

## Questions?

- Open a GitHub Discussion
- Check existing issues and documentation
- Review the docs/ folder for guides

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to DocuAI! 🚀
