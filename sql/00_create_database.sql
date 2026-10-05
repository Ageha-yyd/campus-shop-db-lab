USE [master];
GO
IF DB_ID(N'MilkTeaShopV01') IS NOT NULL
    THROW 51000, 'MilkTeaShopV01 already exists; inspect the target before resetting it.', 1;
GO
CREATE DATABASE [MilkTeaShopV01];
GO
SELECT name, state_desc, compatibility_level
FROM sys.databases
WHERE name = N'MilkTeaShopV01';
GO
