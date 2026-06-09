from setuptools import setup

setup(
    name="repo-scan",
    version="0.2.0",
    packages=["repo_scan"],
    entry_points={
        "console_scripts": [
            "repo-scan=repo_scan:main",
        ],
    },
    python_requires=">=3.10",
)
