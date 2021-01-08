from setuptools import setup

install_requires = open("requirements.txt").read().strip().split("\n")

setup(
    name="benchmark",
    version="0.1",
    py_modules=["benchmark"],
    python_requires=">3.8",
    install_requires=install_requires,
    entry_points="""
        [console_scripts]
        benchmark=cli:cli
    """,
)
