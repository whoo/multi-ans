from __future__ import division  # Use floating point for math calculations

import math

from flask import Blueprint,session

from CTFd.models import Challenges, Solves, db, Flags, Fails,Awards,Submissions,Users
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from CTFd.utils.modes import get_model
from CTFd.utils.user import get_ip



class MultipleChallenge(Challenges):
#    __mapper_args__ = {"polymorphic_identity": "dynamic"}
    id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True
    )

    def __init__(self, *args, **kwargs):
        super(MultipleChallenge, self).__init__(**kwargs)
        self.initial = kwargs["value"]


class MultipleValueChallenge(BaseChallenge):
    id = "multiple"  # Unique identifier used to register challenges
    name = "multiple"  # Name of a challenge type
    templates = {  # Handlebars templates used for each aspect of challenge editing & viewing
        "create": "/plugins/multi-ans/assets/create.html",
        "update": "/plugins/multi-ans/assets/update.html",
        "view": "/plugins/multi-ans/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/multi-ans/assets/create.js",
        "update": "/plugins/multi-ans/assets/update.js",
        "view": "/plugins/multi-ans/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/multi-ans/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        "multi-ans",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )
    challenge_model = MultipleChallenge


    @classmethod
    def read(cls, challenge):
        """
        This method is in used to access the data of a challenge in a format processable by the front end.

        :param challenge:
        :return: Challenge object, data dictionary to be returned to the user
        """
        challenge = MultipleChallenge.query.filter_by(id=challenge.id).first()
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "description": challenge.description,
            "category": challenge.category,
            "state": "visible",
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "type_data": {
                "id": cls.id,
                "name": cls.name,
                "templates": cls.templates,
                "scripts": cls.scripts,
            },
        }
        return data

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
        for attr, value in data.items():
            setattr(challenge, attr, value)
        db.session.commit()

        return challenge

    @classmethod
    def solve(cls, user, team, challenge, request):
        print(f"Sove {user} {team}")
        #super().solve(user, team, challenge, request)  // Do not Solve for MultiAnswser

        data = request.form or request.get_json()
        submission = data["submission"].strip()
        solve = Fails(
            user_id=user.id,
            team_id=team.id if team else None,
            challenge_id=challenge.id,
            ip=get_ip(req=request),
            type="correct",
            provided=submission,
        )

        db.session.add(solve)
        db.session.commit()



    @staticmethod
    def attempt(chal,request):
        print(f"Essai ::: {chal.id} {chal.type}")
        data = request.form or request.get_json()
        submission = data["submission"].strip()
        flags =     Flags.query.filter_by(challenge_id=chal.id).all()

        
        team = Users.query.filter_by(id=1).first()
        sub = Submissions.query.filter_by(
                        challenge_id=chal.id , 
                        provided=submission, 
                        team_id=team.id if team else None
                        ).all()
        if (len(sub)>0):
           return False, "Duplicate"

        print(f"{session['id']}")
        print(f"Keys {chal.value}")
        for flag in flags:
            try:
                print(f">> {flag.data} {flag.content}")
                if (flag.content==submission):
                   award = Awards(
                   user_id=session['id'],
                   team_id=team.id if team else None,
                   name=chal.name,
                   description="test",
                   value=chal.value,
                   category = chal.category,
                   icon="crosshairs"
                   )
                   db.session.add(award)
                   db.session.commit()
                   return True,"Bingo"
            except:
                e = sys.exc_info()[0]
                print(e)
                return False, 'Error'

        award = Awards( 
              user_id=session['id'], 
              team_id=team.id if team else None,
              name=chal.name,
              description="test", 
              value=chal.value*-1, 
              icon="skull",
              category = chal.category
              )
              
        db.session.add(award)
        db.session.commit()
        return False, f"Incorrect ( -{chal.value})"
        


def load(app):
    CHALLENGE_CLASSES["multiple"] = MultipleValueChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/multi-ans/assets/"
    )
