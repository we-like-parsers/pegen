from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='pegen',
    version='0.1.0',
    description="CPython's PEG parser generator",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/we-like-parsers/pegen',
    author='Guido van Rossum, Pablo Galindo, Lysandros Nikolaou',
    author_email='pablogsal@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Compilers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
    ],

    keywords='parser, CPython, PEG, pegen',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    python_requires='>=3.8, <4',
    install_requires=['psutil', 'flask', 'flask-wtf'],
    extras_require={
        'lint': ['black', 'flake8', 'mypy'],
        'test': ['pytest', 'pytest-cov'],
    },
    project_urls={
        'Bug Reports': 'https://github.com/we-like-parsers/pegen/issues',
        'Source': 'https://github.com/we-like-parsers/pegen',
    },
    package_data={
        "pegen": ["templates/*.html"],
    }
)
