import csv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

db = scoped_session(sessionmaker(bind=create_engine(os.getenv("DATABASE_URL"))))


def main():
  with open('books.csv') as f:
    reader = csv.reader(f)
    next(reader)
    for isbn, title, author, year in reader:
      db.execute(
          "INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {
              "isbn": isbn,
              "title": title,
              "author": author,
              "year": year
          })
  # db.execute("DROP TABLE users, reviews, books")
  db.commit()


if __name__ == '__main__':
  main()

# much of this was inspired from cs50's youtube videos on SQL:
# https://www.youtube.com/watch?v=Eda-NmcE5mQ - 2018 version
# https://www.youtube.com/watch?v=PbcfkA_cmqM - 2021 version