from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh.readlines() if line.strip() and not line.startswith("#")]

setup(
    name="lbos-ai",
    version="1.0.0",
    author="Lihan Badenhorst",
    author_email="lihan@example.com",
    description="LBOS-AI: An end-to-end pipeline for multimedia ingestion, dataset generation, and custom model training",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourorg/lbos-ai",
    packages=find_packages(where="lbos_ai"),
    package_dir={"": "lbos_ai"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "lbos-ai-ingest=lbos_ai.data.ingestion_worker:main",
            "lbos-ai-train=lbos_ai.train.trainer:main",
            "lbos_ai-evaluate=lbos_ai.eval.evaluator:main",
        ],
    },
)