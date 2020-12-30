# Module docstring
"""

"""

# Special imports
from __future__ import annotations
import royalnet.royaltyping as t

# External imports
import logging
import re

# Internal imports
from . import conversation as c
from . import sentry as s
from . import bullet as b

# Special global objects
log = logging.getLogger(__name__)


# Code
class Command(c.Conversation):
    """
    A Command is a :class:`~.c.Conversation` which is started by a :class:`~.b.Message` having a text matching
    the :attr:`.pattern`; the named capture groups of the pattern are then passed as keyword arguments to :attr:`.f`.
    """

    def __init__(self, f: c.ConversationProtocol, *, name: str, pattern: re.Pattern):
        super().__init__(f)

        self.name: str = name
        """
        The name of the command, as a :class:`str`.
        """

        self.pattern: re.Pattern = pattern
        """
        The pattern that should be matched by the command.
        """

    async def run(self, *, _sentry: s.Sentry, **base_kwargs) -> t.Optional[c.ConversationProtocol]:
        log.debug(f"Awaiting a bullet...")
        bullet: b.Bullet = await _sentry

        log.debug(f"Received: {bullet!r}")

        log.debug(f"Ensuring a message was received: {bullet!r}")
        if not isinstance(bullet, b.Message):
            log.debug(f"Returning: {bullet!r} is not a message")
            return

        log.debug(f"Getting message text of: {bullet!r}")
        if not (text := await bullet.text()):
            log.debug(f"Returning: {bullet!r} has no text")
            return

        log.debug(f"Searching for pattern: {text!r}")
        if not (match := self.pattern.search(text)):
            log.debug(f"Returning: Couldn't find pattern in {text!r}")
            return

        log.debug(f"Match successful, getting capture groups of: {match!r}")
        message_kwargs: t.Dict[str, str] = match.groupdict()
        
        log.debug(f"Passing args to function: {message_kwargs!r}")
        return await super().run(_sentry=_sentry, **base_kwargs, **message_kwargs)

    def help(self) -> t.Optional[str]:
        """
        Get help about this command. This defaults to returning the docstring of :field:`.f` .

        :return: The help :class:`str` for this command, or :data:`None` if the command has no docstring.
        """
        return self.f.__doc__

    def __repr__(self):
        return f"<{self.__class__.__qualname__}: {self.name}>"


class PartialCommand:
    """
    A PartialCommand is a :class:`.Command` having an unknown :attr:`~.Command.pattern` at the moment of creation.

    The pattern can specified later using :meth:`.complete`.
    """
    def __init__(self, f: c.ConversationProtocol, name: str, syntax: str):
        self.f: c.ConversationProtocol = f
        """
        The function to pass to :attr:`.c.Conversation.f`.
        """

        if not self.name.isalnum():
            raise ValueError("Name should be alphanumeric")
        if not self.name.islower():
            raise ValueError("Name should be lowercase")

        self.name: str = name
        """
        The name of the command to pass to :attr`.Command.name`. Should be lowercase and containing only alphanumeric 
        characters.
        """

        self.syntax: str = syntax
        """
        Part of the pattern from where the arguments should be captured.
        """

    @classmethod
    def new(cls, *args, **kwargs):
        """
        A decorator that instantiates a new :class:`Conversation` object using the decorated function.

        :return: The created :class:`Conversation` object.
                 It can still be called in the same way as the previous function!
        """
        def decorator(f: c.ConversationProtocol):
            partial_command = cls(f=f, *args, **kwargs)
            log.debug(f"Created: {partial_command!r}")
        return decorator

    def complete(self, pattern: str) -> Command:
        """
        Complete the PartialCommand with a pattern, creating a :class:`Command` object.

        :param pattern: The pattern to add to the PartialCommand. It is first :meth:`str.format`\\ ted with the keyword
                        arguments ``name=self.name, syntax=self.syntax`` and later :func:`re.compile`\\ d.
        :return: The complete :class:`Command`.
        """
        pattern: re.Pattern = re.compile(pattern.format(name=self.name, syntax=self.syntax))
        return Command(f=self.f, name=self.name, pattern=pattern)

    def __repr__(self):
        return f"<{self.__class__.__qualname__}: {self.name}>"


# Objects exported by this module
__all__ = (
    "Command",
    "PartialCommand",
)
