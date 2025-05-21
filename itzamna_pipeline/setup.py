from setuptools import find_packages, setup

setup(
    name="itzamna_pipeline",
    packages=find_packages(exclude=["itzamna_pipeline_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
