"""User level routines for the pyfcctab suite"""

def find_bands(bands, frequency=None):
    candidates = []
    if frequency is not None:
        for b in bands:
            if b.bounds[0] <= frequency and b.bounds[1] > frequency:
                candidates.append(b)
    return candidates
