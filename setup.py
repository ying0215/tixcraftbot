from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ticketbot",
    version="0.1.0",
    author="Tsai Jack",
    author_email="your.email@example.com",
    description="專案簡短描述",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        # 在這裡列出相依套件
        # "requests>=2.25.0",
    ],
    entry_points={
        'console_scripts': [
            'my-app=my_package.main:run_app',
        ],
    },
)