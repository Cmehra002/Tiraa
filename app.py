import eventlet
eventlet.monkey_patch()

from project import app, db

def create_database():
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    create_database()
    app.run(debug=True, use_reloader=False)
