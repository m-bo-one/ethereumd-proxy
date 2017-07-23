import os
import sys
import click
from daemonize import Daemonize

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
        settings['config_path'] = datadir
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


@click.command(context_settings=CONTEXT_SETTINGS)
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
@click.option('-pid', metavar='<file>',
              default='ethereum.pid',
              help='Specify pid file (default: ethereum.pid)',
              callback=_refine_pid)
def cli(conf, daemon, datadir, pid):
    """Ethereum Core proxy to geth node."""
    if daemon:
        try:
            server = RPCServer(**conf)
        except ConnectionRefusedError:
            click.echo('Error: geth node not started yet. Abort.')
            sys.exit(1)

        daemon = Daemonize(app="ethereumd_proxy", pid=pid, action=server.run)
        daemon.start()
        click.echo('Ethereum proxy server starting')
        sys.exit(0)
    sys.exit(1)


if __name__ == '__main__':
    cli()


# TODO:
# 1) Add -daemon command for starting server;
# 2) Add -stop command for stoping server;
# 3) Add "command" execution from cli;
