import setuptools

package_name = 'ddb'
prog_name = 'ddb'

setuptools.setup(
  name=package_name,
  version='0.0',
  # Code included in the final package
  packages=[package_name],
  # Runtime dependencies. Test dependencies are specified in tox.ini
  install_requires=['boto3'],
  entry_points={
    'console_scripts': [
      '{prog}={package}:main'.format(prog=prog_name, package=package_name)
    ]
  }
)
