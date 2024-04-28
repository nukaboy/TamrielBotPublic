import json
import random
import re

from cohost.models.user import User
from cohost.models.block import AttachmentBlock, MarkdownBlock
from cohost.network import generate_login_cookies
import random
import requests

# Definitions
infostring = "<details>  <summary><sub>How to rate</sub></summary><p>To rate this place, comment your rating with the ⭐-emoji below. Ratings will be updated every fifteen minutes for recent posts, and a random comment may be featured on the post.</p></details>"
# updateComment = "-comment" in sys.argv TODO

# Read login data
fl = open("login").readlines()
user = fl[0].strip()
pw = fl[1].strip()

# Log in to project
user = User.login(user, pw)
project = user.getProject("Tamriel")

# Get last posts (three pages)
lastPosts = (
    list(project.getPosts(0)) + list(project.getPosts(1)) + list(project.getPosts(2))
)

# For each post...
for p in lastPosts:
    blocks = []
    updateP = False

    # Get blocks
    for b in p.blocks:

        # Markdown block
        if b["type"] == "markdown" and "⭐" in b["markdown"]["content"]:

            # Get html page of post. We need to be logged in to get comments from private pages
            resp = requests.get(
                p.url,
                cookies=generate_login_cookies(user.cookie),
                headers={"User-Agent": "cohost.py"},
            )
            resp.encoding = "utf-8"
            resp = resp.text

            # Find the json block with the comments
            comments = re.findall(r"\"comments\":.*?(?=},\"dataUpdateCount\")", resp)
            comments = json.loads("{" + comments[0] + "}")
            commentList = {}

            # For each comment add it to our comment list
            for cpost in comments["comments"]:
                for comment in comments["comments"][cpost]:
                    commentList[comment["poster"]["handle"]] = comment["comment"][
                        "body"
                    ]
            # Calculate ratings
            totalRating = 0
            ratingCount = 0
            for c in commentList:
                r = commentList[c].count("⭐")
                if r > 0:
                    ratingCount += 1
                    totalRating += r

            # Update the post only if we have at least one rating
            if ratingCount > 0:
                updateP = True
                rating = totalRating / ratingCount

                # Get lines
                lines = b["markdown"]["content"].split("\n")

                # Select featured comment
                dr = random.choice(list(commentList.keys()))
                displayedRating = '"' + commentList[dr] + '" - @' + dr

                # Get description
                descr = lines[0]

                rstr = "⭐" * int(rating)
                textblock = MarkdownBlock(
                    descr
                    + "\n\n"
                    + str(ratingCount)
                    + " Visitors rated this place "
                    + rstr
                    + "\n"
                    + displayedRating
                    + "\n\n\n"
                    + infostring
                )
                blocks.append(textblock)
            else:
                blocks.append(MarkdownBlock(b["markdown"]["content"]))

        # Keep the image as-is. Note that you can't let the filepath be empty, but the image will still stay the same as specified by attachment_id.
        elif b["type"] == "attachment":
            blocks.append(
                AttachmentBlock(
                    filepath="nextImage.jpg",
                    attachment_id=b["attachment"]["attachmentId"],
                    alt_text=b["attachment"]["altText"],
                )
            )
    if updateP:

        # Debug
        print("updating " + str(p.url))

        # do the edit
        p.edit(p.headline, blocks, p.contentWarnings, p.tags).url
