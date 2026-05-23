from setuptools import setup, find_packages

setup(
    name="mathlite",
    version="1.0.0",
    description="Intérprete DSL Matemático — Proyecto Final Lenguajes Formales 2026-1",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "flask>=3.0.0",
        "pymongo>=4.6.0",
        "gunicorn>=21.2.0",
    ],
)
