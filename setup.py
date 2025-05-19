from setuptools import setup, find_packages

setup(
    name="asset-indexer",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.7",
    install_requires=[
        "functions-framework",
        "google-cloud-firestore",
        "google-cloud-pubsub",
        "google-cloud-storage",
        "python-dotenv"
    ],
) 