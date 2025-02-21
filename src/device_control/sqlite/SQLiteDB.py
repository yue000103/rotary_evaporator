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

            # 构建CREATE TABLE SQL语句
            create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
            cursor.execute(create_table_sql)
            logger.debug(f"Table created with SQL: {create_table_sql}")
            cursor.connection.commit()  # 提交事务

    def drop_table(self, table_name):
        with self.get_connection() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            logger.debug(f"Table {table_name} dropped")
            cursor.connection.commit()  # 提交事务

    def execute_query(self, query, params=None):
        with self.get_connection() as cursor:

            if params:
                cursor.execute(query, params)
            else:
               cursor.execute(query)
            cursor.connection.commit()  # 提交事务

            results = cursor.fetchall()
            logger.debug(f"Queried data with query: {query} and params: {params}")
            return results


    def insert_data(self, table_name, columns, data):
        '''
        注意：columns中不能有多余的逗号，否则placeholders会发生错误
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
            cursor.connection.commit()  # 提交事务


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
            # print("query", query)
            logger.debug(f"Executing query: {query} with params: {params}")
            # print("params", params)
            cursor.execute(query, params)
            cursor.connection.commit()  # 提交事务


    def delete_data(self, table_name, condition, params):
        with self.get_connection() as cursor:
            query = f"DELETE FROM {table_name} WHERE {condition}"
            cursor.execute(query, params)
            logger.info(f"Deleted data from {table_name} with query: {query}")
            cursor.connection.commit()  # 提交事务

    def query_data(self, table_name, columns="*", where_clause=None, params=None):
        """
        :param table_name:
        :param columns:"column1, column2"
        :param where_clause:"column1 = ? AND column2 > ?"
        :param params:("value1", 10)
        :return:
        """
        # print(table_name, columns, where_clause, params)
        # self.connect()
        with self.get_connection() as cursor:
                # 构建基本的查询语句
            query = f"SELECT {columns} FROM {table_name}"

            # 如果有条件，则添加 WHERE 子句
            if where_clause:
                query += f" WHERE {where_clause}"

            # 执行查询
            if params:
                # print("columns",columns)
                # print("where_clause",where_clause)
                # print("params",params)
                # print("query",query)

                cursor.execute(query, params)
            else:
                cursor.execute(query)
            cursor.connection.commit()  # 提交事务

                # 获取所有结果
            results =cursor.fetchall()
            # print(results)
            logger.debug(
                f"Queried data from {table_name} with query: {query} and params: {params}"
            )
            return results

    def query_joined_data(self, table1, table2, join_condition, columns="*", where_clause=None, params=None):
        """
        :param table1: 第一个表的名称
        :param table2: 第二个表的名称
        :param join_condition: 两个表的联接条件, 如 "table1.id = table2.foreign_id"
        :param columns: 要查询的列, 例如 "table1.column1, table2.column2" 或者 "*"
        :param where_clause: WHERE 子句条件, 如 "table1.column1 = ? AND table2.column2 > ?"
        :param params: WHERE 子句对应的参数, 如 ("value1", 10)
        :return: 查询结果
        """
        print("table1",table1)
        print("table2",table2)
        print("join_condition",join_condition)
        with self.get_connection() as cursor:
            # 构建联表查询语句
            query = f"SELECT {columns} FROM {table1} JOIN {table2} ON {join_condition}"

            # 如果有条件，则添加 WHERE 子句
            if where_clause:
                query += f" WHERE {where_clause}"

            # 执行查询
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            cursor.connection.commit()  # 提交事务

            # 获取所有结果
            results = cursor.fetchall()

            logger.debug(
                f"Queried joined data from {table1} and {table2} with query: {query} and params: {params}"
            )
            return results

if __name__ == "__main__":
    db = SQLiteDB()
    print(db.db_name)