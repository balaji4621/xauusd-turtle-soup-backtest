# Contributing to XAUUSD Turtle Soup Backtest Suite

Thank you for considering contributing to this quantitative trading backtesting engine! This document provides guidelines and information for contributors.

---

## 🚀 Getting Started

1. **Fork** the repository and clone your fork locally.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the test suite to ensure everything works:
   ```bash
   python -m pytest tests/ -v
   ```

---

## 📋 How to Contribute

### Reporting Bugs
- Use the GitHub Issues tab to report bugs.
- Include the Python version, OS, and steps to reproduce the issue.
- Attach sample CSV data (anonymized if necessary) that triggers the bug.

### Suggesting Enhancements
- Open an issue with the `enhancement` label.
- Describe the feature, its use case, and any proposed implementation details.

### Submitting Pull Requests
1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes and add tests for new functionality.
3. Run the test suite and ensure all tests pass.
4. Commit with a clear, descriptive message.
5. Push to your fork and open a Pull Request.

---

## 🧪 Testing Guidelines

- All new strategy logic must include corresponding unit tests in `tests/`.
- Use `pytest` for running the test suite.
- Ensure tests can run without CSV data files (use synthetic data fixtures).

---

## 📐 Code Style

- Follow PEP 8 for Python code.
- Use descriptive variable names (e.g., `swing_lookback` instead of `sl`).
- Add docstrings to all public functions.
- Keep functions focused and under 50 lines where possible.

---

## 📊 Strategy Development Rules

When adding or modifying trading strategies:
- Always include realistic spread costs in backtests (minimum 1.5 pips for XAUUSD).
- Document the strategy logic, entry/exit criteria, and risk management rules.
- Report performance across multiple timeframes (D1, H4, H1 at minimum).
- Include both gross and net (after-spread) performance metrics.

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project.