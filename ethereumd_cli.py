import os
import sys
import signal
import json
from collections import Mapping

import requests
import click

from ethereumd.proxy.base import ProxyMethod
from ethereumd_proxy import RPCServer


CONTEXT_SETTINGS = dict(help_option_names=['-h', '-help'])


def read_config_file(filename: str) -> {}:
    """
    Read a simple ``'='``-delimited config file.
    Raises :const:`IOError` if unable to open file, or :const:`ValueError`
    if an parse error occurs.
    """
    f = open(filename)
    try:
        cfg = {}
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    (key, value) = line.split('=', 1)
                    cfg[key] = value
                except ValueError:
                    pass  # Happens when line has no '=', ignore
    finally:
        f.close()
    return cfg


def _refine_datadir(ctx, param, value):
    return os.path.realpath(value)


def _refine_conf(ctx, param, value):
    datadir = ctx.params['datadir']
    if value == param.default:
        value = os.path.join(datadir, value)
    elif os.path.isabs(value):
        value = os.path.realpath(value)

    try:
        settings = read_config_file(value)
    except FileNotFoundError:
        click.echo('%s not found.' % value)
        sys.exit(1)
    else:
        if 'ipcconnect' in settings:
            settings['ipcconnect'] = os.path.join(datadir,
                                                  settings['ipcconnect'])

    return settings


def _refine_pid(ctx, param, value):
    datadir = ctx.params['datadir']
    if value == param.default:
        return os.path.join(datadir, value)
    elif os.path.abspath(value):
        return os.path.realpath(value)
    return value


def check_if_server_runned(pid_file):
    try:
        with open(pid_file, "r") as fpid:
            pid = int(fpid.read())
    except (OSError, AttributeError):
        return

    try:
        os.kill(pid, 0)
    except OSError:
        return
    else:
        click.echo('Error: etereumd proxy already runned.')
        sys.exit(1)


def setup_server(config):
    try:
        return RPCServer(**config)
    except FileNotFoundError:
        click.echo('Error: unix socket not found. Is it geth started?')
    except ConnectionRefusedError:
        click.echo('Error: geth node not started yet. Abort.')

    sys.exit(1)


class AliasedGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        method = getattr(ProxyMethod, cmd_name, None)
        if method:
            return self._dynamic_rpc_cmd(ctx, method, cmd_name)
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))

    def _dynamic_rpc_cmd(self, ctx, method, cmd_name):
        @cli.command()
        @click.argument('params', nargs=-1, type=click.UNPROCESSED)
        @click.pass_context
        def _rpc_result(ctx, params):
            conf = ctx.parent.params['conf']
            try:
                response = requests.post(
                    'http://%s:%s' % (conf['ethpconnect'], conf['ethpport']),
                    data=json.dumps({
                        'id': 'ethereum-cli',
                        'method': cmd_name,
                        'params': params,
                    })
                )
            except requests.exceptions.ConnectionError:
                click.echo('error: couldn\'t connect to server: '
                           'unknown (code -1)')
                click.echo('(make sure server is running and you are '
                           'connecting to the correct RPC port)')
                return
            else:
                response = response.json()
                if response['error']:
                    error = response['error']
                    click.echo('error code: %s' % error['code'])
                    if error['code'] == -1:
                        click.echo('error message:\n%s' % method.__doc__)
                    else:
                        click.echo('error message:\n%s' % error['message'])
                    sys.exit(1)
                else:
                    result = response['result']
                    if isinstance(result, Mapping):
                        result = json.dumps(response['result'], indent=4)
                    elif isinstance(result, bool):
                        result = 'true' if result else 'false'
                    click.echo(result)
        return click.Group.get_command(self, ctx, '_rpc_result')


@click.command(context_settings=CONTEXT_SETTINGS, invoke_without_command=True,
               cls=AliasedGroup)
@click.option('-datadir', metavar='<dir>',
              type=click.Path(exists=True, allow_dash=True),
              required=True,
              help='Specify data directory',
              callback=_refine_datadir)
@click.option('-conf', metavar='<file>',
              default='ethereum.conf',
              help='Specify configuration file (default: ethereum.conf)',
              callback=_refine_conf)
@click.option('-daemon',
              is_flag=True,
              help='Run in the background as a daemon and accept commands')
@click.option('-pid', 'pid_file', metavar='<file>',
              default='ethereum.pid',
              help='Specify pid file (default: ethereum.pid)',
              callback=_refine_pid)
@click.pass_context
def cli(ctx, conf, daemon, datadir, pid_file):
    """Ethereum Core proxy to geth node."""
    os.chdir(datadir)
    if daemon and ctx.invoked_subcommand is None:
        check_if_server_runned(pid_file)
        pid = os.fork()
        if pid == 0:
            server = setup_server(conf)
            try:
                with open(pid_file, "w") as fpid:
                    fpid.write(str(os.getpid()))
            except OSError:
                click.echo('Error: can\'nt store pid, abort.')
                sys.exit(1)
            click.echo('Ethereum proxy server starting')
            try:
                server.run()
            except Exception:
                os.remove(pid_file)
    elif ctx.invoked_subcommand is None:
        check_if_server_runned(pid_file)
        setup_server(conf).run()


@cli.command(help='Stop ethereumd proxy server')
@click.pass_context
def stop(ctx):
    pid_file = ctx.parent.params['pid_file']
    try:
        with open(pid_file, "r") as fpid:
            pid = int(fpid.read())
    except OSError as e:
        click.echo('Error: etereumd proxy not runned yet.')
        sys.exit(1)
    except AttributeError:
        click.echo('Error: invalid pid.')
        sys.exit(1)

    try:
        os.kill(int(pid), signal.SIGTERM)
    except OSError:
        click.echo('Error: etereumd proxy was already stoped.')
        sys.exit(1)
    finally:
        os.remove(pid_file)

    click.echo('Ethereum proxy server stoping.')


if __name__ == '__main__':
    cli()


# TODO:
# ~1) Add -daemon command for starting server;
# ~2) Add -stop command for stoping server;
# 3) Add "command" execution from cli;
