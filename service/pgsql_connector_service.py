import logging
import time

import psycopg2 as psycopg2
from dependency_injector import providers

from service.logging_service import LoggingService
from service.property_provider_service import ApplicationSettings, application_container, DatabaseSettings


class PostgresqlConnector:
    logger: LoggingService = application_container.logger
    setting_provider: ApplicationSettings = application_container.setting_provider

    def __init__(self) -> None:
        self.conn = None
        self.cursor = None
        super().__init__()
        db: DatabaseSettings = self.setting_provider.db
        readonly = True
        connect_timeout = 6
        self.logger.info("psql try connect : dbname=%s, user=%s, password=%s, host=%s, port=%s, read-only=%s, connect_timeout=%s"
                          % (db.database, db.username, '*' * len(db.password), db.host, db.port, readonly, connect_timeout))
        self.conn = psycopg2.connect(dbname=db.database, user=db.username, password=db.password, host=db.host,
                                     port=db.port, connect_timeout=connect_timeout)
        self.conn.set_session(readonly=readonly)
        self.logger.info("psql connected")
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.logger.info("psql disconnected")
        self.disconnect()

    def disconnect(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None
        if self.cursor is not None:
            self.cursor.close()
            self.cursor = None

    def execute(self, query, args={}):
        self.logger.debug("psql query start : sql=%s" % (query,))
        start = time.time()
        self.cursor.execute(query, args)
        row = self.cursor.fetchall()
        time_consumed = time.time() - start
        if time_consumed > 5:
            self.logger.info("psql query end (long query report) : sql=%s, time_consumed=%s" % (query, time_consumed))
        else:
            self.logger.debug("psql query end : sql=%s, time_consumed=%s" % (query, time_consumed))

        return row