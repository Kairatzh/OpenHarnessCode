# Contributing to KAIROS Code

Thank you for contributing to **KAIROS Code**!

## Development Guidelines

1. **Keep the Core Minimal**: Any feature that can be a plugin, tool, or workflow should remain outside core runtime.
2. **Adhere to Interfaces**: All subsystems implement Python `Protocol` interfaces.
3. **Local-first**: Never introduce mandatory cloud dependencies.
4. **Developer Ownership**: Never force restrictions or mandatory guardrails that developers cannot bypass or configure.

## Setting Up Your Development Environment

```bash
git clone https://github.com/your-org/kairos-code.git
cd kairos-code
pip install -e ".[dev,all]"
pytest tests/
```

## Creating Custom Components

- Custom agents go into `.harness/agents/<id>.md`
- Custom workflows go into `.harness/workflows/<id>.yaml`
- Custom rules go into `.harness/rules/<name>.md`
- Portable project knowledge goes into `.harness/knowledge/`
