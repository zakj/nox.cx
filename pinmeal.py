from collections import defaultdict

from flask import (Blueprint, abort, current_app as app, json, jsonify,
                   render_template, request)
import jsonschema

pinmeal = Blueprint('pinmeal', __name__)

# TODO: there's no authentication here at all, but do we really care?


# http://flask.pocoo.org/snippets/45/
def request_wants_json():
    best = request.accept_mimetypes.best_match(
        ['application/json', 'text/html'])
    return (
        best == 'application/json' and
        request.accept_mimetypes[best] > request.accept_mimetypes['text/html'])


class Spot(dict):
    ids_key = 'pinmeal:spots'
    spot_key = 'pinmeal:spots:%s'
    next_id_key = 'pinmeal:spots:next-id'
    good_for_options = frozenset(['lunch', 'dinner', 'drinks'])
    schema = {
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            'id': {'type': 'integer', 'minimum': 0, 'readonly': True},
            'name': {'type': 'string', 'required': True, 'minLength': 1},
            'visits': {
                'type': 'array',
                'uniqueItems': True,
                'items': {'type': 'string', 'format': 'date'},
            },
            'goodFor': {
                'type': 'array',
                'uniqueItems': True,
                'minItems': 1,
                'required': True,
                'items': {'type': 'string', 'enum': good_for_options},
            },
        },
    }
    validator = jsonschema.Draft3Validator(schema)

    @classmethod
    def all(cls, redis):
        "Return a list of all spots."
        p = redis.pipeline(transaction=False)
        for id in redis.smembers(cls.ids_key):
            p.get(cls.spot_key % id)
        return [cls(**json.loads(spot)) for spot in p.execute()]

    @classmethod
    def get(cls, redis, id):
        "Return the spot with given ID, or None if it does not exist."
        spot = None
        if redis.sismember(cls.ids_key, id):
            spot = cls(**json.loads(redis.get(cls.spot_key % id)))
        return spot

    def __init__(self, **kwargs):
        self._errors = None
        super(Spot, self).__init__(**kwargs)

    def is_valid(self):
        "Return whether the current spot is valid (validating if necessary)."
        return not bool(self.errors)

    @property
    def errors(self):
        "A (possibly empty) dict mapping field paths to a list of errors."
        if self._errors is None:
            self._errors = defaultdict(list)
            for error in self.validator.iter_errors(self):
                path = '.'.join(reversed(error.path))
                self._errors[path].append(error.message)
        return self._errors

    def save(self, redis):
        if self.errors:
            raise ValueError('invalid objects cannot be saved')
        # If we have a new object, create a key and be sure not to replace any
        # existing object.
        if not 'id' in self:
            self['id'] = redis.incr(self.next_id_key)
            redis.setnx(self.spot_key % self['id'], json.dumps(self))
            redis.sadd(self.ids_key, self['id'])
        # Otherwise just save over the existing object.
        else:
            redis.set(self.spot_key % self['id'], json.dumps(self))


@pinmeal.route('', methods=['GET', 'POST'])
def spots():
    if request.method == 'GET':
        spots = Spot.all(app.redis)
        if request_wants_json():
            return jsonify({'spots': spots})
        return render_template('pinmeal.html', spots=spots)
    else:
        spot = Spot(**request.json)
        if not spot.is_valid():
            response = jsonify({'errors': spot.errors})
            response.status_code = 422
            return response
        spot.save(app.redis)
        return jsonify(spot)


@pinmeal.route('/<id>', methods=['GET', 'PUT'])
def spot(id):
    spot = Spot.get(app.redis, id)
    if not spot:
        abort(404)
    if request.method == 'PUT':
        spot = Spot(**request.json)
        if int(id) != spot['id']:
            abort(422)  # TODO: append to errors instead?
        if not spot.is_valid():
            response = jsonify({'errors': spot.errors})
            response.status_code = 422
            return response
        spot.save(app.redis)
    return jsonify(spot)
