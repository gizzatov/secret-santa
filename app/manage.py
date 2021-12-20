import os
import pty
from typing import Optional

import typer

from santa_bot.app import run_app

app = typer.Typer()


@app.command(help="Run app")
def run(devserver: Optional[bool] = typer.Option(False)):
    typer.echo("Run app")
    run_app(devserver=devserver)


@app.command(help="Apply migrations")
def migrate():
    output_bytes = []

    def read(fd):
        data = os.read(fd, 1024)
        output_bytes.append(data)
        return data

    pty.spawn(['aerich', 'upgrade'], read)


@app.command(help="Make migrations")
def makemigrations(message: str):
    output_bytes = []

    def read(fd):
        data = os.read(fd, 1024)
        output_bytes.append(data)
        return data

    pty.spawn(['aerich', 'migrate', '--name', message], read)


@app.command(help="Run shell")
def shell():
    banner = 'Blockchain shell'

    try:
        import IPython
        from traitlets.config import Config
        c = Config()
        c.InteractiveShellApp.exec_lines = [
            "from termcolor import colored",
            "from santa_bot.db import init_db; print(colored('- init_db imported', 'blue'))",
            "await init_db(); print(colored('- database connection have inited', 'blue'))",
            "print(colored('Blockchain shell is ready!', 'green'))",
        ]
        IPython.start_ipython(config=c, argv=[])
    except ImportError:
        import code
        code.interact(banner, local={})


if __name__ == "__main__":
    app()
