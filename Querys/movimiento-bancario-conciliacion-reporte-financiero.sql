select
	cb.Codigo,
	cb.NumeroCuenta,
	cb.NombreCuenta,
	cb.NombreDeLaMoneda,
	mb.fecha,
	mb.NumeroDocumento,
	(case 
		when mb.TipoConcepto = 1 then 'Egresos'
		else 'Ingresos'
	end) concepto,
	mb.ConsecutivoMovimiento,
	replace(REPLACE(REPLACE(replace(REPLACE(mb.Descripcion, ';',''), '"' , ''),char(13),''),char(10),''),',','#') descripcion,
	(case 
		when mb.GeneradoPor = '2'  then (select pago.CambioaBolivares from Pago where pago.NumeroComprobante = mb.NroMovimientoRelacionado  and pago.ConsecutivoCompania = mb.ConsecutivoCompania )
		when mb.GeneradoPor = '1'  then (select cobranza.CambioAbolivares from Cobranza where Cobranza.numero = mb.NroMovimientoRelacionado  and Cobranza.ConsecutivoCompania = mb.ConsecutivoCompania )
		when mb.GeneradoPor = '8'  then (select anticipo.Cambio from anticipo where anticipo.ConsecutivoAnticipo = mb.NroMovimientoRelacionado  and anticipo.ConsecutivoCompania = mb.ConsecutivoCompania )
		when mb.GeneradoPor = '<'  then 1
		else -1
	end) tasadecambio,
	(case 
		when mb.TipoConcepto = 1 then 0
		else mb.Monto
	end) debe,
	(case 
		when mb.TipoConcepto = 1 then mb.Monto
		else 0
	end) haber,
	mb.Monto total,
	(case 
		when mb.GeneradoPor = '2'  then (select CodigoProveedor from Pago where pago.NumeroComprobante = mb.NroMovimientoRelacionado  and pago.ConsecutivoCompania = mb.ConsecutivoCompania )
		when mb.GeneradoPor = '1'  then (select CodigoCliente from Cobranza where Cobranza.numero = mb.NroMovimientoRelacionado  and Cobranza.ConsecutivoCompania = mb.ConsecutivoCompania )
		when mb.GeneradoPor = '8'  then (select case when CodigoCliente = '' then CodigoProveedor else CodigoCliente end from anticipo where anticipo.ConsecutivoAnticipo = mb.NroMovimientoRelacionado  and anticipo.ConsecutivoCompania = mb.ConsecutivoCompania )
		when mb.GeneradoPor = '<'  then 'J001330321'
		else 'que paso con este'
	end) rif,
	replace(REPLACE(REPLACE(replace(REPLACE(
	(case 
		when mb.GeneradoPor = '2'  then (select pro.NombreProveedor from pago, adm.Proveedor pro where pago.CodigoProveedor = pro.CodigoProveedor and pago.ConsecutivoCompania = pro.ConsecutivoCompania and pago.NumeroComprobante = mb.NroMovimientoRelacionado  and pago.ConsecutivoCompania = mb.ConsecutivoCompania )
		when mb.GeneradoPor = '1'  then (select cli.Nombre from Cobranza, Cliente cli where cli.Codigo = cobranza.CodigoCliente and cli.ConsecutivoCompania = Cobranza.ConsecutivoCompania and Cobranza.numero = mb.NroMovimientoRelacionado  and Cobranza.ConsecutivoCompania = mb.ConsecutivoCompania )
		when mb.GeneradoPor = '8'  then (select case when CodigoCliente = '' then 
																( select pro.nombreproveedor from adm.proveedor pro where anticipo.CodigoProveedor = pro.CodigoProveedor  and anticipo.ConsecutivoCompania = pro.ConsecutivoCompania  )
															else 
																( select cli.nombre from Cliente cli where cli.Codigo = anticipo.CodigoCliente and cli.ConsecutivoCompania = anticipo.ConsecutivoCompania ) 
															end 
															from anticipo where anticipo.ConsecutivoAnticipo = mb.NroMovimientoRelacionado  and anticipo.ConsecutivoCompania = mb.ConsecutivoCompania )
		when mb.GeneradoPor = '<'  then 'FEDERACIÓN VENEZOLANA DE FUTBOL'
		else 'que paso con este'
	end)
	, ';',''), '"' , ''),char(13),''),char(10),''),',','#') nombre_proveedor,
	mb.NombreOperador,
	(case 
		when mb.GeneradoPor = '2'  then (select 
											case 
											when StatusOrdenDePago = 0 then 'vigente'
											else 'anulado'
											end 
										from Pago 
										where pago.NumeroComprobante = mb.NroMovimientoRelacionado 
										and pago.ConsecutivoCompania = mb.ConsecutivoCompania )
		when mb.GeneradoPor = '1'  then (select
											case 
											when StatusCobranza = 0 then 'vigente'
											else 'anulado'
											end from Cobranza where Cobranza.numero = mb.NroMovimientoRelacionado  and Cobranza.ConsecutivoCompania = mb.ConsecutivoCompania )
		when mb.GeneradoPor = '8'  then (select case
											when Status = '1' then 'anulado'
											else 'vigente anticipo'
										end
										from anticipo 
										where anticipo.ConsecutivoAnticipo = mb.NroMovimientoRelacionado  and anticipo.ConsecutivoCompania = mb.ConsecutivoCompania 
										)
		when mb.GeneradoPor = '<'  then 'vigente con bivhito'
		when mb.GeneradoPor = '0'  then 'vigente generadopor0'
		else 'vigente diferente'
	end) status_movimiento

from 
	saw.CuentaBancaria cb,
	MovimientoBancario mb

where

	cb.codigo = mb.CodigoCtaBancaria
	and cb.NumeroCuenta not like '%GEN%RICA%'  
	and upper(mb.Descripcion) not like 'DEVOLUCI%N%'
	and upper(mb.Descripcion) not like '%DEVOLUCI%N%DE%ANTICIPO%'
	and upper(mb.Descripcion) not like 'TRASPASO%'  
	and upper(mb.Descripcion) not like 'REVERSO%'
	and cb.ConsecutivoCompania = mb.ConsecutivoCompania
	and cb.ConsecutivoCompania in (5, 10)
	-- and mb.GeneradoPor not in ('0') -- movimientos bancarios anulados
	and mb.Fecha > '2021-06-30'
	AND mb.Fecha < '2026-02-01'
	-- and mb.ConsecutivoMovimiento = 28071
	
order by mb.fecha desc

