from setuptools import setup

setup(
    name="repo-scan",
    version="0.2.0",
    packages=["repo_scan", "repo_scan.radar"],
    entry_points={
        "console_scripts": [
            "repo-scan=repo_scan:main",
            "radar=repo_scan.radar.cli:main",
        ],
    },
    python_requires=">=3.10",
)
