# 维护

## 获取源码

```bash
git clone https://github.com/dyuu7/dataioc.git
cd dataioc
```

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
- 两份 README 的结构和可运行示例保持对应，文档链接分别指向对应语言。
- 正文段落在源码中保持单行，保留代码块、列表、表格和 API 指令的缩进结构。
- 英文页面作为默认导航来源。
- 简体中文翻译放在对应的 `.zh.md` 页面。
- 使用 `--strict` 构建，让断链和配置警告使 CI 失败。

文档站点由 GitHub Actions 从 `main` 分支构建并发布。

## README 示意图

修改 [Mermaid 源文件](https://github.com/dyuu7/dataioc/blob/main/docs/assets/data-flow.mmd)后，使用 Node.js 和 Mermaid CLI 重新生成 PNG：

```bash
npx -y @mermaid-js/mermaid-cli@11.15.0 -i docs/assets/data-flow.mmd -o docs/assets/data-flow.png -b white -s 3
```

两份 README 共用同一张图，并分别提供对应语言的说明。图片使用绝对 URL，兼容 GitHub 和 PyPI；发布 README 时应同时发布图片文件。

## 发布

更新 `pyproject.toml` 中的版本并刷新 `uv.lock`，然后推送 `vX.Y.Z` tag。发布 workflow 会构建源码包和 wheel，创建或更新 GitHub Release，并通过 Trusted Publishing 将同一批产物发布到 PyPI。
