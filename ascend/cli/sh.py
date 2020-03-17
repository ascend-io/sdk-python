from ascend.cli import global_values
from functools import wraps

import asyncio
import contextlib
import datetime
import functools
import importlib
import inspect
import os
import subprocess
import sys
import threading
import traceback


# Caching lazy decorator
def cached_result(f):
  @wraps(f)
  def wrapper(*args, **kwargs):
    if not wrapper._has_run:
      wrapper._has_run = True
      wrapper._value = f(*args, **kwargs)
    return wrapper._value
  wrapper._has_run = False
  return wrapper


def handle(f):
  def wrapper(*args, **kwargs):
    try:
      f(*args, **kwargs)
    except DieStacklessException as e:
      error(str(e))

      if global_values.DEBUG:
        raise

      exit(1)
  return wrapper


def deprecated(reason):
  """Marks a given function or class as being deprecated"""
  assert isinstance(reason, str)

  def annotator(f):
    return f

  return annotator


# TODO: Figure out how to stream and still extract return value at the
# same time.
# TODO: Clean up this mess...
def call(command, stream=False, stdout=None, stderr=None):
  """Run a command in bash, and return the result of stdout
  If there is a non-zero exit code, throws subprocess.CalledProcessError

  If 'stream' is set, stdout from the shell command is written to real
  stdout instead of being returned as a string.
  """
  debug(f"sh.call({command!r}, stream={stream})")
  if stream:
    if stdout is not None or stderr is not None:
      raise ValueError(
          "You can't specify 'stdout' or stderr if stream is True")
    subprocess.run(command, shell=True, check=True)
  else:
    if stdout is None and stderr is None:
      try:
        run = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            executable='/bin/bash')
        return run.stdout.decode('utf-8')
      except subprocess.CalledProcessError as e:
        debug(f'Silent CalledProcessError exception e: {e.stderr}')
        raise
    else:
      out = subprocess.run(
          command,
          shell=True,
          stdout=stdout,
          stderr=stderr,
          check=True)
      return (None if out is None or out.stdout is None else out.stdout.decode('utf-8'))


def run(command):
  """Like call, but instead of returning a value, dumps the output to
  stdout and stderr.
  """
  return call(command, stream=True)


def check(command):
  """Run the command. If the command is successful return True otherwise, return False."""
  try:
    call(command)
    return True
  except subprocess.CalledProcessError:
    return False


class ShellThread(threading.Thread):

  def __init__(self, todo, name=None, daemon=False):
    super().__init__(name=name, daemon=daemon)
    self.todo = todo

  def run(self):
    self.todo()


def spawn(*args, **kwargs):
  thread = ShellThread(
      (lambda: call(*args, **kwargs)), name=kwargs.pop('name', None))
  thread.start()
  return thread


def prun(command):
  """Like run, but prints what the command is first"""
  info(f'prun: {command}')
  run(command)


def getenv(name, required=True):
  """Get environment variable"""
  value = os.environ.get(name)
  if required and not value:
    die(f"Required environment variable {name} not defined")
  return value


def getenvbool(name):
  return truthy(getenv(name, required=False))


def truthy(value):
  if isinstance(value, str):
    return value.upper() in ('TRUE', 'YES', 'T', 'Y')
  else:
    return bool(value)


def strict_truthy(value):
  if isinstance(value, str):
    if value.upper() in ('TRUE', 'YES', 'T', 'Y', '1'):
      return True
    elif value.upper() in ('FALSE', 'NO', 'F', 'N', '0'):
      return False
    else:
      raise ValueError(f'Could not deduce if {repr(value)} means "true" or "false"')
  elif isinstance(value, bool):
    return value
  elif value is None:
    return False
  else:
    raise TypeError(
        f'strict_truthy requires str, bool or None, but got '
        f'{type(value)} (value = {repr(value)})'
    )


def setenv(name, value):
  """Set an environment variable"""
  debug(f"sh.setenv({name!r}, {value!r})")
  os.environ[name] = value


@contextlib.contextmanager
def pushd(path):
  """Context manager that cd's into a directory, and restores cwd on exit"""
  cwd = os.getcwd()
  if global_values.DEBUG:
    debug(f'pushd -> {path}')
  os.chdir(path)
  yield
  if global_values.DEBUG:
    debug(f'popd -> {cwd}')
  os.chdir(cwd)


def simplify_path(path):
  return os.path.abspath(os.path.realpath(os.path.expanduser(path)))


def die(message):
  """Print an error message and die"""
  raise DieException(message)


def interactive_message(message):
  # We use `print` instead of `sh.info` because this method is used for interactive communication
  # with user. This flow is not supposed to be redirected to somewhere or hidden using logging level
  # configurations.
  print(message, flush=True)


def interactive_approve(message):
  while True:
    interactive_message(f'{message} (y/n) >>> ')
    res = {'y': True, 'yes': True, 'n': False, 'no': False}.get(input().strip().lower())
    if res is not None:
      return res


def interactive_option(message, options) -> int:
  while True:
    interactive_message(message)
    for idx, option in enumerate(options):
      interactive_message(f'  [{idx + 1}] {option}')
    interactive_message(f"Choose one option (type number) >>> ")
    try:
      result = int(input().strip()) - 1
      if 0 <= result and result < len(options):
        return result
    except ValueError:
      pass  # ignore


class DieException(Exception):

  def __init__(self, message):
    super(DieException, self).__init__(message)
    self.message = message

  def __str__(self):
    return self.message


def die_stackless(message):
  """Print an error message and die, and don't print stack trace"""
  raise DieStacklessException(message)


class DieStacklessException(Exception):

  def __init__(self, message):
    super(Exception, self).__init__(message)
    self.message = message

  def __str__(self):
    return str(self.message)


def debug(message):
  if global_values.DEBUG:
    sys.stderr.write(color_for.debug(f'DEBUG: {datetime.datetime.now()}: {message}\n'))


def info(message):
  sys.stderr.write(color_for.info(f'INFO: {message}\n'))


def print_exc_info(exc_info, file):
  if exc_info:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=file)


def warn(message, exc_info=False):
  sys.stderr.write(color_for.warn(f'WARN: {message}\n'))
  print_exc_info(exc_info, sys.stderr)


def error(message, exc_info=False):
  sys.stderr.write(color_for.error(f'ERROR: {message}\n'))
  print_exc_info(exc_info, sys.stderr)


def port_is_ready(port):
  """Uses lsof to see if anyone is listening on the given port
  """
  try:
    return 'LISTEN' in call(f'lsof -i:{port:d}')
  except subprocess.CalledProcessError:
    return False


class Color(object):
  def __init__(self, name, escape_sequence):
    self.name = name
    self.escape_sequence = escape_sequence

  def __call__(self, text):
    return self.escape_sequence + text + no_color.escape_sequence


no_color = Color('no_color', '\033[0m')
yellow = Color('yellow', '\033[1;33m')
red = Color('red', '\033[1;31m')
cyan = Color('cyan', '\033[1;36m')
green = Color('green', '\033[1;32m')


class color_for:
  debug = Color('debug', '\033[94m')
  info = Color('info', '\033[94m')
  warn = yellow
  error = red


# async


_loop = None


def _get_loop():
  global _loop
  if _loop is None:
    _loop = asyncio.get_event_loop()
  return _loop


def run_async(future):
  return _get_loop().run_until_complete(future)


def async_to_sync(f):
  """Converts an async function to a synchronous one.

  This is done by running all the asynchronous content in the current event loop.

  E.g.

  @async_to_sync
  async def foo():
    return await download_something()

  foo()  # No need to explicitly await here
  """
  @functools.wraps(f)
  def wrapper(*args, **kwargs):
    return run_async(f(*args, **kwargs))

  return wrapper

