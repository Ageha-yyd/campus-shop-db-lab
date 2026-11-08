SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO
CREATE OR ALTER VIEW dbo.vw_OrderDetail AS
SELECT o.OrderNo,o.OrderedAt,o.Status,e.EmployeeCode,COALESCE(e.DisplayName,N'待分配') AS EmployeeName,
 o.MemberCode,COALESCE(m.DisplayName,N'匿名顾客') AS MemberName,l.LineNumber,p.ProductCode,p.ProductName,
 l.Quantity,l.UnitPrice,CONVERT(decimal(12,2),l.Quantity*l.UnitPrice) AS LineAmount
FROM dbo.ShopOrder o LEFT JOIN dbo.Employee e ON e.EmployeeCode=o.EmployeeCode
LEFT JOIN dbo.Member m ON m.MemberCode=o.MemberCode JOIN dbo.OrderLine l ON l.OrderNo=o.OrderNo
JOIN dbo.Product p ON p.ProductCode=l.ProductCode;
GO
CREATE OR ALTER PROCEDURE dbo.usp_Orders @ActorId int, @OrderNo varchar(24)=NULL
AS
BEGIN
 SET NOCOUNT ON;
 DECLARE @Role varchar(12)=(SELECT Role FROM dbo.AppUser WHERE UserId=@ActorId AND IsActive=1);
 IF @Role IS NULL OR ((USER_NAME()='mt_customer' OR IS_ROLEMEMBER('web_customer')=1) AND @Role<>'customer')
  THROW 51103,'Actor not allowed.',1;
 SELECT o.OrderNo,o.OrderedAt,o.Status,o.MemberCode,o.EmployeeCode,o.CreatedByUserId,
  CONVERT(decimal(18,2),COALESCE(SUM(l.Quantity*l.UnitPrice),0)) AS Total
 FROM dbo.ShopOrder o LEFT JOIN dbo.OrderLine l ON o.OrderNo=l.OrderNo
 WHERE (@OrderNo IS NULL OR o.OrderNo=@OrderNo) AND (@Role<>'customer' OR o.CreatedByUserId=@ActorId)
 GROUP BY o.OrderNo,o.OrderedAt,o.Status,o.MemberCode,o.EmployeeCode,o.CreatedByUserId
 ORDER BY o.OrderedAt DESC,o.OrderNo;
END;
GO
CREATE OR ALTER PROCEDURE dbo.usp_OrderLines @ActorId int,@OrderNo varchar(24)
AS
BEGIN
 SET NOCOUNT ON;
 DECLARE @Role varchar(12)=(SELECT Role FROM dbo.AppUser WHERE UserId=@ActorId AND IsActive=1);
 IF @Role IS NULL OR ((USER_NAME()='mt_customer' OR IS_ROLEMEMBER('web_customer')=1) AND @Role<>'customer') THROW 51103,'Actor not allowed.',1;
 IF NOT EXISTS(SELECT 1 FROM dbo.ShopOrder WHERE OrderNo=@OrderNo AND (@Role<>'customer' OR CreatedByUserId=@ActorId))
  THROW 51104,'Order not accessible.',1;
 SELECT l.LineNumber,l.ProductCode,p.ProductName,l.Quantity,l.UnitPrice,l.Quantity*l.UnitPrice AS Amount
 FROM dbo.OrderLine l JOIN dbo.Product p ON p.ProductCode=l.ProductCode WHERE l.OrderNo=@OrderNo ORDER BY l.LineNumber;
END;
GO
-- Caller (DAO unit of work) MUST open a transaction and commit/rollback this whole operation.
-- No grant of table writes to clerk/customer. Procedure ownership chain provides limited writes.
CREATE OR ALTER PROCEDURE dbo.usp_OrderSave
 @ActorId int,@OrderNo varchar(24),@Items nvarchar(max),@MemberCode varchar(12)=NULL,@IsNew bit=1
AS
BEGIN
 SET NOCOUNT ON; SET XACT_ABORT ON;
 IF @@TRANCOUNT=0 THROW 51109,'Transaction required.',1;
 DECLARE @Role varchar(12),@Employee varchar(12),@Member varchar(12);
 SELECT @Role=Role,@Employee=EmployeeCode,@Member=MemberCode FROM dbo.AppUser WHERE UserId=@ActorId AND IsActive=1;
 IF @Role IS NULL OR ((USER_NAME()='mt_customer' OR IS_ROLEMEMBER('web_customer')=1) AND @Role<>'customer') THROW 51103,'Actor not allowed.',1;
 IF @Role='customer' SET @MemberCode=@Member;
 DECLARE @Lines TABLE(LineNumber int PRIMARY KEY,ProductCode varchar(12),Quantity int);
 INSERT @Lines SELECT CONVERT(int,[key])+1,JSON_VALUE(value,'$.product_code'),TRY_CONVERT(int,JSON_VALUE(value,'$.quantity')) FROM OPENJSON(@Items);
 IF NOT EXISTS(SELECT 1 FROM @Lines) OR (SELECT COUNT(*) FROM @Lines)>50 OR EXISTS(SELECT 1 FROM @Lines WHERE Quantity IS NULL OR Quantity<1 OR Quantity>100 OR ProductCode IS NULL)
  THROW 51101,'Invalid order lines.',1;
 IF EXISTS(SELECT 1 FROM @Lines l LEFT JOIN dbo.Product p WITH(UPDLOCK,HOLDLOCK) ON p.ProductCode=l.ProductCode WHERE p.ProductCode IS NULL OR p.IsActive=0)
  THROW 51106,'Product unavailable.',1;
 IF @IsNew=1
  INSERT dbo.ShopOrder(OrderNo,EmployeeCode,MemberCode,Status,CreatedByUserId) VALUES(@OrderNo,@Employee,@MemberCode,'DRAFT',@ActorId);
 ELSE
 BEGIN
  IF NOT EXISTS(SELECT 1 FROM dbo.ShopOrder WITH(UPDLOCK,HOLDLOCK) WHERE OrderNo=@OrderNo AND Status='DRAFT' AND (@Role<>'customer' OR CreatedByUserId=@ActorId))
   THROW 51106,'Only accessible drafts can be edited.',1;
  UPDATE dbo.ShopOrder SET MemberCode=@MemberCode WHERE OrderNo=@OrderNo;
  DELETE dbo.OrderLine WHERE OrderNo=@OrderNo;
 END;
 INSERT dbo.OrderLine(OrderNo,LineNumber,ProductCode,Quantity,UnitPrice)
 SELECT @OrderNo,l.LineNumber,l.ProductCode,l.Quantity,p.UnitPrice FROM @Lines l JOIN dbo.Product p ON p.ProductCode=l.ProductCode;
END;
GO
CREATE OR ALTER PROCEDURE dbo.usp_OrderAction @ActorId int,@OrderNo varchar(24),@Action varchar(12)
AS
BEGIN
 SET NOCOUNT ON; SET XACT_ABORT ON;
 IF @@TRANCOUNT=0 THROW 51109,'Transaction required.',1;
 DECLARE @Role varchar(12),@Employee varchar(12),@Owner int,@Status varchar(12),@Applied bit;
 SELECT @Role=Role,@Employee=EmployeeCode FROM dbo.AppUser WHERE UserId=@ActorId AND IsActive=1;
 IF @Role IS NULL OR ((USER_NAME()='mt_customer' OR IS_ROLEMEMBER('web_customer')=1) AND @Role<>'customer') THROW 51103,'Actor not allowed.',1;
 SELECT @Owner=CreatedByUserId,@Status=Status,@Applied=StockApplied FROM dbo.ShopOrder WITH(UPDLOCK,HOLDLOCK) WHERE OrderNo=@OrderNo;
 IF @Status IS NULL OR (@Role='customer' AND (@Owner IS NULL OR @Owner<>@ActorId)) THROW 51104,'Order not accessible.',1;
 IF @Action='delete'
 BEGIN
  IF @Status<>'DRAFT' THROW 51106,'Only drafts can be deleted.',1;
  DELETE dbo.OrderLine WHERE OrderNo=@OrderNo; DELETE dbo.ShopOrder WHERE OrderNo=@OrderNo; RETURN;
 END;
 IF @Action='submit'
 BEGIN
  IF @Role='customer' THROW 51103,'Clerk confirmation required.',1;
  IF @Status<>'DRAFT' THROW 51106,'Only drafts can be submitted once.',1;
  IF NOT EXISTS(SELECT 1 FROM dbo.OrderLine WHERE OrderNo=@OrderNo) THROW 51106,'Empty order.',1;
  -- Lock inventory in stable product-code order before any stock modification.
  DECLARE @Product varchar(12),@Qty int,@OnHand int;
  DECLARE stocks CURSOR LOCAL FAST_FORWARD FOR SELECT ProductCode,SUM(Quantity) FROM dbo.OrderLine WHERE OrderNo=@OrderNo GROUP BY ProductCode ORDER BY ProductCode;
  OPEN stocks; FETCH NEXT FROM stocks INTO @Product,@Qty;
  WHILE @@FETCH_STATUS=0
  BEGIN
   SET @OnHand=NULL;
   SELECT @OnHand=i.Quantity FROM dbo.Inventory i WITH(UPDLOCK,HOLDLOCK) JOIN dbo.Product p WITH(UPDLOCK,HOLDLOCK) ON p.ProductCode=i.ProductCode WHERE i.ProductCode=@Product AND p.IsActive=1;
   IF @OnHand IS NULL OR @OnHand<@Qty THROW 51106,'Insufficient stock.',1;
   UPDATE dbo.Inventory SET Quantity=Quantity-@Qty,UpdatedAt=SYSUTCDATETIME() WHERE ProductCode=@Product;
   FETCH NEXT FROM stocks INTO @Product,@Qty;
  END;
  CLOSE stocks; DEALLOCATE stocks;
  UPDATE dbo.ShopOrder SET Status='COMPLETED',StockApplied=1,EmployeeCode=@Employee WHERE OrderNo=@OrderNo;
 END
 ELSE IF @Action='cancel'
 BEGIN
  IF @Status='CANCELLED' THROW 51106,'Already cancelled.',1;
  IF @Status='COMPLETED' AND (@Role='customer' OR @Applied=0) THROW 51103,'Cancellation not allowed.',1;
  IF @Applied=1
  BEGIN
   -- Inventory is optional: an administrator may delete a sold-out zero row.
   -- A cancellation must recreate that row, rather than silently losing the return.
   DECLARE @ReturnProduct varchar(12),@ReturnQty int,@ExistingStock int;
   DECLARE returns CURSOR LOCAL FAST_FORWARD FOR
    SELECT ProductCode,SUM(Quantity) FROM dbo.OrderLine WHERE OrderNo=@OrderNo GROUP BY ProductCode ORDER BY ProductCode;
   OPEN returns; FETCH NEXT FROM returns INTO @ReturnProduct,@ReturnQty;
   WHILE @@FETCH_STATUS=0
   BEGIN
    SELECT @ReturnProduct=ProductCode FROM dbo.Product WITH(UPDLOCK,HOLDLOCK) WHERE ProductCode=@ReturnProduct;
    SET @ExistingStock=NULL;
    SELECT @ExistingStock=Quantity FROM dbo.Inventory WITH(UPDLOCK,HOLDLOCK) WHERE ProductCode=@ReturnProduct;
    IF @ExistingStock IS NULL
     INSERT dbo.Inventory(ProductCode,Quantity) VALUES(@ReturnProduct,@ReturnQty);
    ELSE
     UPDATE dbo.Inventory SET Quantity=Quantity+@ReturnQty,UpdatedAt=SYSUTCDATETIME() WHERE ProductCode=@ReturnProduct;
    FETCH NEXT FROM returns INTO @ReturnProduct,@ReturnQty;
   END;
   CLOSE returns; DEALLOCATE returns;
  END;
  UPDATE dbo.ShopOrder SET Status='CANCELLED',StockApplied=0 WHERE OrderNo=@OrderNo;
 END
 ELSE THROW 51101,'Unknown action.',1;
END;
GO
CREATE ROLE web_auth;
CREATE ROLE web_admin;
CREATE ROLE web_clerk;
CREATE ROLE web_customer;
GRANT SELECT ON dbo.AppUser TO web_auth;
GRANT SELECT,INSERT,UPDATE,DELETE ON dbo.Product TO web_admin;
GRANT SELECT,INSERT,UPDATE,DELETE ON dbo.Inventory TO web_admin;
GRANT SELECT ON dbo.Member TO web_admin;
GRANT SELECT ON dbo.Employee TO web_admin;
GRANT SELECT ON dbo.Product TO web_clerk,web_customer;
GRANT SELECT ON dbo.Inventory TO web_clerk,web_customer;
GRANT SELECT ON dbo.vw_ProductSales TO web_admin,web_clerk;
GRANT EXECUTE ON dbo.usp_Orders TO web_admin,web_clerk,web_customer;
GRANT EXECUTE ON dbo.usp_OrderLines TO web_admin,web_clerk,web_customer;
GRANT EXECUTE ON dbo.usp_OrderSave TO web_admin,web_clerk,web_customer;
GRANT EXECUTE ON dbo.usp_OrderAction TO web_admin,web_clerk,web_customer;
GO
