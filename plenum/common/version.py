from typing import Tuple, Iterable, Union
from abc import abstractmethod, ABCMeta
import collections
from packaging.version import (
    Version as PEP440Version,
    InvalidVersion as PEP440InvalidVersion
)


class InvalidVersion(ValueError):
    pass


class VersionBase(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def cmp(cls, v1: 'VersionBase', v2: 'VersionBase') -> int:
        """ Compares two instances. """

    @property
    @abstractmethod
    def full(self) -> str:
        """ Full version string. """

    @property
    @abstractmethod
    def parts(self) -> Iterable:
        """ Full version as iterable. """

    @property
    @abstractmethod
    def release(self) -> str:
        """ Release part string. """

    @property
    @abstractmethod
    def release_parts(self) -> Iterable:
        """ Release part as iterable. """

    def __lt__(self, other: 'VersionBase') -> bool:
        return self.cmp(self, other) < 0

    def __gt__(self, other: 'VersionBase') -> bool:
        return self.cmp(self, other) > 0

    def __eq__(self, other: 'VersionBase') -> bool:
        return self.cmp(self, other) == 0

    def __le__(self, other: 'VersionBase') -> bool:
        return self.cmp(self, other) <= 0

    def __ge__(self, other: 'VersionBase') -> bool:
        return self.cmp(self, other) >= 0

    def __ne__(self, other: 'VersionBase') -> bool:
        return self.cmp(self, other) != 0


class PackageVersion(VersionBase):
    @property
    @abstractmethod
    def upstream(self) -> str:
        """ Upstream part of the package. """


class SourceVersion(VersionBase):
    pass


class SemVerBase(VersionBase):
    @property
    def major(self) -> str:
        return self.release_parts[0]

    @property
    def minor(self) -> str:
        return self.release_parts[1]

    @property
    def patch(self) -> str:
        return self.release_parts[2]


# TODO tests
class PEP440BasedVersion(VersionBase):

    @classmethod
    def cmp(cls, v1: 'PEP440BasedVersion', v2: 'PEP440BasedVersion') -> int:
        if v1._version > v2._version:
            return 1
        elif v1._version == v2._version:
            return 0
        else:
            return -1

    def __init__(self, version: str, allow_non_stripped: bool = True):
        if not allow_non_stripped and version != version.strip():
            raise InvalidVersion('version includes leading and/or trailing spaces')

        try:
            self._version = PEP440Version(version)
        except PEP440InvalidVersion as exc:
            # TODO is it the best string to pass
            raise InvalidVersion(str(exc))

        # TODO create API wrappers for dev, pre and post from PEP440Version

    @property
    def public(self) -> str:
        return self._version.public

    @property
    def full(self) -> str:
        res = self._version.public
        if self._version.local:
            res += "+{}".format(self._version.local)
        return res

    @property
    def parts(self) -> Iterable:
        # TODO
        #   - API for add_parts
        add_parts = tuple()
        if self._version.is_devrelease:
            add_parts = ('dev', self._version.dev)
        elif self._version.is_prerelease:
            add_parts = self._version.pre
        elif self._version.is_postrelease:
            add_parts = ('dev', self._version.post)
        return (
            self._version.epoch,
            *self.release_parts,
            *add_parts,
            self._version.local
        )

    @property
    def release(self) -> str:
        return '.'.join(map(str, self.release_parts))

    @property
    def release_parts(self) -> Iterable:
        return self._version.release


# TODO tests
class DigitDotVersion(PEP440BasedVersion):
    def __init__(
            self,
            version: str,
            parts_num: Union[None, int, Iterable[int]]=None,
            **kwargs
    ):
        super().__init__(version, **kwargs)
        # additional restrictions
        if (self._version.is_devrelease or
                self._version.is_prerelease or
                self._version.is_postrelease or
                self._version.epoch or
                self._version.local):
            raise InvalidVersion("only dots and digits are expected")
        if parts_num:
            # TODO docs for typing doesn't specify explicitly whether
            # typing.Iterable can be used instead or not
            if not isinstance(parts_num, collections.abc.Iterable):
                parts_num = [parts_num]
            if len(self.parts) not in parts_num:
                raise InvalidVersion(
                    "invalid number of parts {}, should contain {}"
                    .format(len(self.parts), ' or '.join(map(str, parts_num)))
                )

    @property
    def parts(self) -> Iterable:
        return self._version.release


# TODO allows (silently normalizes) leading zeroes in parts
class SemVerReleaseVersion(DigitDotVersion, SemVerBase):
    def __init__(self, version: str, **kwargs):
        super().__init__(version, parts_num=3, **kwargs)
