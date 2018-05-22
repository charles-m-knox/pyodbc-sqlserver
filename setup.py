import re
from setuptools import setup

with open('requirements.txt') as handle:
    contents = handle.read().split('\n')

requires = []
links = []
regex = '.*#egg=(?P<package>[A-Za-z]+).*'
for content in contents:
    match = re.match(regex, content)
    if match:
        package = match.group('package')
        requires.append(package)
        links.append(content.replace('-e ', ''))
    else:
        requires.append(content)

print('requires: {}'.format(requires))
print('links: {}'.format(links))

setup(
    name='sqlserver',
    version='0.0.2',
    author='Charles Knox',
    author_email='charles.m.knox@gmail.com',
    package_dir={
        '': 'src/main/python'
    },
    packages=[
        'sqlserver'
    ],
    url='https://github.com/charles-m-knox/pyodbc-sqlserver',
    description='Python classes to interact with sql server',
    install_requires=requires,
    dependency_links=links
)
