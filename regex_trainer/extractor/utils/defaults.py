USELESS_TAG = ['style', 'script', 'link', 'video', 'iframe', 'source', 'picture', 'header']

# if one tag in the follow list does not contain any child node nor content, it could be removed
TAGS_CAN_BE_REMOVE_IF_EMPTY = ['section', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span']

USELESS_ATTR = ['share', 'contribution', 'copyright', 'disclaimer', 'recommend', 'related', 'footer', 'comment', 'social', 'submeta']

IMAGE_SEP = "@#"

#to genernate a correct image xpath
BETTER_CONTENT_NODE_REMOVE_TAG = ["strong","font","i"]

USEFUL_ATTR = ("align","width","height")

TITLE_GUESS_XPATH = '//h1//text() | //h2//text() | //h3//text() | //h4//text() | //h5//text()'

VIDEO_GUESS_XPATH = "//video/@src"

CONTENT_TAG = 'p'
