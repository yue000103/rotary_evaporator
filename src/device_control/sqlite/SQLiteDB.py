import sqlite3
import logging
import os
from contextlib import contextmanager

logger = logging.getLogger("SQLiteDB")


class SQLiteDB:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        self.db_name = os.path.join(base_dir, "Chromatograph.sqlite")
        self.connection = None
        self.cursor = None


    def connect(self):
        print("connect",self.connection)
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_name)
            self.cursor = self.connection.cursor()
            logger.debug(f"Database {self.db_name} connection created")

    @contextmanager
    def get_connection(self):
        connection = sqlite3.connect(self.db_name, check_same_thread=False)
        cursor = connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
            connection.close()
    def close(self):
        print("close connect",self.connection)
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        if self.connection:
            self.connection.close()
            logger.debug(f"Database {self.db_name} connection closed")

    def create_table(self, table_name, columns):
        with self.get_connection() as cursor:

            create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
            cursor.execute(create_table_sql)
            logger.debug(f"Table created with SQL: {create_table_sql}")
            cursor.connection.commit()

    def drop_table(self, table_name):
        with self.get_connection() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            logger.debug(f"Table {table_name} dropped")
            cursor.connection.commit()

    def execute_query(self, query, params=None):
        with self.get_connection() as cursor:

            if params:
                cursor.execute(query, params)
            else:
               cursor.execute(query)
            cursor.connection.commit()

            results = cursor.fetchall()
            logger.debug(f"Queried data with query: {query} and params: {params}")
            return results


    def insert_data(self, table_name, columns, data):
        '''
        Note: columns must not have extra commas, otherwise placeholders will error
        :param table_name:
        :param columns: """name1, name2"""
        :param data: [(name1,name2), (name1,name2)]
        :return:
        '''

        with self.get_connection() as cursor:
            placeholders = ", ".join(["?"] * len(columns.split(",")))

            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            print("query",query)
            print("data",data)

            cursor.executemany(query, data)
            logger.info(f"Inserted data into {table_name}")
            cursor.connection.commit()


    def update_data(self, table_name, set_clause, condition, params):
        '''
        :param table_name:
        :param set_clause: """name1 = ?, name2 = ?"""
        :param condition: "name3 = ?"
        :param params: (name1,name2,name3)
        :return:
        '''
        with self.get_connection() as cursor:
            query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
            logger.debug(f"Executing query: {query} with params: {params}")
            cursor.execute(query, params)
            cursor.connection.commit()


    def delete_data(self, table_name, condition, params):
        with self.get_connection() as cursor:
            query = f"DELETE FROM {table_name} WHERE {condition}"
            cursor.execute(query, params)
            logger.info(f"Deleted data from {table_name} with query: {query}")
            cursor.connection.commit()

    def query_data(self, table_name, columns="*", where_clause=None, params=None):
        """
        :param table_name:
        :param columns:"column1, column2"
        :param where_clause:"column1 = ? AND column2 > ?"
        :param params:("value1", 10)
        :return:
        """
        with self.get_connection() as cursor:
            query = f"SELECT {columns} FROM {table_name}"

            if where_clause:
                query += f" WHERE {where_clause}"

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            cursor.connection.commit()

            results =cursor.fetchall()
            logger.debug(
                f"Queried data from {table_name} with query: {query} and params: {params}"
            )
            return results

    def query_joined_data(self, table1, table2, join_condition, columns="*", where_clause=None, params=None):
        """
        :param table1: Name of the first table
        :param table2: Name of the second table
        :param join_condition: Join condition between two tables, e.g., "table1.id = table2.foreign_id"
        :param columns: Columns to query, e.g., "table1.column1, table2.column2" or "*"
        :param where_clause: WHERE clause condition, e.g., "table1.column1 = ? AND table2.column2 > ?"
        :param params: Parameters for WHERE clause, e.g., ("value1", 10)
        :return: Query results
        """
        print("table1",table1)
        print("table2",table2)
        print("join_condition",join_condition)
        with self.get_connection() as cursor:
            query = f"SELECT {columns} FROM {table1} JOIN {table2} ON {join_condition}"

            if where_clause:
                query += f" WHERE {where_clause}"

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            cursor.connection.commit()

            results = cursor.fetchall()

            logger.debug(
                f"Queried joined data from {table1} and {table2} with query: {query} and params: {params}"
            )
            return results

if __name__ == "__main__":
    db = SQLiteDB()
    print(db.db_name)