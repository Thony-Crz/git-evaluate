from setuptools import setup, find_packages

setup(
    name="git-evaluate",
    version="0.1.0",
    description="CLI tool to analyze git staging changes before commit",
    author="Thony-Crz",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "git-evaluate=git_evaluate.cli:main",
        ],
    },
    install_requires=[
        "gitpython>=3.1.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
