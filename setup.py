Copy
# setup.py

from setuptools import setup, find_packages

setup(
    name="my_project",
    version="0.1",
    packages=find_packages(),  # This will include all packages in the project
    install_requires=[],
    author="Your Name",
    author_email="your.email@example.com",
    description="A sample Python project with multiple packages",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/yourusername/my_project",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)