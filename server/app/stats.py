import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

import auth
from series import rts

logger = logging.getLogger(__name__)

stats = Blueprint('stats', __name__, url_prefix='/stats')


@stats.route('/attacks')
@auth.auth_required
def get_attack_series():
    filters = ['type=attack']
    for label in ['sploit', 'team']:
        if value := request.args.get(label):
            filters.append(f'{label}={value}')

    start_ts = 0
    if start := request.args.get('start'):
        start_ts = int(round(datetime.strptime(start, '%Y-%m-%d %H:%M').timestamp()))

    end_ts = -1
    if end := request.args.get('end'):
        end_ts = int(round(datetime.strptime(end, '%Y-%m-%d %H:%M').timestamp()))

    logger.info('Got filters: %s, start_ts=%s, end_ts=%s', filters, start_ts, end_ts)

    data = rts.mrange(
        start_ts,
        end_ts,
        filters=filters,
        aggregation_type='sum',
        bucket_size_msec=60,
        with_labels=True,
    )
    response = []
    for row in data:
        for k, values in row.items():
            response.append({
                'name': k,
                'labels': values[0],
                'data': values[1],
            })

    return jsonify(response)
