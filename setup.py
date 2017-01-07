from setuptools import setup, find_packages


__version__ = '0.0.1'


setup(
    name='aiomailserver',
    version=__version__,
    description='aiomailserver - asyncio based simple mail server',
    long_description="",
    author='https://github.com/kozzztik',
    url='https://github.com/kozzztik/aiomailserver',
    keywords='email',
    packages=find_packages(),
    include_package_data=True,
    license='',  # TODO
    install_requires=[
        'aiosmtpd', 'aiosmtplib'
        ],
    classifiers=[
        'License :: OSI Approved',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Communications :: Email :: Mail Trans\port Agents',
        ],
    )
