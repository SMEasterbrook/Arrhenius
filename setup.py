from setuptools import setup

setup(
    name="website",
    packages=["website", "data", "core"],
    include_package_data=True,
    install_requires=[
        "flask",
    ]
)
