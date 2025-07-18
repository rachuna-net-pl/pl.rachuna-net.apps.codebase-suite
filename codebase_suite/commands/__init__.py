import click
import shutil

from ..core import Context

from .gitlab import gitlab
from .terraform import terraform

print('''
                                                                                                                
                                                                                                            
██████╗  █████╗  ██████╗██╗  ██╗██╗   ██╗███╗   ██╗ █████╗       ███╗   ██╗███████╗████████╗██████╗ ██╗       
██╔══██╗██╔══██╗██╔════╝██║  ██║██║   ██║████╗  ██║██╔══██╗      ████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██║       
██████╔╝███████║██║     ███████║██║   ██║██╔██╗ ██║███████║█████╗██╔██╗ ██║█████╗     ██║   ██████╔╝██║       
██╔══██╗██╔══██║██║     ██╔══██║██║   ██║██║╚██╗██║██╔══██║╚════╝██║╚██╗██║██╔══╝     ██║   ██╔═══╝ ██║       
██║  ██║██║  ██║╚██████╗██║  ██║╚██████╔╝██║ ╚████║██║  ██║      ██║ ╚████║███████╗   ██║██╗██║     ███████╗  
╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝      ╚═╝  ╚═══╝╚══════╝   ╚═╝╚═╝╚═╝     ╚══════╝  
                                                                                                            
    
''')

@click.group(context_settings={'show_default': True})
@click.option('-v','--verbose', count=True, help='Enable verbose output')
@click.option('--no-color', is_flag=True, help='Disable colored output')
@click.pass_context
def commands(ctx: click.Context, verbose, no_color):
    """
    Narzędzie wspomagające devops w codziennej pracy
    """
    ctx.obj = Context(verbose, not no_color)
    
    columns = 150 if shutil.get_terminal_size().columns == None else shutil.get_terminal_size().columns
    ctx.max_content_width=columns

commands.add_command(gitlab)
commands.add_command(terraform)