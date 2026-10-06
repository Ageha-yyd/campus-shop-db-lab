SET NOCOUNT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET NUMERIC_ROUNDABORT OFF;
SET XACT_ABORT OFF;
CREATE TABLE #ConstraintResults (
    TestCase nvarchar(50), Outcome varchar(12), ErrorNumber int, ConstraintName varchar(80), ErrorMessage nvarchar(400)
);
DECLARE @error int, @message nvarchar(400), @valid_rows int;
BEGIN TRANSACTION;
INSERT dbo.Product (ProductCode,ProductName,Category,UnitPrice) VALUES ('D998',N'合法对照饮品',N'测试',1.00);
INSERT dbo.Inventory (ProductCode) VALUES ('D998');
INSERT dbo.ShopOrder (OrderNo,EmployeeCode) VALUES ('MT-CONSTRAINT','E001');
SELECT @valid_rows = COUNT(*) FROM dbo.Product p JOIN dbo.Inventory i ON i.ProductCode=p.ProductCode
WHERE p.ProductCode='D998' AND p.RestockThreshold=10 AND p.IsActive=1 AND i.Quantity=0;
IF @valid_rows <> 1 OR NOT EXISTS (SELECT 1 FROM dbo.ShopOrder WHERE OrderNo='MT-CONSTRAINT' AND MemberCode IS NULL AND Status='COMPLETED')
BEGIN
    ROLLBACK;
    THROW 51060, 'Valid/default/NULL control case failed.', 1;
END;
ROLLBACK;
INSERT #ConstraintResults VALUES (N'valid/default/NULL values','ALLOWED',0,'DEFAULT / NULL',NULL);

-- negative inventory：只接受目标错误号与目标约束；无论成功/失败，都回滚。
SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;
INSERT dbo.Product (ProductCode,ProductName,Category,UnitPrice) VALUES ('D998',N'反例对照饮品',N'测试',1.00);
BEGIN TRY
    INSERT dbo.Inventory (ProductCode,Quantity) VALUES ('D998',-1);
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=LEFT(ERROR_MESSAGE(),400);
END CATCH;
IF XACT_STATE() <> 0 ROLLBACK;
IF @error <> 547 OR COALESCE(@message,N'') NOT LIKE N'%CK_Inventory_Quantity_Nonnegative%'
    THROW 51061, 'Constraint case did not fail for the expected reason: negative inventory.', 1;
INSERT #ConstraintResults VALUES (N'negative inventory','REJECTED',@error,'CK_Inventory_Quantity_Nonnegative',@message);

-- zero price：只接受目标错误号与目标约束；无论成功/失败，都回滚。
SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;

BEGIN TRY
    INSERT dbo.Product (ProductCode,ProductName,Category,UnitPrice) VALUES ('D997',N'零价格测试',N'测试',0);
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=LEFT(ERROR_MESSAGE(),400);
END CATCH;
IF XACT_STATE() <> 0 ROLLBACK;
IF @error <> 547 OR COALESCE(@message,N'') NOT LIKE N'%CK_Product_UnitPrice_Positive%'
    THROW 51061, 'Constraint case did not fail for the expected reason: zero price.', 1;
INSERT #ConstraintResults VALUES (N'zero price','REJECTED',@error,'CK_Product_UnitPrice_Positive',@message);

-- zero threshold：只接受目标错误号与目标约束；无论成功/失败，都回滚。
SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;

BEGIN TRY
    INSERT dbo.Product (ProductCode,ProductName,Category,UnitPrice,RestockThreshold) VALUES ('D997',N'阈值测试',N'测试',1,0);
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=LEFT(ERROR_MESSAGE(),400);
END CATCH;
IF XACT_STATE() <> 0 ROLLBACK;
IF @error <> 547 OR COALESCE(@message,N'') NOT LIKE N'%CK_Product_RestockThreshold_Positive%'
    THROW 51061, 'Constraint case did not fail for the expected reason: zero threshold.', 1;
INSERT #ConstraintResults VALUES (N'zero threshold','REJECTED',@error,'CK_Product_RestockThreshold_Positive',@message);

-- duplicate order：只接受目标错误号与目标约束；无论成功/失败，都回滚。
SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;

BEGIN TRY
    INSERT dbo.ShopOrder (OrderNo,EmployeeCode) VALUES ('MT-20261001-001','E001');
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=LEFT(ERROR_MESSAGE(),400);
END CATCH;
IF XACT_STATE() <> 0 ROLLBACK;
IF @error <> 2627 OR COALESCE(@message,N'') NOT LIKE N'%PK_ShopOrder%'
    THROW 51061, 'Constraint case did not fail for the expected reason: duplicate order.', 1;
INSERT #ConstraintResults VALUES (N'duplicate order','REJECTED',@error,'PK_ShopOrder',@message);

-- duplicate contact：只接受目标错误号与目标约束；无论成功/失败，都回滚。
SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;
INSERT dbo.Member (MemberCode,DisplayName,Phone) VALUES ('M998',N'唯一约束对照','00000000000');
BEGIN TRY
    INSERT dbo.Member (MemberCode,DisplayName,Phone) VALUES ('M999',N'唯一约束反例','00000000000');
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=LEFT(ERROR_MESSAGE(),400);
END CATCH;
IF XACT_STATE() <> 0 ROLLBACK;
IF @error <> 2601 OR COALESCE(@message,N'') NOT LIKE N'%UX_Member_Phone_NotNull%'
    THROW 51061, 'Constraint case did not fail for the expected reason: duplicate contact.', 1;
INSERT #ConstraintResults VALUES (N'duplicate contact','REJECTED',@error,'UX_Member_Phone_NotNull',@message);

-- orphan line：只接受目标错误号与目标约束；无论成功/失败，都回滚。
SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;

BEGIN TRY
    INSERT dbo.OrderLine VALUES ('NO-SUCH-ORDER',1,'D001',1,6.00);
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=LEFT(ERROR_MESSAGE(),400);
END CATCH;
IF XACT_STATE() <> 0 ROLLBACK;
IF @error <> 547 OR COALESCE(@message,N'') NOT LIKE N'%FK_OrderLine_ShopOrder%'
    THROW 51061, 'Constraint case did not fail for the expected reason: orphan line.', 1;
INSERT #ConstraintResults VALUES (N'orphan line','REJECTED',@error,'FK_OrderLine_ShopOrder',@message);

-- zero quantity：只接受目标错误号与目标约束；无论成功/失败，都回滚。
SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;

BEGIN TRY
    INSERT dbo.OrderLine VALUES ('MT-20261001-001',99,'D001',0,6.00);
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=LEFT(ERROR_MESSAGE(),400);
END CATCH;
IF XACT_STATE() <> 0 ROLLBACK;
IF @error <> 547 OR COALESCE(@message,N'') NOT LIKE N'%CK_OrderLine_Quantity_Positive%'
    THROW 51061, 'Constraint case did not fail for the expected reason: zero quantity.', 1;
INSERT #ConstraintResults VALUES (N'zero quantity','REJECTED',@error,'CK_OrderLine_Quantity_Positive',@message);

-- negative sale price：只接受目标错误号与目标约束；无论成功/失败，都回滚。
SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;

BEGIN TRY
    INSERT dbo.OrderLine VALUES ('MT-20261001-001',99,'D001',1,-1.00);
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=LEFT(ERROR_MESSAGE(),400);
END CATCH;
IF XACT_STATE() <> 0 ROLLBACK;
IF @error <> 547 OR COALESCE(@message,N'') NOT LIKE N'%CK_OrderLine_UnitPrice_Nonnegative%'
    THROW 51061, 'Constraint case did not fail for the expected reason: negative sale price.', 1;
INSERT #ConstraintResults VALUES (N'negative sale price','REJECTED',@error,'CK_OrderLine_UnitPrice_Nonnegative',@message);

-- invalid order status：只接受目标错误号与目标约束；无论成功/失败，都回滚。
SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;

BEGIN TRY
    INSERT dbo.ShopOrder (OrderNo,EmployeeCode,Status) VALUES ('MT-CONSTRAINT','E001','PAID');
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=LEFT(ERROR_MESSAGE(),400);
END CATCH;
IF XACT_STATE() <> 0 ROLLBACK;
IF @error <> 547 OR COALESCE(@message,N'') NOT LIKE N'%CK_ShopOrder_Status%'
    THROW 51061, 'Constraint case did not fail for the expected reason: invalid order status.', 1;
INSERT #ConstraintResults VALUES (N'invalid order status','REJECTED',@error,'CK_ShopOrder_Status',@message);

-- missing employee：只接受目标错误号与目标约束；无论成功/失败，都回滚。
SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;

BEGIN TRY
    INSERT dbo.ShopOrder (OrderNo,EmployeeCode) VALUES ('MT-CONSTRAINT','NO-EMPLOYEE');
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=LEFT(ERROR_MESSAGE(),400);
END CATCH;
IF XACT_STATE() <> 0 ROLLBACK;
IF @error <> 547 OR COALESCE(@message,N'') NOT LIKE N'%FK_ShopOrder_Employee%'
    THROW 51061, 'Constraint case did not fail for the expected reason: missing employee.', 1;
INSERT #ConstraintResults VALUES (N'missing employee','REJECTED',@error,'FK_ShopOrder_Employee',@message);

-- required product name：只接受目标错误号与目标约束；无论成功/失败，都回滚。
SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;

BEGIN TRY
    INSERT dbo.Product (ProductCode,ProductName,Category,UnitPrice) VALUES ('D997',NULL,N'测试',1.00);
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=LEFT(ERROR_MESSAGE(),400);
END CATCH;
IF XACT_STATE() <> 0 ROLLBACK;
IF @error <> 515 OR COALESCE(@message,N'') NOT LIKE N'%ProductName%'
    THROW 51061, 'Constraint case did not fail for the expected reason: required product name.', 1;
INSERT #ConstraintResults VALUES (N'required product name','REJECTED',@error,'ProductName',@message);

-- duplicate line key：只接受目标错误号与目标约束；无论成功/失败，都回滚。
SET @error=0; SET @message=NULL;
BEGIN TRANSACTION;

BEGIN TRY
    INSERT dbo.OrderLine VALUES ('MT-20261001-001',1,'D001',1,6.00);
END TRY
BEGIN CATCH
    SELECT @error=ERROR_NUMBER(), @message=LEFT(ERROR_MESSAGE(),400);
END CATCH;
IF XACT_STATE() <> 0 ROLLBACK;
IF @error <> 2627 OR COALESCE(@message,N'') NOT LIKE N'%PK_OrderLine%'
    THROW 51061, 'Constraint case did not fail for the expected reason: duplicate line key.', 1;
INSERT #ConstraintResults VALUES (N'duplicate line key','REJECTED',@error,'PK_OrderLine',@message);

SELECT TestCase, Outcome, ErrorNumber, ConstraintName FROM #ConstraintResults;
SELECT TestCase, ErrorMessage FROM #ConstraintResults WHERE ErrorNumber <> 0;
IF EXISTS (SELECT 1 FROM dbo.Product WHERE ProductCode IN ('D997','D998'))
   OR EXISTS (SELECT 1 FROM dbo.Member WHERE MemberCode IN ('M998','M999'))
   OR EXISTS (SELECT 1 FROM dbo.ShopOrder WHERE OrderNo IN ('MT-CONSTRAINT','NO-SUCH-ORDER'))
    THROW 51062, 'Constraint tests left temporary business data.', 1;
SELECT N'PASS' AS constraint_verification, COUNT(*) AS cases_checked FROM #ConstraintResults;
GO
