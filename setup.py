"""setup.py - 兼容性打包配置"""

from setuptools import setup, find_packages

setup(
    name="netbridge-cli",
    version="0.1.0",
    description="AI Agent多平台互联网能力装配引擎",
    long_description=open("README.md", encoding="utf-8").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="NetBridge Team",
    license="MIT",
    python_requires=">=3.10",
    packages=find_packages(include=["netbridge*"]),
    package_data={
        "netbridge": ["py.typed"],
    },
    entry_points={
        "console_scripts": [
            "netbridge=netbridge.cli:main",
        ],
    },
    install_requires=[],
    extras_require={
        "rss": ["feedparser>=6.0"],
        "youtube": ["yt-dlp>=2024.0"],
        "all": ["feedparser>=6.0", "yt-dlp>=2024.0"],
        "dev": ["pytest>=7.0", "pytest-cov>=4.0", "mypy>=1.0", "ruff>=0.1.0"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
