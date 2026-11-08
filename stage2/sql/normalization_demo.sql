SET NOCOUNT ON;
CREATE TABLE #R(ProductCode varchar(12) PRIMARY KEY,ProductName nvarchar(30) NOT NULL,CategoryCode varchar(12) NOT NULL,CategoryName nvarchar(30) NOT NULL);
INSERT #R VALUES('P01',N'珍珠奶茶','C01',N'奶茶'),('P02',N'椰果奶茶','C01',N'奶茶');
SELECT N'修改前 同类别重复两行' AS Step,* FROM #R;
UPDATE #R SET CategoryName=N'鲜奶茶' WHERE ProductCode='P01';
IF (SELECT COUNT(DISTINCT CategoryName) FROM #R WHERE CategoryCode='C01')<>2 THROW 51300,'Expected anomaly absent.',1;
SELECT N'只改一行产生不一致' AS Step,* FROM #R;
UPDATE #R SET CategoryName=N'奶茶';
SELECT ProductCode,ProductName,CategoryCode INTO #P FROM #R;
SELECT DISTINCT CategoryCode,CategoryName INTO #C FROM #R;
ALTER TABLE #P ADD PRIMARY KEY(ProductCode);
ALTER TABLE #C ADD PRIMARY KEY(CategoryCode);
IF EXISTS(SELECT * FROM #R EXCEPT SELECT p.ProductCode,p.ProductName,p.CategoryCode,c.CategoryName FROM #P p JOIN #C c ON p.CategoryCode=c.CategoryCode)
 THROW 51301,'Decomposition mismatch.',1;
INSERT #C VALUES('C02',N'纯茶');
UPDATE #C SET CategoryName=N'鲜奶茶' WHERE CategoryCode='C01';
SELECT p.ProductCode,p.ProductName,p.CategoryCode,c.CategoryName FROM #P p JOIN #C c ON p.CategoryCode=c.CategoryCode;
PRINT 'PASS anomaly reproduced; decomposition roundtrip equal; standalone category insert and single-row rename succeed';
