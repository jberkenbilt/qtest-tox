This example illustrates basic use of dynamodb with testing. There are tox test environments for testing with an AWS account, moto, and dynamodb local. With moto, as of 1.0.1, conditional expressions still don't work.

In tox.ini, environment variables are used to set up the test environments. Based on the values of those variables, conftest.py, through a fixture, provides a working dynamodb environment and cleans up after it. The rest of the test code doesn't know or care about the environment except for setting up some tests as xfail with moto.

For using the "account" tox environment, you must have AWS configured and credentials set up for an AWS account. For the moto and local tests, no dependency on AWS configuration is present.

