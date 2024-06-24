import argparse
from flask import Flask, jsonify
from omero.gateway import BlitzGateway
from omero_scoper.scopers import OmeroBaseScoper
from omero_scoper.scopers.OmeroSlideScoper import OmeroSlideScoper
from omero_scoper.scopers.OmeroSubjectScoper import OmeroSubjectScoper

class OmeroScoperApp(Flask):
    def __init__(self, import_name, conn, group_id, exclusive_tagset_ids, scoper_type):
        super().__init__(import_name)
        self.scoper = self._get_scoper(conn, group_id, exclusive_tagset_ids, scoper_type)
        self.route('/', methods=['GET'])(self.get_response)
        
    def _get_scoper(self, conn, group_id, exclusive_tagset_ids, scoper_type):
        if scoper_type == 'subject':
            return OmeroSubjectScoper(conn, group_id, exclusive_tagset_ids)
        elif scoper_type == 'slide':
            return OmeroSlideScoper(conn, group_id, exclusive_tagset_ids)
        else:
            raise ValueError(f"Unknown scoper type: {scoper_type}")

    def get_response(self):
        info = self.scoper.get_response()
        return jsonify(info)
    
def main(**kwargs):
    conn_optional_args = {}
    if kwargs.get('port'):
        conn_optional_args.update({'port':kwargs['port']})
    if kwargs.get('secure'):
        conn_optional_args.update({'secure':kwargs['secure']})
    conn = BlitzGateway(kwargs['username'], kwargs['password'], host=kwargs['host'], **conn_optional_args)
    conn.connect()
    
    app = OmeroScoperApp(__name__, conn, kwargs['group_id'], kwargs['exclusive_tagset_ids'], kwargs['scoper_type'])
    app.run(port=args.http_port)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run OmeroBaseScoper as an HTTP endpoint.")
    parser.add_argument('--username', required=True, help='OMERO server username')
    parser.add_argument('--password', required=True, help='OMERO server password')
    parser.add_argument('--host', required=True, help='OMERO server host')
    parser.add_argument('--port', type=int, default=None, help='OMERO server port')
    parser.add_argument('--secure', action='store_true', help='Use secure OMERO server connection')
    parser.add_argument('--group_id', type=int, default=-1, help='Group ID to scope to')
    parser.add_argument('--exclusive_tagset_ids', nargs='+', type=int, default=[], help='List of exclusive tagset IDs')
    parser.add_argument('--scoper_type', required=True, choices=['subject', 'slide'], help='Type of scoper to use')
    parser.add_argument('--http_port', type=int, default=8080, help='Port to run the HTTP server on')

    args = parser.parse_args()
    main(**args)