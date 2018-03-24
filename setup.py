from setuptools import setup, find_packages

setup(name="autoldap",
      version="0.1",
      author="Russell Jancewicz",
      url="https://github.com/russjancewicz/autoldap",
      packages=find_packages(),
      install_requires=["python-ldap==3.0.0b3",
                        "future==0.16.0",
                        "argparse==1.4.0"])
