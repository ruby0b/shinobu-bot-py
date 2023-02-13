

empty_cache = object()


def async_cached_property(async_getter):
    cached = empty_cache

    @property
    async def async_property(self):
        nonlocal cached
        if cached is empty_cache:
            cached = await async_getter(self)
        return cached

    return async_property
