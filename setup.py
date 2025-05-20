from setuptools import setup, find_packages

setup(
    name="pyiturr5etc",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "astropy",
        "intervaltree",
        "matplotlib",
        "natsort",
        "numpy",
        "pandas",
        "pdfplumber",
        "Pint",
        "python-docx",
        "termcolor",
        "Unidecode",
    ],
    python_requires=">=3.9",
)
