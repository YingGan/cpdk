# cpdk
Control Plane Development Kit

Nobody likes coding schemas.

## Tasks for 0.1
- [x] DB: Recurse through models and create schema using sqlalchemy
- [x] CLI: Recurse through models and generate classes for cmd.Cmd
- [x] CLI: Create RedShell daemon & process CLI commands
- [x] CLI: Type verification (int, long, float, string)
- [x] CLI: Support for boolean parameters (negation commands)
- [x] CLI: Support for non-db commands (arp cache, intefaces, etc)
- [x] CPP: Generate C++ header files for models
- [x] CPDKd: Process daemon notifications
- [x] CPDKd: Handle initial load requests from daemons
- [ ] Test: RedShell unit tests (create, delete, list, modify)
- [ ] Docs: Write them!
- [ ] Github: README.md

## Tasks for 0.2
- [ ] DB: Schema Migrations (update, roll-back, etc)
- [ ] Support for message versions

## Tasks for 0.25
- [ ] CLI: Add SSH support to RedShell
- [ ] CLI: Command help

## Tasks for 0.3
- [ ] CLI: Tab completion for show commands (ex: show Server <tab>)
- [ ] CLI: Tab completion for delete commands (ex: delete Server <tab>)
- [ ] CLI: Support for parameters in quotes ex: delete Server "My Server"
- [ ] CLI: Command to show/save/delete/load configuration

## Tasks for 0.4
- [ ] CLI: Use cmd2 module and add support for color!
- [ ] REST API

## Tasks for 0.5
- [ ] CPDKd redundancy channel