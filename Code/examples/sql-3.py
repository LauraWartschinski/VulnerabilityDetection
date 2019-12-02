from dataclasses import dataclass

import pytz

from config import get_connection


def get_visit_count():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        f"select count(*) from visitors;")
    rows = cursor.fetchall()
    connection.commit()
    connection.close()
    return rows[0][0]


@dataclass()
class Visitor:
    ip_address: str
    user_agent: str
    referrer: str
    full_path: str
    visit_time: pytz

    def on_save(self):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            f"insert into visitors (ip_address, user_agent, referrer, full_path, visit_time) values ('{self.ip_address}', '{self.user_agent}', '{self.referrer}', '{self.full_path}', '{self.visit_time}');")
        connection.commit()
        connection.close()
        return 0
