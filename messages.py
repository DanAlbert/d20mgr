"""Module for handling messages that need to be displayed to the user.

Author: Dan Albert <dan@gingerhq.net>
"""
class Messages:
    """Class that contains messages to be displayed to the user.
    
    Messages can be added at any time, and retrieving messages clears the list.
    This ensures that messages will only be displayed once.
    """
    messages = []
    
    @classmethod
    def add(cls, msg):
        cls.messages.append(msg)
    
    @classmethod
    def get(cls):
        msgs = cls.messages
        cls.messages = []
        return msgs
