
# way to define spark context
from datetime import datetime 
from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, col, to_timestamp, stack, expr, lit, split
from pyspark.sql.types import TimestampType, StructField, StructType, StringType, DoubleType
import os



def process_data(time_processing, company):
    spark = SparkSession.builder \
    .appName("Stock Processing") \
    .config("spark.driver.extraClassPath", "/opt/airflow/dags/StockMarketScripts/mssql-jdbc-12.4.2.jre11.jar") \
    .config("spark.executor.extraClassPath", "/opt/airflow/dags/StockMarketScripts/mssql-jdbc-12.4.2.jre11.jar") \
    .config("spark.jars", "/opt/airflow/dags/StockMarketScripts/mssql-jdbc-12.4.2.jre11.jar") \
    .getOrCreate()



    df = spark.read.option("multiline", "true").json("/opt/airflow/dags/StockMarketScripts/data.json")


    timestamps_list = [x for x in df.select('`Time Series (60min)`.*').columns]
    #string_needed = '"'+'","'.join(timestamps_list)+'"'


    df2 = df.selectExpr( "`Time Series (60min)`.* ")#"`Meta Data`.*",


    dfs = []

    for col2 in timestamps_list:
        temp_df = df2.select(
        lit(col2).cast(TimestampType()).alias("timestamp"),
        col(f'`{col2}`.`1. open`').cast(DoubleType()).alias("open_price"),
        col(f'`{col2}`.`2. high`').cast(DoubleType()).alias("low_price"),
        col(f'`{col2}`.`3. low`').cast(DoubleType()).alias("high_price"),
        col(f'`{col2}`.`4. close`').cast(DoubleType()).alias("close_price"),
        col(f'`{col2}`.`5. volume`').cast(DoubleType()).alias("volume_price")
        ).orderBy(col(col2))
        
        dfs.append(temp_df)
    final_df = dfs[0]

    for _ in dfs[1:]:
        final_df = final_df.union(_)


    # the meta data that comes with table
    df_meta_data = df.selectExpr( "`Meta Data`.*")


    df_meta_data.select(split(col("`4. Interval`"),'m')[0]).show()


    df_meta_data = df_meta_data.select(
        col("`1. Information`").alias("info_on_batch"),
        col("`2. Symbol`").alias("company_name"),
        col("`3. Last Refreshed`").cast(TimestampType()).alias("Last_refreshed"),
        split(col("`4. Interval`"),'m')[0].cast(DoubleType()).alias("interval_time(mins)"),
        col("`5. Output Size`").alias("output_size"),
        col("`6. Time Zone`").alias("time_zone"),
    )


    jdbc_url = "jdbc:sqlserver://host.docker.internal:1433;databaseName=Stock_market"
    table_name = "dbo.stock_data"
    properties = {
        "user": "x22",
        "password": "x22",
        "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
        "trustServerCertificate":"true"
    }

    final_df.write \
    .jdbc(url=jdbc_url, table=table_name, mode="append", properties=properties)
    
    
    final_df.coalesce(1).write \
        .mode("overwrite") \
        .option("header", True) \
        .csv(f"/opt/airflow/dags/StockMarketScripts/GeneratedData/{company}/{time_processing}/output.csv")


    table_name = "dbo.meta_data"
    df_meta_data.write \
    .jdbc(url=jdbc_url, table=table_name, mode="append", properties=properties)

    df_meta_data.coalesce(1).write \
        .mode("overwrite") \
        .option("header", True) \
        .csv(f"/opt/airflow/dags/StockMarketScripts/GeneratedData/{company}/{time_processing}/Meta_table_info.csv")

    os.remove("/opt/airflow/dags/StockMarketScripts/data.json")
