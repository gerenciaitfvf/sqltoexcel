SELECT 
	(case 
		when cxc.TipoCxc = '0' then 'Factura'
		when cxc.TipoCxc = '1' then 'Giro'
		when cxc.TipoCxc = '4' then 'Nota de Debito'
		when cxc.TipoCxc = '3' then 'Nota de Credito'
		else cxc.TipoCxc 
	end) tipocxc,
	pro.Codigo proveedor_rif,
	pro.Nombre proveedor_nombre,
	cxc.Numero numerodoc,
	cxc.Fecha as fecha_factura,
	comp.fecha as fecha_cancelacion,
	(
		select sum(MontoDebe) 
		from asiento	 
		where asiento.NumeroComprobante = comp.Numero and 
		asiento.ConsecutivoPeriodo = comp.ConsecutivoPeriodo 
	) monto_factura,
	replace(REPLACE(REPLACE(replace(REPLACE(
	(select max(rfac.Descripcion) from renglonFactura rfac where rfac.NumeroFactura = cxc.Numero)
	, ';',''), '"' , ''),char(13),''),char(10),''),',','#') obs,
	comp.NombreOperador comprobante_operador,
	(case 
		when cxc.Status = '0' then 'Por Cancelar'
		when cxc.Status = '1' then 'Cancelado'
		when cxc.Status = '4' then 'Anulado'
		when cxc.Status = '3' then 'Abonado'
		else cxc.Status
	end) status_cxc ,
	(
		select cuenta.Descripcion
		from cuenta, asiento
		where asiento.NumeroComprobante = comp.Numero 
		and asiento.ConsecutivoPeriodo = comp.ConsecutivoPeriodo
		and asiento.ConsecutivoAsiento = 1
		and asiento.CodigoCuenta = cuenta.Codigo
		and comp.ConsecutivoPeriodo = cuenta.ConsecutivoPeriodo
	) cxc_cuenta,
	cxc.Moneda,
	cxc.CambioAbolivares tasadecambio,
	cxc.MontoGravado,
	cxc.MontoIva,
	(cxc.MontoGravado + cxc.MontoIva) totalCxC,
	cxc.MontoAbonado,
	(cxc.MontoGravado + cxc.MontoIva - cxc.MontoAbonado) restapagarCxC,
	'Con Renglon Factura' modulo_factura,
	dc.NumeroCobranza,
	dc.MontoAbonado,
	dc.MontoAbonadoEnMonedaOriginal,
	dc.CambioAMonedaLocal,
	co.Fecha fecha_cobranza,
	(select cb.codigo from saw.CuentaBancaria cb, MovimientoBancario mb where cb.codigo = mb.CodigoCtaBancaria and co.numero = mb.NroMovimientoRelacionado  and co.ConsecutivoCompania = mb.ConsecutivoCompania and  mb.ConsecutivoCompania = cb.ConsecutivoCompania ) codigo_banco,
	(select cb.NombreCuenta from saw.CuentaBancaria cb, MovimientoBancario mb where cb.codigo = mb.CodigoCtaBancaria and co.numero = mb.NroMovimientoRelacionado  and co.ConsecutivoCompania = mb.ConsecutivoCompania and  mb.ConsecutivoCompania = cb.ConsecutivoCompania) nombre_banco,
	(
	case 
		when cxc.Status = '0' then datediff(day,cxc.Fecha, CURRENT_TIMESTAMP)
		else datediff(day,cxc.Fecha, co.Fecha)
	end
	
	) antiguedad
  FROM 
	[SAWDB].[dbo].[cxc] cxc,
	COMPROBANTE comp,
	Cliente pro,
	DocumentoCobrado dc, 
	Cobranza co
	
  where 
    pro.ConsecutivoCompania = cxc.ConsecutivoCompania
	and pro.Codigo = cxc.CodigoCliente
	and comp.NoDocumentoOrigen like concat('__',cxc.Numero )  
	and exists (
		select * 
		from PERIODO 
		where cxc.ConsecutivoCompania = PERIODO.ConsecutivoCompania 
			and comp.ConsecutivoPeriodo = PERIODO.ConsecutivoPeriodo
		)
	and cxc.ConsecutivoCompania = 10
	and exists (
		select * from renglonFactura rfac where rfac.NumeroFactura = cxc.Numero
	)
	and dc.NumeroCobranza = co.Numero
	and co.ConsecutivoCompania = cxc.ConsecutivoCompania
	and co.StatusCobranza = 0 -- status no anulado de la cobranza
	and dc.NumeroDelDocumentoCobrado = cxc.Numero
	-- and cxc.Numero like '012331' 

UNION

SELECT 
	(case 
		when cxc.TipoCxc = '0' then 'Factura'
		when cxc.TipoCxc = '1' then 'Giro'
		when cxc.TipoCxc = '4' then 'Nota de Debito'
		when cxc.TipoCxc = '3' then 'Nota de Credito'
		else cxc.TipoCxc 
	end) tipocxc,
	pro.Codigo proveedor_rif,
	pro.Nombre proveedor_nombre,
	cxc.Numero numerodoc,
	cxc.Fecha as fecha_factura,
	comp.fecha as fecha_cancelacion,
	(
		select sum(MontoDebe) 
		from asiento	 
		where asiento.NumeroComprobante = comp.Numero and 
		asiento.ConsecutivoPeriodo = comp.ConsecutivoPeriodo 
	) monto_factura,
	REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(cxc.Descripcion, ';',''), '"' , ''),char(13),''),char(10),''),',','#')  obs,
	comp.NombreOperador comprobante_operador,
	(case 
		when cxc.Status = '0' then 'Por Cancelar'
		when cxc.Status = '1' then 'Cancelado'
		when cxc.Status = '4' then 'Anulado'
		when cxc.Status = '3' then 'Abonado'
		else cxc.Status
	end) status_cxc ,
	(
		select cuenta.Descripcion
		from cuenta, asiento
		where asiento.NumeroComprobante = comp.Numero 
		and asiento.ConsecutivoPeriodo = comp.ConsecutivoPeriodo
		and asiento.ConsecutivoAsiento = 1
		and asiento.CodigoCuenta = cuenta.Codigo
		and comp.ConsecutivoPeriodo = cuenta.ConsecutivoPeriodo
	) cxc_cuenta,
	cxc.Moneda,
	cxc.CambioAbolivares tasadecambio,
	cxc.MontoGravado,
	cxc.MontoIva,
	(cxc.MontoGravado + cxc.MontoIva) totalCxC,
	cxc.MontoAbonado,
	(cxc.MontoGravado + cxc.MontoIva - cxc.MontoAbonado) restapagarCxC,
	'Sin Renglon Factura' modulo_factura,
	dc.NumeroCobranza,
	dc.MontoAbonado,
	dc.MontoAbonadoEnMonedaOriginal,
	dc.CambioAMonedaLocal,
	co.Fecha fecha_cobranza,
	(select cb.codigo from saw.CuentaBancaria cb, MovimientoBancario mb where cb.codigo = mb.CodigoCtaBancaria and co.numero = mb.NroMovimientoRelacionado  and co.ConsecutivoCompania = mb.ConsecutivoCompania and  mb.ConsecutivoCompania = cb.ConsecutivoCompania ) codigo_banco,
	(select cb.NombreCuenta from saw.CuentaBancaria cb, MovimientoBancario mb where cb.codigo = mb.CodigoCtaBancaria and co.numero = mb.NroMovimientoRelacionado  and co.ConsecutivoCompania = mb.ConsecutivoCompania and  mb.ConsecutivoCompania = cb.ConsecutivoCompania) nombre_banco,
	(
	case 
		when cxc.Status = '0' then datediff(day,cxc.Fecha, CURRENT_TIMESTAMP)
		else datediff(day,cxc.Fecha, co.Fecha)
	end
	
	) antiguedad
  FROM 
	[SAWDB].[dbo].[cxc] cxc,
	COMPROBANTE comp,
	Cliente pro,
	DocumentoCobrado dc, 
	Cobranza co
	
  where 
    pro.ConsecutivoCompania = cxc.ConsecutivoCompania
	and pro.Codigo = cxc.CodigoCliente
	and comp.NoDocumentoOrigen like concat('__',cxc.Numero )  
	and exists (
		select * 
		from PERIODO 
		where cxc.ConsecutivoCompania = PERIODO.ConsecutivoCompania 
			and comp.ConsecutivoPeriodo = PERIODO.ConsecutivoPeriodo
		)
	and cxc.ConsecutivoCompania = 10
	and not exists (
		select * from renglonFactura rfac where rfac.NumeroFactura = cxc.Numero
	)
	and dc.NumeroCobranza = co.Numero
	and co.ConsecutivoCompania = cxc.ConsecutivoCompania
	and co.StatusCobranza = 0 -- status no anulado de la cobranza
	and dc.NumeroDelDocumentoCobrado = cxc.Numero
 --	and cxc.Numero like '00000001' 

UNION

SELECT 
	(case 
		when cxc.TipoCxc = '0' then 'Factura'
		when cxc.TipoCxc = '1' then 'Giro'
		when cxc.TipoCxc = '4' then 'Nota de Debito'
		when cxc.TipoCxc = '3' then 'Nota de Credito'
		else cxc.TipoCxc 
	end) tipocxc,
	pro.Codigo proveedor_rif,
	pro.Nombre proveedor_nombre,
	cxc.Numero numerodoc,
	cxc.Fecha as fecha_factura,
	comp.fecha as fecha_cancelacion,
	(
		select sum(MontoDebe) 
		from asiento	 
		where asiento.NumeroComprobante = comp.Numero and 
		asiento.ConsecutivoPeriodo = comp.ConsecutivoPeriodo 
	) monto_factura,
	REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(cxc.Descripcion, ';',''), '"' , ''),char(13),''),char(10),''),',','#') obs,
	comp.NombreOperador comprobante_operador,
	(case 
		when cxc.Status = '0' then 'Por Cancelar'
		when cxc.Status = '1' then 'Cancelado'
		when cxc.Status = '4' then 'Anulado'
		when cxc.Status = '3' then 'Abonado'
		else cxc.Status
	end) status_cxc ,
	(
		select cuenta.Descripcion
		from cuenta, asiento
		where asiento.NumeroComprobante = comp.Numero 
		and asiento.ConsecutivoPeriodo = comp.ConsecutivoPeriodo
		and asiento.ConsecutivoAsiento = 1
		and asiento.CodigoCuenta = cuenta.Codigo
		and comp.ConsecutivoPeriodo = cuenta.ConsecutivoPeriodo
	) cxc_cuenta,
	cxc.Moneda,
	cxc.CambioAbolivares tasadecambio,
	cxc.MontoGravado,
	cxc.MontoIva,
	(cxc.MontoGravado + cxc.MontoIva) totalCxC,
	cxc.MontoAbonado,
	(cxc.MontoGravado + cxc.MontoIva - cxc.MontoAbonado) restapagarCxC,
	'Sin Renglon Factura' modulo_factura,
	'' NumeroCobranza,
	0 MontoAbonado,
	0 MontoAbonadoEnMonedaOriginal,
	0 CambioAMonedaLocal,
	'' fecha_cobranza,
	'' codigo_banco,
	'' nombre_banco,
	(
	case 
		when cxc.Status = '0' then datediff(day,cxc.Fecha, CURRENT_TIMESTAMP)
		else datediff(day,cxc.Fecha, CURRENT_TIMESTAMP)
	end
	
	) antiguedad

  FROM 
	[SAWDB].[dbo].[cxc] cxc,
	COMPROBANTE comp,
	Cliente pro
	
  where 
    pro.ConsecutivoCompania = cxc.ConsecutivoCompania
	and pro.Codigo = cxc.CodigoCliente
	and comp.NoDocumentoOrigen like concat('__',cxc.Numero )  
	and exists (
		select * 
		from PERIODO 
		where cxc.ConsecutivoCompania = PERIODO.ConsecutivoCompania 
			and comp.ConsecutivoPeriodo = PERIODO.ConsecutivoPeriodo
		)
	and cxc.ConsecutivoCompania = 10
	and not exists (
		select * from renglonFactura rfac where rfac.NumeroFactura = cxc.Numero
	)
	and not exists (
		select *
		from 
			DocumentoCobrado dc, 
			Cobranza co
		where 
		dc.NumeroCobranza = co.Numero
		and co.ConsecutivoCompania = cxc.ConsecutivoCompania
		and co.StatusCobranza = 0 -- status no anulado de la cobranza
		and dc.NumeroDelDocumentoCobrado = cxc.Numero
	)
	
	-- and cxc.Numero like '012331' 

UNION

SELECT 
	(case 
		when cxc.TipoCxc = '0' then 'Factura'
		when cxc.TipoCxc = '1' then 'Giro'
		when cxc.TipoCxc = '4' then 'Nota de Debito'
		when cxc.TipoCxc = '3' then 'Nota de Credito'
		else cxc.TipoCxc 
	end) tipocxc,
	pro.Codigo proveedor_rif,
	pro.Nombre proveedor_nombre,
	cxc.Numero numerodoc,
	cxc.Fecha as fecha_factura,
	comp.fecha as fecha_cancelacion,
	(
		select sum(MontoDebe) 
		from asiento	 
		where asiento.NumeroComprobante = comp.Numero and 
		asiento.ConsecutivoPeriodo = comp.ConsecutivoPeriodo 
	) monto_factura,
	REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
	(select max(rfac.Descripcion) from renglonFactura rfac where rfac.NumeroFactura = cxc.Numero)
	, ';',''), '"' , ''),char(13),''),char(10),''),',','#')  obs,
	comp.NombreOperador comprobante_operador,
	(case 
		when cxc.Status = '0' then 'Por Cancelar'
		when cxc.Status = '1' then 'Cancelado'
		when cxc.Status = '4' then 'Anulado'
		when cxc.Status = '3' then 'Abonado'
		else cxc.Status
	end) status_cxc ,
	(
		select cuenta.Descripcion
		from cuenta, asiento
		where asiento.NumeroComprobante = comp.Numero 
		and asiento.ConsecutivoPeriodo = comp.ConsecutivoPeriodo
		and asiento.ConsecutivoAsiento = 1
		and asiento.CodigoCuenta = cuenta.Codigo
		and comp.ConsecutivoPeriodo = cuenta.ConsecutivoPeriodo
	) cxc_cuenta,
	cxc.Moneda,
	cxc.CambioAbolivares tasadecambio,
	cxc.MontoGravado,
	cxc.MontoIva,
	(cxc.MontoGravado + cxc.MontoIva) totalCxC,
	cxc.MontoAbonado,
	(cxc.MontoGravado + cxc.MontoIva - cxc.MontoAbonado) restapagarCxC,
	'Con Renglon Factura' modulo_factura,
	'' NumeroCobranza,
	0 MontoAbonado,
	0 MontoAbonadoEnMonedaOriginal,
	0 CambioAMonedaLocal,
	'' fecha_cobranza,
	'' codigo_banco,
	'' nombre_banco,
	(
	case 
		when cxc.Status = '0' then datediff(day,cxc.Fecha, CURRENT_TIMESTAMP)
		else datediff(day,cxc.Fecha, CURRENT_TIMESTAMP)
	end
	
	) antiguedad

  FROM 
	[SAWDB].[dbo].[cxc] cxc,
	COMPROBANTE comp,
	Cliente pro
	
  where 
    pro.ConsecutivoCompania = cxc.ConsecutivoCompania
	and pro.Codigo = cxc.CodigoCliente
	and comp.NoDocumentoOrigen like concat('__',cxc.Numero )  
	and exists (
		select * 
		from PERIODO 
		where cxc.ConsecutivoCompania = PERIODO.ConsecutivoCompania 
			and comp.ConsecutivoPeriodo = PERIODO.ConsecutivoPeriodo
		)
	and cxc.ConsecutivoCompania = 10
	and exists (
		select * from renglonFactura rfac where rfac.NumeroFactura = cxc.Numero
	)
	and not exists (
		select *
		from 
			DocumentoCobrado dc, 
			Cobranza co
		where 
		dc.NumeroCobranza = co.Numero
		and co.ConsecutivoCompania = cxc.ConsecutivoCompania
		and co.StatusCobranza = 0 -- status no anulado de la cobranza
		and dc.NumeroDelDocumentoCobrado = cxc.Numero
	)
	 -- and cxc.Numero like 'A.00000076'

 order by cxc.Numero asc

