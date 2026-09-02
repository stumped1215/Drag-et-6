import gzip
import base64

_DATA = (
    "SEE_LOCAL_FILE"
)
exec(gzip.decompress(base64.b64decode("".join(_DATA))), globals())
