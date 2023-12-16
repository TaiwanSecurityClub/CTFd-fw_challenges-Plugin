import json

from flask import Blueprint

from CTFd.models import Challenges, db
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from CTFd.plugins.migrations import upgrade
from CTFd.plugins.fw_challenges import EndpointLog, Cheater


class FwChallenge(Challenges):
    __tablename__ = "fwChallenge"
    __mapper_args__ = {"polymorphic_identity": "fwstandard"}
    id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True
    )
    endpoints = db.Column(db.JSON, default=[])

    def __init__(self, *args, **kwargs):
        super(FwChallenge, self).__init__(**kwargs)


class FwCheckChallenge(BaseChallenge):
    id = "fwstandard"  # Unique identifier used to register challenges
    name = "fwstandard"  # Name of a challenge type
    templates = {  # Handlebars templates used for each aspect of challenge editing & viewing
        "create": "/plugins/fw_challenges/fw_challenges/assets/create.html",
        "update": "/plugins/fw_challenges/fw_challenges/assets/update.html",
        "view": "/plugins/fw_challenges/fw_challenges/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/fw_challenges/fw_challenges/assets/create.js",
        "update": "/plugins/fw_challenges/fw_challenges/assets/update.js",
        "view": "/plugins/fw_challenges/fw_challenges/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/fw_challenges/fw_challenges/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        "fw_challenges",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )
    challenge_model = FwChallenge

    @classmethod
    def create(cls, request):
        """
        This method is used to process the challenge creation request.

        :param request:
        :return:
        """
        data = request.form or request.get_json()
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
        challenge = FwChallenge.query.filter_by(id=challenge.id).first()
        data = super()read(cls, challenge).update({
            "endpoints": challenge.endpoints,
        })
        return data

    @classmethod
    def solve(cls, user, team, challenge, request):
        super().solve(user, team, challenge, request)
        challenge = FwChallenge.query.filter_by(id=challenge.id).first()
        try:
            for endpoint in challenge.endpoints:
                EndpointLog.query.filter_by(user.id, endpoint).one()
        except:
            try:
                Cheater.query.filter_by(user.id, challenge.id).one()
            except:
                db.session.add(Cheater(user.id, challenge.id))
                db.session.commit()

def load(app):
    upgrade(plugin_name="fw_challenges")
    CHALLENGE_CLASSES["fwstandard"] = FwCheckChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/fw_challenges/fw_challenges/assets/"
    )
