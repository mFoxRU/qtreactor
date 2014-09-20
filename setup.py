"""
Using the QtReactor
-------------------

Before running / importing any other Twisted code, invoke:

::

    app = QApplication(sys.argv) # your code to init Qt
    from twisted.application import reactors
    reactors.installReactor('qt4')

or

::

    app = QApplication(sys.argv) # your code to init Qt
    from twisted.application import reactors
    reactors.installReactor('pyside')

alternatively (gui example):

::

    app = PyQt4.QtGui(sys.argv) # your code to init Qt
    from twisted.application import reactors
    qt4reactor.install

Testing
~~~~~~~

-  test with:

   trial --reactor=qt4 twisted (or twisted.test or
   twisted.test.test\_internet)

Testing with a Gui
~~~~~~~~~~~~~~~~~~

Twisted trial can be run for a Gui test using gtrial. Run Trial in the
same directory as bin/gtrial and it pops up a trivial gui... hit the
buton and it all runs the same... don't use the --reactor option when
calling gtrial... but all the other options appear to work.

::

    cp gtrial <test-directory>

    cd <test-directory> && trial

If you're writing a conventional Qt application and just want twisted as
an addon, you can get that by calling reactor.runReturn() instead of
run(). This call needs to occur after your installation of of the
reactor and after QApplication.exec\_() (or QCoreApplication.exec\_()
whichever you are using.

reactor.run() will also work as expected in a typical twisted
application

Note that if a QApplication or QCoreApplication instance isn't
constructed prior to calling reactor run, an internally owned
QCoreApplication is created and destroyed. This won't work if you call
runReturn instead of run unless you take responsibility for destroying
QCoreApplication yourself...

However, most users want this reactor to do gui stuff so this shouldn't
be an issue.

Performance impact of Qt has been reduced by minimizing use of signaling
which is expensive.

Examples / tests in ghtTests

"""

import os
from setuptools import setup
from glob import glob

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: X11 Applications :: Qt',
    'Framework :: Twisted',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Natural Language :: English',
    'Topic :: Software Development :: Libraries :: Python Modules'
]

setup(
    name='qt4reactor',
    version='1.6.dev1',
    license='MIT',
    classifiers=classifiers,
    author='Glenn H. Tarbox',
    author_email='glenn@tarbox.org',
    description='Twisted Qt Integration',
    long_description=read('README.rst'),
    url='https://github.com/ghtdak/qtreactor',
    download_url='https://github.com/ghtdak/qtreactor/tarball/master/#egg-qt4reactor.1.6.dev.1',
    scripts=glob("./bin/*"),
    py_modules=['qt4reactor'],
    keywords=['Qt', 'twisted'],
    install_requires=['twisted']

)

