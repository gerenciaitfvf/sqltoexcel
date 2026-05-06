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
	REPLACE(REPLACE(REPLACE(cxp.Observaciones, ';',''),char(13),''),char(10),'') obs,
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
	(cxp.MontoGravado + cxp.MontoIva - cxp.MontoAbonado) restapagarCxP

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
	--and cxp.ConsecutivoCompania = 10
	  and cxp.ConsecutivoCompania in (10, 5)
	-- and cxp.Numero = '00006235' --'0073'  --'00006235'

  order by ConsecutivoCxp asc