#!/bin/sh
set -e
rm -rf openstreetmappy* build dist README.md LICENSE setup.py deploy.sh
test "$1" = "clean" && exit

cp -a ../openstreetmappy ../README.md .
cp -a ../COPYING LICENSE

cat<<EOT > setup.py
import setuptools

with open("README.md") as f:
    long_description = f.read().rstrip()

with open("openstreetmappy/VERSION") as f:
    version = f.read().rstrip()

setuptools.setup(
    name="openstreetmappy",
    version=version,
    license="GPLv3+",
    author="Huidae Cho",
    author_email="grass4u@gmail.com",
    description="OpenStreetMapPy is an OpenStreetMap downloader written in Python that is agnostic of GUI frameworks.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/HuidaeCho/openstreetmappy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3",
    package_data={"openstreetmappy": ["VERSION"]},
)
EOT

cat<<EOT > deploy.sh
#!/bin/sh
set -e
pip3 install --user --upgrade twine
twine upload dist/*
EOT
chmod a+x deploy.sh

pip3 install --user --upgrade setuptools wheel
python3 setup.py sdist bdist_wheel
