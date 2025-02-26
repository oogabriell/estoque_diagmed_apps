from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import pyodbc
import os
#import currency

app = Flask(__name__,template_folder='templates', static_folder='static')

server =  os.getenv("SERVER_RM_PROD")
database = os.getenv("DB_RM_PROD")
usuario = os.getenv("DB_USER_RM_PROD")
senha = os.getenv("DB_PASSWORD_RM_PROD")

#print(senha)
#print(variavel)

# Verificar se a variável de ambiente foi definida
if senha is None:
    raise ValueError("Senha não localizada")
if usuario is None:
    raise ValueError("Usuário não localizado")


conn = pyodbc.connect(
    'Driver={ODBC Driver 18 for SQL Server};'
    f'Server={server};'
    f'Database={database};'
    f'UID={usuario};'
    f'PWD={senha};'
    'Encrypt=no;'  # Tente manter a criptografia ativada
    'TrustServerCertificate=yes;'  # Confiança no certificado do servidor
    'Connection Timeout=10;'  # Timeout opcional
)

cursor = conn.cursor()

@app.route('/')
def index():
   
    return render_template('inicial.html')

  
@app.route('/painel', methods=['GET', 'POST'])
def dados_estoque():
    
    # não há parâmetros pois a necessidade dos usuários é de ver tudo que está crítico
    cursor.execute("""
                                                                                       
                                                                                     
                                                                                   
                                                                              
      /***ajustar PARÂMETRO DE DATA*/

	 SELECT  SALDO_DO_ITEM.LOCAL_ESTOQUE,
                                SALDO_DO_ITEM.CODIGOPRD,
                                SALDO_DO_ITEM.NOME_PRODUTO,
                                SALDO_DO_ITEM.U1 UNIDADE, --UNIDADE DE CONTROLE
                                FORMAT( SALDO_DO_ITEM.CUSTOMEDIO,'C', 'pt-BR')CUSTOMEDIO,
                                FORMAT(SALDO_DO_ITEM.SALDO_QTDE,'C', 'pt-BR')SALDO_QTDE,
                                FORMAT(mov_ultimos_meses.MEDIA_3_MESES,'C', 'pt-BR')MEDIA_3_MESES, 
                                (SALDO_DO_ITEM.SALDO_QTDE/NULLIF(mov_ultimos_meses.MEDIA_3_MESES,0)) PERCENTUAL ,                                                          
							    CASE WHEN (SALDO_DO_ITEM.SALDO_QTDE/NULLIF(mov_ultimos_meses.MEDIA_3_MESES,0)) =  0 THEN 'CRÍTICO'
                                        WHEN (SALDO_DO_ITEM.SALDO_QTDE/NULLIF(mov_ultimos_meses.MEDIA_3_MESES,0)) <  0.2 THEN 'CRÍTICO'
                                        WHEN (SALDO_DO_ITEM.SALDO_QTDE/NULLIF(mov_ultimos_meses.MEDIA_3_MESES,0)) >= 0.2 AND (SALDO_DO_ITEM.SALDO_QTDE/NULLIF(mov_ultimos_meses.MEDIA_3_MESES,0)) < 0.75  THEN 'ALERTA'
                                        WHEN (SALDO_DO_ITEM.SALDO_QTDE/NULLIF(mov_ultimos_meses.MEDIA_3_MESES,0)) >= 0.75 AND (SALDO_DO_ITEM.SALDO_QTDE/NULLIF(mov_ultimos_meses.MEDIA_3_MESES,0)) < 1.25  THEN 'NORMAL'
                                        WHEN (SALDO_DO_ITEM.SALDO_QTDE/NULLIF(mov_ultimos_meses.MEDIA_3_MESES,0)) >= 1.25 THEN 'ALTO'
                                     ELSE 'N/A' END AS 'SITUACAO'

                                    
                        FROM    

                                                        
                            (SELECT DISTINCT                            LOCAL_ESTOQUE.CODCOLIGADA,
                                                LOCAL_ESTOQUE.CODFILIAL,
                                                PROD.CODIGOPRD,
                                                PROD.IDPRD,
                                                PROD.NOMEFANTASIA AS 'NOME_PRODUTO',
                                                LOCAL_ESTOQUE.NOME as 'LOCAL_ESTOQUE',
                                                UNIDADES_PRODUTO.RECCREATEDON CRIACAO_UND_CONTROLE,
                                                SALDO.CUSTOMEDIO,
                                                prod.CODUNDCONTROLE AS 'U1',                                                
                                                ISNULL(SALDO.saldofisico2,0)  AS 'SALDO_QTDE',                                              
                                                ROW_NUMBER() OVER (PARTITION BY PROD.CODIGOPRD, LOCAL_ESTOQUE.CODCOLIGADA,LOCAL_ESTOQUE.CODFILIAL  ORDER BY UNIDADES_PRODUTO.RECCREATEDON DESC) AS RANK_UNIDADE_CONTROLE
												
                                        FROM TPRD PROD
                                                        
                                        LEFT JOIN TPRDLOC SALDO
                                        ON PROD.IDPRD = SALDO.IDPRD
										                                        
                                        LEFT JOIN TPRODUTODEF DEF
                                        ON SALDO.IDPRD = DEF.IDPRD
                                            AND SALDO.CODCOLIGADA = DEF.CODCOLIGADA
                                    
                                        LEFT JOIN TLOC LOCAL_ESTOQUE
                                        ON DEF.CODCOLIGADA = LOCAL_ESTOQUE.CODCOLIGADA      
                                        AND SALDO.CODLOC = LOCAL_ESTOQUE.CODLOC
                                        AND SALDO.CODFILIAL = LOCAL_ESTOQUE.CODFILIAL                                       
                                    

                                        LEFT JOIN TPRDUND UNIDADES_PRODUTO
                                        ON prod.CODUNDCONTROLE = UNIDADES_PRODUTO.CODUND
                                            AND DEF.CODCOLIGADA = UNIDADES_PRODUTO.CODCOLIGADA
                                            AND DEF.IDPRD = UNIDADES_PRODUTO.IDPRD

                                        /*TPRDUND COLOCAR A TABELA DE UNIDADE DE CONTROLE X PRODUTO PORÉM TEM QUE VIR SEMPRE O ULTIMO CADASTRO REALIZADO PORQUE PODEM TER HAVIDO MAIS DE UMA UNIDADE DE CONTROLE */


                                        WHERE PROD.INATIVO = 0                                                                                                         
                                            AND PROD.CODUNDCONTROLE IS NOT NULL
                                           
                                
                                        ) SALDO_DO_ITEM
                                        
                                        

                /* ESSA TABELA SERÁ A DE MÉDIA DOS ÚLTIMOS MESES*/

            ,(
                    
					SELECT 
							U.IDPRODUTO,
							u.codcoligada CODCOLIGADA,
							U.CODFILIAL,
							SUM(U.M1) 'M1',
							SUM(U.M2) 'M2',
							SUM(U.M3) 'M3',
							AVG(U.M1 + U.M2 + U.M3) MEDIA_3_MESES
  
							FROM  
							(
								
								SELECT 
									i.codcoligada,
									i.codfilial,
									P.IDPRD IDPRODUTO,  
									0 SALDO, 
									SUM(I.QUANTIDADE) M1, 
									0 M2, 
									0 M3, 
									0 INV_E, 
									0 INV_S, 
									0 MINIMO
								FROM tprd P, TMOV T, TITMMOV I
								WHERE T.CODCOLIGADA = I.CODCOLIGADA 
									AND T.IDMOV = I.IDMOV
									AND I.CODCOLIGADA = P.CODCOLIGADA 
									AND I.IDPRD = P.IDPRD          
									AND T.CODTMV = '1.1.51' 
									AND RIGHT(CONVERT(VARCHAR(10), T.DATAEMISSAO, 103), 7) = right(convert(varchar(10),DATEADD(month,-3,GETDATE()),103),7)
								GROUP BY i.codcoligada, i.codfilial, P.IDPRD
        
								UNION ALL

								SELECT 
									i.codcoligada,
									i.codfilial,
									P.IDPRD IDPRODUTO, 
									0 SALDO, 
									0 M1, 
									SUM(I.QUANTIDADE) M2, 
									0 M3, 
									0 INV_E, 
									0 INV_S, 
									0 MINIMO
								FROM tprd P, TMOV T, TITMMOV I
								WHERE T.CODCOLIGADA = I.CODCOLIGADA 
									AND T.IDMOV = I.IDMOV
									AND I.CODCOLIGADA = P.CODCOLIGADA 
									AND I.IDPRD = P.IDPRD            
									AND T.CODTMV = '1.1.51' 
									AND RIGHT(CONVERT(VARCHAR(10), T.DATAEMISSAO, 103), 7) =  right(convert(varchar(10),DATEADD(month,-2,GETDATE()),103),7)
								GROUP BY i.codcoligada, i.codfilial, P.IDPRD


								UNION ALL

								SELECT 
									i.codcoligada,
									i.codfilial,
									P.IDPRD IDPRODUTO, 
									0 SALDO, 
									0 M1, 
									0 M2, 
									SUM(I.QUANTIDADE) M3, 
									0 INV_E, 
									0 INV_S, 
									0 MINIMO

								FROM tprd P, TMOV T, TITMMOV I

								WHERE T.CODCOLIGADA = I.CODCOLIGADA 
									AND T.IDMOV = I.IDMOV
									AND I.CODCOLIGADA = P.CODCOLIGADA 
									AND I.IDPRD = P.IDPRD
									AND T.CODTMV = '1.1.51' 
									AND RIGHT(CONVERT(VARCHAR(10), T.DATAEMISSAO, 103), 7) =  right(convert(varchar(10),DATEADD(month,-1,GETDATE()),103),7)

								GROUP BY i.codcoligada, i.codfilial, P.IDPRD

								 ) U          
								
						

							group by u.codcoligada,
							u.codfilial,
							u.IDPRODUTO

					

                    ) mov_ultimos_meses


                    WHERE SALDO_DO_ITEM.RANK_UNIDADE_CONTROLE = 1
                        AND SALDO_DO_ITEM.CODCOLIGADA = mov_ultimos_meses.CODCOLIGADA   
                        AND SALDO_DO_ITEM.CODFILIAL = mov_ultimos_meses.CODFILIAL
                        AND SALDO_DO_ITEM.IDPRD =  mov_ultimos_meses.IDPRODUTO 
						AND SALDO_DO_ITEM.CODCOLIGADA = 1
						AND SALDO_DO_ITEM.CODFILIAL = 1
                        AND (SALDO_DO_ITEM.SALDO_QTDE/NULLIF(mov_ultimos_meses.MEDIA_3_MESES,0)) < 0.75
                    
                    ORDER BY PERCENTUAL ASC
                    
                    """,())
    
    
    dados = cursor.fetchall()     
    print(dados)  
    
    return render_template('painel.html', dados=dados)# codcoligadafilial=codcoligadafilial, grupo=grupo)

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

#rotas de espelho
###########################

#rotas das aprovações
@app.route('/aprovacoes',methods=['GET','POST'])
def dados_aprovacoes():      
        
    data_inicial = request.form.get('datainicial')
    data_final = request.form.get('datafinal')
    tipo = request.form.get('tipo')
    nummv = request.form.get('nummv')#para pesquisa do numero do movimento
    codcoligadafilial = request.form.get('codcoligadafilial')    
  
    
    if data_inicial and data_final:
        datainicial = datetime.strptime(data_inicial, '%Y-%m-%d')
        datafinal = datetime.strptime(data_final, '%Y-%m-%d')     
   
    else:
        # Defina um valor padrão ou manipule a lógica para quando as datas não são fornecidas
        datainicial = None
        datafinal = None
        
        
    print('Gabriel')
    print(nummv,datainicial, datafinal,codcoligadafilial)
    #mantive a condição para caso  não seja digitada a data mas o numero do movmento, OU SÓ o moviemnto e a data sim, mas não será usado filtros específicos assim, somente
    # e se sc/oc. coligada/filial e data inicial e final. Futuramente precisarei eliminar as condições
    if not nummv:
        query = cursor.execute("""                            
                            
                            DECLARE @DATAINICIAL AS DATeTIME;
                            DECLARE @DATAFINAL AS DATETIME; 
                            DECLARE @TIPO VARCHAR(20);
                            DECLARE @CODCOLIGADAFILIAL VARCHAR(30);
                         
                                                        
                            SET @DATAINICIAL = ?;
                            SET @DATAFINAL = ?;
                            SET @TIPO = ?;
                            SET @CODCOLIGADAFILIAL = ?
                                                  
                            
                                    
                                                    SELECT CONCAT(T.CODCOLIGADA,'-',T.CODFILIAL) CODCOLIGADAFILIAL,  
                            CASE 
                                WHEN T.CODTMV = '1.1.06' THEN 'Solicitacao'
                                WHEN T.CODTMV = '1.1.11' THEN 'Ordem'
                            END AS Tipo,
                            T.NOMEPRODUTO,
                            T.NATUREZA,
                            T.VALORITEM,
                            T.QUANTIDADEITEM,
                            T.TOTALITEM,
                            T.NUMEROMOV,
                            T.CENTROCUSTO,
                            CONVERT(DATE, T.DATAEMISSAO) AS DATAEMISSAO,
                            
                            /*CASE 
                                WHEN T.USUARIODESAPROVA IS NULL THEN 'SIM'                                                         
                                WHEN T.USUARIODESAPROVA IS NOT NULL THEN 'NÃO'
                                ELSE 'N/A'
                            END AS 'MovAprovado',*/
                            
                            CASE 
                                WHEN T.Aprovado = 'SIM' THEN T.QuemAprovou
                                WHEN T.Aprovado = 'NÃO' THEN ''
                                ELSE ''
                            END AS QuemAprovou,

                            T.Aprovado AS 'Aprovado',

                            T.TIPOAPROVACAO,
                                CASE WHEN T.STATUS = 'N' THEN 'Normal'
                                    WHEN T.STATUS = 'R' THEN 'Não Processado'
                                    WHEN T.STATUS = 'A' THEN 'A Faturar'
                                    WHEN T.STATUS = 'G' THEN 'Parcialmente Recebido'
                                    WHEN  T.STATUS ='F' THEN 'Faturado'
                                    WHEN T.STATUS = 'P' THEN 'Parcialmente Quitado'
                                    WHEN T.STATUS ='Q' THEN 'Quitado'
                                    WHEN  T.STATUS = 'C' THEN 'Cancelado'
                                    WHEN  T.STATUS = 'D' THEN 'Perda'
                                    WHEN T.STATUS = 'I' THEN 'Inativo'
                                    WHEN T.STATUS = 'B' THEN 'Baixado'
                                    WHEN T.STATUS = 'L' THEN 'Liberado'
                                    WHEN  T.STATUS = 'U' THEN 'Em Faturamento' END 
                                                                            STATUS,

                            CASE 
                                WHEN T.QuemDesaprovou IS NOT NULL THEN T.QuemDesaprovou
                                WHEN T.QuemDesaprovou IS NULL THEN ''
                                ELSE ''
                            END QuemDesaprovou, 
                            T.RN

                        FROM 

                        (
                        SELECT  
                                D.SEQUENCIAL, 
                                I.NSEQITMMOV,
                                A.CODCOLIGADA,
                                A.CODFILIAL,
                                A.STATUS,
                                A.IDMOV, 
                                A.CODTMV,
                                CONCAT(G.CODCCUSTO,'-',G.NOME) CENTROCUSTO,
                                CONCAT(O.CODTBORCAMENTO,'-',O.DESCRICAO) AS NATUREZA,
                                CONVERT(DATE, A.DATAEMISSAO) AS DATAEMISSAO,
                                A.NUMEROMOV, 
                                D.CODUSUARIO AS QuemAprovou, 
                                I.IDPRD,
                                I.PRECOUNITARIO VALORITEM,
                                I.QUANTIDADE QUANTIDADEITEM,
                                (I.QUANTIDADE*I.PRECOUNITARIO) TOTALITEM,                             
                                PRODUTO.NOMEFANTASIA AS NOMEPRODUTO,
                                D.USUARIODESAPROVA AS QuemDesaprovou, 
                                D.TIPOAPROVACAO,
                                D.DATADESAPROVA,
                                CASE 
                                    WHEN D.CODUSUARIO IS NULL OR D.USUARIODESAPROVA IS NOT NULL THEN 'PENDENTE' 
                                    WHEN D.CODUSUARIO IS NOT NULL AND D.USUARIODESAPROVA  IS NULL THEN 'SIM'
                                    ELSE 'N/A'
                                END AS 'Aprovado',
                                RANK() OVER(PARTITION BY A.IDMOV ORDER BY D.SEQUENCIAL DESC) AS RN
                            FROM 
                                tmov A
                            LEFT JOIN 
                                TITMMOV I ON A.CODCOLIGADA = I.CODCOLIGADA AND A.IDMOV = I.IDMOV 
                            LEFT JOIN 
                                TPRODUTO PRODUTO ON I.IDPRD = PRODUTO.IDPRD 
                            LEFT JOIN 
                                TMOVAPROVA D ON A.CODCOLIGADA = D.CODCOLIGADA AND A.IDMOV = D.IDMOV AND  I.NSEQITMMOV = D.NSEQITMMOV
                            LEFT JOIN 
                                TTBORCAMENTO O ON I.CODTBORCAMENTO = O.CODTBORCAMENTO                            
							LEFT JOIN GCCUSTO G
							    ON I.CODCOLIGADA = G.CODCOLIGADA AND I.CODCCUSTO = G.CODCCUSTO 
                                                                                               
                        ) T

                        WHERE  (T.CODTMV = '1.1.06'
                            OR T.CODTMV = '1.1.11')
                            
                            AND (
                                T.DATAEMISSAO BETWEEN @DATAINICIAL AND @DATAFINAL

                                )
                                
                            AND T.CODTMV = @TIPO
                            AND T.CODCOLIGADA = SUBSTRING(@CODCOLIGADAFILIAL,1,1)
                            AND T.CODFILIAL  = SUBSTRING(@CODCOLIGADAFILIAL,3,1)
        
                            AND
        
                            T.RN = (
                                SELECT MIN(RN) 

                                FROM 
                                (
                                    SELECT 
                                        RANK() OVER(PARTITION BY A.IDMOV ORDER BY D.SEQUENCIAL DESC) AS RN, produto.NOMEFANTASIA  
                                    FROM 
                                        tmov A
                                
                                    LEFT JOIN 
                                        TITMMOV I ON A.CODCOLIGADA = I.CODCOLIGADA AND A.IDMOV = I.IDMOV
                                    LEFT JOIN 
                                        TPRODUTO PRODUTO ON I.IDPRD = PRODUTO.IDPRD
                                    LEFT JOIN 
                                        TMOVAPROVA D ON A.CODCOLIGADA = D.CODCOLIGADA AND A.IDMOV = D.IDMOV and I.NSEQITMMOV = D.NSEQITMMOV
                                    WHERE 
                                    
                                        A.IDMOV = T.IDMOV
                                    and a.codcoligada = t.codcoligada
                                ) AS Subquery
                            )

                        GROUP BY  
                            T.CODCOLIGADA,
                            T.CODFILIAL,
                            T.CODTMV, 
                            T.NOMEPRODUTO,
                            T.NUMEROMOV,
                            T.QUANTIDADEITEM,
                            T.TOTALITEM,
                            T.VALORITEM,
                            T.NATUREZA,
                            T.CENTROCUSTO,
                            T.DATAEMISSAO,
                            T.QuemDesaprovou,
                            T.Aprovado,
                            T.QuemAprovou,
                            T.TIPOAPROVACAO,
                            T.STATUS,
                            T.DATADESAPROVA,
                            T.RN
                            
                        ORDER BY T.NUMEROMOV,
                                T.NOMEPRODUTO

                            """,(datainicial,datafinal,tipo,codcoligadafilial))
    
    elif not datainicial and not datafinal:       
        
        
        datainicial = datetime.now() 
        datafinal   = datetime.now() - timedelta (days=210)
        
      
        
        query = cursor.execute("""
                            
                            
                            DECLARE @DATAINICIAL AS DATeTIME;
                            DECLARE @DATAFINAL AS DATETIME; 
                            DECLARE @TIPO VARCHAR(20);
                            DECLARE @NUMMV VARCHAR(20);
                            DECLARE @CODCOLIGADAFILIAL VARCHAR(30);
                                                        
                            SET @DATAINICIAL = '2020-01-01 00:00:00';
                            SET @DATAFINAL = '2027-01-01 00:00:00';
                            SET @TIPO = ?;
                            set @nummv = ?
                            SET @CODCOLIGADAFILIAL = ?
                                                  
                            
                                    
                                                    SELECT   CONCAT(T.CODCOLIGADA,'-',T.CODFILIAL) CODCOLIGADAFILIAL, 
                            CASE 
                                WHEN T.CODTMV = '1.1.06' THEN 'Solicitacao'
                                WHEN T.CODTMV = '1.1.11' THEN 'Ordem'
                            END AS Tipo,
                            T.NOMEPRODUTO,
                            T.NATUREZA,
                            T.VALORITEM,
                            T.QUANTIDADEITEM,
                            T.TOTALITEM,
                            T.NUMEROMOV,
                            T.CENTROCUSTO,
                            CONVERT(DATE, T.DATAEMISSAO) AS DATAEMISSAO,
                            
                            /*CASE 
                                WHEN T.USUARIODESAPROVA IS NULL THEN 'SIM'                                                         
                                WHEN T.USUARIODESAPROVA IS NOT NULL THEN 'NÃO'
                                ELSE 'N/A'
                            END AS 'MovAprovado',*/
                            
                            CASE 
                                WHEN T.Aprovado = 'SIM' THEN T.QuemAprovou
                                WHEN T.Aprovado = 'NÃO' THEN ''
                                ELSE ''
                            END AS QuemAprovou,

                            T.Aprovado AS 'Aprovado',

                            T.TIPOAPROVACAO,
                                CASE WHEN T.STATUS = 'N' THEN 'Normal'
                                    WHEN T.STATUS = 'R' THEN 'Não Processado'
                                    WHEN T.STATUS = 'A' THEN 'A Faturar'
                                    WHEN  T.STATUS ='F' THEN 'Faturado'
                                    WHEN T.STATUS = 'P' THEN 'Parcialmente Quitado'
                                    WHEN T.STATUS ='Q' THEN 'Quitado'
                                    WHEN  T.STATUS = 'C' THEN 'Cancelado'
                                    WHEN  T.STATUS = 'D' THEN 'Perda'
                                    WHEN T.STATUS = 'I' THEN 'Inativo'
                                    WHEN T.STATUS = 'B' THEN 'Baixado'
                                    WHEN T.STATUS = 'L' THEN 'Liberado'
                                    WHEN  T.STATUS = 'U' THEN 'Em Faturamento' END 
                                                                            STATUS,

                            CASE 
                                WHEN T.QuemDesaprovou IS NOT NULL THEN T.QuemDesaprovou
                                WHEN T.QuemDesaprovou IS NULL THEN ''
                            END QuemDesaprovou, 
                            T.RN

                        FROM 

                        (
                        SELECT  
                                D.SEQUENCIAL, 
                                I.NSEQITMMOV,
                                A.CODCOLIGADA,
                                A.CODFILIAL,
                                A.STATUS,
                                A.IDMOV, 
                                A.CODTMV,
                                CONCAT(G.CODCCUSTO,'-',G.NOME) CENTROCUSTO,
                                CONCAT(O.CODTBORCAMENTO,'-',O.DESCRICAO) AS NATUREZA,
                                CONVERT(DATE, A.DATAEMISSAO) AS DATAEMISSAO,
                                A.NUMEROMOV, 
                                D.CODUSUARIO AS QuemAprovou, 
                                I.IDPRD,
                                I.PRECOUNITARIO VALORITEM,
                                I.QUANTIDADE QUANTIDADEITEM,
                                (I.QUANTIDADE*I.PRECOUNITARIO) TOTALITEM,
                                PRODUTO.NOMEFANTASIA AS NOMEPRODUTO,
                                D.USUARIODESAPROVA AS QuemDesaprovou, 
                                D.TIPOAPROVACAO,
                                D.DATADESAPROVA,
                                  CASE 
                                    WHEN D.CODUSUARIO IS NULL OR D.USUARIODESAPROVA IS NOT NULL THEN 'PENDENTE' 
                                    WHEN D.CODUSUARIO IS NOT NULL AND D.USUARIODESAPROVA  IS NULL THEN 'SIM'
                                    ELSE 'N/A'
                                END AS 'Aprovado',
                                RANK() OVER(PARTITION BY A.IDMOV ORDER BY D.SEQUENCIAL DESC) AS RN
                            FROM 
                                tmov A
                            LEFT JOIN 
                                TITMMOV I ON A.CODCOLIGADA = I.CODCOLIGADA AND A.IDMOV = I.IDMOV 
                            LEFT JOIN 
                                TPRODUTO PRODUTO ON I.IDPRD = PRODUTO.IDPRD 
                            LEFT JOIN 
                                TMOVAPROVA D ON A.CODCOLIGADA = D.CODCOLIGADA AND A.IDMOV = D.IDMOV AND  I.NSEQITMMOV = D.NSEQITMMOV
                            LEFT JOIN 
                                TTBORCAMENTO O ON I.CODTBORCAMENTO = O.CODTBORCAMENTO
                             LEFT JOIN GCCUSTO G
							    ON I.CODCOLIGADA = G.CODCOLIGADA AND I.CODCCUSTO = G.CODCCUSTO                    
                            
                            
                        ) T

                        WHERE  (T.CODTMV = '1.1.06'
                            OR T.CODTMV = '1.1.11')
                            
                            AND (
                                T.DATAEMISSAO BETWEEN @DATAINICIAL AND @DATAFINAL

                                )
                                
                            AND T.CODTMV = @TIPO
                            AND T.NUMEROMOV = @NUMMV
                            AND T.CODCOLIGADA = SUBSTRING(@CODCOLIGADAFILIAL,1,1)
                            AND T.CODFILIAL  = SUBSTRING(@CODCOLIGADAFILIAL,3,1)
                           
        
                            AND
        
                            T.RN = (
                                SELECT MIN(RN) 

                                FROM 
                                (
                                    SELECT 
                                        RANK() OVER(PARTITION BY A.IDMOV ORDER BY D.SEQUENCIAL DESC) AS RN, produto.NOMEFANTASIA  
                                    FROM 
                                        tmov A
                                
                                    LEFT JOIN 
                                        TITMMOV I ON A.CODCOLIGADA = I.CODCOLIGADA AND A.IDMOV = I.IDMOV
                                    LEFT JOIN 
                                        TPRODUTO PRODUTO ON I.IDPRD = PRODUTO.IDPRD
                                    LEFT JOIN 
                                        TMOVAPROVA D ON A.CODCOLIGADA = D.CODCOLIGADA AND A.IDMOV = D.IDMOV and I.NSEQITMMOV = D.NSEQITMMOV
                                    WHERE 
                                    
                                         A.IDMOV = T.IDMOV
                                    and a.codcoligada = t.codcoligada
                                ) AS Subquery
                            )

                        GROUP BY  
                            T.CODCOLIGADA,
                            T.CODFILIAL,
                            T.CODTMV, 
                            T.NOMEPRODUTO,
                            T.NUMEROMOV,
                            T.TOTALITEM,
                            T.VALORITEM,
                            T.QUANTIDADEITEM,                           
                            T.CENTROCUSTO,
                            T.NATUREZA,
                            T.DATAEMISSAO,
                            T.QuemDesaprovou,
                            T.Aprovado,
                            T.QuemAprovou,
                            T.TIPOAPROVACAO,
                            T.STATUS,
                            T.DATADESAPROVA,
                            T.RN
                            
                        ORDER BY T.NUMEROMOV,
                                T.NOMEPRODUTO

                            """,(tipo,nummv,codcoligadafilial))
    else:
        query = cursor.execute("""
                            
                            
                            DECLARE @DATAINICIAL AS DATeTIME;
                            DECLARE @DATAFINAL AS DATETIME; 
                            DECLARE @TIPO VARCHAR(20);
                            DECLARE @NUMMV VARCHAR(20);
                            DECLARE @CODCOLIGADAFILIAL VARCHAR(30);
                                                        
                            SET @DATAINICIAL = ?;
                            SET @DATAFINAL = ?;
                            SET @TIPO = ?;
                            set @NUMMV = ?
                            SET @CODCOLIGADAFILIAL = ?
                                                  
                            
                                    
                                                    SELECT    CONCAT(T.CODCOLIGADA,'-',T.CODFILIAL) CODCOLIGADAFILIAL,
                            CASE 
                                WHEN T.CODTMV = '1.1.06' THEN 'Solicitacao'
                                WHEN T.CODTMV = '1.1.11' THEN 'Ordem'
                            END AS Tipo,
                            T.NOMEPRODUTO,
                            T.NATUREZA,
                            T.VALORITEM,
                            T.QUANTIDADEITEM,
                            T.TOTALITEM,
                            T.NUMEROMOV,
                            T.CENTROCUSTO,
                            CONVERT(DATE, T.DATAEMISSAO) AS DATAEMISSAO,
                            
                            /*CASE 
                                WHEN T.USUARIODESAPROVA IS NULL THEN 'SIM'                                                         
                                WHEN T.USUARIODESAPROVA IS NOT NULL THEN 'NÃO'
                                ELSE 'N/A'
                            END AS 'MovAprovado',*/
                            
                            CASE 
                                WHEN T.Aprovado = 'SIM' THEN T.QuemAprovou
                                WHEN T.Aprovado = 'NÃO' THEN ''
                            END AS QuemAprovou,

                            T.Aprovado AS 'Aprovado',

                            T.TIPOAPROVACAO,
                                CASE WHEN T.STATUS = 'N' THEN 'Normal'
                                    WHEN T.STATUS = 'R' THEN 'Não Processado'
                                    WHEN T.STATUS = 'G' THEN 'Parcialmente Recebido'
                                    WHEN T.STATUS = 'A' THEN 'A Faturar'
                                    WHEN  T.STATUS ='F' THEN 'Faturado'
                                    WHEN T.STATUS = 'P' THEN 'Parcialmente Quitado'
                                    WHEN T.STATUS ='Q' THEN 'Quitado'
                                    WHEN  T.STATUS = 'C' THEN 'Cancelado'
                                    WHEN  T.STATUS = 'D' THEN 'Perda'
                                    WHEN T.STATUS = 'I' THEN 'Inativo'
                                    WHEN T.STATUS = 'B' THEN 'Baixado'
                                    WHEN T.STATUS = 'L' THEN 'Liberado'
                                    WHEN  T.STATUS = 'U' THEN 'Em Faturamento' END 
                                                                            STATUS,

                            CASE 
                                WHEN T.QuemDesaprovou IS NOT NULL THEN T.QuemDesaprovou
                                WHEN T.QuemDesaprovou IS NULL THEN ''
                            END QuemDesaprovou, 
                            T.RN

                        FROM 

                        (
                        SELECT  
                                D.SEQUENCIAL, 
                                I.NSEQITMMOV,
                                A.CODCOLIGADA,
                                A.CODFILIAL,
                                A.STATUS,
                                A.IDMOV, 
                                A.CODTMV,
                                CONCAT(G.CODCCUSTO,'-',G.NOME) CENTROCUSTO,
                                CONCAT(O.CODTBORCAMENTO,'-',O.DESCRICAO) AS NATUREZA,
                                CONVERT(DATE, A.DATAEMISSAO) AS DATAEMISSAO,
                                A.NUMEROMOV, 
                                D.CODUSUARIO AS QuemAprovou, 
                                I.IDPRD,
                                I.PRECOUNITARIO VALORITEM,
                                I.QUANTIDADE QUANTIDADEITEM,
                                (I.QUANTIDADE*I.PRECOUNITARIO) TOTALITEM,
                                PRODUTO.NOMEFANTASIA AS NOMEPRODUTO,
                                D.USUARIODESAPROVA AS QuemDesaprovou, 
                                D.TIPOAPROVACAO,
                                D.DATADESAPROVA,
                               CASE 
                                    WHEN D.CODUSUARIO IS NULL OR D.USUARIODESAPROVA IS NOT NULL THEN 'PENDENTE' 
                                    WHEN D.CODUSUARIO IS NOT NULL AND D.USUARIODESAPROVA  IS NULL THEN 'SIM'
                                    ELSE 'N/A'
                                END AS 'Aprovado',
                                RANK() OVER(PARTITION BY A.IDMOV ORDER BY D.SEQUENCIAL DESC) AS RN
                            FROM 
                                tmov A
                            LEFT JOIN 
                                TITMMOV I ON A.CODCOLIGADA = I.CODCOLIGADA AND A.IDMOV = I.IDMOV 
                            LEFT JOIN 
                                TPRODUTO PRODUTO ON I.IDPRD = PRODUTO.IDPRD 
                            LEFT JOIN 
                                TMOVAPROVA D ON A.CODCOLIGADA = D.CODCOLIGADA AND A.IDMOV = D.IDMOV AND  I.NSEQITMMOV = D.NSEQITMMOV
                            LEFT JOIN 
                                TTBORCAMENTO O ON I.CODTBORCAMENTO = O.CODTBORCAMENTO
                            LEFT JOIN GCCUSTO G
							    ON I.CODCOLIGADA = G.CODCOLIGADA AND I.CODCCUSTO = G.CODCCUSTO                                                 
                            
                            
                        ) T

                        WHERE  (T.CODTMV = '1.1.06'
                            OR T.CODTMV = '1.1.11')
                            
                            AND (
                                T.DATAEMISSAO BETWEEN @DATAINICIAL AND @DATAFINAL

                                )
                                
                            AND T.CODTMV = @TIPO
                            and T.NUMEROMOV = @NUMMV
                            AND T.CODCOLIGADA = SUBSTRING(@CODCOLIGADAFILIAL,1,1)
                            AND T.CODFILIAL  = SUBSTRING(@CODCOLIGADAFILIAL,3,1)
                            
                           
        
                            AND
        
                            T.RN = (
                                SELECT MIN(RN) 

                                FROM 
                                (
                                    SELECT 
                                        RANK() OVER(PARTITION BY A.IDMOV ORDER BY D.SEQUENCIAL DESC) AS RN, produto.NOMEFANTASIA  
                                    FROM 
                                        tmov A
                                
                                    LEFT JOIN 
                                        TITMMOV I ON A.CODCOLIGADA = I.CODCOLIGADA AND A.IDMOV = I.IDMOV
                                    LEFT JOIN 
                                        TPRODUTO PRODUTO ON I.IDPRD = PRODUTO.IDPRD
                                    LEFT JOIN 
                                        TMOVAPROVA D ON A.CODCOLIGADA = D.CODCOLIGADA AND A.IDMOV = D.IDMOV and I.NSEQITMMOV = D.NSEQITMMOV
                                    WHERE 
                                    
                                        A.IDMOV = T.IDMOV
                                    and a.codcoligada = t.codcoligada
                                ) AS Subquery
                            )

                        GROUP BY  
                            T.CODCOLIGADA,
                            T.CODFILIAL,
                            T.CODTMV, 
                            T.NOMEPRODUTO,
                            T.NUMEROMOV,
                            T.TOTALITEM,
                            T.QUANTIDADEITEM,
                            T.VALORITEM,
                            T.NATUREZA,
                            T.CENTROCUSTO,
                            T.DATAEMISSAO,
                            T.QuemDesaprovou,
                            T.Aprovado,
                            T.QuemAprovou,
                            T.TIPOAPROVACAO,
                            T.STATUS,
                            T.DATADESAPROVA,
                            T.RN
                            
                        ORDER BY T.NUMEROMOV,
                                T.NOMEPRODUTO

                            """,(datainicial,datafinal,tipo,nummv,codcoligadafilial))
        
    
    dados = query.fetchall()
    
    print(datainicial)
    print('-----------')
    print(datafinal)
    print(nummv)
    print(codcoligadafilial)
    
    return render_template('aprovacoes.html',dados=dados, tipo=tipo, datainicial=datainicial,datafinal=datafinal, nummv=nummv)



if __name__ == '__main__':
    app.run(debug=True)