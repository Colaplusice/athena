from flask_script import Manager, Shell

from app import create_app

app = create_app()
manager = Manager(app)

manager.add_command("shell", Shell())
if __name__ == "__main__":
    manager.run()
