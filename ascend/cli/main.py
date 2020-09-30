from ascend.client import Client
from ascend.resource_definitions import ResourceSession
from ascend.cli import cli, global_values
from ascend.cli import sh
from ascend import credentials

import contextlib
import subprocess
import sys
import traceback
import yaml

recursive_flag = cli.Flag("--recursive", "-r", default=None, required=False, action="store_true",
                          help="include children objects")
directory_flag = cli.Flag("--directory", "-d", default=None, required=False, action="store_true",
                          help="create a directory structure for resources, otherwise all "
                               "resources will be integrated together. Requires output flag to be "
                               "set")
output_flag = cli.Flag("--output", "-o", default=None, required=False,
                       help="output filesystem path, otherwise will go to stdout")
input_flag = cli.Flag("--input", "-i", default=None, required=False,
                      help="input file or directory path")
host_flag = cli.FlagOrEnv("--host", "-H", envvars=("ASCEND_HOST",), default=None, required=False,
                          help="Example: `--host trial.ascend.io`")
resource_flag = cli.Flag("resource", help="resource path to use, "
                                          "Example: `my_data_service.my_dataflow`")
config_flag = cli.Flag("--config", help="yaml file to render resource definitions with jinja. "
                                        "Will be namespaced under `config`")
delete_flag = cli.Flag("--delete", "-d", default=None, required=False, action="store_true",
                       help="Delete resources in Ascend that do not exist in the resource "
                            "definition")
credentials_flag = cli.Flag("--credentials",
                            help="(Deprecated) Override component credentials file to use")

dry_run_flag = cli.Flag("--dry-run", default=False, action="store_true",
                        help="Do not run commands against API (can cause premature failures)")


class FailureHandler(contextlib.AbstractContextManager):
    def __init__(self, name):
        self.name = name

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return
        else:
            traceback.print_exception(exc_type, exc_val, exc_tb)
            if isinstance(exc_val, KeyError):
                sh.die(f"Resource does not exist: {exc_val}")
            else:
                sh.die(f"Unable to {self.name} resource definition(s): {exc_val}")


@cli.command_from_block
class app:

    name = "ascend",

    help = "CLI over the Ascend Python SDK used for resource operations"

    plugins = [cli.debug_flag_plugin]
    subcommands = []

    @plugins.append
    @cli.plugin_from_block
    class ascend_plugin:

        name = "ascend"

        def context_gen(args):
            try:
                yield
            except (sh.DieException, subprocess.CalledProcessError) as e:
                sys.stderr.write(sh.color_for.error(f"FATAL: {e!s}\n"))
                sys.exit(1)

    @subcommands.append
    @cli.command_from_block
    class get:
        plugins = [
            recursive_flag,
            directory_flag,
            output_flag,
            host_flag,
            resource_flag,
        ]

        def action(args):
            # Argument validation
            if args.directory and not args.output:
                sh.die("Unable to output to a directory without the output flag (-o).")
                return

            with FailureHandler('get'):
                client = Client.build(hostname=args.host)
                rs = ResourceSession(client, client.get_session())
                rs.get(args.resource, args)


    @subcommands.append
    @cli.command_from_block
    class apply:
        plugins = [
            host_flag,
            recursive_flag,
            input_flag,
            delete_flag,
            config_flag,
            credentials_flag,
            resource_flag,
            dry_run_flag,
        ]

        def action(args):
            with FailureHandler('apply'):
                client = Client.build(hostname=args.host)
                if args.config is not None:
                    config_file = args.config
                    try:
                        with open(config_file, 'r') as f:
                            args.config = yaml.load(f.read(), Loader=yaml.SafeLoader)
                    except Exception as e:
                        raise Exception(f'Failure to load config from {config_file}: {e}')
                else:
                    args.config = {}

                rs = ResourceSession(client, client.get_session())
                rs.apply(args.resource, {}, args)

    @subcommands.append
    @cli.command_from_block
    class delete:
        plugins = [
            recursive_flag,
            host_flag,
            resource_flag,
            dry_run_flag,
        ]

        def action(args):
            with FailureHandler('delete'):
                client = Client.build(hostname=args.host)
                rs = ResourceSession(client, client.get_session())
                rs.delete(args.resource, args)

    @subcommands.append
    @cli.command_from_block
    class list:
        plugins = [
            recursive_flag,
            host_flag,
            resource_flag,
        ]

        def action(args):
            with FailureHandler('list'):
                client = Client.build(hostname=args.host)
                rs = ResourceSession(client, client.get_session())
                rs.list(args.resource, args.recursive)


if __name__ == "__main__":
    app.main()
