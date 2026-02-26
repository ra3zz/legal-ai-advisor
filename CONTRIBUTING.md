# Contributing to Legal AI Advisor

Thank you for your interest in contributing! This document provides guidelines for contributing to the Legal AI Advisor project.

## Getting Started

### Prerequisites
- Python 3.8+
- pip or conda
- Git

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/legal-ai-advisor.git
   cd legal-ai-advisor
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ..
   ```

4. **Setup environment variables**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your GROQ_API_KEY
   ```

5. **Run tests**
   ```bash
   ./run.sh tests
   ```

## Development Workflow

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small

### Running the Application
```bash
./run.sh chat          # Start interactive chat
./run.sh build-graph   # Build knowledge graph from PDF
./run.sh tests         # Run test suite
```

### Before Submitting a Pull Request

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Keep commits atomic and well-documented
   - Write meaningful commit messages
   - Update relevant documentation

3. **Test your changes**
   ```bash
   ./run.sh tests
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**
   - Describe what your change does
   - Reference any related issues (#123)
   - Include examples or before/after if applicable

## Reporting Issues

### Bug Reports
Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
- Error messages and stack traces
- Relevant code snippets

### Feature Requests
Include:
- Clear description of the feature
- Use case and motivation
- Possible implementation approach
- Examples of how it would be used

## Architecture Overview

### Core Components

**RAG Service** (`backend/services/rag_service.py`)
- Document search and retrieval
- Hybrid search capabilities (TF-IDF + semantic)

**Graph Service** (`backend/services/graph_service.py`)
- Knowledge graph management
- Entity and relation extraction
- Graph-based reranking

**Groq Service** (`backend/services/groq_service.py`)
- LLM integration
- Entity extraction
- Response processing

**CLI Interface** (`backend/cli_chat.py`)
- User interaction
- Query processing
- Response formatting

### Database Schema
- Documents table (PDF content)
- Vector embeddings (TF-IDF)
- Chat history tracking
- Graph relations

## Testing

Tests are located in `backend/`:
- `test_suite.py` - Comprehensive test coverage
- `test_rag.py` - RAG-specific tests

```bash
# Run all tests
./run.sh tests

# Run specific test file
python -m pytest backend/test_suite.py -v

# Run with coverage
python -m pytest --cov=backend backend/
```

## Documentation

- **README.md** - Project overview and quick start
- **DEVELOPER.md** - Development guide
- **GRAPH_RAG_INTEGRATION_README.md** - Technical details
- **QUICKSTART.md** - 30-second quick start

Update documentation when:
- Adding new features
- Changing API behavior
- Adding new modules
- Improving clarity

## Questions or Need Help?

- Check existing issues and discussions
- Read the DEVELOPER.md guide
- Review code comments and docstrings
- Open an issue with the `question` label

## Code of Conduct

Please review our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

---

Thank you for contributing to making Legal AI Advisor better! 🙏
