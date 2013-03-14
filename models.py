"""Models used by the application.

Author: Dan Albert <dan@gingerhq.net>
"""
from google.appengine.ext import ndb
from google.appengine.api import users


class Character(ndb.Model):
    """A D20 character."""
    name = ndb.StringProperty("Character name", default="New Character")
    owner = ndb.UserProperty("")

    strength = ndb.IntegerProperty()
    dexterity = ndb.IntegerProperty()
    constitution = ndb.IntegerProperty()
    intelligence = ndb.IntegerProperty()
    wisdom = ndb.IntegerProperty()
    charisma = ndb.IntegerProperty()

    base_attack_bonus = ndb.IntegerProperty()
    fortitue = ndb.IntegerProperty()
    reflex = ndb.IntegerProperty()
    will = ndb.IntegerProperty()

    classes = ndb.PickleProperty("Serialized dictionary of the character's" +
                               "classes")
    skills = ndb.PickleProperty("Serialized dictionary of the character's" +
                               "skils")
    feats = ndb.StringProperty("List of the character's feats", repeated=True)
    spells = ndb.StringProperty("List of the character's spells", repeated=True)

    def __unicode__(self):
        return self.name
