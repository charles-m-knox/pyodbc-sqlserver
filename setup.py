"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup  # , find_packages

setup(
    name='sqlserver',  # Required
    version='0.0.1',  # Required
    description='Helper classes for interacting with SQL Server and pyodbc',  # Required
    url='https://github.com/charles-m-knox/pyodbc-sqlserver',  # Optional
    author='Charles M Knox',  # Optional
    author_email='charles.m.knox@gmail.com',  # Optional
    classifiers=[  # Optional
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Database',
        'License :: Freeware',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='sqlserver pyodbc',  # Optional
    package_dir={
        '': 'src/'
    },
    packages=[
        'sqlserver'
    ],
    install_requires=['pyodbc==4.0.22'],  # Optional
    extras_require={  # Optional
        'dev': [
            'pyodbc==4.0.22',
            'flake8==3.5.0',
            'yamllint==1.8.1',
            'pyyaml==3.12'
        ],
        # 'test': ['coverage'],
    },
    project_urls={  # Optional
        'Source': 'https://github.com/charles-m-knox/pyodbc-sqlserver',
    },
)
