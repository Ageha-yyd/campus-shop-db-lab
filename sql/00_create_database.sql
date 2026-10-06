USE [master];
SET NOCOUNT ON;
IF DB_ID(N'MilkTeaShopV01') IS NOT NULL
    THROW 51000, 'MilkTeaShopV01 already exists; inspect the target before resetting it.', 1;
-- Use server-owned default folders and unique physical filenames. A preserved,
-- renamed experiment database may still own the old MilkTeaShopV01.mdf file.
DECLARE @data_path nvarchar(4000)=CONVERT(nvarchar(4000),SERVERPROPERTY('InstanceDefaultDataPath'));
DECLARE @log_path nvarchar(4000)=CONVERT(nvarchar(4000),SERVERPROPERTY('InstanceDefaultLogPath'));
IF @data_path IS NULL OR @log_path IS NULL
    THROW 51001, 'SQL Server default data/log folders are unavailable.', 1;
DECLARE @suffix varchar(32)=REPLACE(CONVERT(varchar(36),NEWID()),'-','');
DECLARE @create_sql nvarchar(max)=N'CREATE DATABASE [MilkTeaShopV01] ON PRIMARY '
    + N'(NAME=N''MilkTeaShopV01'', FILENAME=N'''
    + REPLACE(@data_path+N'MilkTeaShopV01_'+@suffix+N'.mdf',N'''',N'''''')
    + N''') LOG ON (NAME=N''MilkTeaShopV01_log'', FILENAME=N'''
    + REPLACE(@log_path+N'MilkTeaShopV01_'+@suffix+N'_log.ldf',N'''',N'''''') + N''');';
EXEC sys.sp_executesql @create_sql;
SELECT name, state_desc, compatibility_level
FROM sys.databases
WHERE name = N'MilkTeaShopV01';
GO
