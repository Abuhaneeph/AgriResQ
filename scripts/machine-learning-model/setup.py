from setuptools import setup, find_packages

setup(
    name="disaster_relief_pool",
    version="0.1",
    packages=find_packages("src"),   # Specify that packages are under src
    package_dir={"": "src"},         # Specify src as the root package directory
)
