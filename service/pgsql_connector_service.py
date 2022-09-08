import logging

import psycopg2 as psycopg2

from service.property_provider_service import ApplicationSettings, ApplicationContainer, DatabaseSettings

log = logging.getLogger(__name__)


class PostgresqlConnector:
    setting_provider: ApplicationSettings = ApplicationContainer().setting_provider()

    def __init__(self) -> None:
        self.conn = None
        self.cursor = None
        super().__init__()
        db: DatabaseSettings = self.setting_provider.db
        self.conn = psycopg2.connect(dbname=db.database, user=db.username, password=db.password, host=db.host,
                                     port=db.port)
        self.conn.set_session(readonly=True)
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.disconnect()

    def disconnect(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None
        if self.cursor is not None:
            self.cursor.close()
            self.cursor = None

    def execute(self, query, args={}):
        self.cursor.execute(query, args)
        row = self.cursor.fetchall()
        return row