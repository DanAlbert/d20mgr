"""Models used by the application.

Author: Dan Albert <dan@gingerhq.net>
"""
from google.appengine.ext import ndb
from google.appengine.api import users


class Character(ndb.Model):
    """A D20 character."""
    name = ndb.StringProperty("Character name", default="New Character")
    owner = ndb.UserProperty("")

    strength = ndb.IntegerProperty(default=10)
    dexterity = ndb.IntegerProperty(default=10)
    constitution = ndb.IntegerProperty(default=10)
    intelligence = ndb.IntegerProperty(default=10)
    wisdom = ndb.IntegerProperty(default=10)
    charisma = ndb.IntegerProperty(default=10)

    base_attack_bonus = ndb.IntegerProperty(default=10)
    fortitue = ndb.IntegerProperty(default=10)
    reflex = ndb.IntegerProperty(default=10)
    will = ndb.IntegerProperty(default=10)

    classes = ndb.PickleProperty("Serialized dictionary of the character's" +
                               "classes")
    skills = ndb.PickleProperty("Serialized dictionary of the character's" +
                               "skils")
    feats = ndb.StringProperty("List of the character's feats", repeated=True)
    spells = ndb.StringProperty("List of the character's spells", repeated=True)

    def __unicode__(self):
        return self.name
