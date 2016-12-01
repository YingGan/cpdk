# Control Plane Development Kit (CPDK)
#### Because nobody likes coding schemas. 

[![Build Status](https://travis-ci.org/zimventures/cpdk.svg?branch=TravisCL)](https://travis-ci.org/zimventures/cpdk)
[![Documentation Status](https://readthedocs.org/projects/cpdk/badge/?version=latest)](http://cpdk.readthedocs.io/en/latest/?badge=latest)

## What is CPDK?
The Control Plane Development Kit (CPDK) is a collection of utilities and applications which allows developers
to quickly, and painlessly, integrate control plane functionality into their application. 

The high level architecture of CPDK is shown in the following diagram:
![CPDK Architecture](https://github.com/zimventures/cpdk/blob/master/docs/topology.PNG "CPDK Architecture")

## Batteries Included
- Python-based database schema declaration
- Automatically generated CLI (easily customizable)
- Automatically generated C++ classes (for use in your daemons)

## Quickstart Guide
1. Within models directory create a .py file
2. Inside your models file, define classes and fields for schema
3. Run cpdk-util.py --exportcpp (generates header files)
4. Create your C++ classes, inheriting from CPDK generated ones and overriding appropriate methods
5. Run cpdk-util.py --syncdb (generates database schema)
6. Run cpdk-util.py --buildcli (generates CLI)
7. Run python CPDKd.py (starts CPDK daemon)
8. Run python redshell.py (starts CLI)
9. Run your daemon
10. Dance. Dance like nobody is watching.

## Roadmap
See the 'issues' section for future releases and planned features. 

## Author
CPDK was designed and developed by Rob Zimmerman in 2016. See the [CONTRIBUTORS](https://github.com/zimventures/cpdk/blob/master/docs/CONTRIBUTORS.md) file for more credits. 

## License
This project is licensed under the MIT License - see the [LICENSE](https://github.com/zimventures/cpdk/blob/master/docs/LICENSE) file for details. 

## Acknowledgements
A special hat-tip goes to the following projects, who's work helped speed CPDK's development immeasurably.

- [SQLAlchemy](http://www.sqlalchemy.org/)
- [json](https://github.com/nlohmann/json)
- [ZeroMQ](http://zeromq.org/)
- [Python!](https://www.python.org/)
