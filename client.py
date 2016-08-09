import requests
import json
import logging


class WebServicesClient(object):
    def __init__(self, url, username, password, no_execute):
        self._url = url
        self._username = username
        self._password = password
        self._no_execute = no_execute

    def _create_session(self):
        logging.debug('Creating Request Session')
        session = requests.Session()
        session.auth = (self._username, self._password)
        session.verify = False
        session.headers = {'content-type': 'application/json'}
        return session

    def _close_session(self, session):
        logging.debug('Closing Request Session')
        session.close()

    def execute_get(self, service_path):
        get_url = self._url + service_path
        items =[]
        logging.info('Executing REST API GET Request with url: %s', get_url)
        print "Executing Get Request with url : " + get_url
        if not self._no_execute:
            session = self._create_session()
            r = session.get(get_url, params='')
            logging.debug('Get Request Response: %s', r)
            logging.info('Response status code is  %s', r.status_code)
            if r.status_code == 200:
                logging.info('Request successful.')
                json_response = r.text
                items = json.loads(json_response)

            else:
                # @TODO throw error?
                logging.error('GET request rejected.')
                print (r.status_code)
            self._close_session(session)
        else:
            # setting a dummy value
            items = [{'name': 'select01', 'host': 'host01','status':'unknown', 'state': 'powered_on'}]
        return items

    def execute_post(self, service_path, data):
        post_url = self._url + service_path
        logging.info('Executing REST API POST Request with url: %s and data %s', post_url, data)
        print "Executing Post Request with url : " + post_url + " with data " + str(data)
        if not self._no_execute:
            session = self._create_session()
            logging.debug('post payload %s', json.dumps(data))

            r = session.post(post_url, data=json.dumps(data))
            logging.debug('Post Request Response: %s', r)
            logging.info('Response status code is  %s', r.status_code)
            print "post request status" + str(r.status_code)
            if r.status_code != 202:
                # @TODO throw error?
                logging.error('Post request rejected. %s', r)
                print 'Error: post request not accepted'
            else:
                logging.info('Request accepted.')
            self._close_session(session)

    def execute_put(self, service_path, data):
        put_url = self._url + service_path
        print "Executing Put Request with url : " + put_url + " and data : " + str(data)
        logging.info('Executing REST API PUT Request with url: %s and data: %s', put_url, str(data))
        if not self._no_execute:
            session = self._create_session()
            r = session.put(put_url, json.dumps(data))
            logging.info('Response status code is  %s', r.status_code)
            logging.debug('Put Request Response: %s', r)
            print "put request status" + str(r.status_code)
            if r.status_code != 202:
                logging.error('Post request rejected.')
                print 'Error: put request not accepted'
                # @TODO throw error?
            else:
                logging.info('Request accepted.')
            self._close_session(session)

    def execute_delete(self, service_path):
        delete_url = self._url + service_path
        print "Executing Delete Request with url : " + delete_url
        logging.info('Executing REST API DELETE Request with url: %s', delete_url)
        if not self._no_execute:
            session = self._create_session()
            r = session.delete(delete_url)
            logging.info('Response status code is  %s', r.status_code)
            logging.debug('Delete Request Response: %s', r)
            print "delete request status" + str(r.status_code)
            if r.status_code == 204 or r.status_code == 202 :
                logging.error('Delete request accpeted.')
                print 'Error: delete request  accepted'
            else:
                # @TODO throw error?
                logging.error('Delete request rejected.')
                print 'Error: delete request not accepted'
            self._close_session(session)