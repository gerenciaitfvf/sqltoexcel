/****** Script for SelectTopNRows command from SSMS CXP ******/
SELECT 
	(case 
		when cxp.TipoDeCxp = '0' then 'Factura'
		when cxp.TipoDeCxp = '1' then 'Giro'
		when cxp.TipoDeCxp = '4' then 'Nota de Debito'
		when cxp.TipoDeCxp = '3' then 'Nota de Credito'
		else cxp.TipoDeCxp 
	end) tipocxp,
	pro.CodigoProveedor proveedor_rif,
	pro.NombreProveedor proveedor_nombre,
	concat('''',  cxp.Numero) numerodoc,
	cxp.Fecha as fecha_factura,
	cxp.FechaCancelacion as fecha_cancelacion,
	comp.fecha as fecha_comprobante,
	(
		select sum(MontoDebe) 
		from ASIENTO 
		where asiento.NumeroComprobante = comp.Numero and 
		asiento.ConsecutivoPeriodo = comp.ConsecutivoPeriodo 
	) monto_factura_bs,
	replace(REPLACE(REPLACE(replace(REPLACE(cxp.Observaciones, ';',''), '"' , ''),char(13),''),char(10),''),',','#') obs,
	comp.NombreOperador comprobante_operador,
	(case 
		when cxp.Status = '0' then 'Por Cancelar'
		when cxp.Status = '1' then 'Cancelado'
		when cxp.Status = '4' then 'Anulado'
		when cxp.Status = '3' then 'Abonado'
		else cxp.Status
	end) status_cxp,
	(
		select cuenta.Descripcion
		from cuenta, asiento
		where asiento.NumeroComprobante = comp.Numero 
		and asiento.ConsecutivoPeriodo = comp.ConsecutivoPeriodo
		and asiento.ConsecutivoAsiento = 1
		and asiento.CodigoCuenta = cuenta.Codigo
		and comp.ConsecutivoPeriodo = cuenta.ConsecutivoPeriodo
	) cxp_cuenta,
	cxp.Moneda,
	cxp.CambioAbolivares tasadecambio,
	cxp.MontoGravado,
	cxp.MontoIva,
	(cxp.MontoGravado + cxp.MontoIva) totalCxP,
	cxp.MontoAbonado,
	(cxp.MontoGravado + cxp.MontoIva - cxp.MontoAbonado) restapagarCxP,
	dp.NumeroComprobante numeropago,
	dp.MontoAbonado,
	dp.MontoEnMonedaOriginalDeCxP,
	dp.CambioAMonedaDelPago tasacambiopago,
	p.Fecha fecha_pago,
	p.NumeroCheque,
	(case 
		when p.StatusOrdenDePago = '0' then 'Vigente'
		when p.StatusOrdenDePago = '1' then 'Anulado'
		else cxp.Status
	end) status_pago,
	'TIENE PAGO' referencia_pago
	
  FROM 
	[SAWDB].[dbo].[cxP] cxp,
	COMPROBANTE comp,
	Proveedor pro,
	Pago p,
	DocumentoPagado dp

  where 
    pro.ConsecutivoCompania = cxp.ConsecutivoCompania
	and pro.CodigoProveedor = cxp.CodigoProveedor
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
	-- and cxp.Numero = 'AC-10112023' --'0073'  --'00006235'

union

SELECT 
	(case 
		when cxp.TipoDeCxp = '0' then 'Factura'
		when cxp.TipoDeCxp = '1' then 'Giro'
		when cxp.TipoDeCxp = '4' then 'Nota de Debito'
		when cxp.TipoDeCxp = '3' then 'Nota de Credito'
		else cxp.TipoDeCxp 
	end) tipocxp,
	pro.CodigoProveedor proveedor_rif,
	pro.NombreProveedor proveedor_nombre,
	concat('''',  cxp.Numero) numerodoc,
	cxp.Fecha as fecha_factura,
	cxp.FechaCancelacion as fecha_cancelacion,
	comp.fecha as fecha_comprobante,
	(
		select sum(MontoDebe) 
		from ASIENTO 
		where asiento.NumeroComprobante = comp.Numero and 
		asiento.ConsecutivoPeriodo = comp.ConsecutivoPeriodo 
	) monto_factura_bs,
	replace(REPLACE(REPLACE(replace(REPLACE(cxp.Observaciones, ';',''), '"' , ''),char(13),''),char(10),''),',','#') obs,
	comp.NombreOperador comprobante_operador,
	(case 
		when cxp.Status = '0' then 'Por Cancelar'
		when cxp.Status = '1' then 'Cancelado'
		when cxp.Status = '4' then 'Anulado'
		when cxp.Status = '3' then 'Abonado'
		else cxp.Status
	end) status_cxp,
	(
		select cuenta.Descripcion
		from cuenta, asiento
		where asiento.NumeroComprobante = comp.Numero 
		and asiento.ConsecutivoPeriodo = comp.ConsecutivoPeriodo
		and asiento.ConsecutivoAsiento = 1
		and asiento.CodigoCuenta = cuenta.Codigo
		and comp.ConsecutivoPeriodo = cuenta.ConsecutivoPeriodo
	) cxp_cuenta,
	cxp.Moneda,
	cxp.CambioAbolivares tasadecambio,
	cxp.MontoGravado,
	cxp.MontoIva,
	(cxp.MontoGravado + cxp.MontoIva) totalCxP,
	cxp.MontoAbonado,
	(cxp.MontoGravado + cxp.MontoIva - cxp.MontoAbonado) restapagarCxP,
	0 numeropago,
	0 MontoAbonado,
	0 MontoEnMonedaOriginalDeCxP,
	0 tasacambiopago,
	'' fecha_pago,
	'' NumeroCheque,
	'NO PAGO' status_pago,
	'NO PAGO' referencia_pago
	
  FROM 
	[SAWDB].[dbo].[cxP] cxp,
	COMPROBANTE comp,
	Proveedor pro

  where 
    pro.ConsecutivoCompania = cxp.ConsecutivoCompania
	and pro.CodigoProveedor = cxp.CodigoProveedor
	and cxp.ConsecutivoCxp = comp.ConsecutivoDocOrigen
	and exists (
		select * 
		from PERIODO 
		where cxp.ConsecutivoCompania = PERIODO.ConsecutivoCompania 
			and comp.ConsecutivoPeriodo = PERIODO.ConsecutivoPeriodo
		)
	and cxp.ConsecutivoCompania = 10
	and not exists (
		select * 
		from Pago p, DocumentoPagado dp
		where dp.NumeroComprobante = p.NumeroComprobante
		and dp.NumeroDelDocumentoPagado = cxp.Numero
		and cxp.ConsecutivoCompania = p.ConsecutivoCompania
		and p.Origen not in (0) -- se excluyen pagos tipo retencion
		and p.CodigoProveedor = cxp.CodigoProveedor
	)


  order by numerodoc asc