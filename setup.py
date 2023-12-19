from setuptools import setup, find_packages

# List of requirements
requirements = []  # This could be retrieved from requirements.txt
# Package (minimal) configuration
setup(
    name="njl-corf",
    version="0.01",
    description="Various CORF-related tools",
    packages=find_packages(),  # __init__.py folders search
    install_requires=requirements,
)
