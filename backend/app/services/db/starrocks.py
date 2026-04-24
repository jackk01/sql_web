from app.services.db.mysql import MySQLClient


class StarRocksClient(MySQLClient):
    driver_label = "StarRocks"

