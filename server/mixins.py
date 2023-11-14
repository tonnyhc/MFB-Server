class ChoicesEnumMixin:
    @classmethod
    def choices(cls):
        return [(x.name, x.value) for x in cls]
    @classmethod
    def max_len(cls):
        return max(len(choice[1]) for choice in cls.choices()) + 1  # +1 for safety margin