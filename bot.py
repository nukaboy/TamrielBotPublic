import json
import os
import random
import sys
from cohost.models.user import User
from cohost.models.block import AttachmentBlock, MarkdownBlock
import random
import wget
from PIL import Image

# Definitions
PLACEFILE = "pages.json"
infostring = "<details>  <summary><sub>How to rate</sub></summary><p>To rate this place, comment your rating with the ⭐-emoji below. Ratings will be updated every fifteen minutes for recent posts, and a random comment may be featured on the post.</p></details>"

# Log in to project
fl = open("login").readlines()
user = fl[0].strip()
pw = fl[1].strip()

user = User.login(user, pw)
project = user.getProject("Tamriel")

# Load JSON of places
places = {}
places = json.load(open(PLACEFILE))

# Select a place
placeIndex = random.randint(0, len(places["places"]) - 1)
place = places["places"][placeIndex]

# There are so many Online entries, lets balance it out
if place["Game"] == "Online":
    placeIndex = random.randint(0, len(places["places"]) - 1)
    place = places["places"][placeIndex]

# Get values and do renamings where necessary
title = place["Title"]
name = place["Name"]
game = place["Game"]
description = place["Desc"]
imageURL = place["ImageURL"]
URL = place["URL"]

if game == "Online":
    game = "elder scrolls online"

# Debugging
print(title)

# Debugging
if not "-dry" in sys.argv:

    # Download image
    image = wget.download(imageURL)

    # Make sure image is jpg, remove old image
    with Image.open(image) as im:
        im.convert("RGB").save("nextImage.jpg", "JPEG")
    os.remove(image)

    # Make post
    blocks = [
        AttachmentBlock(
            "nextImage.jpg",
            alt_text="This content is licensed under the ​Creative Commons by-sa license (http://creativecommons.org/licenses/by-sa/2.5/). It is taken from "
            + URL,
        ),
        MarkdownBlock(
            description + "\n\n0 Visitors rated this place\n\n\n" + infostring
        ),
    ]

    newPost = project.post(
        name,
        blocks,
        tags=[
            "cohost.py",
            "elder scrolls",
            "The Elder Scrolls",
            "tamriel",
            "bot",
            game,
        ],
    )

    # place place in list for posted places
    places["places"].remove(place)
    place["posted"] = True
    places["donePlaces"].append(place)
    with open(PLACEFILE, "w+") as cj:
        json.dump(places, cj)
