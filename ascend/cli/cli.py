"""Utilities for quickly creating new nestable command line interfaces.

Example usage:

```

from ascend.cli import cli

@cli.command_from_block
class hello:

  def action(args):
    print('Hello world!')

@cli.command_from_block
class add:

  plugins = [
    cli.Flag('first', type=int),
    cli.Flag('second', type=int),
  ]

  def action(args):
    print(f'The result of {args.first} + {args.second} = {args.first+args.second}')

app = cli.Branch(
  name='my-app',
  subcommands=[hello, add],
  help='''
  Usage:
    ./my-app hello  # 'Hello world!'
    ./my-app add 82 3  # 'The result of 82 + 3 = 85'
  '''
)

if __name__ == '__main__':
  app.main()

```


"""
from ascend.cli import global_values
from ascend.cli import sh
import abc
import argparse
import contextlib
import os


class Plugin(object):
  def init(self, parser: argparse.ArgumentParser):
    """
    Initialize the parser with any desired flags.
    """

  def context_gen(self, args):
    """
    Generator that describes the Context manager to use when running the command.

    context_gen should be implemented as a generator that can be passed to
    contextlib.contextmanager to create a context manager.

    This is for executing arbitrary code before and after the body of a command is run.
    """
    yield

  @contextlib.contextmanager
  def context_manager(self, args):
    yield from self.context_gen(args)


class BlockPlugin(Plugin):
  def __init__(self, init, context_gen):
    self._init = init
    self._context_gen = context_gen

  def init(self, parser):
    if self._init is not None:
      return self._init(parser)

  def context_gen(self, args):
    if self._context_gen is not None:
      yield from self._context_gen(args)


def plugin_from_block(cls):
  return BlockPlugin(
      init=cls.init if hasattr(cls, 'init') else None,
      context_gen=cls.context_gen if cls.context_gen else None,
  )


class InitParserPlugin(Plugin):
  def __init__(self, f):
    self.f = f

  def init(self, parser):
    self.f(parser)


class ContextPlugin(Plugin):
  """Convenience Plugin subclass for creating a plugin from a generator
  """

  def __init__(self, generator_func):
    self.generator_func = generator_func

  def init(self, parser):
    pass

  def context_gen(self, args):
    yield from self.generator_func(args)


class Flag(Plugin):
  """Convenience Plugin subclass for setting flags.
  """

  def __init__(self, *args, **kwargs):
    self.args = args
    self.kwargs = kwargs

  def init(self, parser: argparse.ArgumentParser):
    parser.add_argument(*self.args, **self.kwargs)

  def context_gen(self, args):
    yield


class FlagOrEnv(Plugin):
  """Convenience Plugin subclass for declaring a flag that may get its value from an
  environment variable.
  """

  def __init__(self, *args, envvars, **kwargs):
    self.args = args
    self.kwargs = kwargs
    self.envvars = tuple(envvars)

  def init(self, parser: argparse.ArgumentParser):
    self.dest = parser.add_argument(*self.args, **self.kwargs).dest


  def context_gen(self, args):
    if getattr(args, self.dest) is None:
      for envvar in self.envvars:
        if os.getenv(envvar) is not None:
          setattr(args, self.dest, os.getenv(envvar))
          break
      else:
        if self.envvars:
          sh.die_stackless(
              f'Either flag {self.dest} must be supplied or one of the environment variables '
              f"{', '.join(self.envvars)} must be set")
        else:
          sh.die_stackless(f'Flag {self.dest} must be supplied')
    yield


class DebugFlagPlugin(Plugin):
  """Plugin that adds a --debug flag to the command, automatically setting or unsetting
  the DEBUG flag.
  """

  def init(self, parser: argparse.ArgumentParser):
    parser.add_argument('--debug', dest='debug', action='store_true')
    parser.add_argument('--nodebug', dest='debug', action='store_false')
    parser.set_defaults(debug=False)

  def context_gen(self, args):
    global_values.DEBUG = args.debug
    sh.debug(f'DEBUG = {args.debug}')
    yield


debug_flag_plugin = DebugFlagPlugin()


class Command(abc.ABC):
  def __init__(self, name, *, aliases=(), help=None, plugins=()):
    self.name = name
    self.aliases = tuple(aliases)
    self.help = help
    self.plugins = plugins

  def run(self, args):
    """
    The method that actual runs this Command. This method should not be overriden.
    To override behavior, subclasses should implement '_call'.
    """
    with contextlib.ExitStack() as stack:
      for plugin in self.plugins:
        stack.enter_context(plugin.context_manager(args))
      return self._call(args)

  @abc.abstractmethod
  def _call(self, args):
    """
    The method that defines the actual running behavior of this command.
    To actually run this command, the method 'run' should be preferred.
    """

  def _init_parser(self, parser: argparse.ArgumentParser):
    """
    Initializes the given parser for this command.

    Prefer using 'make_parser' instead when appropriate.
    """
    for plugin in self.plugins:
      plugin.init(parser)

  def _make_subparser(self, subparsers):
    """
    Creates a new parser that is a subparser of another argparse parser.

    Should really only need to be used by _init_parser.
    """
    parser = subparsers.add_parser(self.name, aliases=self.aliases,
                                   help=self.help, formatter_class=argparse.RawTextHelpFormatter)
    self._init_parser(parser)
    return parser

  def make_parser(self):
    """
    Creates a top level parser for this command.
    """
    parser = argparse.ArgumentParser(
        prog=self.name, description=self.help, formatter_class=argparse.RawTextHelpFormatter)
    self._init_parser(parser)
    return parser

  @sh.handle
  def main(self, arglist=None):
    """
    Run this Command like it's main
    """
    return self.run(self.make_parser().parse_args(args=arglist))


class Branch(Command):
  """A Branch is a command that is composed of other subcommands."""

  def __init__(self, *args, subcommands, **kwargs):
    super().__init__(*args, **kwargs)
    self.subcommands = tuple(subcommands)
    self._command_table = dict()

    for subcommand in self.subcommands:
      for name in {subcommand.name} | set(subcommand.aliases):
        if name in self._command_table:
          raise ValueError(f'Duplicate subcommand name {name}')
      for name in {subcommand.name} | set(subcommand.aliases):
        self._command_table[name] = subcommand

  def _subparser_command_dest(self):
    return f'_cli_Branch_command_for_{self.name}_{id(self)}'

  def _call(self, args):
    return self._command_table[getattr(args, self._subparser_command_dest())].run(args)

  def _init_parser(self, parser: argparse.ArgumentParser):
    super()._init_parser(parser)
    subparsers = parser.add_subparsers(
        title=self.name,
        description=self.help,
        dest=self._subparser_command_dest(),
    )
    subparsers.required = True
    for subcommand in self.subcommands:
      subcommand._make_subparser(subparsers)


class Leaf(Command):
  """A Leaf is a Command that performs a single action."""

  def __init__(self, *args, action, **kwargs):
    super().__init__(*args, **kwargs)
    self.action = action
    if not callable(action):
      raise TypeError(f'Command action must be callable but got {action!r}')

  def _call(self, args):
    return self.action(args)


def command_from_block(cls):
  """Convenience decorator for creating a Command instance from a class block.

  If the given class block defines a 'subcommands' member, this function will return a
  Branch command.

  If the given class block defines an 'action' member, this function will return a
  Leaf command.

  If the given class block defines both 'subcommands' and 'action', this function will
  throw an exception.
  """
  name = cls.name if hasattr(cls, 'name') else cls.__name__
  aliases = cls.aliases if hasattr(cls, 'aliases') else ()
  doc = cls.help if hasattr(cls, 'help') else cls.__doc__

  plugins = list(cls.plugins) if hasattr(cls, 'plugins') else []
  if hasattr(cls, 'init_parser'):
    plugins.append(InitParserPlugin(cls.init_parser))

  type_ = None
  if hasattr(cls, 'subcommands') and cls.subcommands is not None:
    type_ = Branch
    kwargs = {'subcommands': cls.subcommands}

  if hasattr(cls, 'action') and cls.action is not None:
    if type_ is not None:
      raise TypeError(
          'class block passed to command_from_block cannot have both "action" and "subcommands" '
          'field defined',
      )
    type_ = Leaf
    kwargs = {'action': cls.action}

  if type_ is None:
    raise TypeError("At least one of 'subcommands' or 'action' must be supplied")

  return type_(name=name, aliases=aliases, help=doc, plugins=plugins, **kwargs)
