# *-* coding: utf-8 -*-
from fabric.api import env, local

## Git settings
env.repo_root = local("dirname `git rev-parse --git-dir`").strip()


def dbshell(**kwargs):
    """Run the project's tests"""
    _run_django_command('dbshell', **kwargs)


def runserver(**kwargs):
    """Run the project's own HTTP server"""
    _run_django_command('runserver', **kwargs)


def runtests(**kwargs):
    """Run the project's development server"""
    kwargs['settings'] = 'test'
    _run_django_command('test', **kwargs)


def syncdb(**kwargs):
    """Run the database synchronization"""
    _run_django_command('syncdb', **kwargs)

def shell(**kwargs):
    """Run the ipython shell with the Django settings"""
    _run_django_command('shell', **kwargs)

def _run_django_command(command, **kwargs):
    """Run Django's manage.py command"""
    if command not in ('runserver', 'test', 'dbshell', 'syncdb', 'shell'):
        raise ValueError("Invalid command")

    env.settings = kwargs.get('settings', 'devel')
    apps = kwargs.get('apps', '') if command == 'test' else ''

    local('python "%s/project/manage.py" %s %s '
        '--settings=settings.%s' % (
            env.repo_root, command, apps, env.settings),
        capture = False,
    )
