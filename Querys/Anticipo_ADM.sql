/****** Script for SelectTopNRows command from SSMS CXP ******/
SELECT 
	(case 
		when ant.Tipo = '1' then 'CxP'
		else ant.Tipo 
	end) tipocxp,
	pro.CodigoProveedor proveedor_rif,
	pro.NombreProveedor proveedor_nombre,
	ant.Numero numero_anticipo,
	ant.Fecha as fecha_original,
	(case 
		when ant.Status = '2' then 'Parcialmente Usado'
		when ant.Status = '0' then 'Vigente'
		when ant.Status = '1' then 'Anulado'
		when ant.Status = '3' then 'Completamente Usado'
		when ant.Status = '4' then 'Completamente Devuelto'
		when ant.Status = '5' then 'Parcialmente Devuelto'
		else ant.Status
	end) status_anticipo,
	(case 
		when ant.Status = '2' then ant.Fecha
		when ant.Status = '0' then ant.Fecha
		when ant.Status = '1' then ant.FechaAnulacion
		when ant.Status = '3' then ant.FechaCancelacion
		when ant.Status = '4' then ant.FechaDevolucion
		when ant.Status = '5' then ant.Fecha
		else ant.Fecha
	end) fecha_status_anticipo,
	ant.Moneda,
	ant.MontoTotal,
	ant.MontoUsado,
	ant.MontoDevuelto,
	ant.MontoDiferenciaEnDevolucion,
	(ant.MontoTotal - ant.MontoUsado) MontoRestante,
	ant.CodigoCuentaBancaria,
	ctaban.NombreCuenta cuenta_bancaria,
	replace(REPLACE(REPLACE(replace(REPLACE(ant.Descripcion, ';',''), '"' , ''),char(13),''),char(10),''),',','#') obs,
	cxp.Numero numero_cxp,
	dp.NumeroComprobante numeropago,
	dp.MontoEnMonedaOriginalDeCxP,
	dp.MontoAbonado,
	dp.CambioAMonedaDelPago tasacambiopago,
	p.Fecha fecha_pago,
	p.NumeroCheque,
	(case 
		when p.StatusOrdenDePago = '0' then 'Vigente'
		when p.StatusOrdenDePago = '1' then 'Anulado'
		else cxp.Status
	end) status_pago
	
  FROM 
	anticipo ant,
	anticipoPagado antpa,
	COMPROBANTE comp,
	Proveedor pro,
	Pago p,
	DocumentoPagado dp,
	cxp,
	CuentaBancaria ctaban

  where 
    pro.ConsecutivoCompania = ant.ConsecutivoCompania
	and ant.ConsecutivoCompania = ctaban.ConsecutivoCompania
	and pro.CodigoProveedor = ant.CodigoProveedor
	and ant.Numero = antpa.NumeroAnticipo
	and p.NumeroComprobante = antpa.NumeroComprobante
	and cxp.ConsecutivoCxp = comp.ConsecutivoDocOrigen
	and exists (
		select * 
		from PERIODO 
		where cxp.ConsecutivoCompania = PERIODO.ConsecutivoCompania 
			and comp.ConsecutivoPeriodo = PERIODO.ConsecutivoPeriodo
		)
	and cxp.ConsecutivoCompania = 10
	and dp.NumeroComprobante = p.NumeroComprobante
	and dp.NumeroDelDocumentoPagado = cxp.Numero
	and cxp.ConsecutivoCompania = p.ConsecutivoCompania
	and p.Origen not in (0) -- se excluyen pagos tipo retencion
	and p.CodigoProveedor = cxp.CodigoProveedor
	and ctaban.Codigo = ant.CodigoCuentaBancaria
	-- and ant.Numero in ('42196739' , '62971423')
	-- and cxp.Numero = '00-00000144' --'0073'  --'00006235'

union
	
	SELECT 
	(case 
		when ant.Tipo = '1' then 'CxP'
		else ant.Tipo 
	end) tipocxp,
	pro.CodigoProveedor proveedor_rif,
	pro.NombreProveedor proveedor_nombre,
	ant.Numero numero_anticipo,
	ant.Fecha as fecha_original,
	(case 
		when ant.Status = '2' then 'Parcialmente Usado'
		when ant.Status = '0' then 'Vigente'
		when ant.Status = '1' then 'Anulado'
		when ant.Status = '3' then 'Completamente Usado'
		when ant.Status = '4' then 'Completamente Devuelto'
		when ant.Status = '5' then 'Parcialmente Devuelto'
		else ant.Status
	end) status_anticipo,
	(case 
		when ant.Status = '2' then ant.Fecha
		when ant.Status = '0' then ant.Fecha
		when ant.Status = '1' then ant.FechaAnulacion
		when ant.Status = '3' then ant.FechaCancelacion
		when ant.Status = '4' then ant.FechaDevolucion
		when ant.Status = '5' then ant.Fecha
		else ant.Fecha
	end) fecha_status_anticipo,
	ant.Moneda,
	ant.MontoTotal,
	ant.MontoUsado,
	ant.MontoDevuelto,
	ant.MontoDiferenciaEnDevolucion,
	(ant.MontoTotal - ant.MontoUsado) MontoRestante,
	ant.CodigoCuentaBancaria,
	ctaban.NombreCuenta cuenta_bancaria,
	replace(REPLACE(REPLACE(replace(REPLACE(ant.Descripcion, ';',''), '"' , ''),char(13),''),char(10),''),',','#') obs,
	'' numero_cxp,
	0 numeropago,
	0 MontoEnMonedaOriginalDeCxP,
	0 MontoAbonado,
	'' tasacambiopago,
	'' fecha_pago,
	'' NumeroCheque,
	'NO TIENE' status_pago
	
  FROM 
	anticipo ant,
	Proveedor pro,
	CuentaBancaria ctaban

  where 
    pro.ConsecutivoCompania = ant.ConsecutivoCompania
	and ant.ConsecutivoCompania = ctaban.ConsecutivoCompania
	and pro.CodigoProveedor = ant.CodigoProveedor
	-- and ant.Numero = antpa.NumeroAnticipo
	and ant.ConsecutivoCompania = 10
	and ant.Status = '0' 
	and ctaban.Codigo = ant.CodigoCuentaBancaria
	-- and ant.Numero in ('42196739' , '62971423')
	-- and cxp.Numero = '00-00000144' --'0073'  --'00006235'


order by numero_anticipo
