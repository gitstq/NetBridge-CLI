.PHONY: install test build clean lint format check help

# 默认目标
help: ## 显示帮助
	@echo "NetBridge-CLI 构建命令"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## 安装项目（开发模式）
	pip install -e .
	@echo "安装完成"

install-all: ## 安装项目及所有可选依赖
	pip install -e ".[all]"
	@echo "安装完成（含所有可选依赖）"

install-dev: ## 安装开发依赖
	pip install -e ".[dev]"
	@echo "开发依赖安装完成"

test: ## 运行测试
	python -m pytest tests/ -v --tb=short

test-cov: ## 运行测试（含覆盖率）
	python -m pytest tests/ -v --cov=netbridge --cov-report=term-missing

lint: ## 代码检查
	ruff check netbridge/ tests/

format: ## 代码格式化
	ruff format netbridge/ tests/

typecheck: ## 类型检查
	mypy netbridge/

check: lint typecheck test ## 完整检查（lint + typecheck + test）

build: ## 构建分发包
	python -m build
	@echo "构建完成"

clean: ## 清理构建产物
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name *.egg-info -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info
	@echo "清理完成"

run: ## 运行CLI
	python -m netbridge.cli $(ARGS)

mcp: ## 启动MCP Server
	python -m netbridge.cli mcp

version: ## 显示版本
	python -c "from netbridge import __version__; print(f'NetBridge v{__version__}')"
