from setuptools import setup

setup(
    name="repo-scan",
    version="0.2.0",
    packages=["repo_scan", "repo_scan.radar", "repo_scan.hub"],
    entry_points={
        "console_scripts": [
            "repo-scan=repo_scan:main",
            "radar=repo_scan.radar.cli:main",
        ],
    },
    python_requires=">=3.10",
    extras_require={"dev": ["pytest>=8", "syrupy>=5", "radon", "lizard"]},
)
