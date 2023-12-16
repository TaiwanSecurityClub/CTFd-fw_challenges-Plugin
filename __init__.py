import json
import flask

from CTFd.models import db
from CTFd.utils.decorators import authed_only,get_current_user
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.wireguard import WireguardDB
from CTFd.utils.user import get_ip

conf = None

class EndpointLog(db.Model):
    __tablename__ = "endpointLog"
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    userid = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    endpoint = db.Column(db.String(128))

    def __init__(self, userid, endpoint):
        self.userid = userid
        self.endpoint = endpoint

class Cheater(db.Model):
    __tablename__ = "cheater"
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    userid = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    challengesid = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE", onupdate="CASCADE")
    )

    def __init__(self, userid, challengesid):
        self.userid = userid
        self.challengesid = challengesid

def loadconfig():
    global conf
    dir_path = Path(__file__).parent.resolve()
    with open(os.path.join(dir_path, 'config.yaml')) as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)

def get_plugin_names():
    modules = sorted(glob.glob(os.path.dirname(__file__) + "/*"))
    blacklist = {"__pycache__"}
    plugins = []
    for module in modules:
        module_name = os.path.basename(module)
        if os.path.isdir(module) and module_name not in blacklist:
            plugins.append(module_name)
    return plugins

def load(app):
    app.db.create_all()

    if app.config.get("SAFE_MODE", False) is False:
        for plugin in get_plugin_names():
            module = "." + plugin
            module = importlib.import_module(module, package="CTFd.plugins.fw_challenges")
            module.load(app)
            print(" * Loaded fw_challenges module, %s" % module)
    else:
        print("SAFE_MODE is enabled. Skipping plugin loading.")
    
    @app.route('/plugins/fw_challenges/setlog',methods=['POST'])
    def setlog():
        ip = get_ip(req=request)
        if ip not in conf['accessips']:
            return
        data = request.get_json()
        userid = WireguardDB.query.filter_by(index=data['index']).first().userid
        try:
            EndpointLog.query.filter_by(userid, data['endpoint']).one()
        except:
            db.session.add(EndpointLog(userid, data['endpoint']))
            db.session.commit()
        return True

