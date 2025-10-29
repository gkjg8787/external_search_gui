from domain.models.search import search
from . import util as db_util


def create_table():
    db_util.create_db_and_tables()
