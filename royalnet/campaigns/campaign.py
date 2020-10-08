from __future__ import annotations
from royalnet.typing import *
import logging
import inspect
import datetime
from .challenge import Challenge, TrueChallenge
from .exc import *
log = logging.getLogger(__name__)

__all__ = (
    "Campaign",
)


class Campaign:
    """
    The Campaign module allows for branching generator-based back-and-forths between the software and the
    user.

    A Campaign consists of multiple chained Adventures, which are Generators yielding tuples with a Campaign and
    optional data.
    """

    def __init__(self, start: Adventure, *args, **kwargs):
        """
        Initialize a Campaign object.

        .. warning:: Do not use this, use the Campaign.create() method instead!

        :param start: The starting adventure for the Campaign.
        """
        self.adventure: Adventure = start
        self.challenge: Challenge = TrueChallenge()
        self.last_update: datetime.datetime = ...

    @classmethod
    def create(cls, start: Adventure, *args, **kwargs) -> Tuple[Campaign, ...]:
        """
        Create a new Campaign object.

        :param start: The starting Adventure for the Campaign.
        :return: A tuple containing the created Campaign and optionally a list of extra output.
        """
        campaign = cls(start=start, *args, **kwargs)
        output = campaign.next()
        return campaign, *output

    def next(self, data: Any = None) -> List:
        """
        Try to advance the Campaign with the passed data.

        :param data: The data to pass to the current Adventure.
        :return: Optional additional data returned by the Adventure.
        :raises ChallengeFailedError: if the data passed fails the Challenge check.
        """
        self.last_update = datetime.datetime.now()
        if not self.challenge.filter(data):
            raise ChallengeFailedError(f"{data} failed the {self.challenge} challenge")
        result = self.adventure.send(data)
        if inspect.isgenerator(result):
            self.adventure.close()
            self.adventure = result
            return self.next(data)
        elif isinstance(result, Challenge):
            self.challenge = result
            return []
        elif result is None:
            return []
        elif isinstance(result, tuple) and len(result) > 0:
            if isinstance(result[0], Challenge):
                self.challenge, *output = result
                return output
            elif result[0] is None:
                _, *output = result
                return output
        else:
            raise TypeError(f"Adventure yielded an invalid type: {result.__class_}")
