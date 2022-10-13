import collections


class InheritMapMixin:
    """Adds :py:class:`collections.ChainMap` class attributes based on MRO.

    The added class attributes provide each subclass with its own mapping that
    works just like method resolution: each ancestor type in ``__mro__`` is
    visited until an entry is found in the ancestor-owned map.

    For example, for an inheritance DAG of ``InheritMapMixin`` <- ``Foo`` <-
    ``Bar`` <- ``Baz`` and a desired attribute name of ``"_m"``:

    1. ``Foo._m`` is set to ``ChainMap({})``.
    2. ``Bar._m`` is set to ``ChainMap({}, Foo._m.maps[0])``.
    3. ``Baz._m`` is set to ``ChainMap({}, Bar._m.maps[0], Foo._m.maps[0])``.
    """

    @classmethod
    def __init_subclass__(cls, *, inherit_map_attrs=None, **kwargs):
        """Adds :py:class:`collections.ChainMap` class attributes based on MRO.

        :param inherit_map_attrs:
            Optional iterable of names of class attributes that will be set to a
            :py:class:`collections.ChainMap` containing the MRO-based list of
            ancestor maps.
        """
        super().__init_subclass__(**kwargs)
        attrs = getattr(cls, "_inherit_map_attrs", set())
        if inherit_map_attrs:
            attrs = {*attrs, *inherit_map_attrs}
            cls._inherit_map_attrs = attrs
        for attr in attrs:
            maps = [{}]  # maps[0] is for cls itself.
            for c in cls.__mro__[1:]:  # cls.__mro__[0] is cls itself.
                if (
                        issubclass(c, InheritMapMixin) and
                        c is not InheritMapMixin and
                        attr in getattr(c, "_inherit_map_attrs", set())
                ):
                    maps.append(getattr(c, attr).maps[0])
            setattr(cls, attr, collections.ChainMap(*maps))
