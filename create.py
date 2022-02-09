import os

from sqlalchemy import create_engine
from models import *

engine = create_engine(os.getenv("DATABASE_URL"))


def main():
  Base.metadata.create_all(engine)


if __name__ == '__main__':
  main()

# inspired from the below youtube tutorial on sqlalchemy:
# https://www.youtube.com/watch?v=cc0xt9uuKQo