# CommandRegistry.py -- Shine commands registry
# Copyright (C) 2007, 2009 CEA
#
# This file is part of shine
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# $Id$

# Base command class definition
from Base.Command import Command

# Import list of enabled commands (defined in the module __init__.py)
from Shine.Commands import commandList

from Exceptions import *


# ----------------------------------------------------------------------
# Command Registry
# ----------------------------------------------------------------------


class CommandRegistry:
    """Container object to deal with commands."""

    def __init__(self):
        self.cmd_list = []
        self.cmd_dict = {}
        self.cmd_optargs = {}

        # Autoload commands
        self._load()

    def __len__(self):
        "Return the number of commands."
        return len(self.cmd_list)

    def __iter__(self):
        "Iterate over available commands."
        for cmd in self.cmd_list:
            yield cmd

    # Private methods

    def _load(self):
        for cmdobj in commandList:
            self.register(cmdobj())

    # Public methods

    def get(self, name):
        return self.cmd_dict[name]

    def register(self, cmd):
        "Register a new command."
        assert isinstance(cmd, Command)

        self.cmd_list.append(cmd)
        self.cmd_dict[cmd.get_name()] = cmd

        # Keep an eye on ALL option arguments, this is to insure a global
        # options coherency within shine and allow us to intermix options and
        # command -- see execute() below.
        opt_len = len(cmd.getopt_string)
        for i in range(0, opt_len):
            c = cmd.getopt_string[i]
            if c == ':':
                continue
            has_arg = not (i == opt_len - 1) and (cmd.getopt_string[i+1] == ':')
            if c in self.cmd_optargs:
                assert self.cmd_optargs[c] == has_arg, "Incoherency in option arguments"
            else:
                self.cmd_optargs[c] = has_arg 

    def execute(self, args):
        """
        Execute a shine script command.
        """
        # Get command and options. Options and command may be intermixed.
        command = None
        new_args = []
        try:
            # Find command through options...
            next_is_arg = False
            for opt in args:
                if opt.startswith('-'):
                    new_args.append(opt)
                    next_is_arg = self.cmd_optargs[opt[-1:]]
                elif next_is_arg:
                    new_args.append(opt)
                    next_is_arg = False
                else:
                    if command:
                        # Command has already been found, so?
                        if command.has_subcommand():
                            # The command supports subcommand: keep it in new_args.
                            new_args.append(opt)
                        else:
                            raise CommandHelpException("Syntax error.", command)
                    else:
                        command = self.get(opt)
                    next_is_arg = False
        except KeyError, e:
            raise CommandNotFoundError(opt)

        # Parse
        command.parse(new_args)

        # Execute
        return command.execute()

