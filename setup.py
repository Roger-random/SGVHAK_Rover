from setuptools import setup

setup(
	name='SGVHAK_Rover',
	packages=['SGVHAK_Rover'],
	include_package_data=True,
	install_requires=[
                'adafruit-pca9685',
		'flask',
		'pyserial'],
	)
