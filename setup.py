import setuptools

kwargs = {'version': '1.14'}

with open('README.md', 'r') as f:
    kwargs['long_description'] = f.read()
    kwargs['long_description_content_type'] = 'text/markdown'

setuptools.setup(
    name='django-better-choices',
    author='Alexander Lokhman',
    author_email='alex.lokhman@gmail.com',
    description='Better choices library for Django web framework',
    keywords=['django', 'choices'],
    license='MIT',
    url='https://github.com/lokhman/django-better-choices',
    download_url=f'https://github.com/lokhman/django-better-choices/tarball/{kwargs["version"]}',
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    packages=setuptools.find_packages(),
    python_requires='>=3.7',
    zip_safe=True,
    **kwargs
)
