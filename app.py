# coding=utf-8

from StringIO import StringIO
import os

from cachetools.func import rr_cache
from flask import Flask, jsonify
from flask_cors import CORS
from mercantile import Tile
from PIL import Image
from werkzeug.wsgi import DispatcherMiddleware

from tiler import InvalidTileRequest, read_tile


APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT', '')

app = Flask('oam-tiler')
CORS(app)
app.config['APPLICATION_ROOT'] = APPLICATION_ROOT


@app.errorhandler(InvalidTileRequest)
def handle_invalid_tile_request(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(IOError)
def handle_ioerror(error):
    return '', 404


@rr_cache()
@app.route('/<id>/<int:z>/<int:x>/<int:y>.png')
def get_tile(id, z, x, y):
    im = Image.new("RGBA", (256, 256), None)
    # TODO try using multiprocessing for this
    for id in ("57fc935b84ae75bb00ec751b", "57fc988f84ae75bb00ec751d"):
        try:
            tile = read_tile(id, Tile(x, y, z))
            im.paste(tile)
        except InvalidTileRequest:
            pass

    out = StringIO()
    im.save(out, 'png')

    return out.getvalue(), 200, {
        'Content-Type': 'image/png'
    }


@rr_cache()
@app.route('/<id>/<int:z>/<int:x>/<int:y>@<int:scale>x.png')
def get_scaled_tile(id, z, x, y, scale):
    tile = read_tile(id, Tile(x, y, z), scale=scale)

    return tile, 200, {
        'Content-Type': 'image/png'
    }


app.wsgi_app = DispatcherMiddleware(None, {
    app.config['APPLICATION_ROOT']: app.wsgi_app
})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
