"""
Setup configuration for DocuAI package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="docuai",
    version="1.0.0",
    author="DocuAI Team",
    description="Multi-format RAG system implementing all 5 blog concepts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/docuai",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        line.strip()
        for line in open("requirements.txt").readlines()
        if line.strip() and not line.startswith("#")
    ],
)
