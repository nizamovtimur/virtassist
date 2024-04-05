from config import app
import views


if __name__ == '__main__':
    app.run(host=app.config['ADMIN_PANEL_HOST'],
            port=app.config['ADMIN_PANEL_PORT'], debug=True)
