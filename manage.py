from flask.cli import FlaskGroup
from app import app, db
from models import User
import click

cli = FlaskGroup(app)

@cli.command("create-user")
@click.option('--username', prompt='Username', help='The username of the user')
@click.option('--email', prompt='Email', help='The email address of the user')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password of the user')
@click.option('--admin', is_flag=True, help='Make this user an administrator')
def create_user(username, email, password, admin):
    """Create a new user."""
    user = User(
        username=username,
        email=email,
        is_admin=admin,
        is_active=True
    )
    user.set_password(password)
    
    db.session.add(user)
    try:
        db.session.commit()
        click.echo(f'Successfully created {"admin" if admin else "user"}: {username}')
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error creating user: {e}', err=True)

@cli.command("list-users")
def list_users():
    """List all users."""
    users = User.query.all()
    if not users:
        click.echo('No users found.')
        return
    
    click.echo('\nUsers:')
    for user in users:
        click.echo(f'- {user.username} ({"admin" if user.is_admin else "user"}) - {user.email}')

@cli.command("delete-user")
@click.argument('username')
def delete_user(username):
    """Delete a user by username."""
    user = User.query.filter_by(username=username).first()
    if not user:
        click.echo(f'User {username} not found.')
        return
    
    if click.confirm(f'Are you sure you want to delete user {username}?'):
        db.session.delete(user)
        try:
            db.session.commit()
            click.echo(f'Successfully deleted user: {username}')
        except Exception as e:
            db.session.rollback()
            click.echo(f'Error deleting user: {e}', err=True)

if __name__ == '__main__':
    cli()
