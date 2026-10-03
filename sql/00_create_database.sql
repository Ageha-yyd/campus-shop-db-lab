USE [master];
GO
IF DB_ID(N'CampusShopV01') IS NOT NULL
    THROW 51000, 'CampusShopV01 already exists; inspect the target before resetting it.', 1;
GO
CREATE DATABASE [CampusShopV01];
GO
SELECT name, state_desc, compatibility_level
FROM sys.databases
WHERE name = N'CampusShopV01';
GO
