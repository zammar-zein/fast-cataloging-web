def normalize(raw: str) -> str:
    """Return a validated ISBN-13, converting from ISBN-10 if needed.

    Raises ValueError for anything that isn't a real ISBN.
    """
    s = raw.replace("-", "").replace(" ", "").upper()

    if len(s) == 13 and s.isdigit():
        if _sum13(s) % 10 != 0:
            raise ValueError(f"not a valid ISBN: {raw!r}")
        return s

    if len(s) == 10:
        total = 0
        for i, ch in enumerate(s):
            if ch == "X" and i == 9:
                digit = 10
            elif ch.isdigit():
                digit = int(ch)
            else:
                raise ValueError(f"not a valid ISBN: {raw!r}")
            total += (10 - i) * digit
        if total % 11 != 0:
            raise ValueError(f"not a valid ISBN: {raw!r}")

        core = "978" + s[:9]
        check = (10 - _sum13(core) % 10) % 10
        return core + str(check)

    raise ValueError(f"not a valid ISBN: {raw!r}")


def _sum13(digits: str) -> int:
    """Weighted sum behind the ISBN-13 check digit (weights 1,3,1,3,...)."""
    return sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
