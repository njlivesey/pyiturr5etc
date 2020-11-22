"""Handles keeping track of changes to the FCC tables document"""


class Version(object):
    """A store for version-specific information on the FCC tables"""

    def __init__(self, date):
        """Initialize the Version information from the database"""
        self.page_patches = database["page_patches_" + date]
        self.layouts = database["layouts_" + date]

    def patch_page(self, page):
        """Provide a correct page number for a page where the right answer is hard to find"""
        return self.page_patches.get(page, page)

    def get_layout(self, page, row=0):
        entry = self.layouts[page]
        clauses = entry.split(",")
        layouts = []
        for c in clauses:
            words = c.strip().split("*")
            if len(words) == 1:
                count = 1
            elif len(words) == 2:
                count = int(words[1])
            else:
                raise ValueError(f"Badly formatted layout {entry}")
            for i in range(count):
                layouts.append(words[0])
        return layouts[min(row, len(layouts) - 1)]


database = dict()

database["page_patches_20200818"] = {
    "International Table": "Page 5",
    "NG527A": "Page 52",
    "Flexible Use (30)": "Page 54",
}

database["layouts_20200818"] = {
    "Page 1": "012357/9",
    "Page 2": "023467/8",
    "Page 3": "012345/6",
    "Page 4": "012345/6",
    "Page 5": "012356/7",  # Messy
    "Page 6": "011234/5",
    "Page 7": "013467/8",  # Messy
    "Page 8": "013456/7",
    "Page 9": "023467/8",
    "Page 10": "012345/6",
    "Page 11": "012356/7",
    "Page 12": "011234/5",
    "Page 13": "013468/9",
    "Page 14": "000123/4",
    "Page 15": "012356/7",
    "Page 16": "012345/6",
    "Page 17": "012345/6",
    "Page 18": "012345/6",
    "Page 19": "034567/8",
    "Page 20": "023456/7",
    "Page 21": "012345/6",
    "Page 22": "012356/7",
    "Page 23": "012345/6",
    "Page 24": "012345/6",
    "Page 25": "012345/6",
    "Page 26": "000134/5",
    "Page 27": "012356/7",
    "Page 28": "012345/6",
    "Page 29": "012345/6",
    "Page 30": "012345/6",
    "Page 31": "012356/7",
    # Page 32 is tacked on to 31
    "Page 33": "023467/8",
    "Page 34": "023445/6",
    "Page 35": "012356/7",
    "Page 36": "012345/6",
    "Page 37": "012345/6",
    "Page 38": "011234/5",
    "Page 39": "012345/7*3, 023456/7*4, 012346/7",
    "Page 40": "023456/8*5, 024567/8",
    "Page 41": "012345/6",
    # Page 42 is tacked on to 41
    "Page 43": "024678/9",
    # Page 44 is tacked on to 43
    "Page 45": "012345/6",
    "Page 46": "000123/4",
    "Page 47": "012345/6",
    "Page 48": "012345/6",
    "Page 49": "012345/6",
    "Page 50": "012345/6",
    "Page 51": "023456/7",
    "Page 52": "012345/7",
    "Page 53": "012345/6",
    "Page 54": "012345/6",
    "Page 55": "012345/6",
    "Page 56": "012345/6",
    "Page 57": "012345/6",
    "Page 58": "012345/6",
    "Page 59": "012345/6",
    "Page 60": "011234/5",
    "Page 61": "012345/6",
    "Page 62": "000123/4",
    "Page 63": "012345/6",
    "Page 64": "000123/4",
    "Page 65": "012345/6",
    "Page 66": "000112/3",
    "Page 67": "012345/6",
    "Page 68": "000123/5",
}
