# cpdk
Control Plane Development Kit

Nobody likes coding schemas.

## Major Development Tasks for 1.0
- [x] DB: Recurse through models and create schema using sqlalchemy
- [x] CLI: Recurse through models and generate classes for cmd.Cmd
- [x] CLI: Create RedShell daemon & process CLI commands
- [ ] CLI: Tab completion for show commands
- [ ] CLI: Tab completion for delete commands
- [ ] CLI: Type verification
- [ ] CLI: Support for boolean parameters
- [ ] CLI: Use cmd2 module and add support for color!
- [ ] CPP: Generate CPP/H files for models
- [ ] CPDKd: Process daemon notifications
- [ ] CPDKd: Handle initial load requests from daemons