# 维护

## 本地检查

```bash
uv sync --frozen
uv run pytest --cov --cov-report=term-missing
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run mkdocs build --strict
uv build --no-sources
```

测试矩阵覆盖 Python 3.9 至 3.14，以及 NumPy 1.26 和 2.x。

## 文档规则

- `README.md` 保持简短，直接服务于开始使用。
- 英文页面作为默认导航来源。
- 简体中文翻译放在对应的 `.zh.md` 页面。
- 使用 `--strict` 构建，让断链和配置警告使 CI 失败。

文档站点由 GitHub Actions 从 `main` 分支构建并发布。

## 发布

更新 `pyproject.toml` 中的版本并刷新 `uv.lock`，然后推送 `vX.Y.Z` tag。发布 workflow
会构建源码包和 wheel，创建或更新 GitHub Release，并通过 Trusted Publishing 将同一批产物发布到 PyPI。
