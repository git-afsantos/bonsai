import os
from setuptools import setup, find_packages

# Utility function to read the README file. Used for the long_description.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name            = "bonsai-code",
    version         = "0.1.3",
    author          = "Andre Santos",
    author_email    = "andre.f.santos@inesctec.pt",
    description     = "Static analysis library.",
    long_description= read("README.rst"),
    license         = "MIT",
    keywords        = "static-analysis ast parsing",
    url             = "https://github.com/git-afsantos/bonsai",
    packages        = find_packages(),
    entry_points    = {"console_scripts": ["bonsai = bonsai.bonsai:main"]},
    package_data    = {},
    install_requires= [],
    zip_safe        = True
)
