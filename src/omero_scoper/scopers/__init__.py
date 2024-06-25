import logging
from datetime import datetime
from urllib.parse import urlparse
from omero.gateway import BlitzGateway, TagAnnotationWrapper, BlitzObjectWrapper
import threading

TagAnnotationWrapper.__hash__ = lambda self : self.getId()
BlitzObjectWrapper.__hash__ = lambda self : self.getId()

class OmeroBaseScoper:
    def __init__(self, conn: BlitzGateway, group_id: int = -1, exclusive_tagset_ids=[]):
        self.conn = conn
        self.group_id = group_id
        self.exclusive_tagset_ids = exclusive_tagset_ids
        self.hostname = urlparse(self.conn.host).hostname
        self.response = None
        self.response_compilation_datetime = None
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self.refresh_thread = threading.Thread(target=self._periodic_refresh, daemon=True)
        self.is_refreshing = False

        # Start the initial response compilation and the background refresh thread
        logging.info("Initializing and compiling the initial response.")
        self.compile_response()
        self.refresh_thread.start()
    
    def get_child_tags(self, tag):
        child_tags =  [ x.getChild() for x in self.conn.getAnnotationLinks('TagAnnotation', parent_ids=[tag.getId()])]
        return child_tags
        
    def organize_tagsets(self, tags):
        tags = list(tags)
        tagsets = {'orphan': []}
        child_to_parent = []

        # First pass: identify tagsets and children
        for tag in tags:
            children = self.get_child_tags(tag)
            if children:
                tagsets.update({tag: children})
                child_to_parent.extend([x.getId() for x in children])

        # Second pass: identify orphan tags
        for tag in tags:
            if tag.getId() not in child_to_parent:
                tagsets['orphan'].append(tag)

        return tagsets
    
    def pull_info(self):
        """
        This method should be implemented by the child class to pull the required information from the OMERO server.
        Connection to omero server is managed externally, simply use the self.conn object to interact with the server.
        """
        raise NotImplementedError(f'pull_info method not implemented in the {self.__class__.__name__} class.')

    def compile_response(self):
        with self.lock:
            if self.is_refreshing:
                logging.info("A refresh operation is already in progress.")
                return
            self.is_refreshing = True

        logging.info("Starting the response compilation.")
        try:
            if self.conn.connect() is False:
                raise Exception("Connection to OMERO server failed.")
            self.conn.SERVICE_OPTS.setOmeroGroup(self.group_id)

            response = self.pull_info()

            with self.lock:
                self.response = response
                self.response_compilation_datetime = datetime.now()
                logging.info("Response compilation completed.")
        finally:
            with self.lock:
                self.is_refreshing = False
                logging.info("Refresh operation completed.")
            self.conn.close(hard=False)
            self.conn._resetOmeroClient()

    def _periodic_refresh(self):
        while not self._stop_event.is_set():
            logging.info("Waiting for 12 hours before the next periodic refresh.")
            # Sleep for 12 hours
            self._stop_event.wait(12 * 60 * 60)
            if not self._stop_event.is_set():
                logging.info("Starting periodic refresh.")
                self.compile_response()

    def _background_refresh(self):
        logging.info("Triggering a background refresh.")
        # Run the compile response in a background thread
        threading.Thread(target=self.compile_response).start()

    def get_response(self):
        with self.lock:
            if self.response is None:
                logging.info("Initial response not available, compiling response.")
                self.compile_response()
            # refresh every 2 hours
            elif (datetime.now() - self.response_compilation_datetime).seconds > 7200: 
                if not self.is_refreshing:
                    logging.info("Response is stale, triggering a background refresh.")
                    self._background_refresh()
                else:
                    logging.info("Response is stale, but a refresh is already in progress.")
            return self.response

    def stop_refresh(self):
        logging.info("Stopping the periodic refresh thread.")
        self._stop_event.set()
        self.refresh_thread.join()