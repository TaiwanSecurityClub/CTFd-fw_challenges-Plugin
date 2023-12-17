import json

from flask import Blueprint

from CTFd.models import Challenges, db
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from CTFd.plugins.dynamic_challenges import DynamicChallenge, DynamicValueChallenge
from CTFd.plugins.migrations import upgrade
from CTFd.plugins.fw_challenges import EndpointLog, Cheater

plugin_name = __name__.split('.')[-2]
challenge_name = __name__.split('.')[-1]

challenge_type = "fwdynamic"

class FwDynamicChallenge(DynamicChallenge):
    __tablename__ = "fw_dynamic_challenge"
    __mapper_args__ = {"polymorphic_identity": challenge_type}
    id = db.Column(
        db.Integer, db.ForeignKey("dynamic_challenge.id", ondelete="CASCADE"), primary_key=True
    )
    endpoints = db.Column(db.JSON, default=[])

    def __init__(self, *args, **kwargs):
        super(FwDynamicChallenge, self).__init__(**kwargs)


class FwCheckDynamicChallenge(DynamicValueChallenge):
    id = challenge_type  # Unique identifier used to register challenges
    name = challenge_type  # Name of a challenge type
    templates = {  # Handlebars templates used for each aspect of challenge editing & viewing
        "create": f"/plugins/{plugin_name}/{challenge_name}/assets/create.html",
        "update": f"/plugins/{plugin_name}/{challenge_name}/assets/update.html",
        "view": f"/plugins/{plugin_name}/{challenge_name}/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": f"/plugins/{plugin_name}/{challenge_name}/assets/create.js",
        "update": f"/plugins/{plugin_name}/{challenge_name}/assets/update.js",
        "view": f"/plugins/{plugin_name}/{challenge_name}/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = f"/plugins/{plugin_name}/{challenge_name}/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        challenge_name,
        __name__,
        template_folder="templates",
        static_folder="assets",
    )
    challenge_model = FwDynamicChallenge

    @classmethod
    def create(cls, request):
        """
        This method is used to process the challenge creation request.

        :param request:
        :return:
        """
        data = request.form or request.get_json()
        if 'endpoints' in data:
            data['endpoints'] = [ a.strip() for a in data['endpoints'].split(',') ]

        challenge = cls.challenge_model(**data)

        db.session.add(challenge)
        db.session.commit()

        return challenge

    @classmethod
    def update(cls, challenge, request):
        """
        This method is used to update the information associated with a challenge. This should be kept strictly to the
        Challenges table and any child tables.

        :param challenge:
        :param request:
        :return:
        """
        data = request.form or request.get_json()
        if 'endpoints' in data:
            data['endpoints'] = [ a.strip() for a in data['endpoints'].split(',') ]
        for attr, value in data.items():
            setattr(challenge, attr, value)

        db.session.commit()
        return challenge

    @classmethod
    def read(cls, challenge):
        """
        This method is in used to access the data of a challenge in a format processable by the front end.

       :param challenge:
        :return: Challenge object, data dictionary to be returned to the user
        """
        challenge = FwDynamicChallenge.query.filter_by(id=challenge.id).first()
        data = super().read(challenge)
        data.update({
            "endpoints": ','.join(challenge.endpoints),
        })
        return data

    @classmethod
    def solve(cls, user, team, challenge, request):
        super().solve(user, team, challenge, request)
        challenge = FwDynamicChallenge.query.filter_by(id=challenge.id).first()
        for endpoint in challenge.endpoints:
            try:
                EndpointLog.query.filter_by(userid=user.id, endpoint=endpoint).one()
                return
            except:
                pass

        try:
            Cheater.query.filter_by(userid=user.id, challengesid=challenge.id).one()
        except:
            db.session.add(Cheater(user.id, challenge.id))
            db.session.commit()

def load(app):
    CHALLENGE_CLASSES[challenge_type] = FwCheckDynamicChallenge
    register_plugin_assets_directory(
        app, base_path=f"/plugins/{plugin_name}/{challenge_name}/assets/"
    )
