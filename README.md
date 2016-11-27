# cpdk
Control Plane Development Kit

Nobody likes coding schemas.

## Major Development Tasks for 1.0
- [x] DB: Recurse through models and create schema using sqlalchemy
- [ ] DB: Schema Migrations (update, roll-back, etc)
- [x] CLI: Recurse through models and generate classes for cmd.Cmd
- [x] CLI: Create RedShell daemon & process CLI commands
- [ ] CLI: Tab completion for show commands
- [ ] CLI: Tab completion for delete commands
- [ ] CLI: Type verification
- [ ] CLI: Support for boolean parameters
- [ ] CLI: Support for non-db commands (arp cache, intefaces, etc)
- [ ] CLI: Use cmd2 module and add support for color!
- [x] CPP: Generate C++ header files for models
- [ ] CPDKd: Process daemon notifications
- [x] CPDKd: Handle initial load requests from daemons
- [ ] Support for message versions