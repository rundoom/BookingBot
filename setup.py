from distutils.core import setup

setup(
    name='Bookbot',
    version='0.1',
    author='Dmitry Borisov',
    python_requires=">=3.6.*",
    entry_points={
        'console_scripts': [
            'bookbot = bookbot.bookingbot:main'
        ]
    }
)
