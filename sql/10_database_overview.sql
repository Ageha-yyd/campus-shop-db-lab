SET NOCOUNT ON;

-- 只读检查：显示当前数据库和 dbo 业务表清单，不修改数据。
SELECT DB_NAME() AS database_name, COUNT(*) AS dbo_table_count
FROM sys.tables
WHERE schema_id = SCHEMA_ID(N'dbo');

SELECT name AS table_name
FROM sys.tables
WHERE schema_id = SCHEMA_ID(N'dbo')
ORDER BY name;
GO
