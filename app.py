from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import pyodbc


app = Flask(__name__,template_folder='templates', static_folder='static')

# Configurar a conexão com o banco de dados SQL Server
conn = pyodbc.connect(
    'Driver={SQL Server};'
    'Server=138.219.91.72,38000;'
    'Database=C8KRDC_128994_RM_PD;'
    'UID=CLT128994gabriel.gomes;'
    'PWD=iptju40167HJDMT@?;'
)

# Criar um cursor para executar consultas SQL
cursor = conn.cursor()

# Rota para exibir os leads
@app.route('/')
def index():
   
    return render_template('inicial.html')

    # Rota para exibir os leads
    
@app.route('/painel', methods=['GET', 'POST'])
def dados_estoque():
    
    codcoligadafilial =''
    
            
    #se estiver executando uma ação
    if request.method =='POST':
    
        codcoligadafilial = request.form.get('codcoligadafilial')
        grupo = request.form.get('grupo')
        
            
    #se estiver pesquisando sem preencher a filial
    if not codcoligadafilial:
        return render_template('painel.html')
        #return f"Por favor, preencha a COLIGADA e a filial",400
    
    codcoligadafilial = str(codcoligadafilial)     
    print(codcoligadafilial)
    print(grupo)
    cursor.execute("""
                    DECLARE @CODCOLIGADAFILIAL VARCHAR(3);
                    DECLARE @GRUPO VARCHAR(2);
                   
                    SET @CODCOLIGADAFILIAL = ?;
                    SET @GRUPO =?

					
					SELECT GERAL.C, GERAL.D, GERAL.U1, GERAL.U2, GERAL.U3, GERAL.SD, GERAL.M1, GERAL.M2, GERAL.M3, GERAL.MEDIA, GERAL.SUGESTAO, '', GERAL.INV1, GERAL.INV2, GERAL.PMEDIO, GERAL.MINIMO,
					CASE WHEN (GERAL.SD >0  AND GERAL.SUGESTAO=0 ) THEN 'ALTO' ELSE 
					CASE WHEN (GERAL.SD >0 AND (GERAL.SUGESTAO/GERAL.SD) > 2.5) THEN 'NORMAL' ELSE 
					CASE WHEN (GERAL.SD >0 AND (GERAL.SUGESTAO/GERAL.SD) > 2) THEN 'NORMAL' ELSE 
					CASE WHEN (GERAL.SD = 0 AND GERAL.SUGESTAO>0 ) THEN 'BAIXO' ELSE
					CASE WHEN (GERAL.SD > 0 AND GERAL.SUGESTAO>0) THEN 'BAIXO' ELSE
					CASE WHEN (GERAL.SD = 0 AND GERAL.SUGESTAO=0 ) THEN
						 CASE WHEN GERAL.MINIMO > 0 THEN 'ABAIXO DO MINIMO' ELSE 'ZERADO' END ELSE
					'NAO DEFINIDO' END END END END END END 'ESTOQUE_MINIMO'
					FROM 
					(
					SELECT U.CODIGO C, P.DESCRICAO D, UND.CODUNDCONTROLE U1, UND.CODUNDCOMPRA U2,UND.CODUNDVENDA U3, SUM(U.SALDO) SD, SUM(U.M1) M1, SUM(U.M2) M2, SUM(U.M3) M3, 
						   (SUM(U.M1)+SUM(U.M2)+SUM(U.M3))/3 MEDIA, 
					CASE WHEN SUM(U.SALDO) > ((SUM(U.M1)+SUM(U.M2)+SUM(U.M3))/3) THEN 0  ELSE
						((SUM(U.M1)+SUM(U.M2)+SUM(U.M3))/3) - SUM(U.SALDO) END SUGESTAO,
						SUM(U.INV_E) INV1, SUM(U.INV_S) INV2, P.CUSTOMEDIO PMEDIO, SUM(U.MINIMO) MINIMO
   

					FROM TPRD P LEFT JOIN TPRODUTODEF UND ON P.CODCOLIGADA = UND.CODCOLIGADA AND P.IDPRD = UND.IDPRD,
					(
					 select P.CODIGOPRD CODIGO, ISNULL(L.SALDOFISICO2,0) SALDO, 0 M1, 0 M2, 0 M3 ,0 INV_E, 0 INV_S, 0 MINIMO
					 from tprd P 
						  LEFT JOIN TPRDLOC L ON P.CODCOLIGADA=L.CODCOLIGADA AND P.IDPRD = L.IDPRD
							   AND P.CODCOLIGADA=SUBSTRING(@CODCOLIGADAFILIAL,1,1) AND L.CODFILIAL=SUBSTRING(@CODCOLIGADAFILIAL,3,1) 
							   AND SUBSTRING(P.CODIGOPRD,1,2)=@GRUPO
                               AND SUBSTRING(P.CODIGOPRD,1,2)<>'02'
           
					UNION ALL
					 select P.CODIGOPRD CODIGO, 0 SALDO, 0 M1, 0 M2, 0 M3 ,0 INV_E, 0 INV_S, ISNULL(L.SALDFISMIN,0) MINIMO
					 from TPRD P 
						  LEFT JOIN TPRDLOCINFO L ON P.CODCOLIGADA=L.CODCOLIGADA AND P.IDPRD = L.IDPRD
							   AND P.CODCOLIGADA=SUBSTRING(@CODCOLIGADAFILIAL,1,1) AND L.CODFILIAL=SUBSTRING(@CODCOLIGADAFILIAL,3,1) 
							   AND SUBSTRING(P.CODIGOPRD,1,2)=@GRUPO
                               AND SUBSTRING(P.CODIGOPRD,1,2)<>'02'

					UNION ALL
					SELECT P.CODIGOPRD CODIGO, 0 SALDO, SUM(I.QUANTIDADE) M1, 0 M2, 0  M3,0 INV_E, 0 INV_S, 0 MINIMO
					from tprd P, TMOV T, TITMMOV I
					WHERE T.CODCOLIGADA=I.CODCOLIGADA AND T.IDMOV=I.IDMOV
					AND I.CODCOLIGADA=P.CODCOLIGADA AND I.IDPRD=P.IDPRD
					AND T.CODCOLIGADA=SUBSTRING(@CODCOLIGADAFILIAL,1,1) AND T.CODFILIAL=SUBSTRING(@CODCOLIGADAFILIAL,3,1)
					AND SUBSTRING(P.CODIGOPRD,1,2)=@GRUPO
                    AND T.CODTMV='1.1.51' AND right(convert(varchar(10),T.DATAEMISSAO,103),7) = right(convert(varchar(10),getdate()-90,103),7)
					GROUP BY P.CODIGOPRD
  
					UNION ALL
					SELECT P.CODIGOPRD CODIGO, 0 SALDO, 0 M1,SUM(I.QUANTIDADE) M2, 0 M3,0 INV_E, 0 INV_S, 0 MINIMO
					from tprd P, TMOV T, TITMMOV I
					WHERE T.CODCOLIGADA=I.CODCOLIGADA AND T.IDMOV=I.IDMOV
					AND I.CODCOLIGADA=P.CODCOLIGADA AND I.IDPRD=P.IDPRD
					AND T.CODCOLIGADA=SUBSTRING(@CODCOLIGADAFILIAL,1,1) AND T.CODFILIAL=SUBSTRING(@CODCOLIGADAFILIAL,3,1)
					AND SUBSTRING(P.CODIGOPRD,1,2)=@GRUPO
                    AND T.CODTMV='1.1.51' AND right(CONVERT(VARCHAR(10),T.DATAEMISSAO,103),7)= right(convert(varchar(10),getdate()-59,103),7)
					GROUP BY P.CODIGOPRD
  
					UNION ALL
					SELECT P.CODIGOPRD CODIGO, 0 SALDO, 0 M1, 0 M2, SUM(I.QUANTIDADE) M3,0 INV_E, 0 INV_S, 0 MINIMO
					from tprd P, TMOV T, TITMMOV I
					WHERE T.CODCOLIGADA=I.CODCOLIGADA AND T.IDMOV=I.IDMOV
					AND I.CODCOLIGADA=P.CODCOLIGADA AND I.IDPRD=P.IDPRD
					AND T.CODCOLIGADA=SUBSTRING(@CODCOLIGADAFILIAL,1,1) AND T.CODFILIAL=SUBSTRING(@CODCOLIGADAFILIAL,3,1)
					AND SUBSTRING(P.CODIGOPRD,1,2)=@GRUPO
                    AND T.CODTMV='1.1.51' AND right(CONVERT(VARCHAR(10),T.DATAEMISSAO,103),7)= right(convert(varchar(10),getdate()-30,103),7)
					GROUP BY P.CODIGOPRD
  
					UNION ALL
					SELECT P.CODIGOPRD CODIGO, 0 SALDO, 0 M1, 0 M2,0 M3,SUM(I.QUANTIDADE) INV_E, 0 INV_S, 0 MINIMO
					from tprd P, TMOV T, TITMMOV I
					WHERE T.CODCOLIGADA=I.CODCOLIGADA AND T.IDMOV=I.IDMOV
					AND I.CODCOLIGADA=P.CODCOLIGADA AND I.IDPRD=P.IDPRD
					AND T.CODCOLIGADA=SUBSTRING(@CODCOLIGADAFILIAL,1,1) AND T.CODFILIAL=SUBSTRING(@CODCOLIGADAFILIAL,3,1)
					AND SUBSTRING(P.CODIGOPRD,1,2)=@GRUPO
                    AND T.CODTMV='4.1.01' AND right(CONVERT(VARCHAR(10),T.DATAEMISSAO,103),7)= right(convert(varchar(10),getdate()-30,103),7)
					GROUP BY P.CODIGOPRD
  
					UNION ALL
					SELECT P.CODIGOPRD CODIGO, 0 SALDO, 0 M1, 0 M2, 0 M3, 0 INV_E, SUM(I.QUANTIDADE) INV_S, 0 MINIMO
					from tprd P, TMOV T, TITMMOV I
					WHERE T.CODCOLIGADA=I.CODCOLIGADA AND T.IDMOV=I.IDMOV
					AND I.CODCOLIGADA=P.CODCOLIGADA AND I.IDPRD=P.IDPRD
					AND T.CODCOLIGADA=SUBSTRING(@CODCOLIGADAFILIAL,1,1) AND T.CODFILIAL=SUBSTRING(@CODCOLIGADAFILIAL,3,1)
					AND SUBSTRING(P.CODIGOPRD,1,2)=@GRUPO
                    AND T.CODTMV='4.1.03' AND right(CONVERT(VARCHAR(10),T.DATAEMISSAO,103),7)= right(convert(varchar(10),getdate()-30,103),7)
					GROUP BY P.CODIGOPRD
					) U
					WHERE P.CODCOLIGADA =SUBSTRING(@CODCOLIGADAFILIAL,1,1) AND P.CODIGOPRD=U.CODIGO
                    AND SUBSTRING(P.CODIGOPRD,1,2)=@GRUPO
					AND P.ULTIMONIVEL=1 AND SUBSTRING(P.CODIGOPRD,1,2)<>'02'
					AND P.INATIVO=0 
					GROUP BY U.CODIGO, P.DESCRICAO,P.CUSTOMEDIO,UND.CODUNDCONTROLE, UND.CODUNDCOMPRA, UND.CODUNDVENDA
					) GERAL

					ORDER BY GERAL.D """,(codcoligadafilial,grupo))
    
    
    dados = cursor.fetchall()       
    
    return render_template('painel.html', dados=dados, codcoligadafilial=codcoligadafilial, grupo=grupo)

#rotas e funções da tela de transferencia#
@app.route('/transferencia',methods=['GET','POST'])
def dados_transferencia():
    
          
    
    origem = ''
    destino = ''
    query = ''
    dados= ''    
    
    
    #request by name  
    datainicial = request.form.get('datainicial')
    if datainicial:
            datainicial = datetime.strptime(datainicial, '%Y-%m-%d').strftime('%d/%m/%Y')    
    datafinal = request.form.get('datafinal')
    if datafinal:
            datafinal = datetime.strptime(datafinal, '%Y-%m-%d').strftime('%d/%m/%Y')  
    

    origem = request.form.get('origem') 
    destino = request.form.get('destino')        
   		    
    print(datainicial)
    print(datafinal)
    print(origem)
    print(destino)
    
    query = cursor.execute("""
                   DECLARE @DATAINICIAL VARCHAR(10);
			       DECLARE  @DATAFINAL VARCHAR(10);
				   DECLARE @ORIGEM VARCHAR(30);
				   DECLARE @DESTINO VARCHAR(30);
                  
                   SET @DATAINICIAL = ?;
			       SET @DATAFINAL = ?;
				   SET @ORIGEM = ?;
				   SET @DESTINO = ?;
			       
                  
					select  /* tabela principal tabela de movimentos TMOV*/
					t.codcoligada, 
					t.numeromov,
					CONVERT(VARCHAR,t.dataemissao,103) DATAEMISSAO,
					(tit.quantidade * tit.valorbrutoitem) VALOR,				
					gfilial.NOMEFANTASIA ORIGEM,
					DESTINO.FILIALDESTINO DESTINO,
					t.CODTMV,
					t.STATUS,
					prod.DESCRICAO,
                    convert(varchar,t.dataemissao,103),
					concat(cast(tit.quantidade as int),' ',tit.codund),
				
					CASE WHEN T.STATUS = 'N' THEN 'NORMAL'
						WHEN T.STATUS = 'A' THEN 'PENDENTE'
						WHEN T.STATUS = 'G' THEN 'PARC.RECEB'
						WHEN T.STATUS = 'F' THEN 'A PAGAR'
						WHEN T.STATUS = 'P' THEN 'Parc.Quitado'
						WHEN T.STATUS = 'Q' THEN 'Quitado'
						WHEN T.STATUS = 'C' THEN 'Cancelado'
						WHEN T.STATUS = 'D' THEN 'Perda'
						WHEN T.STATUS = 'I' THEN 'Inativo'
						WHEN T.STATUS = 'R' THEN 'Não processado'
						WHEN T.STATUS = 'B' THEN 'Bloqueado'
						WHEN T.STATUS = 'U' THEN 'Em faturamento'
						WHEN T.STATUS = 'O' THEN 'Aguardando Análise'
						WHEN T.STATUS = 'Y' THEN 'Nao iniciado'
						WHEN T.STATUS = 'E' THEN 'Em andamento'
						WHEN T.STATUS = 'Z' THEN 'Terminado'   END STATUS,

				
				
					t.RECCREATEDBY 'CRIADO_POR',
					t.RECMODIFIEDBY 'ULTIMA_MODIFICACAO'
				
			from tmov t

			inner join TITMMOV tit /*TABELA DE ITEM*/
			on t.idmov = tit.IDMOV 
			and tit.codcoligada = t.codcoligada

			inner join TPRODUTO prod
			on tit.IDPRD = prod.IDPRD

			inner join gfilial /*TABELA DE FILIAL*/
			on t.codcoligada = gfilial.codcoligada
			and t.CODFILIAL = gfilial.CODFILIAL  
			and tit.CODCOLIGADA = gfilial.codcoligada 
			and tit.CODfilial = gfilial.codfilial
			
			inner join gcoligada
			ON GFILIAL.CODCOLIGADA = GCOLIGADA.CODCOLIGADA
			
			/*subquery como uma tabela pois a chave de filial é a mesma para destino e origem, então foi criada uma tabela 'DESTINO' para join com a chave da filial destino*/
			inner join (select t.codcoligada,t.CODFILIALDESTINO,t.idmov, g.NOMEFANTASIA FILIALDESTINO 
						FROM TMOV t 
						LEFT JOIN GFILIAL g
						ON T.CODCOLIGADA = G.CODCOLIGADA and T.CODFILIALDESTINO = G.CODFILIAL 
						LEFT JOIN GCOLIGADA 
						ON G.CODCOLIGADA = GCOLIGADA.CODCOLIGADA) DESTINO
						
			on t.codcoligada = DESTINO.codcoligada 
			and t.idmov = DESTINO.idmov 
			and t.CODFILIALdestino = DESTINO.CODFILIALDESTINO

			where 
				t.CODTMV = '3.1.01'
			AND (CONVERT(DATE, t.dataemissao, 103) >= CONVERT(DATE, @DATAINICIAL, 103)
				AND CONVERT(DATE, t.dataemissao, 103) <= CONVERT(DATE, @DATAFINAL, 103))
			and gfilial.NOMEFANTASIA = @ORIGEM
			and DESTINO.FILIALDESTINO = @DESTINO

                   """,(datainicial,datafinal,origem,destino))
    
    #CONVERTER DATA QUE VEM DO FORMULÁRIO#
    dados = query.fetchall()
    #print(dados)
    return render_template('transferencia.html',dados=dados,datainicial=datainicial,datafinal=datafinal,origem=origem,destino=destino)



if __name__ == '__main__':
    app.run(debug=True)
