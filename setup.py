from distutils.core import setup

desc = ""
try: desc=open('README.rst').read()
except: pass
setup(
    name='autolux',
    version='0.0.14',
    author='okay',
    author_email='okay.zed+kk@gmail.com',
    packages=['autolux' ],
    scripts=['bin/autolux'],
    url='http://github.com/okayzed/autolux',
    license='MIT',
    description='an auto luxer',
    long_description=desc
    )

